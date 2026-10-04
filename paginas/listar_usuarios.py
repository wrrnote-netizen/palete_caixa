import streamlit as st
from banco_dados.db import listar_usuarios

def pagina_listar():
    st.header(":busts_in_silhouette: Usuários Cadastrados")
    usuarios = listar_usuarios()
    # print(f"{usuarios = }")
    if not usuarios:
        st.info(":information_source: Nenhum usuário cadastrado!")
        return

    STATUS_CORES = {
        "ativo": ":large_blue_circle:",
        "inativo": ":red_circle:"
    }

    for u in usuarios:
        icone = STATUS_CORES.get(u["status"], ":white_circle:")
        tipo_badge = ":crown:" if u.get("tipo") == "admin" else \
        ":bust_in_silhouette:"

        with st.expander(f"{icone} {tipo_badge} {u['razao_social']}"):
            col1, col2 = st.columns(2)
            col1.write(f"**ID:** {u['id']}")
            col2.write(f"**Contato:** {u['nome_usuario']}")
            col1.write(f"**Status:** {u['status']}")
            col2.write(f"**Tipo:** {u['tipo']}")
            col2.write(f"**E-mail:** {u['email_contato']}")
            st.caption(f"**Criado em:** :date: {u['data_criacao']}")
