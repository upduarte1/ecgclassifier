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
            st.session_state.username = username  # ✅ Definido apenas se o login for válido
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
        st.rerun()

    st.header("📤 Envie seus arquivos")

    # Upload dos arquivos
    file_xlsx = st.file_uploader("Arquivo .xlsx com sinais ECG", type=["xlsx"])
    file_csv = st.file_uploader("Arquivo .csv com classificações anteriores", type=["csv"])

    # Upload do arquivo com classificações do usuário
    file_csv = st.file_uploader("Arquivo .csv com classificações anteriores", type=["csv"])
    
    if file_xlsx is not None:
        try:
            df_ecg = pd.read_excel(file_xlsx)
            if not {"signal_id", "ecg_signal", "heart_rate"}.issubset(df_ecg.columns):
                st.error("O arquivo .xlsx precisa ter colunas 'signal_id', 'ecg_signal' e 'heart_rate'.")
                st.stop()
        except Exception as e:
            st.error(f"Erro ao processar o .xlsx: {e}")
            st.stop()
    
        # Processa classificações
        if file_csv is not None:
            try:
                df_classificacoes = pd.read_csv(file_csv)
    
                # Garante que todas as colunas esperadas existam
                colunas_esperadas = ["signal_id", "user", "classificacao", "comment", "timestamp"]
                for col in colunas_esperadas:
                    if col not in df_classificacoes.columns:
                        df_classificacoes[col] = ""
            except Exception as e:
                st.error(f"Erro ao processar o .csv de classificações: {e}")
                st.stop()
        else:
            # Cria novo DataFrame se não houver CSV
            df_classificacoes = pd.DataFrame(columns=["signal_id", "user", "classificacao", "comment", "timestamp"])
    
        # Salva no session_state com segurança
        st.session_state.df_classificacoes = df_classificacoes
        st.session_state.df_ecg = df_ecg


    if file_xlsx is not None:
        try:
            df_ecg = pd.read_excel(file_xlsx)
            if not {"signal_id", "heart_rate", "ecg_signal"}.issubset(df_ecg.columns):
                st.error("O arquivo .xlsx precisa ter colunas: 'signal_id', 'heart_rate' e 'ecg_signal'.")
                st.stop()
        except Exception as e:
            st.error(f"Erro ao processar o .xlsx: {e}")
            st.stop()

        # Carrega ou inicia classificações
        if file_csv is not None:
            try:
                df_classificacoes = pd.read_csv(file_csv)
            except Exception as e:
                st.error(f"Erro ao processar o .csv de classificações: {e}")
                st.stop()
        else:
            df_classificacoes = pd.DataFrame(columns=["signal_id", "user", "classificacao", "comment", "timestamp"])

        # Inicializa classificações em sessão
        if st.session_state.df_classificacoes is None:
            st.session_state.df_classificacoes = df_classificacoes

        usuario = st.session_state.username
        df_classificacoes = st.session_state.df_classificacoes
        usuario = st.session_state.username
        
        if "user" not in df_classificacoes.columns:
            st.error("Coluna 'user' não encontrada nas classificações.")
            st.stop()
        
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
                ecg_vals = [float(v.strip()) for v in str(sinal_raw).split(",") if v.strip() != ""]
            except:
                st.error(f"Sinal {sinal_id} contém dados de ECG inválidos.")
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
                st.session_state.df_classificacoes = pd.concat([
                    st.session_state.df_classificacoes,
                    pd.DataFrame([nova])
                ], ignore_index=True)
                st.success("Classificação salva!")
                st.rerun()

        # Exibir classificações atuais
        with st.expander("🔍 Ver classificações feitas nesta sessão"):
            st.dataframe(st.session_state.df_classificacoes)

        # Finalizar e baixar
        st.markdown("---")
        st.subheader("📁 Finalizar classificação")

        if st.button("📥 Finalizar e baixar classificações"):
            csv_final = st.session_state.df_classificacoes.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️ Baixar classificações atualizadas",
                data=csv_final,
                file_name=f"classificacoes_{usuario}.csv",
                mime="text/csv"
            )
    else:
        st.info("Envie um arquivo .xlsx com colunas 'signal_id', 'heart_rate' e 'ecg_signal'.")
