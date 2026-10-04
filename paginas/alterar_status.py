import streamlit as st
from banco_dados.db import listar_usuarios, listar_tipos_status, alterar_status


def pagina_alterar_status():
    st.header("🔄 Alterar Status de Usuário")

    usuarios = listar_usuarios()
    # Apenas usuários não-admin podem ter o status alterado
    usuarios_regular = [u for u in usuarios if u.get("tipo") != "admin"]

    if not usuarios_regular:
        st.info("Nenhum usuário regular cadastrado.")
        return

    opcoes = {f"{u['razao_social']} ({u['nome_usuario']})": u for u in usuarios_regular}
    selecionado = st.selectbox("Selecione o usuário", list(opcoes.keys()))
    usuario = opcoes[selecionado]

    st.caption(f"Status atual: **{usuario['status']}**")

    opcoes_status = listar_tipos_status()
    # Pré-seleciona o status atual na lista
    idx_atual = opcoes_status.index(usuario["status"]) if usuario["status"] in opcoes_status else 0
    novo_status = st.selectbox("Novo Status", opcoes_status, index=idx_atual)

    if st.button("Salvar", type="primary"):
        if novo_status == usuario["status"]:
            st.warning("O status selecionado é igual ao atual. Nenhuma alteração feita.")
        else:
            alterar_status(usuario["id"], novo_status)
            st.success(f"Status de **{usuario['razao_social']}** alterado para **{novo_status}**.")
            # st.rerun()
