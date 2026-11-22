from splitcalc.models import Expense, Group
from splitcalc.balances import compute_balances

# Відтворення BUG-001: 100 грн порівну на трьох
g = Group("Піца")
for name in ["Оля", "Петро", "Ірина"]:
    g.add_member(name)
g.add_expense(Expense("Оля", 10000, "UAH", ["Оля", "Петро", "Ірина"], description="Піца"))
b = compute_balances(g)
print(b, sum(b.values()))
