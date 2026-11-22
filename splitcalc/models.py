"""Моделі даних. Усі суми зберігаються в копійках (цілі числа)."""
from dataclasses import dataclass, field


class SplitType:
    EQUAL = "порівну"
    PERCENT = "у відсотках"
    EXACT = "у сумах"


@dataclass
class Expense:
    payer: str
    amount: int              # у копійках
    currency: str
    participants: list
    split_type: str = SplitType.EQUAL
    shares: dict = field(default_factory=dict)   # відсотки або копійки
    description: str = ""
    category: str = "Інше"


@dataclass
class Group:
    name: str
    base_currency: str = "UAH"
    members: list = field(default_factory=list)
    expenses: list = field(default_factory=list)

    def add_member(self, name):
        if not name or name in self.members:
            raise ValueError("Ім'я порожнє або вже є в групі")
        self.members.append(name)

    def remove_member(self, name):
        if any(name == e.payer or name in e.participants for e in self.expenses):
            raise ValueError("Учасник бере участь у витратах — видалення неможливе")
        self.members.remove(name)

    def add_expense(self, e):
        if e.amount <= 0:
            raise ValueError("Сума має бути більшою за нуль")
        if e.payer not in self.members or not set(e.participants) <= set(self.members):
            raise ValueError("Невідомий учасник")
        if e.split_type == SplitType.PERCENT and sum(e.shares.values()) != 100:
            raise ValueError("Сума відсотків має дорівнювати 100")
        if e.split_type == SplitType.EXACT and sum(e.shares.values()) != e.amount:
            raise ValueError("Сума часток не дорівнює сумі витрати")
        self.expenses.append(e)
