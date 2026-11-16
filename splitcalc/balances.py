"""Модуль розрахунку балансів учасників."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN

from .currency import CurrencyConverter
from .models import CENT, Expense, Group, SplitType, money


def _distribute_remainder(shares: dict[str, Decimal], total: Decimal, order: list[str]) -> dict[str, Decimal]:
    """Додає копійки, що загубилися при округленні, першим учасникам за порядком.

    Гарантує, що сума часток точно дорівнює сумі витрати.
    """
    diff = money(total) - sum(shares.values())
    step = CENT if diff > 0 else -CENT
    i = 0
    while diff != 0:
        name = order[i % len(order)]
        shares[name] += step
        diff -= step
        i += 1
    return shares


def split_expense(expense: Expense, amount: Decimal) -> dict[str, Decimal]:
    """Розподіляє суму `amount` (уже в основній валюті) між учасниками витрати."""
    people = expense.participants
    if expense.split_type is SplitType.EQUAL:
        share = money(Decimal(amount) / len(people))
        return {p: share for p in people}
    elif expense.split_type is SplitType.PERCENT:
        shares = {
            p: (Decimal(amount) * expense.shares[p] / 100).quantize(CENT, rounding=ROUND_DOWN)
            for p in people
        }
    else:  # EXACT: частки задані у валюті витрати — перераховуємо пропорційно
        ratio = Decimal(amount) / expense.amount
        shares = {p: (expense.shares[p] * ratio).quantize(CENT, rounding=ROUND_DOWN) for p in people}
    return _distribute_remainder(shares, amount, people)


@dataclass
class BalanceLine:
    """Рядок пояснення: як витрата вплинула на баланс учасника."""
    description: str
    paid: Decimal
    share: Decimal

    @property
    def effect(self) -> Decimal:
        return self.paid - self.share


def compute_balances(group: Group, converter: CurrencyConverter) -> dict[str, Decimal]:
    """Баланс = сплачено учасником − його частка в усіх витратах.

    Додатний баланс — учаснику мають повернути гроші, від'ємний — учасник винен.
    """
    balances = {m: Decimal("0.00") for m in group.members}
    for e in group.expenses:
        amount = converter.convert(e.amount, e.currency, group.base_currency)
        amount = money(amount)
        balances[e.payer] += amount
        for person, share in split_expense(e, amount).items():
            balances[person] -= share
    return balances


def explain_balance(group: Group, converter: CurrencyConverter, member: str) -> list[BalanceLine]:
    """Пояснює, з яких витрат склався баланс учасника."""
    lines: list[BalanceLine] = []
    for e in group.expenses:
        if member != e.payer and member not in e.participants:
            continue
        amount = money(converter.convert(e.amount, e.currency, group.base_currency))
        paid = amount if e.payer == member else Decimal("0.00")
        share = split_expense(e, amount).get(member, Decimal("0.00"))
        title = e.description or e.category
        lines.append(BalanceLine(title, paid, share))
    return lines
