"""Конвертація валют за таблицею курсів (без інтернету)."""

RATES = {"UAH": 1.0, "USD": 41.5, "EUR": 48.2, "PLN": 11.3}  # грн за 1 одиницю


def convert(amount, from_cur, to_cur, rates=RATES):
    """Переводить суму в копійках з однієї валюти в іншу."""
    if from_cur not in rates or to_cur not in rates:
        raise ValueError(f"Невідома валюта: {from_cur if from_cur not in rates else to_cur}")
    return round(amount * rates[from_cur] / rates[to_cur])
