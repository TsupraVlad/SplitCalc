"""Тести модуля звітів (SCF_09, SCF_10)."""
from decimal import Decimal

from splitcalc.currency import CurrencyConverter
from splitcalc.models import Expense, Group
from splitcalc.reports import category_stats, explanation_report, export_report, settlement_report

D = Decimal
PEOPLE = ["Андрій", "Богдан", "Василь"]


def make_group() -> Group:
    g = Group("Подорож", members=list(PEOPLE))
    g.add_expense(Expense("Андрій", D("3000"), "UAH", PEOPLE, description="Квартира", category="Житло"))
    g.add_expense(Expense("Богдан", D("900"), "UAH", PEOPLE, description="Продукти", category="Продукти"))
    g.add_expense(Expense("Василь", D("1500"), "UAH", PEOPLE, description="Таксі", category="Транспорт"))
    return g


def test_settlement_report_contains_plan():
    text = settlement_report(make_group(), CurrencyConverter())
    assert "ЗВІТ ГРУПИ «Подорож»" in text
    assert "План розрахунків (переказів: 2)" in text
    assert "Богдан → Андрій: 900.00 UAH" in text
    assert "Разом: 5400.00 UAH" in text


def test_category_stats_sorted():
    g = make_group()
    g.add_expense(Expense("Андрій", D("10"), "EUR", PEOPLE, category="Продукти"))  # 482 грн
    stats = category_stats(g, CurrencyConverter())
    assert list(stats) == ["Житло", "Транспорт", "Продукти"]
    assert stats["Продукти"] == D("1382.00")


def test_explanation_total():
    text = explanation_report(make_group(), CurrencyConverter(), "Андрій")
    assert "Квартира" in text
    assert "Підсумковий баланс: +1200.00 UAH" in text


def test_export(tmp_path):
    text = settlement_report(make_group(), CurrencyConverter())
    path = export_report(text, tmp_path / "звіт.txt")
    assert path.read_text(encoding="utf-8") == text
