import streamlit as st
import pandas as pd
from datetime import datetime

# Configuração da página
st.set_page_config("Classificador de ECG", layout="centered")

# Usuários e senhas (simples, para testes)
USERS = {"user1": "1234", "user2": "1234", "user3": "1234"}

# Estado de sessão
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "df_classificacoes" not in st.session_state:
    st.session_state.df_classificacoes = None
if "df_ecg" not in st.session_state:
    st.session_state.df_ecg = None

# Login
if not st.session_state.authenticated:
    st.title("🔐 Login")

    with st.form("login_form"):
        username = st.selectbox("Usuário", list(USERS.keys()))
        password = st.text_input("Senha", type="password")
        login_button = st.form_submit_button("Entrar")

    if login_button:
        if username in USERS and password == USERS[username]:
            st.session_state.authenticated = True
            st.session_state.username = username
            st.success("Login realizado com sucesso!")
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")

# Após login
else:
    st.title("⚕️ Classificador de ECG")
    st.sidebar.success(f"Logado como: {st.session_state.username}")
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.df_classificacoes = None
        st.session_state.df_ecg = None
        st.rerun()

    st.header("📤 Envie seus arquivos")

    # Upload dos arquivos
    file_ecg = st.file_uploader("Arquivo .xlsx com sinais ECG", type=["xlsx"], key="ecg_upload")
    file_class = st.file_uploader("Arquivo .xlsx com classificações anteriores", type=["xlsx"], key="class_upload")

    if file_ecg is not None:
        try:
            df_ecg = pd.read_excel(file_ecg)
            if not {"signal_id", "ecg_signal", "heart_rate"}.issubset(df_ecg.columns):
                st.error("O arquivo .xlsx de ECG precisa conter as colunas: 'signal_id', 'ecg_signal', 'heart_rate'.")
                st.stop()
            st.session_state.df_ecg = df_ecg
        except Exception as e:
            st.error(f"Erro ao processar o arquivo ECG: {e}")
            st.stop()

    if file_class is not None:
        try:
            df_classificacoes = pd.read_excel(file_class)
            st.session_state.df_classificacoes = df_classificacoes
        except Exception as e:
            st.error(f"Erro ao processar o arquivo de classificações: {e}")
            st.stop()
    elif file_ecg is not None and st.session_state.df_classificacoes is None:
        st.session_state.df_classificacoes = pd.DataFrame(columns=["signal_id", "user", "classificacao", "comment", "timestamp"])

    # Prosseguir somente se ECG foi carregado
    if st.session_state.df_ecg is not None:
        df_ecg = st.session_state.df_ecg
        df_classificacoes = st.session_state.df_classificacoes
        usuario = st.session_state.username

        if not "user" in df_classificacoes.columns:
            df_classificacoes = pd.DataFrame(columns=["signal_id", "user", "classificacao", "comment", "timestamp"])

        ids_classificados = df_classificacoes[df_classificacoes["user"] == usuario]["signal_id"].tolist()
        sinais_disponiveis = df_ecg[~df_ecg["signal_id"].isin(ids_classificados)]

        if sinais_disponiveis.empty:
            st.success("🎉 Você já classificou todos os sinais disponíveis!")
        else:
            sinal = sinais_disponiveis.iloc[0]
            sinal_id = sinal["signal_id"]
            heart_rate = sinal["heart_rate"]
            sinal_raw = sinal["ecg_signal"]

            try:
                ecg_vals = [float(v.strip()) for v in str(sinal_raw).split(",") if v.strip()]
            except:
                st.error(f"Sinal {sinal_id} contém dados inválidos.")
                st.stop()

            st.subheader(f"Sinal ID: {sinal_id}")
            st.write(f"Frequência cardíaca estimada: **{heart_rate} bpm**")
            st.line_chart(ecg_vals[:9000])  # 30s @ 300Hz

            st.markdown("### Escolha a classificação:")
            classificacao = st.radio("Classificação:", ["Fibrillation", "Normal", "Noisy", "Other"])
            comentario = st.text_input("Comentário (opcional):")

            if st.button("✅ Confirmar classificação"):
                nova = {
                    "signal_id": sinal_id,
                    "user": usuario,
                    "classificacao": classificacao,
                    "comment": comentario,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                df_classificacoes = pd.concat([df_classificacoes, pd.DataFrame([nova])], ignore_index=True)
                st.session_state.df_classificacoes = df_classificacoes
                st.success("Classificação salva!")
                st.rerun()

        with st.expander("📋 Classificações feitas nesta sessão"):
            st.dataframe(st.session_state.df_classificacoes)

        st.markdown("---")
        st.subheader("📥 Finalizar classificação")

        if st.button("⬇️ Finalizar e baixar classificações"):
            df_final = st.session_state.df_classificacoes
            xlsx_bytes = pd.ExcelWriter("/tmp/temp_classificacoes.xlsx", engine="xlsxwriter")
            df_final.to_excel(xlsx_bytes, index=False, sheet_name="Classificacoes")
            xlsx_bytes.close()
            with open("/tmp/temp_classificacoes.xlsx", "rb") as f:
                st.download_button(
                    label="📥 Baixar como Excel",
                    data=f,
                    file_name=f"classificacoes_{usuario}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    else:
        st.info("Envie o arquivo .xlsx com colunas 'signal_id', 'heart_rate' e 'ecg_signal'.")
