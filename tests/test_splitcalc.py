from splitcalc.balances import compute_balances
from splitcalc.models import Expense, Group, SplitType
from splitcalc.settlement import minimize_transfers


def make_group(*names):
    g = Group("Тест")
    for n in names:
        g.add_member(n)
    return g


def test_example_from_proposal():
    g = make_group("Андрій", "Богдан", "Василь")
    people = list(g.members)
    g.add_expense(Expense("Андрій", 300000, "UAH", people))
    g.add_expense(Expense("Богдан", 90000, "UAH", people))
    g.add_expense(Expense("Василь", 150000, "UAH", people))
    assert compute_balances(g) == {"Андрій": 120000, "Богдан": -90000, "Василь": -30000}


def test_transfers():
    transfers = minimize_transfers({"Андрій": 120000, "Богдан": -90000, "Василь": -30000})
    assert transfers == [("Богдан", "Андрій", 90000), ("Василь", "Андрій", 30000)]


def test_percent_split():
    g = make_group("Оля", "Петро")
    g.add_expense(Expense("Оля", 10000, "UAH", ["Оля", "Петро"], SplitType.PERCENT, {"Оля": 70, "Петро": 30}))
    assert compute_balances(g) == {"Оля": 3000, "Петро": -3000}


def test_currency():
    g = make_group("Оля", "Петро")
    g.add_expense(Expense("Оля", 1000, "EUR", ["Оля", "Петро"]))   # 10 EUR = 482 грн
    assert compute_balances(g) == {"Оля": 24100, "Петро": -24100}


def test_bug001_equal_split_100_for_3():
    g = make_group("Оля", "Петро", "Ірина")
    g.add_expense(Expense("Оля", 10000, "UAH", ["Оля", "Петро", "Ірина"]))
    b = compute_balances(g)
    assert sum(b.values()) == 0
    assert minimize_transfers(b) == [("Петро", "Оля", 3333), ("Ірина", "Оля", 3333)]
