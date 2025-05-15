import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from datetime import datetime

st.set_page_config(page_title="Classificador ECG", layout="wide")
st.title("🫀 Classificador de Sinais ECG")

# Upload manual do arquivo
uploaded_file = st.file_uploader("📁 Carregue o arquivo de sinais (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        if not all(col in df.columns for col in ["signal_id", "heart_rate", "ecg_signal"]):
            st.error("❌ O arquivo deve conter as colunas: signal_id, heart_rate, ecg_signal.")
            st.stop()

        # Evitar reler em cada interação
        if "df_signals" not in st.session_state:
            st.session_state.df_signals = df
            st.session_state.current_index = 0
            st.session_state.classifications = []

        df = st.session_state.df_signals
        index = st.session_state.current_index

        if index >= len(df):
            st.success("🎉 Todos os sinais foram classificados!")
            if st.button("⬇️ Baixar classificações"):
                class_df = pd.DataFrame(st.session_state.classifications)
                csv_path = "classificacoes.csv"
                class_df.to_csv(csv_path, index=False)
                st.download_button("📥 Download CSV", data=class_df.to_csv(index=False), file_name="classificacoes.csv")
            st.stop()

        row = df.iloc[index]
        signal_id = row["signal_id"]
        heart_rate = row["heart_rate"]
        try:
            ecg_signal = [float(x.strip()) for x in str(row["ecg_signal"]).split(",") if x.strip()]
        except:
            st.error(f"Erro ao converter o sinal {signal_id}")
            st.stop()

        # Exibir informações e gráfico
        st.subheader(f"🆔 Sinal: {signal_id}")
        st.write(f"❤️ FC: {heart_rate:.1f} bpm")

        t = np.arange(len(ecg_signal)) / 300  # 300 Hz
        fig, ax = plt.subplots(figsize=(12, 4))
        ax.plot(t, ecg_signal, color="black")
        ax.set_title(f"ECG Sinal {signal_id}")
        ax.set_xlabel("Tempo (s)")
        ax.set_ylabel("Amplitude")
        st.pyplot(fig)

        # Classificação
        st.markdown("### 🏷️ Classificação")
        label = st.radio("Selecione:", ["Normal", "Fibrillation", "Noisy", "Other"])
        comment = st.text_input("Comentário (opcional)")

        if st.button("✅ Confirmar"):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.classifications.append({
                "signal_id": signal_id,
                "heart_rate": heart_rate,
                "classification": label,
                "comment": comment,
                "timestamp": timestamp
            })
            st.session_state.current_index += 1
            st.experimental_rerun()

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
else:
    st.info("📤 Faça upload de um arquivo .xlsx para começar.")
