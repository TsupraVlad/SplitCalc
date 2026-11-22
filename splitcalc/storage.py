"""Збереження груп у JSON-файлах."""
import json
from dataclasses import asdict
from pathlib import Path

from .models import Expense, Group

DATA_DIR = Path.home() / ".splitcalc"


def save_group(group, folder=DATA_DIR):
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{group.name}.json"
    path.write_text(json.dumps(asdict(group), ensure_ascii=False, indent=2), encoding="utf-8")


def load_group(name, folder=DATA_DIR):
    data = json.loads((folder / f"{name}.json").read_text(encoding="utf-8"))
    data["expenses"] = [Expense(**e) for e in data["expenses"]]
    return Group(**data)


def list_groups(folder=DATA_DIR):
    return sorted(p.stem for p in folder.glob("*.json")) if folder.exists() else []
