import streamlit as st
from paginas.login import pagina_login

st.set_page_config(page_title="Palete-Caixa",
                   page_icon="📦",
                   layout="centered")

# print(st.session_state)

if "usuario" not in st.session_state:
    st.session_state.usuario = None

print(st.session_state.usuario)

if st.session_state.usuario is None:
    pagina_login()

