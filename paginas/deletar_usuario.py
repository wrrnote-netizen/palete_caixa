import streamlit as st
from banco_dados.db import listar_usuarios, deletar_usuario


def pagina_deletar():
    st.header("🗑️ Deletar Usuário")
    usuarios = listar_usuarios()
    if not usuarios:
        st.info("Nenhum usuário para deletar.")
        return

    opcoes = {f"{u['razao_social']} ({u['nome_usuario']})": u["id"] for u in usuarios}
    selecionado = st.selectbox("Selecione o usuário", list(opcoes.keys()))
    usuario_id = opcoes[selecionado]

    if usuario_id == st.session_state.usuario["id"]:
        st.warning("Você não pode deletar sua própria conta.")
        return

    st.warning(
        f"O usuário **{selecionado}** será **desativado** (soft-delete). "
        "Esta ação pode ser revertida diretamente no banco."
    )

    confirmacao = st.text_input("Digite o nome de usuário para confirmar:")
    nome_confirmar = next(u["nome_usuario"] for u in usuarios if u["id"] == usuario_id)

    if st.button("Confirmar Deleção", type="primary"):
        if confirmacao != nome_confirmar:
            st.error("Confirmação incorreta. Digite exatamente o nome de usuário.")
        else:
            deletar_usuario(usuario_id)
            st.success(f"Usuário **{selecionado}** desativado com sucesso.")
            # st.rerun()
