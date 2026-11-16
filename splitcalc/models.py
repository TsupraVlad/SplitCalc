"""Моделі даних SplitCalc: учасник, витрата, група."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum

CENT = Decimal("0.01")


def money(value) -> Decimal:
    """Перетворює значення на суму з двома знаками після коми."""
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


class SplitType(str, Enum):
    """Спосіб розподілу витрати між учасниками."""
    EQUAL = "equal"      # порівну
    PERCENT = "percent"  # у відсотках
    EXACT = "exact"      # у конкретних сумах


class ValidationError(ValueError):
    """Помилка перевірки введених даних."""


@dataclass
class Expense:
    """Одна витрата: хто заплатив, скільки, у якій валюті і за кого."""
    payer: str
    amount: Decimal
    currency: str
    participants: list[str]
    split_type: SplitType = SplitType.EQUAL
    shares: dict[str, Decimal] = field(default_factory=dict)
    description: str = ""
    category: str = "Інше"

    def validate(self) -> None:
        if self.amount <= 0:
            raise ValidationError("Сума витрати має бути більшою за нуль")
        if not self.participants:
            raise ValidationError("Потрібно вказати хоча б одного учасника витрати")
        if len(set(self.participants)) != len(self.participants):
            raise ValidationError("Учасники витрати повторюються")
        if self.split_type is SplitType.PERCENT:
            total = sum(self.shares.get(p, Decimal(0)) for p in self.participants)
            if total != Decimal(100):
                raise ValidationError(f"Сума відсотків має дорівнювати 100, а не {total}")
        if self.split_type is SplitType.EXACT:
            total = sum(self.shares.get(p, Decimal(0)) for p in self.participants)
            if money(total) != money(self.amount):
                raise ValidationError(
                    f"Сума часток ({money(total)}) не дорівнює сумі витрати ({money(self.amount)})"
                )

    def to_dict(self) -> dict:
        return {
            "payer": self.payer,
            "amount": str(self.amount),
            "currency": self.currency,
            "participants": list(self.participants),
            "split_type": self.split_type.value,
            "shares": {k: str(v) for k, v in self.shares.items()},
            "description": self.description,
            "category": self.category,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Expense":
        return cls(
            payer=data["payer"],
            amount=Decimal(data["amount"]),
            currency=data["currency"],
            participants=list(data["participants"]),
            split_type=SplitType(data.get("split_type", "equal")),
            shares={k: Decimal(v) for k, v in data.get("shares", {}).items()},
            description=data.get("description", ""),
            category=data.get("category", "Інше"),
        )


@dataclass
class Group:
    """Група учасників зі спільними витратами."""
    name: str
    base_currency: str = "UAH"
    members: list[str] = field(default_factory=list)
    expenses: list[Expense] = field(default_factory=list)

    def add_member(self, name: str) -> None:
        name = name.strip()
        if not name:
            raise ValidationError("Ім'я учасника не може бути порожнім")
        if name in self.members:
            raise ValidationError(f"Учасник «{name}» уже є в групі")
        self.members.append(name)

    def remove_member(self, name: str) -> None:
        if name not in self.members:
            raise ValidationError(f"Учасника «{name}» немає в групі")
        for e in self.expenses:
            if e.payer == name or name in e.participants:
                raise ValidationError(f"Учасник «{name}» бере участь у витратах — видалення неможливе")
        self.members.remove(name)

    def add_expense(self, expense: Expense) -> None:
        if expense.payer not in self.members:
            raise ValidationError(f"Платника «{expense.payer}» немає в групі")
        for p in expense.participants:
            if p not in self.members:
                raise ValidationError(f"Учасника «{p}» немає в групі")
        expense.validate()
        self.expenses.append(expense)

    def remove_expense(self, index: int) -> Expense:
        if not 0 <= index < len(self.expenses):
            raise ValidationError("Витрати з таким номером не існує")
        return self.expenses.pop(index)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "base_currency": self.base_currency,
            "members": list(self.members),
            "expenses": [e.to_dict() for e in self.expenses],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Group":
        return cls(
            name=data["name"],
            base_currency=data.get("base_currency", "UAH"),
            members=list(data.get("members", [])),
            expenses=[Expense.from_dict(e) for e in data.get("expenses", [])],
        )
