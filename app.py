import streamlit as st
import pandas as pd
import numpy as np
import io
import matplotlib.pyplot as plt
from datetime import datetime

USERS = {
    "User 1": ("1", "1234"),
    "User 2": ("2", "1234"),
    "User 3": ("3", "1234")
}

df = pd.read_excel("ecgs.xlsx")

# Ver tipo de coluna
print(df["signal"].dtype)

# Ver os primeiros sinais
for i in range(3):
    print(f"--- Sinal {i+1} ---")
    print(df["signal"].iloc[i])
    print(type(df["signal"].iloc[i]))

def show_ecg_plot(signal, sampling_frequency=300, signal_id=None):
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    import streamlit as st

    try:
        # Se vier como pandas Series
        if isinstance(signal, pd.Series):
            signal = signal.values

        # Se vier como string: tratar manualmente
        if isinstance(signal, str):
            signal = signal.replace("Nan", "NaN")  # uniformizar
            raw_values = signal.split(",")
            values = []
            for val in raw_values:
                val = val.strip()
                try:
                    values.append(float(val))
                except ValueError:
                    continue  # ignora valores inválidos
            signal = np.array(values)

        # Se vier como lista ou array
        else:
            signal = np.array(signal, dtype=float)

        # Remover NaNs ou infinitos
        signal = signal[np.isfinite(signal)]

    except Exception as e:
        st.error(f"Erro ao processar sinal ECG {signal_id}: {e}")
        return

    if len(signal) == 0:
        st.warning(f"ECG signal ID {signal_id} está vazio ou inválido.")
        return

    # Definir tempo e limitar a 30s
    t = np.arange(len(signal)) / sampling_frequency
    duration = 30
    samples_to_show = int(duration * sampling_frequency)
    t = t[:samples_to_show]
    signal = signal[:samples_to_show]

    # Criar o gráfico
    fig, ax = plt.subplots(figsize=(16, 6), dpi=100)
    ax.set_facecolor("white")
    ax.set_xlim([0, 30])
    ax.set_ylim([-200, 500])
    ax.set_xlabel("Tempo (segundos)")
    ax.set_ylabel("ECG (μV)")
    ax.set_title(f"ECG Signal ID {signal_id}" if signal_id else "ECG Signal")

    # Grades verticais (tempo)
    for i in np.arange(0, 30, 0.2):
        ax.axvline(i, color='red', linewidth=0.5, alpha=0.3)
    for i in np.arange(0, 30, 0.04):
        ax.axvline(i, color='red', linewidth=0.5, alpha=0.1)

    # Grades horizontais (amplitude)
    for i in np.arange(-200, 500, 50):
        ax.axhline(i, color='red', linewidth=0.5, alpha=0.3)
    for i in np.arange(-200, 500, 10):
        ax.axhline(i, color='red', linewidth=0.5, alpha=0.1)

    # Plot do sinal
    ax.plot(t, signal, color='black', linewidth=0.8)
    ax.set_xticks(np.arange(0, 30.1, 2.5))
    ax.set_yticks(np.arange(-200, 550, 100))

    # Mostrar no Streamlit
    plt.tight_layout()
    st.pyplot(fig)



def login():
    st.title("Login")
    selected_user = st.selectbox("Selecionar utilizador", list(USERS.keys()))
    password = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        user_id, correct_pass = USERS[selected_user]
        if password == correct_pass:
            st.session_state["user"] = user_id
            st.session_state["user_name"] = selected_user
            st.success("Login com sucesso!")
            st.rerun()
        else:
            st.error("Senha incorreta.")

def upload_files():
    st.title("Carregar Ficheiros")
    ecg_file = st.file_uploader("Carregar ECGs (ecgs.xlsx)", type="xlsx")
    class_file = st.file_uploader("Carregar Classificações (classificacoes.xlsx)", type="xlsx")

    if ecg_file and class_file:
        try:
            ecgs = pd.read_excel(ecg_file)
            classificacoes = pd.read_excel(class_file)

            if "signal_id" not in ecgs.columns or "signal_id" not in classificacoes.columns:
                st.error("Coluna 'signal_id' ausente num dos ficheiros.")
                return

            st.session_state["ecgs"] = ecgs
            st.session_state["classificacoes"] = classificacoes
            st.success("Ficheiros carregados com sucesso!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao ler os ficheiros: {e}")

def classificacao_interface(user):
    st.title(f"Classificação - Utilizador {user}")
    ecgs = st.session_state["ecgs"]
    classificacoes = st.session_state["classificacoes"]

    classificados_user = classificacoes[classificacoes["user"] == int(user)]["signal_id"].unique()
    pendentes = ecgs[~ecgs["signal_id"].isin(classificados_user)]

    if pendentes.empty:
        st.success("Todos os registos já foram classificados.")
        if st.button("Guardar e Finalizar Sessão"):
            save_and_download(classificacoes)
        return

    ecg_row = pendentes.iloc[0]
    signal_id = ecg_row["signal_id"]
    signal = ecg_row.drop(["signal_id", "heart_rate"], errors="ignore").values
    heart_rate = ecg_row["heart_rate"] if "heart_rate" in ecg_row else "N/A"

    st.subheader(f"Sinal ID: {signal_id}")
    st.markdown(f"**Heart Rate:** {heart_rate} bpm")

    show_ecg_plot(signal, signal_id=signal_id)

    st.markdown("### Classificação:")
    cols = st.columns(3)
    if cols[0].button("✅ Normal"):
        salvar_classificacao(user, signal_id, "Normal", "")
    if cols[1].button("⚠️ Arritmia"):
        salvar_classificacao(user, signal_id, "Arritmia", "")
    if cols[2].button("❓ Outro"):
        salvar_classificacao(user, signal_id, "Outro", "")

    comentario = st.text_area("Comentário (opcional)")
    if st.button("Submeter Comentário"):
        salvar_classificacao(user, signal_id, "Comentado", comentario)

    if st.button("Guardar e Finalizar Sessão"):
        save_and_download(classificacoes)

def salvar_classificacao(user, signal_id, classificacao, comentario=""):
    nova = {
        "signal_id": signal_id,
        "user": int(user),
        "classificacao": classificacao,
        "comment": comentario,
        "timestamp": datetime.now()
    }
    st.session_state["classificacoes"] = pd.concat([
        st.session_state["classificacoes"], pd.DataFrame([nova])
    ], ignore_index=True)
    st.success(f"Classificação '{classificacao}' registada para sinal {signal_id}")
    st.rerun()

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

def sidebar_info():
    if "user" in st.session_state:
        st.sidebar.markdown(f"👤 **Bem-vindo, {st.session_state.get('user_name', 'Utilizador')}**")
        if st.sidebar.button("🔓 Logout"):
            st.session_state.clear()
            st.rerun()

def main():
    st.set_page_config("Classificação de ECGs", layout="wide")
    sidebar_info()

    if "user" not in st.session_state:
        login()
    elif "ecgs" not in st.session_state or "classificacoes" not in st.session_state:
        upload_files()
    else:
        classificacao_interface(st.session_state["user"])

if __name__ == "__main__":
    main()
