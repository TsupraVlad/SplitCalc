"""Текстові звіти."""
from .balances import compute_balances, explain_balance
from .currency import convert
from .settlement import minimize_transfers


def money(kop):
    return f"{kop / 100:.2f}"


def settlement_report(group):
    cur = group.base_currency
    balances = compute_balances(group)
    lines = [f"Група «{group.name}»", "Баланси:"]
    for name, b in balances.items():
        lines.append(f"  {name:<10} {'+' if b > 0 else ''}{money(b)} {cur}")
    lines.append("Перекази:")
    for debtor, creditor, amount in minimize_transfers(balances):
        lines.append(f"  {debtor} → {creditor}: {money(amount)} {cur}")
    lines.append("За категоріями:")
    for cat, total in category_stats(group).items():
        lines.append(f"  {cat:<10} {money(total)} {cur}")
    return "\n".join(lines)


def category_stats(group):
    stats = {}
    for e in group.expenses:
        stats[e.category] = stats.get(e.category, 0) + convert(e.amount, e.currency, group.base_currency)
    return stats


def explanation_report(group, member):
    lines = [f"Баланс учасника {member}:"]
    total = 0
    for desc, paid, share in explain_balance(group, member):
        lines.append(f"  {desc:<12} сплатив {money(paid):>8}, частка {money(share):>8}")
        total += paid - share
    lines.append(f"  Разом: {money(total)} {group.base_currency}")
    return "\n".join(lines)
