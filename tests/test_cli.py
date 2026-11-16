"""Наскрізні тести консольного інтерфейсу (SCF_01–SCF_04, SCF_12)."""
from decimal import Decimal

from splitcalc.cli import App
from splitcalc.storage import Storage


def run_app(tmp_path, inputs):
    feed = iter(inputs)
    out: list[str] = []
    app = App(Storage(tmp_path), input_fn=lambda _prompt: next(feed), output_fn=out.append)
    return app, out


def expense(desc, category, payer, amount):
    # опис, категорія, платник, сума, валюта (Enter), за всіх (Enter), порівну
    return ["3", desc, category, payer, amount, "", "", "1"]


def test_full_scenario(tmp_path):
    inputs = (["1", "Подорож", ""]
              + ["1", "Андрій", "1", "Богдан", "1", "Василь"]
              + expense("Квартира", "1", "1", "3000")
              + expense("Продукти", "2", "2", "900")
              + expense("Таксі", "3", "3", "1500")
              + ["6", "0", "0"])
    app, out = run_app(tmp_path, inputs)
    app.run()
    text = "\n".join(out)
    assert "+1200.00" in text
    assert "Богдан → Андрій: 900.00" in text
    assert "Василь → Андрій: 300.00" in text
    saved = Storage(tmp_path).load_group("Подорож")
    assert saved.members == ["Андрій", "Богдан", "Василь"]
    assert len(saved.expenses) == 3


def test_invalid_amount_is_reprompted(tmp_path):
    app, out = run_app(tmp_path, ["абв", "-5", "99,90"])
    assert app.ask_amount("Сума: ") == Decimal("99.90")
    assert any("Введіть число" in line for line in out)
    assert any("більшою за нуль" in line for line in out)
