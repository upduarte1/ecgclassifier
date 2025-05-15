import streamlit as st
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from datetime import datetime

# Configuração
DATA_PATH = "data/ecg.xlsx"
CLASS_PATH = "data/classificacoes.csv"

# Carregar dados
@st.cache_data
def load_ecg_data():
    df = pd.read_excel(DATA_PATH)
    df = df.dropna(subset=["ecg_signal", "signal_id", "heart_rate"])
    df["signal_id"] = df["signal_id"].astype(int)
    return df

def load_classifications():
    if os.path.exists(CLASS_PATH):
        return pd.read_csv(CLASS_PATH)
    else:
        return pd.DataFrame(columns=["signal_id", "user", "classification", "timestamp", "comment"])

def save_classification(signal_id, user, label, comment):
    df = load_classifications()
    new_row = {
        "signal_id": signal_id,
        "user": user,
        "classification": label,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "comment": comment
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(CLASS_PATH, index=False)

# Autenticação básica
USERS = {"user1": "1234", "user2": "1234"}
if "auth" not in st.session_state:
    st.session_state.auth = False
    st.session_state.user = ""

if not st.session_state.auth:
    st.title("Login")
    username = st.selectbox("Usuário", list(USERS.keys()))
    password = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if USERS.get(username) == password:
            st.session_state.auth = True
            st.session_state.user = username
            st.rerun()
        else:
            st.error("Credenciais inválidas")
    st.stop()

# App principal
st.sidebar.success(f"Olá, {st.session_state.user}")
if st.sidebar.button("Logout"):
    st.session_state.auth = False
    st.session_state.user = ""
    st.rerun()

# Carregar dados
ecg_df = load_ecg_data()
class_df = load_classifications()

# Verificar sinais não classificados
classified_ids = set(class_df[class_df["user"] == st.session_state.user]["signal_id"])
available_signals = ecg_df[~ecg_df["signal_id"].isin(classified_ids)]

if available_signals.empty:
    st.success("🎉 Todos os sinais foram classificados!")
    st.stop()

# Mostrar primeiro sinal disponível
row = available_signals.iloc[0]
signal_id = row["signal_id"]
heart_rate = row["heart_rate"]
signal = np.array([float(x) for x in row["ecg_signal"].split(",") if x.strip()])

st.subheader(f"Sinal ID: {signal_id}")
st.write(f"Frequência cardíaca: **{heart_rate:.1f} bpm**")

def plot_ecg(signal, sampling_rate=300):
    t = np.arange(len(signal)) / sampling_rate
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(t, signal, color='black')
    ax.set_title("ECG")
    ax.set_xlabel("Tempo (s)")
    ax.set_ylabel("Amplitude (uV)")
    st.pyplot(fig)

plot_ecg(signal)

# Classificação
labels = ["Normal", "Fibrillation", "Noisy", "Other"]
label = st.radio("Classificação:", labels, horizontal=True)
comment = st.text_input("Comentário (opcional):")

if st.button("Salvar classificação"):
    save_classification(signal_id, st.session_state.user, label, comment)
    st.success("Classificação salva com sucesso!")
    st.rerun()
