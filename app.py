import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

st.title("Classificador de ECG")

# Upload do arquivo de sinais
uploaded_file = st.file_uploader("📤 Envie seu arquivo .xlsx com sinais ECG", type=["xlsx"])

if uploaded_file:
    try:
        df_sinais = pd.read_excel(uploaded_file)
        st.success("Arquivo carregado com sucesso!")

        # Verifica se o CSV já existe, senão cria um DataFrame vazio
        if os.path.exists("classificacoes.csv"):
            df_classificacoes = pd.read_csv("classificacoes.csv")
        else:
            df_classificacoes = pd.DataFrame(columns=["signal_id", "user", "classificacao", "comentario"])

        # Mostra os sinais disponíveis
        sinais_disponiveis = df_sinais["signal_id"].tolist()
        sinais_classificados = df_classificacoes["signal_id"].tolist()
        sinais_para_classificar = [sid for sid in sinais_disponiveis if sid not in sinais_classificados]

        if sinais_para_classificar:
            sinal_id = sinais_para_classificar[0]
            st.subheader(f"📌 Sinal ID: {sinal_id}")

            # Extrair e plotar sinal
            ecg_raw = df_sinais[df_sinais["signal_id"] == sinal_id]["ecg_signal"].values[0]
            ecg_signal = [float(x) for x in ecg_raw.split(",") if x.strip() not in ["", "-"]]
            t = np.arange(len(ecg_signal)) / 300.0

            fig, ax = plt.subplots(figsize=(12, 4))
            ax.plot(t, ecg_signal, linewidth=1)
            ax.set_title("ECG Signal")
            ax.set_xlabel("Tempo (s)")
            ax.set_ylabel("Amplitude (μV)")
            st.pyplot(fig)

            # Classificação
            classificacao = st.radio("Classificação:", ["Normal", "Fibrillation", "Noisy", "Other"])
            comentario = st.text_input("Comentário (opcional):")
            usuario = st.text_input("Seu nome:")

            if st.button("Salvar Classificação"):
                if not usuario:
                    st.warning("Por favor, insira seu nome.")
                else:
                    nova_classificacao = {
                        "signal_id": sinal_id,
                        "user": usuario,
                        "classificacao": classificacao,
                        "comentario": comentario
                    }

                    df_classificacoes = pd.concat([df_classificacoes, pd.DataFrame([nova_classificacao])], ignore_index=True)
                    df_classificacoes.to_csv("classificacoes.csv", index=False)
                    st.success("✅ Classificação salva com sucesso!")
                    st.experimental_rerun()
        else:
            st.success("🎉 Todos os sinais foram classificados!")
            st.download_button("📥 Baixar classificações", df_classificacoes.to_csv(index=False), file_name="classificacoes.csv", mime="text/csv")

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
else:
    st.info("Envie um arquivo .xlsx com colunas 'signal_id' e 'ecg_signal'.")
