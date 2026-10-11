import math

import matplotlib.pyplot as plt
from matplotlib.patches import Patch


def _gerar_figura(solucoes: list, L: int, W: int, dims: list, qtd_maxima: int, destacar_area: bool = False):
    """Gera figura matplotlib com as soluções em grade (até 2 por linha).

    ``solucoes`` contém listas de (tipo, orientação, x, y); ``dims`` contém
    (comprimento, largura) de cada tipo de caixa, na ordem dos tipos.
    """
    n = len(solucoes)
    ncols = min(n, 2)
    nrows = math.ceil(n / 2)
    fig, axes = plt.subplots(nrows, ncols, figsize=(10 * ncols, 10 * nrows), squeeze=False)
    fig.set_facecolor("#f4f4f4")

    cmap = plt.get_cmap("tab10")
    cores = {t: cmap((t - 1) % 10) for t in range(1, len(dims) + 1)}

    for idx, (ax, solucao) in enumerate(zip(axes.flat, solucoes), start=1):
        ax.set_facecolor("#f4f4f4")
        ax.set_xlim(-1, L + 1)
        ax.set_ylim(-1, W + 1)
        ax.set_aspect("equal")
        ax.grid(alpha=0.3)

        # Borda da palete
        for x0, y0, x1, y1 in [(0, 0, L, 0), (0, 0, 0, W), (0, W, L, W), (L, 0, L, W)]:
            ax.plot([x0, x1], [y0, y1], "k-", lw=2)

        for n_caixa, (t, o, p, q) in enumerate(solucao, start=1):
            cl, cw = dims[t - 1] if o == 1 else dims[t - 1][::-1]
            ax.add_patch(plt.Rectangle(
                xy=(p, q), width=cl, height=cw,
                facecolor=cores[t], edgecolor="white", lw=1,
                hatch="//" if o == 2 else None,
            ))
            ax.text(
                p + cl / 2, q + cw / 2, f"{n_caixa}\nT{t}",
                ha="center", va="center", fontsize=12, color="#f4f4f4",
            )

        contagem = ", ".join(
            f"T{t}: {sum(1 for c in solucao if c[0] == t)}" for t in range(1, len(dims) + 1)
        )
        area_livre = L * W - sum(
            dims[t - 1][0] * dims[t - 1][1] for t, _, _, _ in solucao
        )
        extra = f" | livre: {area_livre} cm² ({100 * area_livre / (L * W):.1f}%)"
        ax.set_title(
            f"Solução {idx} — {len(solucao)} caixas  (máx. teórico: {qtd_maxima})"
            f"\n(L={L}cm, W={W}cm | {contagem}{extra})",
            fontsize=16,
        )
        ax.tick_params(labelsize=12)

    for ax in list(axes.flat)[n:]:
        ax.set_visible(False)

    legenda = [
        Patch(facecolor=cores[t], label=f"T{t}: {c}×{w} cm")
        for t, (c, w) in enumerate(dims, start=1)
    ] + [Patch(facecolor="white", edgecolor="gray", hatch="//", label="Rotacionada")]
    fig.legend(handles=legenda, loc="lower center", ncol=min(len(legenda), 6), fontsize=14,
               bbox_to_anchor=(0.5, 0))
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    return fig
