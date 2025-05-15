import streamlit as st
import pandas as pd
from datetime import datetime

# Configurações iniciais
st.set_page_config("Classificador de ECG", layout="centered")

# Usuários e senhas
USERS = {"user1": "1234", "user2": "1234", "user3": "1234"}

# Estado de sessão
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""

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
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha inválidos.")

# Após login
else:
    st.title("⚕️ Classificador de ECG")
    st.sidebar.success(f"Logado como: {st.session_state.username}")
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.experimental_rerun()

    st.header("📤 Envie seus arquivos")

    # Upload do arquivo com sinais
    file_xlsx = st.file_uploader("Arquivo .xlsx com sinais ECG", type=["xlsx"])

    # Upload do arquivo com classificações do usuário
    file_csv = st.file_uploader("Arquivo .csv com classificações anteriores", type=["csv"])

    if file_xlsx is not None:
        try:
            df_ecg = pd.read_excel(file_xlsx)
            if not {"signal_id", "ecg_signal"}.issubset(df_ecg.columns):
                st.error("O arquivo .xlsx precisa ter colunas 'signal_id' e 'ecg_signal'.")
                st.stop()
        except Exception as e:
            st.error(f"Erro ao processar o .xlsx: {e}")
            st.stop()

        # Carrega ou cria DataFrame de classificações
        if file_csv is not None:
            try:
                df_classificacoes = pd.read_csv(file_csv)
            except Exception as e:
                st.error(f"Erro ao processar o .csv de classificações: {e}")
                st.stop()
        else:
            df_classificacoes = pd.DataFrame(columns=["signal_id", "user", "classificacao", "comentario", "timestamp"])

        # Filtra sinais ainda não classificados por este usuário
        usuario = st.session_state.username
        ids_classificados = df_classificacoes[df_classificacoes["user"] == usuario]["signal_id"].tolist()
        sinais_disponiveis = df_ecg[~df_ecg["signal_id"].isin(ids_classificados)]

        if sinais_disponiveis.empty:
            st.success("🎉 Você já classificou todos os sinais disponíveis!")
        else:
            sinal = sinais_disponiveis.iloc[0]
            sinal_id = sinal["signal_id"]
            sinal_raw = sinal["ecg_signal"]

            try:
                ecg_vals = [float(v.strip()) for v in str(sinal_raw).split(",") if v.strip() != ""]
            except:
                st.error(f"Sinal {sinal_id} com dados inválidos.")
                st.stop()

            st.subheader(f"Sinal ID: {sinal_id}")
            st.line_chart(ecg_vals[:9000])  # 30s @ 300Hz

            st.markdown("### Escolha a classificação:")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.button("⚠️ Fibrillation"):
                    st.session_state.temp_classificacao = "Fibrillation"
            with col2:
                if st.button("✅ Normal"):
                    st.session_state.temp_classificacao = "Normal"
            with col3:
                if st.button("⚡ Noisy"):
                    st.session_state.temp_classificacao = "Noisy"
            with col4:
                if st.button("❓ Other"):
                    st.session_state.temp_classificacao = "Other"

            # Comentário e confirmação
            if "temp_classificacao" in st.session_state:
                st.write(f"Selecionado: **{st.session_state.temp_classificacao}**")
                comentario = st.text_input("Comentário (opcional):")
                if st.button("✅ Confirmar classificação"):
                    nova = {
                        "signal_id": sinal_id,
                        "user": usuario,
                        "classificacao": st.session_state.temp_classificacao,
                        "comentario": comentario,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    df_classificacoes = pd.concat([df_classificacoes, pd.DataFrame([nova])], ignore_index=True)
                    st.success("Classificação salva!")
                    # Download do CSV atualizado
                    csv_atualizado = df_classificacoes.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="⬇️ Baixar classificações atualizadas",
                        data=csv_atualizado,
                        file_name=f"classificacoes_{usuario}.csv",
                        mime="text/csv"
                    )
                    # Limpa estado temporário e recarrega
                    del st.session_state["temp_classificacao"]
                    st.experimental_rerun()
    else:
        st.info("Envie um arquivo .xlsx com colunas 'signal_id' e 'ecg_signal'.")
