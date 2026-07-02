"""
Persistência local das fichas de personagem.
Salva cada personagem como um arquivo .json separado, o que facilita
fazer backup, compartilhar uma ficha específica ou sincronizar depois.
"""
from __future__ import annotations

import json
import os
from typing import List, Optional

from models import Character

CHARACTERS_SUBDIR = "characters"


def get_storage_dir(base_dir: Optional[str] = None) -> str:
    """
    Retorna o diretório onde as fichas são salvas.
    No app rodando de verdade, `base_dir` deve ser App.user_data_dir
    (pasta privada do app, correta tanto no Android quanto no desktop).
    Se não for informado, usa uma pasta local ./characters (útil para testes).
    """
    base = base_dir or os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base, CHARACTERS_SUBDIR)
    os.makedirs(path, exist_ok=True)
    return path


def _path_for(character_id: str, base_dir: Optional[str] = None) -> str:
    return os.path.join(get_storage_dir(base_dir), f"{character_id}.json")


def save_character(character: Character, base_dir: Optional[str] = None) -> None:
    path = _path_for(character.id, base_dir)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(character.to_dict(), f, ensure_ascii=False, indent=2)


def load_character(character_id: str, base_dir: Optional[str] = None) -> Character:
    path = _path_for(character_id, base_dir)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Character.from_dict(data)


def delete_character(character_id: str, base_dir: Optional[str] = None) -> None:
    path = _path_for(character_id, base_dir)
    if os.path.exists(path):
        os.remove(path)


def list_characters(base_dir: Optional[str] = None) -> List[Character]:
    """Retorna todos os personagens salvos, ordenados por nome."""
    folder = get_storage_dir(base_dir)
    result = []
    for filename in os.listdir(folder):
        if filename.endswith(".json"):
            char_id = filename[:-5]
            try:
                result.append(load_character(char_id, base_dir))
            except (json.JSONDecodeError, TypeError, KeyError):
                continue  # ignora arquivo corrompido em vez de derrubar o app
    result.sort(key=lambda c: c.name.lower())
    return result
