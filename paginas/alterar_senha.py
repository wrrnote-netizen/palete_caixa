import streamlit as st
from banco_dados.db import alterar_senha

def pagina_alterar_senha():
    st.header(":key: Alterar Senha")
    usuario = st.session_state.usuario
    st.caption(f"Alterando senha de: **{usuario['razao_social']}** "
               f"(`{usuario['nome_usuario']}`)")

    with st.form("form_mudar_senha"):
        nova_senha = st.text_input("Nova Senha", type="password", placeholder="(min 6 caracteres) Ex: ******")
        confirmar_senha = st.text_input("Confirmar Senha", type="password")
        salvar = st.form_submit_button("Salvar")

    if salvar:
        if len(nova_senha) < 6:
            st.warning(":warning: A senha deve ter no mínimo 6 caracteres.")
        elif nova_senha != confirmar_senha:
            st.error(":warning: As senhas não coincidem.")
        else:
            alterar_senha(usuario_id=usuario["id"],
                          nova_senha=nova_senha)
            st.success(":white_check_mark: Senha alterada com sucesso!")
            
            st.session_state.usuario = None
            st.rerun()
    

    