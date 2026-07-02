"""
Ficha Portátil de D&D — app mobile em Kivy.

Fluxo:
  CharacterListScreen -> lista personagens salvos, permite criar/abrir/apagar
  SheetScreen          -> ficha completa e editável, com histórico da campanha

Rodar no desktop para testar:
    pip install kivy
    python main.py

Empacotar para Android:
    pip install buildozer
    buildozer android debug
"""
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.properties import StringProperty, ObjectProperty
from kivy.uix.recycleview import RecycleView
from kivy.metrics import dp

import os

from models import Character, Attack, InventoryItem, Spell, modifier_str
import storage

KV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sheet.kv")


# ---------------------------------------------------------------------------
# Popups auxiliares
# ---------------------------------------------------------------------------

def open_confirm_popup(title_text, message, on_confirm, size_hint=(0.85, 0.35)):
    """Popup de confirmação simples (sim/não), construído em Python puro."""
    layout = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
    layout.add_widget(Label(text=message, color=(0.1, 0.1, 0.1, 1)))

    btn_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
    cancel_btn = Button(text="Cancelar", background_normal="", background_color=(0.5, 0.5, 0.5, 1))
    confirm_btn = Button(text="Confirmar", background_normal="", background_color=(0.55, 0.18, 0.18, 1))
    btn_row.add_widget(cancel_btn)
    btn_row.add_widget(confirm_btn)
    layout.add_widget(btn_row)

    popup = Popup(title=title_text, content=layout, size_hint=size_hint, auto_dismiss=False)

    cancel_btn.bind(on_release=lambda *_: popup.dismiss())

    def do_confirm(*_):
        try:
            on_confirm()
        finally:
            popup.dismiss()

    confirm_btn.bind(on_release=do_confirm)
    popup.open()
    return popup


def open_form_popup(title_text, fields, on_save, size_hint=(0.9, 0.6)):
    """
    Cria e abre um popup simples de formulário, construído inteiramente em
    Python (sem regra .kv própria) — evita problemas de binding específicos
    de subclasses customizadas de Popup declaradas em kv.

    fields: lista de tuplas (chave, rótulo, texto_inicial, multiline)
    on_save: função chamada com um dict {chave: texto} quando o usuário
             confirma. O popup já fecha sozinho depois.
    """
    layout = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(8), size_hint_y=None)
    layout.bind(minimum_height=layout.setter("height"))

    inputs = {}
    for key, label_text, initial, multiline in fields:
        layout.add_widget(Label(
            text=label_text,
            size_hint_y=None,
            height=dp(20),
            halign="left",
            valign="middle",
            color=(0.2, 0.2, 0.2, 1),
            text_size=(None, None),
        ))
        text_input = TextInput(
            text=initial or "",
            multiline=multiline,
            size_hint_y=None,
            height=dp(90) if multiline else dp(40),
        )
        inputs[key] = text_input
        layout.add_widget(text_input)

    btn_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
    cancel_btn = Button(text="Cancelar", background_normal="", background_color=(0.5, 0.5, 0.5, 1))
    save_btn = Button(text="Salvar", background_normal="", background_color=(0.55, 0.18, 0.18, 1))
    btn_row.add_widget(cancel_btn)
    btn_row.add_widget(save_btn)
    layout.add_widget(btn_row)

    popup = Popup(title=title_text, content=layout, size_hint=size_hint, auto_dismiss=False)

    def do_cancel(*_):
        popup.dismiss()

    def do_save(*_):
        values = {key: widget.text for key, widget in inputs.items()}
        try:
            on_save(values)
        finally:
            popup.dismiss()

    cancel_btn.bind(on_release=do_cancel)
    save_btn.bind(on_release=do_save)
    popup.open()
    return popup



# ---------------------------------------------------------------------------
# Tela: lista de personagens
# ---------------------------------------------------------------------------

class CharacterRow(BoxLayout):
    char_id = StringProperty("")
    char_name = StringProperty("")
    char_summary = StringProperty("")


class CharacterListScreen(Screen):
    def on_pre_enter(self, *args):
        self.refresh()

    def refresh(self):
        app = App.get_running_app()
        rv = self.ids.char_rv
        rv.data = []
        for c in storage.list_characters(app.data_dir):
            summary = f"{c.race} {c.char_class} {c.level}".strip()
            rv.data.append({
                "char_id": c.id,
                "char_name": c.name,
                "char_summary": summary,
            })

    def open_character(self, char_id: str):
        app = App.get_running_app()
        char = storage.load_character(char_id, app.data_dir)
        app.open_sheet(char)

    def new_character(self):
        app = App.get_running_app()
        char = Character(name="Novo Personagem")
        storage.save_character(char, app.data_dir)
        app.open_sheet(char)

    def ask_delete(self, char_id: str, char_name: str):
        def confirm():
            app = App.get_running_app()
            storage.delete_character(char_id, app.data_dir)
            self.refresh()

        open_confirm_popup(
            "Apagar personagem",
            f'Apagar "{char_name}"? Essa ação não pode ser desfeita.',
            confirm,
        )


# ---------------------------------------------------------------------------
# Tela: ficha do personagem
# ---------------------------------------------------------------------------

class AttackRow(BoxLayout):
    attack_name = StringProperty("")
    attack_bonus = StringProperty("")
    attack_damage = StringProperty("")
    index = ObjectProperty(0)


class InventoryRow(BoxLayout):
    item_name = StringProperty("")
    item_qty = StringProperty("")
    item_notes = StringProperty("")
    index = ObjectProperty(0)


class HistoryRow(BoxLayout):
    entry_text = StringProperty("")
    entry_timestamp = StringProperty("")


class SpellRow(BoxLayout):
    spell_name = StringProperty("")
    spell_level = StringProperty("")
    spell_notes = StringProperty("")
    index = ObjectProperty(0)


class SheetScreen(Screen):
    character: Character = None

    def load_character(self, character: Character):
        self.character = character
        self.refresh_all()

    # -- refresh helpers -----------------------------------------------
    def refresh_all(self):
        c = self.character
        ids = self.ids

        ids.name_input.text = c.name
        ids.race_input.text = c.race
        ids.class_input.text = c.char_class
        ids.subclass_input.text = c.subclass
        ids.background_input.text = c.background
        ids.level_input.text = str(c.level)

        for attr in ["str", "dex", "con", "int", "wis", "cha"]:
            ids[f"{attr}_score"].text = str(getattr(c, f"{attr}_score"))
            ids[f"{attr}_mod"].text = modifier_str(getattr(c, f"{attr}_score"))

        ids.ac_input.text = str(c.ac)
        ids.hp_current_input.text = str(c.hp_current)
        ids.hp_max_input.text = str(c.hp_max)
        ids.hp_temp_input.text = str(c.hp_temp)
        ids.speed_input.text = str(c.speed)
        ids.prof_input.text = str(c.proficiency_bonus)
        ids.initiative_label.text = modifier_str(c.dex_score)

        ids.notes_input.text = c.notes
        ids.features_input.text = "\n".join(c.features)
        ids.resources_input.text = "\n".join(c.resources)
        ids.spell_slots_input.text = c.spell_slots
        ids.spellcasting_input.text = c.spellcasting_ability

        self.refresh_attacks()
        self.refresh_inventory()
        self.refresh_spells()
        self.refresh_history()

    def refresh_attacks(self):
        rv = self.ids.attacks_rv
        rv.data = [
            {"attack_name": a.name, "attack_bonus": a.bonus, "attack_damage": a.damage, "index": i}
            for i, a in enumerate(self.character.attacks)
        ]

    def refresh_inventory(self):
        rv = self.ids.inventory_rv
        rv.data = [
            {
                "item_name": it.name,
                "item_qty": f"x{it.quantity}",
                "item_notes": it.notes,
                "index": i,
            }
            for i, it in enumerate(self.character.inventory)
        ]

    def refresh_history(self):
        rv = self.ids.history_rv
        rv.data = [
            {"entry_text": h.text, "entry_timestamp": h.timestamp}
            for h in self.character.history
        ]

    def refresh_spells(self):
        rv = self.ids.spells_rv
        rv.data = [
            {
                "spell_name": s.name,
                "spell_level": s.level,
                "spell_notes": s.notes,
                "index": i,
            }
            for i, s in enumerate(self.character.spells)
        ]

    # -- salvar campos de texto no objeto Character ----------------------
    def commit_fields(self):
        c = self.character
        ids = self.ids
        c.name = ids.name_input.text.strip() or "Sem nome"
        c.race = ids.race_input.text.strip()
        c.char_class = ids.class_input.text.strip()
        c.subclass = ids.subclass_input.text.strip()
        c.background = ids.background_input.text.strip()
        c.level = self._to_int(ids.level_input.text, c.level)

        for attr in ["str", "dex", "con", "int", "wis", "cha"]:
            setattr(c, f"{attr}_score", self._to_int(ids[f"{attr}_score"].text, getattr(c, f"{attr}_score")))

        c.ac = self._to_int(ids.ac_input.text, c.ac)
        c.hp_current = self._to_int(ids.hp_current_input.text, c.hp_current)
        c.hp_max = self._to_int(ids.hp_max_input.text, c.hp_max)
        c.hp_temp = self._to_int(ids.hp_temp_input.text, c.hp_temp)
        c.speed = self._to_int(ids.speed_input.text, c.speed)
        c.proficiency_bonus = self._to_int(ids.prof_input.text, c.proficiency_bonus)

        c.notes = ids.notes_input.text
        c.features = [line for line in ids.features_input.text.splitlines() if line.strip()]
        c.resources = [line for line in ids.resources_input.text.splitlines() if line.strip()]
        c.spell_slots = ids.spell_slots_input.text
        c.spellcasting_ability = ids.spellcasting_input.text

    @staticmethod
    def _to_int(text: str, fallback: int) -> int:
        try:
            return int(text)
        except (ValueError, TypeError):
            return fallback

    # -- ações de PV rápidas ---------------------------------------------
    def quick_damage(self, amount_text: str):
        amount = self._to_int(amount_text, 0)
        self.character.apply_damage(amount)
        self.ids.hp_current_input.text = str(self.character.hp_current)

    def quick_heal(self, amount_text: str):
        amount = self._to_int(amount_text, 0)
        self.character.apply_healing(amount)
        self.ids.hp_current_input.text = str(self.character.hp_current)

    # -- ataques / inventário ---------------------------------------------
    def add_attack(self):
        self.character.attacks.append(Attack())
        self.refresh_attacks()

    def remove_attack(self, index: int):
        if 0 <= index < len(self.character.attacks):
            del self.character.attacks[index]
            self.refresh_attacks()

    def edit_attack(self, index: int):
        if not (0 <= index < len(self.character.attacks)):
            return
        attack = self.character.attacks[index]

        def save(values):
            attack.name = values["name"].strip() or attack.name
            attack.bonus = values["bonus"].strip() or attack.bonus
            attack.damage = values["damage"].strip() or attack.damage
            self.refresh_attacks()

        open_form_popup(
            "Editar ataque",
            [
                ("name", "Nome do ataque", attack.name, False),
                ("bonus", "Bônus de acerto (ex: +7)", attack.bonus, False),
                ("damage", "Dano (ex: 1d12+6 cortante)", attack.damage, False),
            ],
            save,
        )

    def add_item(self):
        self.character.inventory.append(InventoryItem())
        self.refresh_inventory()

    def remove_item(self, index: int):
        if 0 <= index < len(self.character.inventory):
            del self.character.inventory[index]
            self.refresh_inventory()

    def edit_item(self, index: int):
        if not (0 <= index < len(self.character.inventory)):
            return
        item = self.character.inventory[index]

        def save(values):
            item.name = values["name"].strip() or item.name
            item.quantity = self._to_int(values["qty"], item.quantity)
            item.notes = values["notes"].strip()
            self.refresh_inventory()

        open_form_popup(
            "Editar item",
            [
                ("name", "Nome do item", item.name, False),
                ("qty", "Quantidade", str(item.quantity), False),
                ("notes", "Descrição / anotações", item.notes, True),
            ],
            save,
        )

    # -- magias ---------------------------------------------
    def add_spell(self):
        self.character.spells.append(Spell())
        self.refresh_spells()

    def remove_spell(self, index: int):
        if 0 <= index < len(self.character.spells):
            del self.character.spells[index]
            self.refresh_spells()

    def edit_spell(self, index: int):
        if not (0 <= index < len(self.character.spells)):
            return
        spell = self.character.spells[index]

        def save(values):
            spell.name = values["name"].strip() or spell.name
            spell.level = values["level"].strip() or spell.level
            spell.school = values["school"].strip()
            spell.notes = values["notes"].strip()
            self.refresh_spells()

        open_form_popup(
            "Editar magia",
            [
                ("name", "Nome da magia", spell.name, False),
                ("level", "Nível (ex: Truque, 1º, 2º...)", spell.level, False),
                ("school", "Escola (ex: Evocação)", spell.school, False),
                ("notes", "Efeito / alcance / componentes", spell.notes, True),
            ],
            save,
            size_hint=(0.9, 0.75),
        )

    # -- histórico da campanha ---------------------------------------------
    def add_history_entry(self):
        def save(values):
            self.character.add_history(values["text"])
            self.refresh_history()

        open_form_popup(
            "Novo registro da campanha",
            [("text", "O que mudou na história / na ficha?", "", True)],
            save,
            size_hint=(0.9, 0.45),
        )

    # -- salvar em disco ---------------------------------------------
    def save_and_back(self):
        self.commit_fields()
        app = App.get_running_app()
        storage.save_character(self.character, app.data_dir)
        app.back_to_list()

    def delete_and_back(self):
        def confirm():
            app = App.get_running_app()
            storage.delete_character(self.character.id, app.data_dir)
            app.back_to_list()

        open_confirm_popup(
            "Apagar personagem",
            f'Apagar "{self.character.name}"? Essa ação não pode ser desfeita.',
            confirm,
        )


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

class DndSheetApp(App):
    title = "Ficha de D&D"

    def build(self):
        # Diretório de dados privado do app (funciona no Android e no desktop)
        self.data_dir = self.user_data_dir
        os.makedirs(self.data_dir, exist_ok=True)

        Builder.load_file(KV_FILE)
        sm = ScreenManager()
        sm.add_widget(CharacterListScreen(name="list"))
        sm.add_widget(SheetScreen(name="sheet"))
        self.sm = sm
        return sm

    def open_sheet(self, character: Character):
        sheet_screen = self.sm.get_screen("sheet")
        sheet_screen.load_character(character)
        self.sm.current = "sheet"

    def back_to_list(self):
        self.sm.current = "list"
        self.sm.get_screen("list").refresh()


if __name__ == "__main__":
    DndSheetApp().run()
