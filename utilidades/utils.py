import os
import re
import subprocess
import threading
from signal import SIGKILL

import pulp as plp
from pulp import LpProblem

FOLGA_LIMITE_RIGIDO = 10  # segundos extras antes de matar o solver

def _slug(texto: str) -> str:
    """Converte string para nome seguro de chave S3."""
    return re.sub(r"[^\w\-]", "_", texto.strip().lower())

def _ponto_dentro_caixa(ponto: tuple, bl: tuple, l: int, w: int) -> bool:
    """Verifica se o ponto (x, y) está dentro da caixa com canto inferior esquerdo bl."""
    x, y = ponto
    p, q = bl
    return p <= x < p + l and q <= y < q + w


def _varname2tuple(varname: str) -> tuple:
    """Converte o nome de variável PuLP (ex: 'C_(1,_2,_3)') para tupla (1, 2, 3)."""
    return tuple(
        int(x) for x in str(varname)
        .replace("C_", "").replace("(", "").replace(")", "").split(",_")
    )


def _extrair_solucao(prob: LpProblem) -> list:
    """Retorna lista ordenada de (orientação, x, y) para variáveis ativas."""
    return sorted(
        [_varname2tuple(v.name) for v in prob.variables()
         if v.varValue is not None and v.varValue == 1.0],
        key=lambda x: (x[1], x[2]),
    )


def _pids_do_solver(diretorio_tmp: str) -> list:
    """PIDs dos processos cuja linha de comando referencia o diretorio temporario."""
    saida = subprocess.run(
        ["pgrep", "-f", diretorio_tmp], capture_output=True, text=True
    ).stdout
    return [int(pid) for pid in saida.split() if int(pid) != os.getpid()]


def resolver_com_limite(problema: LpProblem, solver, tempo_limite: float) -> bool:
    """Resolve ``problema`` e mata o processo do solver se passar do limite.

    O limite nativo do CBC (-sec) nao e checado durante o LP/presolve de modelos
    grandes, entao um watchdog encerra o processo apos ``tempo_limite`` + folga.
    ``solver.tmpDir`` deve ser exclusivo desta chamada: e ele que identifica o
    processo, sem afetar solves concorrentes. Retorna True se o solver terminou
    por conta propria.
    """
    parar = threading.Event()
    estourou = threading.Event()

    def vigiar():
        while not parar.is_set() and not _pids_do_solver(solver.tmpDir):
            parar.wait(0.2)
        # O tempo conta a partir da criacao do processo, nao da escrita do modelo
        if parar.wait(tempo_limite + FOLGA_LIMITE_RIGIDO):
            return
        estourou.set()
        for pid in _pids_do_solver(solver.tmpDir):
            try:
                os.kill(pid, SIGKILL)
            except ProcessLookupError:
                pass

    vigia = threading.Thread(target=vigiar, daemon=True)
    vigia.start()
    try:
        problema.solve(solver)
    except plp.PulpSolverError:
        if not estourou.is_set():
            raise
    finally:
        parar.set()
        vigia.join()
    return not estourou.is_set()
