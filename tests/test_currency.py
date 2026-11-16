"""Тести модуля конвертації валют (SCF_06)."""
from decimal import Decimal

import pytest

from splitcalc.currency import CurrencyConverter
from splitcalc.models import ValidationError


def test_convert():
    conv = CurrencyConverter()
    assert conv.convert(Decimal("100"), "USD", "UAH") == Decimal("4150.00")
    assert conv.convert(Decimal("4150"), "UAH", "USD") == Decimal("100.00")
    assert conv.convert(Decimal("10"), "EUR", "EUR") == Decimal("10")
    conv.set_rate("usd", "40")
    assert conv.convert(Decimal("2"), "USD", "UAH") == Decimal("80.00")


@pytest.mark.parametrize("code, rate", [("US", "40"), ("USD", "0"), ("UAH", "2")])
def test_invalid_rates(code, rate):
    with pytest.raises(ValidationError):
        CurrencyConverter().set_rate(code, rate)
