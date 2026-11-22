"""Мінімізація кількості переказів (жадібний алгоритм)."""


def minimize_transfers(balances):
    """Повертає список (боржник, кредитор, сума); переказів не більше n − 1."""
    if sum(balances.values()) != 0:
        raise ValueError("Сума балансів має дорівнювати нулю")
    debtors = sorted([[-b, n] for n, b in balances.items() if b < 0], reverse=True)
    creditors = sorted([[b, n] for n, b in balances.items() if b > 0], reverse=True)
    transfers = []
    i = j = 0
    while i < len(debtors) and j < len(creditors):
        pay = min(debtors[i][0], creditors[j][0])
        transfers.append((debtors[i][1], creditors[j][1], pay))
        debtors[i][0] -= pay
        creditors[j][0] -= pay
        i += debtors[i][0] == 0
        j += creditors[j][0] == 0
    return transfers
