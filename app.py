import streamlit as st
import pandas as pd
import io
from datetime import datetime

USERS = {"1": "1234", "2": "1234", "3": "1234"}

def login():
    st.title("Login")
    username = st.text_input("Utilizador (1, 2 ou 3)")
    password = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if username in USERS and USERS[username] == password:
            st.session_state["user"] = username
            st.success("Login com sucesso!")
            st.rerun()
        else:
            st.error("Credenciais inválidas")

def upload_files():
    st.title("Carregamento de Ficheiros")
    ecg_file = st.file_uploader("Carregar ECGs (ecgs.xlsx)", type="xlsx")
    class_file = st.file_uploader("Carregar Classificações (classificacoes.xlsx)", type="xlsx")

    if ecg_file and class_file:
        try:
            ecgs = pd.read_excel(ecg_file)
            classificacoes = pd.read_excel(class_file)

            # Verificação básica
            if "signal_id" not in ecgs.columns or "signal_id" not in classificacoes.columns:
                st.error("Ficheiros inválidos: coluna 'signal_id' ausente.")
                return

            st.session_state["ecgs"] = ecgs
            st.session_state["classificacoes"] = classificacoes
            st.success("Ficheiros carregados com sucesso!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao ler os ficheiros: {e}")

def classificacao_interface(user):
    st.title(f"Classificação de ECGs - Utilizador {user}")

    ecgs = st.session_state["ecgs"]
    classificacoes = st.session_state["classificacoes"]

    # Sinais já classificados por este utilizador
    classificados_user = classificacoes[classificacoes["user"] == int(user)]["signal_id"].unique()

    # Selecionar sinais ainda não classificados por este user
    pendentes = ecgs[~ecgs["signal_id"].isin(classificados_user)]

    if pendentes.empty:
        st.success("Todos os registos foram classificados por este utilizador.")
        if st.button("Guardar e Finalizar Sessão"):
            save_and_download(st.session_state["classificacoes"])
        return

    ecg_row = pendentes.iloc[0]
    signal_id = ecg_row["signal_id"]

    st.subheader(f"Sinal #{signal_id}")
    st.dataframe(ecg_row.to_frame().T)

    classificacao = st.radio("Classificação", ["Normal", "Arritmia", "Outro"])
    comentario = st.text_area("Comentário (opcional)")

    if st.button("Submeter Classificação"):
        nova_linha = {
            "signal_id": signal_id,
            "user": int(user),
            "classificacao": classificacao,
            "comment": comentario,
            "timestamp": datetime.now()
        }
        st.session_state["classificacoes"] = pd.concat(
            [st.session_state["classificacoes"], pd.DataFrame([nova_linha])],
            ignore_index=True
        )
        st.success("Classificação registada.")
        st.rerun()

    if st.button("Guardar e Finalizar Sessão"):
        save_and_download(st.session_state["classificacoes"])

def save_and_download(df):
    output = io.BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    st.download_button(
        label="📥 Download Classificações Atualizadas",
        data=output,
        file_name="classificacoes_atualizadas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    if st.button("Terminar Sessão"):
        st.session_state.clear()
        st.rerun()

def main():
    st.set_page_config(page_title="Classificador de ECGs")
    if "user" not in st.session_state:
        login()
    elif "ecgs" not in st.session_state or "classificacoes" not in st.session_state:
        upload_files()
    else:
        classificacao_interface(st.session_state["user"])

if __name__ == "__main__":
    main()
