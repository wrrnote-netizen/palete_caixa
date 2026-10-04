import streamlit as st
from paginas.login import pagina_login
from paginas.listar_usuarios import pagina_listar
from paginas.criar_usuario import pagina_criar
from paginas.alterar_senha import pagina_alterar_senha

st.set_page_config(page_title="Palete-Caixa",
                   page_icon="📦",
                   layout="centered")
# print(st.session_state)

if "usuario" not in st.session_state:
    st.session_state.usuario = None

# print(st.session_state.usuario)

if st.session_state.usuario is None:
    pagina_login()
else:
    usuario = st.session_state.usuario
    is_admin = usuario.get("tipo") == "admin"

    with st.sidebar:
        tipo_badge = ":crown: Admin" if is_admin else \
        ":bust_in_silhouette: Regular"
        st.markdown(f"**Olá {usuario['razao_social']}!**")
        st.caption(f"Usuário: `{usuario['nome_usuario']}` | "
                   f"Tipo: {tipo_badge}")
        st.divider()
        opcoes_menu = (["Modelo Palete-Caixa", "Listar Usuários", 
                       "Criar Usuário", "Alterar Status", "Alterar Senha", 
                       "Deletar Usuário"]
                       if is_admin else ["Modelo Palete-Caixa", "Alterar Senha"]
        )

        pagina = st.radio("Menu", opcoes_menu, index=0,
                          label_visibility="collapsed")
        st.divider()

        if st.button(":door: Sair"):
            st.session_state.usuario = None
            st.rerun()

    if pagina == "Listar Usuários":
        pagina_listar()
    elif pagina == "Criar Usuário":
        pagina_criar()
    elif pagina == "Alterar Senha":
        pagina_alterar_senha()
