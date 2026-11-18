"""Utilitários comuns: hash de textos, localização do jogo e gerenciamento de backups."""
import glob
import hashlib
import json
import os
import re
import shutil
import sys

BACKUP = "_backup_ptbr"


def h(s):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:20]


def sha1_arquivo(p):
    m = hashlib.sha1()
    with open(p, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            m.update(bloco)
    return m.hexdigest()


def dados_dir():
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, "dados")
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dados")


def carregar_dados(nome):
    with open(os.path.join(dados_dir(), nome), encoding="utf-8") as f:
        return json.load(f)


def jogo_valido(p):
    return bool(p) and os.path.isfile(os.path.join(p, "HushHush.exe")) and os.path.isdir(os.path.join(p, "HushHush_Data"))


def _bibliotecas_steam():
    raizes = []
    if sys.platform == "win32":
        try:
            import winreg
            for hive, chave in ((winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam"), (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")):
                try:
                    with winreg.OpenKey(hive, chave) as k:
                        for nome in ("SteamPath", "InstallPath"):
                            try:
                                raizes.append(winreg.QueryValueEx(k, nome)[0])
                            except OSError:
                                pass
                except OSError:
                    pass
        except ImportError:
            pass
    for pf in (os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles")):
        if pf:
            raizes.append(os.path.join(pf, "Steam"))
    libs = []
    for r in raizes:
        r = os.path.normpath(r)
        libs.append(r)
        vdf = os.path.join(r, "steamapps", "libraryfolders.vdf")
        if os.path.isfile(vdf):
            try:
                txt = open(vdf, encoding="utf-8", errors="replace").read()
                for m in re.finditer(r'"path"\s+"([^"]+)"', txt):
                    libs.append(os.path.normpath(m.group(1).replace("\\\\", "\\")))
            except OSError:
                pass
    vistos, out = set(), []
    for l in libs:
        if l.lower() not in vistos:
            vistos.add(l.lower())
            out.append(l)
    return out


def procurar_jogo():
    achados = []
    for lib in _bibliotecas_steam():
        p = os.path.join(lib, "steamapps", "common", "Hush Hush")
        if jogo_valido(p) and p not in achados:
            achados.append(p)
    return achados


class Backup:
    """Mantém uma cópia intacta (inglês) de cada arquivo alterado.
    Se a Steam atualizar/verificar um arquivo depois da instalação, o arquivo atual deixa de
    coincidir com o que gravamos e passa a ser tratado como o novo original."""

    def __init__(self, game):
        self.game = game
        self.data = os.path.join(game, "HushHush_Data")
        self.root = os.path.join(game, BACKUP)
        self.orig = os.path.join(self.root, "orig")
        self.estado_path = os.path.join(self.root, "estado.json")
        self.estado = {}
        if os.path.isfile(self.estado_path):
            try:
                self.estado = json.load(open(self.estado_path, encoding="utf-8"))
            except (OSError, ValueError):
                self.estado = {}

    def atual(self, rel):
        return os.path.join(self.data, *rel.split("/"))

    def original(self, rel):
        cur = self.atual(rel)
        bk = os.path.join(self.orig, *rel.split("/"))
        os.makedirs(os.path.dirname(bk), exist_ok=True)
        if not os.path.exists(bk):
            shutil.copy2(cur, bk)
        else:
            gravado = self.estado.get(rel)
            if gravado and sha1_arquivo(cur) != gravado:
                shutil.copy2(cur, bk)
        return bk

    def registrar(self, rel):
        self.estado[rel] = sha1_arquivo(self.atual(rel))

    def salvar(self):
        os.makedirs(self.root, exist_ok=True)
        json.dump(self.estado, open(self.estado_path, "w", encoding="utf-8"), indent=1)

    def restaurar(self, log=print):
        n = 0
        for rel in list(self.estado):
            bk = os.path.join(self.orig, *rel.split("/"))
            cur = self.atual(rel)
            if os.path.exists(bk) and os.path.exists(cur) and sha1_arquivo(cur) == self.estado[rel]:
                shutil.copy2(bk, cur)
                n += 1
            elif os.path.exists(bk) and os.path.exists(cur):
                log(f"  ignorado (já alterado pela Steam): {rel}")
        self.estado = {}
        self.salvar()
        return n
