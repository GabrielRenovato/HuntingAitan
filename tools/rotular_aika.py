"""Rotula janelas AikaClient por PID, sem alterar o cliente ou seus arquivos."""
from __future__ import annotations

import ctypes
import json
import os
import time
from pathlib import Path

user32 = ctypes.windll.user32
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)


def perfis() -> dict[int, str]:
    raiz = Path(os.environ.get("APPDATA", ""))
    encontrados: dict[int, str] = {}
    for pasta, nome in (
        ("HuntingAitan-Domination", "Domination"),
        ("HuntingAitan-alfeim", "alfeim"),
        ("HuntingAitan-SweThc", "SweThc"),
    ):
        arquivo = raiz / pasta / "profile.json"
        try:
            dados = json.loads(arquivo.read_text(encoding="utf-8"))
            pid = int(dados.get("client_pid", 0))
            if pid > 0:
                encontrados[pid] = nome
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            continue
    return encontrados


def janelas_por_pid() -> dict[int, list[int]]:
    saida: dict[int, list[int]] = {}

    @EnumWindowsProc
    def visitar(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        saida.setdefault(int(pid.value), []).append(int(hwnd))
        return True

    user32.EnumWindows(visitar, 0)
    return saida


def aplicar() -> None:
    nomes = perfis()
    janelas = janelas_por_pid()
    for pid, nome in nomes.items():
        for hwnd in janelas.get(pid, ()):
            user32.SetWindowTextW(hwnd, nome)


if __name__ == "__main__":
    while True:
        aplicar()
        time.sleep(1.0)
