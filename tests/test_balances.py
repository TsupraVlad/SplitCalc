"""Тести розрахунку балансів (SCF_07, SCF_09)."""
from decimal import Decimal

import pytest

from splitcalc.balances import compute_balances, explain_balance
from splitcalc.currency import CurrencyConverter
from splitcalc.models import Expense, Group, SplitType, ValidationError

D = Decimal
PEOPLE = ["Андрій", "Богдан", "Василь"]


def make_group() -> Group:
    g = Group("Подорож")
    for p in PEOPLE:
        g.add_member(p)
    return g


def proposal_group() -> Group:
    """Контрольний приклад з технічного завдання (ЛР2)."""
    g = make_group()
    g.add_expense(Expense("Андрій", D("3000"), "UAH", PEOPLE, description="Житло", category="Житло"))
    g.add_expense(Expense("Богдан", D("900"), "UAH", PEOPLE, description="Продукти", category="Продукти"))
    g.add_expense(Expense("Василь", D("1500"), "UAH", PEOPLE, description="Таксі", category="Транспорт"))
    return g


def test_example_from_proposal():
    b = compute_balances(proposal_group(), CurrencyConverter())
    assert b == {"Андрій": D("1200.00"), "Богдан": D("-900.00"), "Василь": D("-300.00")}


def test_balances_sum_to_zero():
    g = proposal_group()
    g.add_expense(Expense("Богдан", D("1000"), "UAH", ["Андрій", "Богдан"], category="Кафе"))
    assert sum(compute_balances(g, CurrencyConverter()).values()) == 0


def test_percent_split():
    g = make_group()
    g.add_expense(Expense("Андрій", D("1000"), "UAH", PEOPLE, SplitType.PERCENT,
                          {"Андрій": D("50"), "Богдан": D("30"), "Василь": D("20")}))
    b = compute_balances(g, CurrencyConverter())
    assert b == {"Андрій": D("500.00"), "Богдан": D("-300.00"), "Василь": D("-200.00")}


def test_exact_split():
    g = make_group()
    g.add_expense(Expense("Богдан", D("700"), "UAH", ["Андрій", "Богдан"], SplitType.EXACT,
                          {"Андрій": D("450"), "Богдан": D("250")}))
    b = compute_balances(g, CurrencyConverter())
    assert b == {"Андрій": D("-450.00"), "Богдан": D("450.00"), "Василь": D("0.00")}


def test_foreign_currency_converted_to_base():
    g = make_group()
    g.add_expense(Expense("Василь", D("30"), "USD", PEOPLE))  # 30 × 41.50 = 1245 грн
    b = compute_balances(g, CurrencyConverter())
    assert b["Василь"] == D("830.00")
    assert b["Андрій"] == b["Богдан"] == D("-415.00")


def test_explain_balance_matches_balance():
    g = proposal_group()
    conv = CurrencyConverter()
    balances = compute_balances(g, conv)
    for member in PEOPLE:
        lines = explain_balance(g, conv, member)
        assert sum((ln.effect for ln in lines), D("0.00")) == balances[member]


def test_invalid_percent_rejected():
    g = make_group()
    with pytest.raises(ValidationError):
        g.add_expense(Expense("Андрій", D("100"), "UAH", PEOPLE, SplitType.PERCENT,
                              {"Андрій": D("50"), "Богдан": D("30"), "Василь": D("10")}))


def test_unknown_payer_rejected():
    g = make_group()
    with pytest.raises(ValidationError):
        g.add_expense(Expense("Галина", D("100"), "UAH", PEOPLE))
