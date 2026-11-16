"""Модуль мінімізації кількості переказів."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Transfer:
    """Переказ від боржника до кредитора."""
    debtor: str
    creditor: str
    amount: Decimal

    def __str__(self) -> str:
        return f"{self.debtor} → {self.creditor}: {self.amount:.2f}"


def minimize_transfers(balances: dict[str, Decimal]) -> list[Transfer]:
    """Жадібний алгоритм: найбільший боржник платить найбільшому кредитору.

    Для n учасників з ненульовим балансом дає не більше ніж n − 1 переказ.
    """
    if sum(balances.values()) != 0:
        raise ValueError("Сума балансів має дорівнювати нулю")
    debtors = sorted(((-b, n) for n, b in balances.items() if b < 0), reverse=True)
    creditors = sorted(((b, n) for n, b in balances.items() if b > 0), reverse=True)
    debtors = [[a, n] for a, n in debtors]
    creditors = [[a, n] for a, n in creditors]
    transfers: list[Transfer] = []
    i = j = 0
    while i < len(debtors) and j < len(creditors):
        pay = min(debtors[i][0], creditors[j][0])
        transfers.append(Transfer(debtors[i][1], creditors[j][1], pay))
        debtors[i][0] -= pay
        creditors[j][0] -= pay
        if debtors[i][0] == 0:
            i += 1
        if creditors[j][0] == 0:
            j += 1
    return transfers
