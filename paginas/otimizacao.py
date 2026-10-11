import io
import json
import re
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from otimizacao.solver import resolver, OBJETIVOS
from armazenamento.backend import salvar_solucao, listar_solucoes, baixar_imagem, baixar_metadata, NOME as NOME_ARMAZENAMENTO

from utilidades.utils import _slug

# ─── Seção: Nova Solução ──────────────────────────────────────────────────────

def _secao_nova_solucao():
    nome_solucao = st.text_input(
        "Nome da Solução / Pedido",
        placeholder="Ex.: Pedido #2024-001 — Cliente XYZ",
        key="opt_nome",
    )

    st.divider()
    st.subheader("Palete")
    col1, col2 = st.columns(2)
    comp_palete = col1.number_input("Comprimento do palete (cm)", min_value=1.0, value=120.0, step=0.5, format="%.1f", key="opt_cp")
    larg_palete = col2.number_input("Largura do palete (cm)",      min_value=1.0, value=100.0, step=0.5, format="%.1f", key="opt_lp")

    st.subheader("Tipos de caixa")
    st.caption("Adicione uma linha por tipo de caixa. A quantidade mínima garante que o tipo apareça na solução.")
    tabela_caixas = st.data_editor(
        pd.DataFrame([{"Comprimento (cm)": 30.0, "Largura (cm)": 20.0, "Qtd. mínima": 0}]),
        num_rows="dynamic",
        width="stretch",
        hide_index=True,
        column_config={
            "Comprimento (cm)": st.column_config.NumberColumn(min_value=1.0, step=0.5, format="%.1f", required=True),
            "Largura (cm)":     st.column_config.NumberColumn(min_value=1.0, step=0.5, format="%.1f", required=True),
            "Qtd. mínima":      st.column_config.NumberColumn(min_value=0, step=1, format="%d", default=0),
        },
        key="opt_caixas",
    )
    objetivo = st.radio(
        "Função objetivo",
        OBJETIVOS,
        horizontal=True,
        key="opt_objetivo",
        help="A primeira opção maximiza o número de caixas no palete; a segunda "
             "maximiza a área coberta, ou seja, minimiza o espaço que sobra.",
    )
    col3, col4 = st.columns(2)
    qtd_solucoes = col3.number_input("Quantidade de soluções", min_value=1, max_value=10, value=2, step=1, key="opt_qtd_sol")
    tempo_limite = col4.number_input("Tempo limite por solução (s)", min_value=5, max_value=600, value=60, step=5, key="opt_tempo")

    st.divider()

    if st.button("▶ Executar Otimização", type="primary", width="stretch", key="btn_exec"):
        if not nome_solucao.strip():
            st.warning("Informe o nome da solução / pedido.")
            st.session_state.pop("opt_resultado", None)
            return

        tabela = tabela_caixas.dropna(subset=["Comprimento (cm)", "Largura (cm)"])
        caixas = [
            (float(r["Comprimento (cm)"]), float(r["Largura (cm)"]),
             0 if pd.isna(r["Qtd. mínima"]) else int(r["Qtd. mínima"]))
            for _, r in tabela.iterrows()
        ]
        if not caixas:
            st.warning("Informe ao menos um tipo de caixa.")
            st.session_state.pop("opt_resultado", None)
            return
        if any(round(c) < 1 or round(w) < 1 for c, w, _ in caixas):
            st.warning("As dimensões das caixas devem ser de pelo menos 1 cm.")
            st.session_state.pop("opt_resultado", None)
            return

        params = {
            "comprimento_palete_cm": comp_palete,
            "largura_palete_cm":     larg_palete,
            "caixas": [
                {"tipo": t, "comprimento_cm": c, "largura_cm": w, "qtd_minima": q}
                for t, (c, w, q) in enumerate(caixas, start=1)
            ],
            "objetivo": objetivo,
            "qtd_solucoes": int(qtd_solucoes),
            "tempo_limite_s": int(tempo_limite),
        }

        with st.spinner("Executando otimização... ⏳"):
            solucoes, qtd_maxima, fig = resolver(comp_palete, larg_palete, caixas, int(qtd_solucoes), int(tempo_limite), objetivo)

        if fig is None:
            st.error("O solver não encontrou solução viável para os parâmetros informados dentro do tempo limite. Tente reduzir os tipos de caixa ou aumentar o tempo.")
            st.session_state.pop("opt_resultado", None)
            return

        usuario = st.session_state.usuario["nome_usuario"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefixo = f"{_slug(nome_solucao.strip())}_{timestamp}"

        qtds = [len(s) for s in solucoes]
        area_palete = round(comp_palete) * round(larg_palete)
        qtds_por_tipo = [
            {f"T{t}": sum(1 for c in s if c[0] == t) for t in range(1, len(caixas) + 1)}
            for s in solucoes
        ]
        areas_livres = [
            area_palete - sum(round(caixas[t - 1][0]) * round(caixas[t - 1][1]) for t, _, _, _ in s)
            for s in solucoes
        ]
        for linha, livre in zip(qtds_por_tipo, areas_livres):
            linha["Espaço livre (cm²)"] = livre
            linha["Espaço livre (%)"] = round(100 * livre / area_palete, 1)
        meta = {
            "nome_solucao": nome_solucao.strip(),
            "timestamp": timestamp,
            "parametros": params,
            "qtd_caixas_solucoes": qtds,
            "qtd_caixas_por_tipo": qtds_por_tipo,
            "area_livre_cm2": areas_livres,
            "posicoes": [
                [{"tipo": t, "orientacao": o, "x": p, "y": q} for t, o, p, q in s]
                for s in solucoes
            ],
            "qtd_caixas_sol1": qtds[0],
            "qtd_caixas_sol2": qtds[1] if len(qtds) > 1 else 0,
        }

        # Renderiza a figura em memória e fecha para liberar recursos
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        plt.close(fig)
        img_bytes = buf.getvalue()

        chave_base = salvar_solucao(usuario, prefixo, img_bytes, meta)

        st.session_state["opt_resultado"] = {
            "img_bytes":     img_bytes,
            "chave_base":    chave_base,
            "qtds":          qtds,
            "qtds_por_tipo": qtds_por_tipo,
            "qtd_maxima":    qtd_maxima,
            "nome_arquivo":  f"{_slug(nome_solucao.strip())}_solucoes.png",
        }

    # Exibe resultado armazenado (persiste entre re-runs do Streamlit)
    if "opt_resultado" in st.session_state:
        res = st.session_state["opt_resultado"]
        resumo = "  |  ".join(f"Solução {i}: **{q} caixas**" for i, q in enumerate(res["qtds"], start=1))
        st.success(f"{resumo}  |  Máximo teórico: **{res['qtd_maxima']}**")
        st.dataframe(
            pd.DataFrame(res["qtds_por_tipo"], index=[f"Solução {i}" for i in range(1, len(res["qtds"]) + 1)]),
            width="stretch",
        )
        st.image(res["img_bytes"], width="stretch")
        col_info, col_dl = st.columns([3, 1])
        col_info.caption(f"Salvo em {NOME_ARMAZENAMENTO}: `{res['chave_base']}`")
        col_dl.download_button(
            label="⬇️ Baixar",
            data=res["img_bytes"],
            file_name=res["nome_arquivo"],
            mime="image/png",
            key="dl_nova",
        )


# ─── Seção: Histórico ─────────────────────────────────────────────────────────

def _secao_historico():
    usuario = st.session_state.usuario["nome_usuario"]
    solucoes = listar_solucoes(usuario)

    if not solucoes:
        st.info("Nenhuma solução salva para este usuário.")
        return

    selecionado = st.selectbox("Selecione uma solução salva", solucoes, key="hist_sel")

    meta = baixar_metadata(usuario, selecionado)
    if meta:
        st.subheader(meta.get("nome_solucao", selecionado))
        qtds = meta.get("qtd_caixas_solucoes") or [
            meta.get("qtd_caixas_sol1", "—"), meta.get("qtd_caixas_sol2", "—")
        ]
        cols = st.columns(len(qtds) + 1)
        for i, (col, qtd) in enumerate(zip(cols, qtds), start=1):
            col.metric(f"Caixas — Sol. {i}", qtd)
        ts = meta.get("timestamp", "")
        cols[-1].metric("Data", f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}" if len(ts) >= 8 else "—")
        with st.expander("Parâmetros"):
            st.json(meta.get("parametros", {}))

    img_bytes = baixar_imagem(usuario, selecionado)
    if img_bytes:
        st.image(img_bytes, width="stretch")
        st.download_button(
            label="⬇️ Baixar imagem",
            data=img_bytes,
            file_name=f"{selecionado}.png",
            mime="image/png",
            key="dl_hist",
        )
    else:
        st.warning(f"Imagem não encontrada em {NOME_ARMAZENAMENTO} para esta solução.")


# ─── Página principal ─────────────────────────────────────────────────────────

def pagina_otimizacao():
    st.header("📦 Otimização de Palete")

    aba_nova, aba_hist = st.tabs(["▶ Nova Solução", "📂 Histórico"])

    with aba_nova:
        _secao_nova_solucao()

    with aba_hist:
        _secao_historico()

