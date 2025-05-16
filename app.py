import streamlit as st
import pandas as pd
import io

# Usuários válidos
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
    ecg_file = st.file_uploader("Carregar ECGs (ecgs.xlsx)", type="xlsx", key="ecg")
    class_file = st.file_uploader("Carregar Classificações (classificacoes.xlsx)", type="xlsx", key="class")

    if ecg_file and class_file:
        try:
            ecgs = pd.read_excel(ecg_file)
            classificacoes = pd.read_excel(class_file)
            st.session_state["ecgs"] = ecgs
            st.session_state["classificacoes"] = classificacoes
            st.session_state["original_class_file"] = class_file.name
            st.success("Ficheiros carregados com sucesso!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao ler os ficheiros: {e}")

def classificacao_interface(user):
    st.title(f"Classificação de ECGs - Utilizador {user}")
    
    ecgs = st.session_state["ecgs"]
    classificacoes = st.session_state["classificacoes"]

    class_user_col = f"class_user_{user}"
    if class_user_col not in classificacoes.columns:
        classificacoes[class_user_col] = None

    dados_pendentes = classificacoes[classificacoes[class_user_col].isna()]

    if dados_pendentes.empty:
        st.success("Todos os registos foram classificados!")
        if st.button("Guardar e Finalizar Sessão"):
            save_and_download(classificacoes)
        return

    idx = dados_pendentes.index[0]
    ecg_id = classificacoes.loc[idx, "id"]
    ecg_row = ecgs[ecgs["id"] == ecg_id]

    st.write("### Dados do ECG")
    st.dataframe(ecg_row)

    classificacao = st.radio("Classificação", ["Normal", "Arritmia", "Outro"])
    
    if st.button("Submeter Classificação"):
        classificacoes.at[idx, class_user_col] = classificacao
        st.session_state["classificacoes"] = classificacoes
        st.rerun()

    if st.button("Guardar e Finalizar Sessão"):
        save_and_download(classificacoes)

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
    st.success("Pode agora descarregar o ficheiro atualizado.")
    if st.button("Terminar Sessão"):
        st.session_state.clear()
        st.rerun()

def main():
    if "user" not in st.session_state:
        login()
    elif "ecgs" not in st.session_state or "classificacoes" not in st.session_state:
        upload_files()
    else:
        classificacao_interface(st.session_state["user"])

if __name__ == "__main__":
    main()
