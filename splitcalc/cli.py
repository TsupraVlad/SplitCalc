"""Консольний інтерфейс SplitCalc."""
from . import storage
from .currency import RATES
from .models import Expense, Group, SplitType
from .reports import explanation_report, settlement_report

CATEGORIES = ["Житло", "Продукти", "Транспорт", "Розваги", "Інше"]


def ask_money(prompt):
    """Запитує суму, поки не буде введено додатне число; повертає копійки."""
    while True:
        try:
            value = float(input(prompt).replace(",", "."))
            if value > 0:
                return round(value * 100)
            print("  ! Сума має бути більшою за нуль")
        except ValueError:
            print("  ! Введіть число, наприклад 250 або 99.90")


def choose(prompt, options):
    for i, o in enumerate(options, 1):
        print(f"  {i}. {o}")
    while True:
        n = input(prompt)
        if n.isdigit() and 1 <= int(n) <= len(options):
            return options[int(n) - 1]
        print("  ! Немає такого номера")


def add_expense(group):
    desc = input("Опис: ")
    category = choose("Категорія: ", CATEGORIES)
    payer = choose("Хто заплатив: ", group.members)
    amount = ask_money("Сума: ")
    currency = input(f"Валюта [{group.base_currency}]: ").upper() or group.base_currency
    who = input("За кого (номери через кому, Enter — за всіх): ")
    people = [group.members[int(i) - 1] for i in who.split(",")] if who else list(group.members)
    split = choose("Розподіл: ", [SplitType.EQUAL, SplitType.PERCENT, SplitType.EXACT])
    shares = {}
    for p in people if split != SplitType.EQUAL else []:
        shares[p] = float(input(f"  Частка {p}: ").replace(",", "."))
        shares[p] = round(shares[p] * 100) if split == SplitType.EXACT else int(shares[p])
    if currency not in RATES:
        raise ValueError(f"Невідома валюта: {currency}")
    group.add_expense(Expense(payer, amount, currency, people, split, shares, desc, category))


def group_menu(group):
    while True:
        print(f"\n== {group.name} ({group.base_currency}): {', '.join(group.members) or 'немає учасників'} ==")
        print("1. Додати учасника  2. Видалити учасника  3. Додати витрату  4. Витрати\n"
              "5. Видалити витрату  6. Розрахувати  7. Пояснити баланс  8. Звіт у файл  0. Назад")
        c = input("> ")
        try:
            if c == "1":
                group.add_member(input("Ім'я: ").strip())
            elif c == "2":
                group.remove_member(choose("Кого: ", group.members))
            elif c == "3":
                add_expense(group)
            elif c == "4":
                for i, e in enumerate(group.expenses, 1):
                    print(f"  {i}. {e.description} — {e.payer}, {e.amount / 100:.2f} {e.currency}, "
                          f"{e.split_type}, за: {', '.join(e.participants)}")
            elif c == "5":
                group.expenses.pop(int(input("Номер витрати: ")) - 1)
            elif c == "6":
                print(settlement_report(group))
            elif c == "7":
                print(explanation_report(group, choose("Учасник: ", group.members)))
            elif c == "8":
                name = f"{group.name}_звіт.txt"
                open(name, "w", encoding="utf-8").write(settlement_report(group))
                print(f"Звіт збережено у файл {name}")
            elif c == "0":
                return
            storage.save_group(group)
        except (ValueError, IndexError) as err:
            print(f"  ! Помилка: {err}")


def rates_menu():
    for cur, rate in RATES.items():
        print(f"  {cur}: {rate}")
    cur = input("Валюта для зміни (Enter — назад): ").upper()
    if cur:
        RATES[cur] = float(input("Курс (грн за 1): ").replace(",", "."))


def main():
    print("SplitCalc — розподіл спільних витрат")
    while True:
        print("\n1. Нова група  2. Відкрити групу  3. Курси валют  0. Вихід")
        c = input("> ")
        if c == "1":
            group = Group(input("Назва групи: "), input("Валюта групи [UAH]: ").upper() or "UAH")
            group_menu(group)
        elif c == "2" and storage.list_groups():
            group_menu(storage.load_group(choose("Група: ", storage.list_groups())))
        elif c == "3":
            rates_menu()
        elif c == "0":
            break
