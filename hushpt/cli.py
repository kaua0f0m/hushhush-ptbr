"""Instalador da tradução PT-BR de Hush Hush."""
import argparse
import os
import sys
import time

from . import VERSAO
from .core import Backup, jogo_valido, procurar_jogo

TITULO = f"Hush Hush - Tradução PT-BR  v{VERSAO}"


def _console():
    if sys.platform == "win32":
        os.system("chcp 65001 >nul")
    for f in (sys.stdout, sys.stderr):
        try:
            f.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def _pausa(args):
    if not args.sem_pausa and sys.stdin and sys.stdin.isatty():
        try:
            input("\nPressione Enter para fechar...")
        except EOFError:
            pass


def _escolher_jogo(args):
    if args.jogo:
        if not jogo_valido(args.jogo):
            raise SystemExit(f"'{args.jogo}' não parece ser a pasta do Hush Hush (faltam HushHush.exe / HushHush_Data).")
        return args.jogo
    achados = procurar_jogo()
    if len(achados) == 1:
        print(f"Jogo encontrado: {achados[0]}")
        return achados[0]
    if len(achados) > 1:
        for i, p in enumerate(achados, 1):
            print(f"  [{i}] {p}")
        r = input("Qual instalação? ").strip()
        if r.isdigit() and 1 <= int(r) <= len(achados):
            return achados[int(r) - 1]
    print("Não encontrei o Hush Hush automaticamente.")
    p = input("Cole aqui o caminho da pasta do jogo (a que contém HushHush.exe): ").strip().strip('"')
    if not jogo_valido(p):
        raise SystemExit("Pasta inválida.")
    return p


def _checar_jogo_aberto():
    if sys.platform != "win32":
        return
    import subprocess
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq HushHush.exe"], capture_output=True, text=True).stdout
    except Exception:
        return
    if "HushHush.exe" in out:
        raise SystemExit("O Hush Hush está aberto. Feche o jogo e execute de novo.")


def instalar(game):
    from . import codigo, dialogo, fonte, interface
    _checar_jogo_aberto()
    bk = Backup(game)
    t0 = time.time()
    print("\n[1/4] Diálogos")
    dialogo.aplicar(bk)
    print("[2/4] Fontes (acentos)")
    fonte.aplicar(bk)
    print("[3/4] Menus e interface")
    interface.aplicar(bk)
    print("[4/4] Textos do código")
    codigo.aplicar(bk)
    bk.salvar()
    print(f"\nPronto! Tradução instalada em {time.time() - t0:.0f}s.")
    print("Abra o jogo normalmente pela Steam.")
    print("Se a Steam atualizar o jogo ou você verificar a integridade dos arquivos, rode este instalador de novo.")


def restaurar(game):
    _checar_jogo_aberto()
    n = Backup(game).restaurar()
    print(f"\n{n} arquivos restaurados para o inglês original.")


def main(argv=None):
    _console()
    ap = argparse.ArgumentParser(description=TITULO)
    ap.add_argument("acao", nargs="?", choices=["instalar", "restaurar"], help="o que fazer (padrão: pergunta)")
    ap.add_argument("--jogo", help="pasta do jogo (a que contém HushHush.exe)")
    ap.add_argument("--sem-pausa", action="store_true", help="não esperar Enter ao final")
    args = ap.parse_args(argv)
    print("=" * len(TITULO))
    print(TITULO)
    print("=" * len(TITULO))
    print("Criador: kaua0f0m | Tradução: Claude Code (Sonnet)")
    print("Jogo 16+ na Steam; as cenas adultas ficam na DLC NSFW (18+).")
    print("Você precisa ter o Hush Hush original instalado pela Steam.\n")
    try:
        acao = args.acao
        if not acao:
            print("  [1] Instalar a tradução")
            print("  [2] Restaurar o jogo original (inglês)")
            r = input("Escolha (1/2): ").strip()
            acao = "restaurar" if r == "2" else "instalar"
        game = _escolher_jogo(args)
        if acao == "instalar":
            instalar(game)
        else:
            restaurar(game)
    except SystemExit as e:
        if e.code not in (None, 0):
            print(f"\nErro: {e.code}")
            _pausa(args)
            return 1
    except KeyboardInterrupt:
        print("\nCancelado.")
        return 1
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\nErro inesperado: {e}\nSeus arquivos originais continuam em '_backup_ptbr' dentro da pasta do jogo; use 'restaurar' se algo ficou estranho.")
        _pausa(args)
        return 1
    _pausa(args)
    return 0
