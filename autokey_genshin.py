import json
import os
import threading
import time
import tkinter as tk
from tkinter import ttk

from pynput import keyboard
from pynput.keyboard import Key

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

DEFAULTS = {
    "toggle_key": "alt+f",
    "target_key": "f",
    "interval_ms": 50,
}

MODIFIER_KEYS = {
    "alt", "alt_l", "alt_r", "alt_gr",
    "ctrl", "ctrl_l", "ctrl_r",
    "shift", "shift_l", "shift_r",
    "cmd", "cmd_l", "cmd_r",
}


def normalize_mod(name):
    return name.split("_")[0]


def parse_key(name):
    name = str(name).strip().lower()
    if hasattr(Key, name):
        return getattr(Key, name)
    if len(name) == 1:
        return name
    return None


def parse_combo(s):
    parts = [p.strip().lower() for p in str(s).split("+")]
    mods = {normalize_mod(p) for p in parts if p in MODIFIER_KEYS}
    keys = [p for p in parts if p not in MODIFIER_KEYS]
    if len(keys) != 1:
        return None
    return mods, keys[0]


def key_label(key):
    if isinstance(key, Key):
        return key.name
    if hasattr(key, "char") and key.char is not None:
        return str(key.char).lower()
    return str(key).lower()


class AutoKeyApp:
    def __init__(self, root):
        self.root = root
        root.title("Auto Key Presser")
        root.resizable(False, False)

        self.config = dict(DEFAULTS)
        self.load_config()

        self.enabled = False
        self.recording = None
        self.pressed_mods = set()

        self.toggle_mods, self.toggle_keyname = parse_combo(self.config["toggle_key"])
        self.target_keyobj = parse_key(self.config["target_key"])
        self.interval_ms = int(self.config["interval_ms"])

        self.controller = keyboard.Controller()

        self.build_ui()
        self.update_ui()

        self.listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release,
        )
        self.listener.daemon = True
        self.listener.start()

        threading.Thread(target=self.click_loop, daemon=True).start()

        self._ui_enabled = self.enabled
        self._ui_recording = self.recording
        self.root.after(100, self.poll_ui)

        root.protocol("WM_DELETE_WINDOW", self.on_close)

    def poll_ui(self):
        if (self._ui_enabled != self.enabled
                or self._ui_recording != self.recording):
            self._ui_enabled = self.enabled
            self._ui_recording = self.recording
            self.update_ui()
        self.root.after(100, self.poll_ui)

    def build_ui(self):
        frm = ttk.Frame(self.root, padding=16)
        frm.grid()

        ttk.Label(frm, text="Auto Key Presser (Genshin)",
                  font=("Segoe UI", 14, "bold")).grid(row=0, column=0, columnspan=3, pady=(0, 14))

        ttk.Label(frm, text="Tecla ativar/desativar:").grid(row=1, column=0, sticky="w")
        self.toggle_label = ttk.Label(frm, text="", width=20, relief="sunken", anchor="center")
        self.toggle_label.grid(row=1, column=1, padx=8)
        self.record_toggle_btn = ttk.Button(frm, text="Gravar", width=10,
                                            command=self.start_record_toggle)
        self.record_toggle_btn.grid(row=1, column=2)

        ttk.Label(frm, text="Tecla a pressionar:").grid(row=2, column=0, sticky="w", pady=(6, 0))
        self.target_label = ttk.Label(frm, text="", width=20, relief="sunken", anchor="center")
        self.target_label.grid(row=2, column=1, padx=8, pady=(6, 0))
        self.record_target_btn = ttk.Button(frm, text="Gravar", width=10,
                                            command=self.start_record_target)
        self.record_target_btn.grid(row=2, column=2, pady=(6, 0))

        ttk.Label(frm, text="Intervalo (ms):").grid(row=3, column=0, sticky="w", pady=(6, 0))
        self.interval_var = tk.StringVar(value=str(self.interval_ms))
        self.interval_var.trace_add("write", self.on_interval_change)
        self.interval_entry = ttk.Entry(frm, textvariable=self.interval_var, width=10)
        self.interval_entry.grid(row=3, column=1, sticky="w", padx=8, pady=(6, 0))
        ttk.Label(frm, text="50ms = 20 cliques/s").grid(row=3, column=2, sticky="w", pady=(6, 0))

        self.status_label = ttk.Label(frm, text="", font=("Segoe UI", 12, "bold"),
                                      width=26, anchor="center")
        self.status_label.grid(row=4, column=0, columnspan=3, pady=(16, 0))

        self.toggle_btn = ttk.Button(frm, text="", width=26, command=self.toggle_enabled)
        self.toggle_btn.grid(row=5, column=0, columnspan=3, pady=(6, 0))

        self.save_btn = ttk.Button(frm, text="Salvar configuração", command=self.save_config)
        self.save_btn.grid(row=6, column=0, columnspan=3, pady=(12, 0))

        self.hint_label = ttk.Label(frm, text="Dica: rode como Admin se o jogo rodar como Admin.",
                                    foreground="#888888")
        self.hint_label.grid(row=7, column=0, columnspan=3, pady=(12, 0))

    def update_ui(self):
        if self.recording == "toggle":
            self.toggle_label.config(text="Pressione o combo...")
            self.record_toggle_btn.config(text="Cancelar")
        else:
            self.toggle_label.config(text=self.config["toggle_key"])
            self.record_toggle_btn.config(text="Gravar")
        if self.recording == "target":
            self.target_label.config(text="Pressione a tecla...")
            self.record_target_btn.config(text="Cancelar")
        else:
            self.target_label.config(text=self.config["target_key"])
            self.record_target_btn.config(text="Gravar")
        if self.enabled:
            self.status_label.config(text="ATIVADO", foreground="#1a7f37")
            self.toggle_btn.config(text="Desativar")
        else:
            self.status_label.config(text="DESATIVADO", foreground="#c03030")
            self.toggle_btn.config(text="Ativar")

    def on_interval_change(self, *_):
        try:
            value = int(float(self.interval_var.get()))
        except (ValueError, TypeError):
            return
        self.interval_ms = max(1, min(value, 60000))

    def get_interval(self):
        return self.interval_ms

    def click_loop(self):
        while True:
            if self.enabled and self.target_keyobj is not None:
                self.controller.press(self.target_keyobj)
                self.controller.release(self.target_keyobj)
            time.sleep(self.get_interval() / 1000.0)

    def on_press(self, key, injected):
        if injected:
            return
        name = key_label(key)
        if name in MODIFIER_KEYS:
            self.pressed_mods.add(normalize_mod(name))
            return
        if self.recording:
            self.finish_recording(key, name)
            return
        if self.toggle_mods == self.pressed_mods and name == self.toggle_keyname:
            self.toggle_enabled()

    def on_release(self, key, injected):
        if injected:
            return
        name = key_label(key)
        if name in MODIFIER_KEYS:
            self.pressed_mods.discard(normalize_mod(name))

    def toggle_enabled(self):
        self.enabled = not self.enabled

    def start_record_toggle(self):
        self.recording = None if self.recording == "toggle" else "toggle"
        self.pressed_mods = set()
        self.update_ui()

    def start_record_target(self):
        self.recording = None if self.recording == "target" else "target"
        self.pressed_mods = set()
        self.update_ui()

    def finish_recording(self, key, name):
        rec = self.recording
        if rec == "toggle":
            mods = sorted(self.pressed_mods)
            combo = "+".join(mods + [name])
            parsed = parse_combo(combo)
            if parsed is None:
                return
            self.toggle_mods, self.toggle_keyname = parsed
            self.config["toggle_key"] = combo
        elif rec == "target":
            self.target_keyobj = parse_key(name)
            self.config["target_key"] = name
        self.recording = None

    def save_config(self):
        interval = self.get_interval()
        self.config["interval_ms"] = interval
        self.interval_var.set(str(interval))
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            self.hint_label.config(text="Configuração salva em config.json", foreground="#1a7f37")
        except OSError as exc:
            self.hint_label.config(text=f"Erro ao salvar: {exc}", foreground="#c03030")

    def load_config(self):
        if not os.path.exists(CONFIG_PATH):
            return
        try:
            with open(CONFIG_PATH, encoding="utf-8") as f:
                data = json.load(f)
            for key in DEFAULTS:
                if key in data:
                    self.config[key] = data[key]
        except (OSError, ValueError):
            pass

    def on_close(self):
        self.enabled = False
        self.root.destroy()


def main():
    root = tk.Tk()
    AutoKeyApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
