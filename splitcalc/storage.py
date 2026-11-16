"""Модуль локального збереження даних у JSON-файлах."""
from __future__ import annotations

import json
import os
from pathlib import Path

from .currency import CurrencyConverter
from .models import Group, ValidationError


def default_data_dir() -> Path:
    env = os.environ.get("SPLITCALC_HOME")
    return Path(env) if env else Path.home() / ".splitcalc"


class Storage:
    """Зберігає групи та курси валют у теці користувача."""

    def __init__(self, data_dir: Path | None = None):
        self.data_dir = Path(data_dir) if data_dir else default_data_dir()
        self.groups_dir = self.data_dir / "groups"
        self.groups_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _safe_name(name: str) -> str:
        cleaned = "".join(c if c.isalnum() or c in " _-" else "_" for c in name).strip()
        if not cleaned:
            raise ValidationError("Некоректна назва групи")
        return cleaned

    def _group_path(self, name: str) -> Path:
        return self.groups_dir / f"{self._safe_name(name)}.json"

    def save_group(self, group: Group) -> Path:
        path = self._group_path(group.name)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(group.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)  # атомарний запис: файл не пошкодиться при збої
        return path

    def load_group(self, name: str) -> Group:
        path = self._group_path(name)
        if not path.exists():
            raise ValidationError(f"Групу «{name}» не знайдено")
        try:
            return Group.from_dict(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, KeyError) as exc:
            raise ValidationError(f"Файл групи «{name}» пошкоджено") from exc

    def list_groups(self) -> list[str]:
        names = []
        for p in sorted(self.groups_dir.glob("*.json")):
            try:
                names.append(json.loads(p.read_text(encoding="utf-8"))["name"])
            except (json.JSONDecodeError, KeyError):
                continue
        return names

    def delete_group(self, name: str) -> None:
        path = self._group_path(name)
        if path.exists():
            path.unlink()

    def save_rates(self, converter: CurrencyConverter) -> None:
        (self.data_dir / "rates.json").write_text(
            json.dumps(converter.to_dict(), indent=2), encoding="utf-8"
        )

    def load_rates(self) -> CurrencyConverter:
        path = self.data_dir / "rates.json"
        if path.exists():
            try:
                return CurrencyConverter.from_dict(json.loads(path.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, ArithmeticError):
                pass
        return CurrencyConverter()
