"""
rodar.py

Executa serial.py e paralelizado.py em sequencia, exibe a saida
em tempo real no terminal e salva cada resultado em evidencias/.

Uso:
    python3 rodar.py
"""

import subprocess
import sys
import os
from datetime import date


EVIDENCIAS = 'evidencias'


def rodar_e_salvar(script, caminho_saida):
    print(f"\n{'=' * 62}")
    print(f"   Iniciando: {script}")
    print(f"   Salvando em: {caminho_saida}")
    print(f"{'=' * 62}\n")

    proc = subprocess.Popen(
        [sys.executable, script],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='replace',
    )

    linhas = []
    for linha in proc.stdout:
        print(linha, end='', flush=True)
        linhas.append(linha)
    proc.wait()

    os.makedirs(EVIDENCIAS, exist_ok=True)
    with open(caminho_saida, 'w', encoding='utf-8') as f:
        f.write(f"Script           : {script}\n")
        f.write(f"Data de execucao : {date.today().strftime('%d/%m/%Y')}\n")
        f.write('=' * 62 + '\n\n')
        f.writelines(linhas)

    status = 'OK' if proc.returncode == 0 else f'ERRO (codigo {proc.returncode})'
    print(f"\n-> {status} — salvo em {caminho_saida}")
    return proc.returncode


def main():
    hoje = date.today().strftime('%Y-%m-%d')

    rc1 = rodar_e_salvar('serial.py',       os.path.join(EVIDENCIAS, f'saida_serial_{hoje}.txt'))
    rc2 = rodar_e_salvar('paralelizado.py', os.path.join(EVIDENCIAS, f'saida_paralelizado_{hoje}.txt'))

    print(f"\n{'=' * 62}")
    print(f"   Execucao concluida — {hoje}")
    print(f"   serial.py      : {'OK' if rc1 == 0 else 'ERRO'}")
    print(f"   paralelizado.py: {'OK' if rc2 == 0 else 'ERRO'}")
    print(f"   Arquivos em    : {os.path.abspath(EVIDENCIAS)}")
    print(f"{'=' * 62}")


if __name__ == '__main__':
    main()
