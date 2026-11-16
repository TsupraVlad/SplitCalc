"""Консольний інтерфейс SplitCalc (українською мовою)."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from . import __version__
from .balances import compute_balances
from .currency import CurrencyConverter
from .models import Expense, Group, SplitType, ValidationError
from .settlement import minimize_transfers
from .storage import Storage

CATEGORIES = ["Житло", "Продукти", "Транспорт", "Розваги", "Кафе", "Інше"]


class App:
    """Головний цикл застосунку. Функції вводу/виводу можна підмінити для тестів."""

    def __init__(self, storage: Storage | None = None, input_fn=input, output_fn=print):
        self.storage = storage or Storage()
        self.converter: CurrencyConverter = self.storage.load_rates()
        self.input = input_fn
        self.print = output_fn

    # ---------- допоміжні методи вводу ----------
    def ask(self, prompt: str) -> str:
        return self.input(prompt).strip()

    def ask_amount(self, prompt: str) -> Decimal:
        while True:
            raw = self.ask(prompt).replace(",", ".")
            try:
                value = Decimal(raw)
            except InvalidOperation:
                self.print("  ! Введіть число, наприклад 250 або 99.90")
                continue
            if value <= 0:
                self.print("  ! Сума має бути більшою за нуль")
                continue
            return value

    def choose(self, prompt: str, options: list[str]) -> str:
        for i, opt in enumerate(options, 1):
            self.print(f"  {i}. {opt}")
        while True:
            raw = self.ask(prompt)
            if raw.isdigit() and 1 <= int(raw) <= len(options):
                return options[int(raw) - 1]
            self.print(f"  ! Введіть номер від 1 до {len(options)}")

    # ---------- головне меню ----------
    def run(self) -> None:
        self.print(f"SplitCalc {__version__} — розподіл спільних витрат")
        while True:
            self.print("\nГОЛОВНЕ МЕНЮ\n  1. Створити групу\n  2. Відкрити групу\n"
                       "  3. Список груп\n  4. Курси валют\n  0. Вихід")
            choice = self.ask("Ваш вибір: ")
            if choice == "1":
                self.create_group()
            elif choice == "2":
                self.open_group()
            elif choice == "3":
                self.list_groups()
            elif choice == "4":
                self.rates_menu()
            elif choice == "0":
                self.print("До побачення!")
                return
            else:
                self.print("  ! Невідомий пункт меню")

    def create_group(self) -> None:
        name = self.ask("Назва групи: ")
        if not name:
            self.print("  ! Назва не може бути порожньою")
            return
        if name in self.storage.list_groups():
            self.print(f"  ! Група «{name}» уже існує")
            return
        cur = self.ask("Основна валюта [UAH]: ").upper() or "UAH"
        if not self.converter.supports(cur):
            self.print(f"  ! Невідома валюта {cur}. Додайте її в меню «Курси валют»")
            return
        group = Group(name=name, base_currency=cur)
        self.storage.save_group(group)
        self.print(f"Групу «{name}» створено.")
        self.group_menu(group)

    def open_group(self) -> None:
        names = self.storage.list_groups()
        if not names:
            self.print("  Груп ще немає. Створіть нову.")
            return
        name = self.choose("Номер групи: ", names)
        self.group_menu(self.storage.load_group(name))

    def list_groups(self) -> None:
        names = self.storage.list_groups()
        self.print("Збережені групи:" if names else "  Груп ще немає.")
        for n in names:
            self.print(f"  • {n}")

    def rates_menu(self) -> None:
        self.print("Курси валют (грн за 1 одиницю):")
        for code, rate in self.converter.rates.items():
            self.print(f"  {code}: {rate}")
        code = self.ask("Код валюти для зміни (Enter — назад): ").upper()
        if not code:
            return
        try:
            self.converter.set_rate(code, self.ask_amount(f"Новий курс {code}: "))
            self.storage.save_rates(self.converter)
            self.print("Курс збережено.")
        except ValidationError as exc:
            self.print(f"  ! {exc}")

    # ---------- меню групи ----------
    def group_menu(self, group: Group) -> None:
        actions = {
            "1": self.add_member, "2": self.remove_member, "3": self.add_expense,
            "4": self.show_expenses, "5": self.remove_expense, "6": self.show_report,
        }
        while True:
            self.print(f"\nГРУПА «{group.name}» ({group.base_currency}) — учасників: "
                       f"{len(group.members)}, витрат: {len(group.expenses)}\n"
                       "  1. Додати учасника\n  2. Видалити учасника\n  3. Додати витрату\n"
                       "  4. Переглянути витрати\n  5. Видалити витрату\n"
                       "  6. Розрахувати (баланси та перекази)\n  0. Назад")
            choice = self.ask("Ваш вибір: ")
            if choice == "0":
                return
            action = actions.get(choice)
            if action is None:
                self.print("  ! Невідомий пункт меню")
                continue
            try:
                if action(group):
                    self.storage.save_group(group)
            except ValidationError as exc:
                self.print(f"  ! {exc}")

    def add_member(self, group: Group) -> bool:
        group.add_member(self.ask("Ім'я учасника: "))
        self.print("Учасника додано.")
        return True

    def remove_member(self, group: Group) -> bool:
        if not group.members:
            self.print("  У групі немає учасників.")
            return False
        group.remove_member(self.choose("Кого видалити: ", group.members))
        self.print("Учасника видалено.")
        return True

    def add_expense(self, group: Group) -> bool:
        if len(group.members) < 2:
            self.print("  ! Спочатку додайте щонайменше двох учасників")
            return False
        desc = self.ask("Опис витрати: ")
        self.print("Категорія:")
        category = self.choose("Номер категорії: ", CATEGORIES)
        self.print("Хто заплатив:")
        payer = self.choose("Номер платника: ", group.members)
        amount = self.ask_amount("Сума: ")
        currency = self.ask(f"Валюта [{group.base_currency}]: ").upper() or group.base_currency
        if not self.converter.supports(currency):
            raise ValidationError(f"Невідома валюта {currency}")
        raw = self.ask("За кого (номери через кому, Enter — за всіх): ")
        if raw:
            try:
                idx = [int(x) for x in raw.replace(" ", "").split(",")]
                participants = [group.members[i - 1] for i in idx if i >= 1]
                if len(participants) != len(idx):
                    raise IndexError
            except (ValueError, IndexError):
                raise ValidationError("Некоректний перелік учасників")
        else:
            participants = list(group.members)
        self.print("Спосіб розподілу:")
        mode = self.choose("Номер способу: ", ["Порівну", "У відсотках", "У конкретних сумах"])
        split = {"Порівну": SplitType.EQUAL, "У відсотках": SplitType.PERCENT,
                 "У конкретних сумах": SplitType.EXACT}[mode]
        shares: dict[str, Decimal] = {}
        if split is not SplitType.EQUAL:
            unit = "%" if split is SplitType.PERCENT else currency
            for p in participants:
                shares[p] = self.ask_amount(f"  Частка {p} ({unit}): ")
        group.add_expense(Expense(payer, amount, currency, participants, split, shares, desc, category))
        self.print("Витрату додано.")
        return True

    def show_expenses(self, group: Group) -> bool:
        if not group.expenses:
            self.print("  Витрат ще немає.")
        for i, e in enumerate(group.expenses, 1):
            who = "всі" if set(e.participants) == set(group.members) else ", ".join(e.participants)
            self.print(f"  {i}. {e.description or '—'} [{e.category}] — {e.payer} заплатив "
                       f"{e.amount:.2f} {e.currency}, за: {who}")
        return False

    def remove_expense(self, group: Group) -> bool:
        self.show_expenses(group)
        if not group.expenses:
            return False
        raw = self.ask("Номер витрати для видалення: ")
        if not raw.isdigit():
            raise ValidationError("Введіть номер витрати")
        group.remove_expense(int(raw) - 1)
        self.print("Витрату видалено.")
        return True

    def show_report(self, group: Group) -> bool:
        if not group.expenses:
            self.print("  Витрат ще немає — розраховувати нічого.")
            return False
        cur = group.base_currency
        balances = compute_balances(group, self.converter)
        self.print("Баланси учасників:")
        for name, bal in balances.items():
            shown = f"{bal:+.2f}" if bal else f"{bal:.2f}"
            self.print(f"  {name:<12} {shown:>11} {cur}")
        transfers = minimize_transfers(balances)
        if not transfers:
            self.print("Усі учасники розрахувалися — переказів не потрібно.")
        for k, t in enumerate(transfers, 1):
            self.print(f"  {k}. {t.debtor} → {t.creditor}: {t.amount:.2f} {cur}")
        return False


def main() -> None:
    try:
        App().run()
    except (KeyboardInterrupt, EOFError):
        print("\nРоботу завершено.")
