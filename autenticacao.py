import streamlit as st
import os


def login():

    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False


    if st.session_state.autenticado:
        return True


    st.title("🔐 Acesso Restrito")

    usuario = st.text_input("Usuário")

    senha = st.text_input(
        "Senha",
        type="password"
    )


    if st.button("Entrar"):

        usuario_correto = os.getenv("USUARIO_ADMIN")
        senha_correta = os.getenv("SENHA_ADMIN")


        if usuario == usuario_correto and senha == senha_correta:

            st.session_state.autenticado = True
            st.rerun()

        else:
            st.error("Usuário ou senha inválidos")


    return False