"""Модуль конвертації валют (працює без інтернету, за таблицею курсів)."""
from __future__ import annotations

from decimal import Decimal

from .models import ValidationError, money

# Курси за замовчуванням: скільки гривень коштує 1 одиниця валюти.
# Користувач може змінити їх у меню «Курси валют».
DEFAULT_RATES: dict[str, Decimal] = {
    "UAH": Decimal("1"),
    "USD": Decimal("41.50"),
    "EUR": Decimal("48.20"),
    "PLN": Decimal("11.30"),
}


class CurrencyConverter:
    """Переводить суми між валютами через гривню."""

    def __init__(self, rates: dict[str, Decimal] | None = None):
        self.rates: dict[str, Decimal] = dict(DEFAULT_RATES if rates is None else rates)

    def set_rate(self, code: str, rate) -> None:
        code = code.strip().upper()
        rate = Decimal(str(rate))
        if len(code) != 3 or not code.isalpha():
            raise ValidationError("Код валюти має складатися з трьох літер, напр. USD")
        if rate <= 0:
            raise ValidationError("Курс має бути більшим за нуль")
        if code == "UAH" and rate != 1:
            raise ValidationError("Курс гривні завжди дорівнює 1")
        self.rates[code] = rate

    def supports(self, code: str) -> bool:
        return code.upper() in self.rates

    def convert(self, amount: Decimal, from_code: str, to_code: str) -> Decimal:
        from_code, to_code = from_code.upper(), to_code.upper()
        for code in (from_code, to_code):
            if code not in self.rates:
                raise ValidationError(f"Невідома валюта: {code}")
        if from_code == to_code:
            return Decimal(amount)
        in_uah = Decimal(amount) * self.rates[from_code]
        return money(in_uah / self.rates[to_code])

    def to_dict(self) -> dict:
        return {k: str(v) for k, v in self.rates.items()}

    @classmethod
    def from_dict(cls, data: dict) -> "CurrencyConverter":
        return cls({k: Decimal(v) for k, v in data.items()})
