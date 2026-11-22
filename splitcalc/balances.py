"""Розрахунок балансів учасників."""
from .currency import convert
from .models import SplitType


def split_expense(e, amount):
    """Частка кожного учасника в копійках."""
    people = e.participants
    if e.split_type == SplitType.EQUAL:
        share = amount // len(people)
        return {p: share for p in people}
    if e.split_type == SplitType.PERCENT:
        shares = {p: amount * e.shares[p] // 100 for p in people}
    else:
        shares = {p: e.shares[p] * amount // e.amount for p in people}
    shares[people[0]] += amount - sum(shares.values())   # залишок копійок — першому
    return shares


def compute_balances(group):
    """Баланс = сплачено − частка. Додатний — учаснику винні, від'ємний — винен він."""
    balances = {m: 0 for m in group.members}
    for e in group.expenses:
        amount = convert(e.amount, e.currency, group.base_currency)
        balances[e.payer] += amount
        for person, share in split_expense(e, amount).items():
            balances[person] -= share
    return balances


def explain_balance(group, member):
    """Рядки (опис, сплатив, частка) для всіх витрат учасника."""
    lines = []
    for e in group.expenses:
        if member == e.payer or member in e.participants:
            amount = convert(e.amount, e.currency, group.base_currency)
            paid = amount if e.payer == member else 0
            lines.append((e.description, paid, split_expense(e, amount).get(member, 0)))
    return lines
