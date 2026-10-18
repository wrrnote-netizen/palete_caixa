"""
Módulo de otimização do problema Palete-Caixa.

Dado um palete (L x W) e um ou mais tipos de caixa (l x w, quantidade mínima),
resolve via PL inteira (PuLP/CBC) o problema de maximizar o número de caixas
encaixadas, sem sobreposição. Gera soluções distintas por meio de cortes que
impedem a repetição de layouts já encontrados.
"""

import os
import sys
import tempfile
import time

import pulp as plp
from graficos.plotagem import _gerar_figura
from utilidades.utils import resolver_com_limite


OBJETIVO_QUANTIDADE = "Maximizar quantidade de caixas"
OBJETIVO_AREA_LIVRE = "Minimizar espaço livre no palete"
OBJETIVOS = (OBJETIVO_QUANTIDADE, OBJETIVO_AREA_LIVRE)


# ─── Solver ──────────────────────────────────────────────────────────────

def _somas_atingiveis(dimensoes: list, limite: int) -> list:
    """Coordenadas candidatas: combinações não negativas das dimensões até ``limite``."""
    somas = {0}
    for dimensao in dimensoes:
        somas = {
            soma + qtd * dimensao
            for soma in somas
            for qtd in range((limite - soma) // dimensao + 1)
        }
    return sorted(somas)


def resolver(
    palete_comp: float,
    palete_larg: float,
    caixas: list,
    qtd_solucoes: int = 2,
    tempo_limite: float | None = 60,
    objetivo: str = OBJETIVO_QUANTIDADE,
) -> tuple:
    """
    Resolve o problema de empacotamento via PL inteira (PuLP/CBC).

    Parâmetros
    ----------
    palete_comp, palete_larg : dimensões do palete (cm, arredondadas para int)
    caixas                   : lista de (comprimento, largura, qtd_minima) por tipo
    qtd_solucoes             : quantidade de layouts distintos desejados
    objetivo                 : OBJETIVO_QUANTIDADE (maximiza o nº de caixas) ou
                               OBJETIVO_AREA_LIVRE (minimiza a área não coberta do palete)
    tempo_limite             : segundos por solução (None desliga). Ao estourar, mantém a
                               melhor solução viável já encontrada; sem nenhuma, a busca para

    Retorno
    -------
    (solucoes, qtd_maxima, fig)
      - solucoes   : lista de listas de tuplas (tipo, orientação, x, y); tipo começa em 1
      - qtd_maxima : cota superior teórica (L·W / menor área de caixa)
      - fig        : figura matplotlib com as soluções encontradas
    Retorna (None, qtd_maxima, None) se inviável.
    """
    if not caixas:
        raise ValueError("Informe ao menos um tipo de caixa.")
    if objetivo not in OBJETIVOS:
        raise ValueError(f"objetivo deve ser um de {OBJETIVOS}.")
    if qtd_solucoes < 1:
        raise ValueError("qtd_solucoes deve ser positivo.")
    if tempo_limite is not None and tempo_limite <= 0:
        raise ValueError("tempo_limite deve ser positivo.")

    # Normaliza: L >= W
    L, W = sorted([int(round(palete_comp)), int(round(palete_larg))], reverse=True)
    dims = [(int(round(c)), int(round(w))) for c, w, _ in caixas]
    qtds_minimas = [int(q) for _, _, q in caixas]
    if any(c <= 0 or w <= 0 for c, w in dims):
        raise ValueError("As dimensões das caixas devem ser positivas.")

    qtd_maxima = (L * W) // min(c * w for c, w in dims)

    # Dimensões (comprimento, largura) por tipo e orientação
    orient = {
        (t, o): (dims[t - 1] if o == 1 else dims[t - 1][::-1])
        for t in range(1, len(dims) + 1) for o in (1, 2)
    }

    menor_lado = min(min(d) for d in dims)
    lados = sorted({lado for d in dims for lado in d})
    H = _somas_atingiveis(lados, L - menor_lado)
    V = _somas_atingiveis(lados, W - menor_lado)

    lista_variaveis = [
        (t, o, p, q)
        for (t, o), (cl, cw) in orient.items()
        for p in H if p + cl <= L
        for q in V if q + cw <= W
    ]
    if not lista_variaveis:
        return None, qtd_maxima, None

    # ── Modelo ────────────────────────────────────────────────────────────────
    prob = plp.LpProblem(name="Palete-Caixa", sense=plp.LpMinimize)
    x = plp.LpVariable.dicts(name="C", indices=lista_variaveis, cat=plp.LpBinary)
    if objetivo == OBJETIVO_QUANTIDADE:
        prob += -plp.lpSum(x.values()), "Objetivo"
    else:
        area = lambda c: orient[(c[0], c[1])][0] * orient[(c[0], c[1])][1]
        prob += L * W - plp.lpSum(area(c) * x[c] for c in lista_variaveis), "Objetivo"

    # Não-sobreposição: basta verificar os pontos (r, s) ∈ H × V, pois a
    # interseção de duas caixas sempre contém o maior dos cantos inferiores.
    cobertura = {}
    for chave in lista_variaveis:
        t, o, p, q = chave
        cl, cw = orient[(t, o)]
        for r in H:
            if r >= p + cl:
                break
            if r < p:
                continue
            for s in V:
                if s >= q + cw:
                    break
                if s >= q:
                    cobertura.setdefault((r, s), []).append(x[chave])
    for n, linha in enumerate(cobertura.values()):
        if len(linha) > 1:
            prob += plp.lpSum(linha) <= 1, f"R1_{n}"

    for t, qtd_min in enumerate(qtds_minimas, start=1):
        if qtd_min > 0:
            prob += plp.lpSum(x[c] for c in lista_variaveis if c[0] == t) >= qtd_min, f"R2_{t}"

    print(
        f"Modelo [{objetivo}]: {len(lista_variaveis)} variáveis binárias, {len(prob.constraints)} restrições, "
        f"{sum(len(c) for c in prob.constraints.values())} coeficientes não nulos "
        f"(|H|={len(H)}, |V|={len(V)}), limite por solução: "
        f"{'sem limite' if tempo_limite is None else f'{tempo_limite}s'}"
    )

    # ── Resolução (N soluções distintas) ─────────────────────────────────────
    diretorio_tmp = tempfile.TemporaryDirectory(prefix="palete_caixa_")
    cbc_homebrew = "/opt/homebrew/bin/cbc"
    if sys.platform == "darwin" and os.path.exists(cbc_homebrew):
        solver_obj = plp.COIN_CMD(path=cbc_homebrew, msg=0)
    else:
        # CBC embutido no PuLP (Windows, Linux e macOS)
        solver_obj = plp.PULP_CBC_CMD(msg=0)
    solver_obj.tmpDir = diretorio_tmp.name
    if tempo_limite is not None:
        solver_obj.timeLimit = tempo_limite

    solucoes = []
    try:
        for k in range(qtd_solucoes):
            inicio = time.time()
            if tempo_limite is None:
                prob.solve(solver_obj)
                terminou = True
            else:
                terminou = resolver_com_limite(prob, solver_obj, tempo_limite)
            valores = [x[c].value() for c in lista_variaveis]
            tem_solucao = terminou and None not in valores and prob.sol_status in (
                plp.LpSolutionOptimal, plp.LpSolutionIntegerFeasible
            )
            print(
                f"Solução {k + 1}: {time.time() - inicio:.1f}s, "
                f"{'encontrada' if tem_solucao else 'sem solução'} "
                f"({'limite de tempo excedido' if not terminou else plp.LpStatus[prob.status]})"
            )
            if not tem_solucao:
                break
            selecionadas = [c for c in lista_variaveis if x[c].value() > 0.5]
            solucoes.append(sorted(selecionadas, key=lambda c: (c[2], c[3], c[0], c[1])))

            # Corte "no-good": impede que o mesmo layout seja encontrado novamente
            conjunto = set(selecionadas)
            prob += (
                plp.lpSum(x[c] for c in conjunto)
                - plp.lpSum(x[c] for c in lista_variaveis if c not in conjunto)
                <= len(conjunto) - 1
            ), f"R3_{k}"
    finally:
        diretorio_tmp.cleanup()

    if not solucoes:
        return None, qtd_maxima, None

    fig = _gerar_figura(solucoes, L, W, dims, qtd_maxima, objetivo == OBJETIVO_AREA_LIVRE)
    return solucoes, qtd_maxima, fig
