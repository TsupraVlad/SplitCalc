"""Модуль звітів: план розрахунків, пояснення балансів, статистика за категоріями."""
from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from .balances import compute_balances, explain_balance
from .currency import CurrencyConverter
from .models import Group, money
from .settlement import minimize_transfers


def category_stats(group: Group, converter: CurrencyConverter) -> dict[str, Decimal]:
    stats: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    for e in group.expenses:
        stats[e.category] += money(converter.convert(e.amount, e.currency, group.base_currency))
    return dict(sorted(stats.items(), key=lambda kv: kv[1], reverse=True))


def settlement_report(group: Group, converter: CurrencyConverter) -> str:
    cur = group.base_currency
    balances = compute_balances(group, converter)
    transfers = minimize_transfers(balances)
    total = sum(category_stats(group, converter).values(), Decimal("0.00"))
    out = [f"ЗВІТ ГРУПИ «{group.name}»", "=" * 44]
    out.append(f"Учасників: {len(group.members)}   Витрат: {len(group.expenses)}   "
               f"Разом: {total:.2f} {cur}")
    out.append("")
    out.append("Баланси учасників:")
    for name, bal in balances.items():
        shown = f"{bal:+.2f}" if bal else f"{bal:.2f}"
        status = "отримує" if bal > 0 else ("винен" if bal < 0 else "розрахувався")
        out.append(f"  {name:<12} {shown:>11} {cur}  ({status})")
    out.append("")
    if transfers:
        out.append(f"План розрахунків (переказів: {len(transfers)}):")
        for k, t in enumerate(transfers, 1):
            out.append(f"  {k}. {t.debtor} → {t.creditor}: {t.amount:.2f} {cur}")
    else:
        out.append("Усі учасники розрахувалися — переказів не потрібно.")
    out.append("")
    out.append("Витрати за категоріями:")
    for cat, amount in category_stats(group, converter).items():
        pct = (amount / total * 100) if total else Decimal(0)
        out.append(f"  {cat:<14} {amount:>10.2f} {cur}  {pct:5.1f}%")
    return "\n".join(out)


def explanation_report(group: Group, converter: CurrencyConverter, member: str) -> str:
    cur = group.base_currency
    lines = explain_balance(group, converter, member)
    out = [f"Пояснення балансу: {member}", "-" * 44,
           f"  {'Витрата':<18}{'Сплатив':>10}{'Частка':>10}"]
    total = Decimal("0.00")
    for ln in lines:
        out.append(f"  {ln.description[:17]:<18}{ln.paid:>10.2f}{ln.share:>10.2f}")
        total += ln.effect
    out.append("-" * 44)
    out.append(f"  Підсумковий баланс: {total:+.2f} {cur}")
    return "\n".join(out)


def export_report(text: str, path: Path) -> Path:
    path = Path(path)
    path.write_text(text, encoding="utf-8")
    return path
