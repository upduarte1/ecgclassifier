import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import io

st.set_page_config(layout="wide")

# Sessão
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Login
USERS = ["user1", "user2", "user3"]
PASSWORD = "1234"

if not st.session_state.authenticated:
    st.title("🔐 Login")

    with st.form("login_form"):
        usuario = st.selectbox("Usuário", USERS)
        senha = st.text_input("Senha", type="password")
        login = st.form_submit_button("Entrar")

        if login:
            if senha == PASSWORD:
                st.session_state.authenticated = True
                st.session_state.usuario = usuario
                st.success("Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("Senha incorreta.")
    st.stop()

# Interface principal
st.sidebar.success(f"Bem-vindo, {st.session_state.usuario}")

# Upload de arquivos
st.title("🩺 Classificador de ECG")

st.header("1. Carregue os arquivos necessários")

xlsx_file = st.file_uploader("📥 Arquivo de sinais ECG (.xlsx)", type=["xlsx"])
csv_file = st.file_uploader("📥 Classificações anteriores (.csv)", type=["csv"])

if not xlsx_file or not csv_file:
    st.warning("Por favor, carregue ambos os arquivos para continuar.")
    st.stop()

# Leitura dos dados
try:
    df_ecg = pd.read_excel(xlsx_file)
    df_classificacoes = pd.read_csv(csv_file)
except Exception as e:
    st.error(f"Erro ao ler arquivos: {e}")
    st.stop()

# Processamento de sinais
def parse_signal(signal_str):
    return np.array([float(x.strip()) for x in signal_str.split(",") if x.strip() not in ["", "-"]])

# Identifica sinais não classificados
usuario = st.session_state.usuario
sinais_classificados = set(df_classificacoes[df_classificacoes["user"] == usuario]["signal_id"])
sinais_disponiveis = df_ecg[~df_ecg["signal_id"].isin(sinais_classificados)]

if sinais_disponiveis.empty:
    st.success("🎉 Todos os sinais foram classificados por você!")
    st.download_button("📁 Baixar classificações atualizadas",
                       df_classificacoes.to_csv(index=False),
                       file_name=f"classificacoes_{usuario}.csv",
                       mime="text/csv")
    st.stop()

# Seleciona primeiro sinal disponível
sinal = sinais_disponiveis.iloc[0]
sinal_id = sinal["signal_id"]
sinal_raw = parse_signal(sinal["ecg_signal"])
heart_rate = sinal["heart_rate"]

st.subheader(f"2. Sinal ID: {sinal_id}")
st.write(f"Heart Rate: {heart_rate} bpm")

# Plot ECG
def plot_signal(signal, sampling_rate=300):
    t = np.arange(len(signal)) / sampling_rate
    fig, ax = plt.subplots(figsize=(15, 4))
    ax.plot(t, signal, color='black')
    ax.set_title("ECG Signal")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude (μV)")
    ax.grid(True)
    return fig

st.pyplot(plot_signal(sinal_raw))

# Classificação
st.subheader("3. Classifique o sinal")

col1, col2, col3, col4 = st.columns(4)
rotulo = None

with col1:
    if st.button("⚠️ Fibrillation"):
        rotulo = "Fibrillation"
with col2:
    if st.button("✅ Normal"):
        rotulo = "Normal"
with col3:
    if st.button("⚡ Noisy"):
        rotulo = "Noisy"
with col4:
    if st.button("❓ Other"):
        rotulo = "Other"

if rotulo:
    comentario = st.text_input("Comentário (opcional):")
    if st.button("✔️ Confirmar classificação"):
        from datetime import datetime
        
        nova_class = {
            "signal_id": sinal_id,
            "user": usuario,
            "classificacao": rotulo,
            "comentario": comentario,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        df_classificacoes = pd.concat([df_classificacoes, pd.DataFrame([nova_class])], ignore_index=True)
        st.success(f"Sinal {sinal_id} classificado como '{rotulo}'")
        # Atualiza CSV em memória
        st.download_button("📁 Baixar classificações atualizadas",
                           df_classificacoes.to_csv(index=False),
                           file_name=f"classificacoes_{usuario}.csv",
                           mime="text/csv")
        st.rerun()
