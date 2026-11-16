"""Тести збереження даних (SCF_11)."""
from decimal import Decimal

import pytest

from splitcalc.models import Expense, Group, SplitType, ValidationError
from splitcalc.storage import Storage


def test_save_and_load_group(tmp_path):
    st = Storage(tmp_path)
    g = Group("Подорож", "UAH", ["Андрій", "Богдан"])
    g.add_expense(Expense("Андрій", Decimal("150.50"), "EUR", ["Андрій", "Богдан"], SplitType.EXACT,
                          {"Андрій": Decimal("100.50"), "Богдан": Decimal("50")}, "Музей", "Розваги"))
    st.save_group(g)
    assert st.list_groups() == ["Подорож"]
    assert st.load_group("Подорож") == g


def test_load_missing_group(tmp_path):
    with pytest.raises(ValidationError):
        Storage(tmp_path).load_group("Немає такої")


def test_rates_persist(tmp_path):
    st = Storage(tmp_path)
    conv = st.load_rates()
    conv.set_rate("GBP", "52.75")
    st.save_rates(conv)
    assert Storage(tmp_path).load_rates().rates["GBP"] == Decimal("52.75")
