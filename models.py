"""
Modelos de dados da ficha de personagem de D&D.
Este módulo é puro Python (sem dependência do Kivy), então pode ser
testado e reutilizado independentemente da interface gráfica.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Any


def modifier(score: int) -> int:
    """Calcula o modificador de um atributo a partir do valor (regra padrão de D&D)."""
    return (score - 10) // 2


def modifier_str(score: int) -> str:
    mod = modifier(score)
    return f"+{mod}" if mod >= 0 else str(mod)


@dataclass
class Attack:
    name: str = "Novo ataque"
    bonus: str = "+0"
    damage: str = "1d6"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Attack":
        return Attack(**d)


@dataclass
class InventoryItem:
    name: str = "Novo item"
    quantity: int = 1
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "InventoryItem":
        return InventoryItem(**d)


@dataclass
class Spell:
    name: str = "Nova magia"
    level: str = "Truque"  # ex: "Truque", "1º", "2º"...
    school: str = ""       # ex: "Evocação"
    notes: str = ""        # efeito/descrição resumida, alcance, componentes etc.

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Spell":
        return Spell(**d)


@dataclass
class HistoryEntry:
    """Um registro do que mudou na ficha ao longo da campanha."""
    text: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "HistoryEntry":
        return HistoryEntry(**d)


@dataclass
class Character:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "Novo Personagem"
    race: str = ""
    char_class: str = ""
    subclass: str = ""
    background: str = ""
    level: int = 1

    # Atributos
    str_score: int = 10
    dex_score: int = 10
    con_score: int = 10
    int_score: int = 10
    wis_score: int = 10
    cha_score: int = 10

    # Combate
    ac: int = 10
    hp_current: int = 10
    hp_max: int = 10
    hp_temp: int = 0
    speed: int = 30
    proficiency_bonus: int = 2

    # Recursos com uso limitado (ex: Fúria, espaços de magia) -> "nome: usados/total"
    resources: List[str] = field(default_factory=list)

    attacks: List[Attack] = field(default_factory=list)
    inventory: List[InventoryItem] = field(default_factory=list)
    features: List[str] = field(default_factory=list)  # traços de classe/talentos
    notes: str = ""  # personalidade, história, anotações livres

    spells: List[Spell] = field(default_factory=list)
    spell_slots: str = ""  # texto livre, ex: "1º: 4/4   2º: 2/2"
    spellcasting_ability: str = ""  # ex: "Sabedoria (CD 15, +7 para acertar)"

    history: List[HistoryEntry] = field(default_factory=list)

    # ---- Modificadores calculados ----
    @property
    def str_mod(self) -> int:
        return modifier(self.str_score)

    @property
    def dex_mod(self) -> int:
        return modifier(self.dex_score)

    @property
    def con_mod(self) -> int:
        return modifier(self.con_score)

    @property
    def int_mod(self) -> int:
        return modifier(self.int_score)

    @property
    def wis_mod(self) -> int:
        return modifier(self.wis_score)

    @property
    def cha_mod(self) -> int:
        return modifier(self.cha_score)

    @property
    def initiative(self) -> int:
        return self.dex_mod

    # ---- Ações de conveniência (usadas pela UI) ----
    def apply_damage(self, amount: int):
        """Aplica dano, consumindo PV temporário primeiro."""
        if amount <= 0:
            return
        if self.hp_temp > 0:
            absorbed = min(self.hp_temp, amount)
            self.hp_temp -= absorbed
            amount -= absorbed
        self.hp_current = max(0, self.hp_current - amount)

    def apply_healing(self, amount: int):
        if amount <= 0:
            return
        self.hp_current = min(self.hp_max, self.hp_current + amount)

    def add_history(self, text: str):
        if text.strip():
            self.history.insert(0, HistoryEntry(text=text.strip()))

    # ---- Serialização ----
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["attacks"] = [a.to_dict() if isinstance(a, Attack) else a for a in self.attacks]
        d["inventory"] = [i.to_dict() if isinstance(i, InventoryItem) else i for i in self.inventory]
        d["spells"] = [s.to_dict() if isinstance(s, Spell) else s for s in self.spells]
        d["history"] = [h.to_dict() if isinstance(h, HistoryEntry) else h for h in self.history]
        return d

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Character":
        d = dict(d)  # cópia rasa
        d["attacks"] = [Attack.from_dict(a) for a in d.get("attacks", [])]
        d["inventory"] = [InventoryItem.from_dict(i) for i in d.get("inventory", [])]
        d["spells"] = [Spell.from_dict(s) for s in d.get("spells", [])]
        d["history"] = [HistoryEntry.from_dict(h) for h in d.get("history", [])]
        return Character(**d)
