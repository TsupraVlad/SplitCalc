"""Тести мінімізації переказів (SCF_08)."""
from decimal import Decimal

import pytest

from splitcalc.settlement import Transfer, minimize_transfers

D = Decimal


def apply(balances, transfers):
    result = dict(balances)
    for t in transfers:
        result[t.debtor] += t.amount
        result[t.creditor] -= t.amount
    return result


def test_example_from_proposal():
    balances = {"Андрій": D("1200"), "Богдан": D("-900"), "Василь": D("-300")}
    assert minimize_transfers(balances) == [
        Transfer("Богдан", "Андрій", D("900")),
        Transfer("Василь", "Андрій", D("300")),
    ]


def test_at_most_n_minus_1_transfers():
    balances = {"A": D("50.10"), "B": D("20"), "C": D("-30.05"), "D": D("-25.05"),
                "E": D("-15"), "F": D("0")}
    nonzero = sum(1 for b in balances.values() if b)
    assert len(minimize_transfers(balances)) <= nonzero - 1


def test_transfers_settle_all_debts():
    balances = {"A": D("100"), "B": D("-33.33"), "C": D("-33.33"), "D": D("-33.34")}
    settled = apply(balances, minimize_transfers(balances))
    assert all(v == 0 for v in settled.values())


def test_everyone_settled_no_transfers():
    assert minimize_transfers({"A": D("0"), "B": D("0")}) == []


def test_unbalanced_input_rejected():
    with pytest.raises(ValueError):
        minimize_transfers({"A": D("10"), "B": D("-5")})
