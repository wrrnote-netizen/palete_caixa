import streamlit as st
from banco_dados.db import (criar_usuario, 
                            listar_tipos_status, 
                            listar_tipos_usuario
                            )
def pagina_criar():
    st.header(":heavy_plus_sign: Criar Novo Usuário")

    opcoes_tipos_usuarios = listar_tipos_usuario()

    with st.form("form_criar"):
        col1, col2 = st.columns(2)
        cnpj = col1.text_input("CNPJ (somente números)", 
                               placeholder="Ex: 12345678000195")
        razao_social = col2.text_input("Razão Social", placeholder="Ex: Empresa Exemplo LTDA")
        nome_fantasia = col1.text_input("Nome Fantasia", placeholder="Ex: Nome da Fantasia")
        nome_contato = col2.text_input("Nome do Contato", placeholder="Ex: João da Silva")
        telefone = col1.text_input("Telefone", type = "phone", placeholder="Ex: (11) 1234-5678", autocomplete="tel")
        email = col2.text_input("E-mail", type="email",placeholder="Ex: exemplo@dominio.com")

        st.divider()
        col1, col2 = st.columns(2)

        nome_usuario = col1.text_input("Nome de Usuário", placeholder="Ex: joao.silva")
        tipo = col2.selectbox("Tipo de Usuário", opcoes_tipos_usuarios)
        senha = col1.text_input("Senha", type="password", placeholder="(min 6 caracteres) Ex: ******")
        confirmar_senha = col2.text_input("Confirmar Senha", type="password", placeholder="Ex: ******")

        criar = st.form_submit_button("Criar Usuário")

    if criar:
        erros = []
        if not cnpj or len(cnpj) != 14 or not cnpj.isdigit():
            erros.append("CNPJ deve ter exatamente 14 digitos "\
                         "numéricos.")
        if not razao_social:
            erros.append("Razão Social é obrigatória.")
        if not nome_usuario:
            erros.append("Nome de Usuário é obrigatório.")
        
        if not senha:
            erros.append("Senha é obrigatória.")
        elif len(senha) < 6:
            erros.append("Senha deve ter no mínimo 6 caracteres.")
        if not confirmar_senha:
            erros.append("Confirmar Senha é obrigatório.")
        if senha != confirmar_senha:
            erros.append("As senhas não coincidem.")

        if erros:
            for e in erros:
                st.warning(f":warning: {e}")
            return
        
    dados = {
            "cnpj": cnpj,
            "razao_social": razao_social,
            "nome_fantasia": nome_fantasia,
            "nome_contato": nome_contato,
            "telefone_contato": telefone,
            "nome_usuario": nome_usuario,
            "status": "ativo",
            "tipo": tipo,
    }
    erro = criar_usuario(dados, senha)
    if erro:
        st.error(erro)
    else:
        st.success(f"Usuário **{nome_usuario}** criado com sucesso!")

