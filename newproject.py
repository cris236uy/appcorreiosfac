import streamlit as st
import pandas as pd
from datetime import date

# --- Inicialização do Estado ---
# Inicializa o dataframe de hábitos se ainda não existir
if 'habits_df' not in st.session_state:
    st.session_state.habits_df = pd.DataFrame({
        'Hábito': ['Correr 5km', 'Ler 10 páginas', 'Estudo Silencioso 1h'],
        'Ativo': [True, True, True]
    })
    st.session_state.records_df = pd.DataFrame(columns=['Data', 'Hábito', 'Status', 'Comentários'])

st.set_page_config(layout="wide", page_title="Disciplina Implacável")
st.title("🔥 The Accountability Tracker")
st.markdown("---")

# --- Estrutura de Abas ---
tab1, tab2, tab3 = st.tabs(["🎯 Get After It (Hoje)", "📈 Painel de Controle", "⚙️ Gerenciar Hábitos"])

# --- TAB 1: Acompanhamento Diário ---
with tab1:
    today = date.today().strftime("%Y-%m-%d")
    st.header(f"Missão de Hoje: {today}")

    # Itera sobre os hábitos ativos
    for habit in st.session_state.habits_df[st.session_state.habits_df['Ativo'] == True]['Hábito']:
        col1, col2, col3 = st.columns([0.4, 0.3, 0.3])

        with col1:
            st.subheader(f"💪 {habit}")

        # Verifica se já foi registrado hoje
        if today in st.session_state.records_df['Data'].values and habit in \
                st.session_state.records_df[st.session_state.records_df['Data'] == today]['Hábito'].values:
            status = st.session_state.records_df[
                (st.session_state.records_df['Data'] == today) & (st.session_state.records_df['Hábito'] == habit)][
                'Status'].iloc[0]
            st.success(f"**Status:** {status} (Registrado)")
            continue

        # Botões de registro
        with col2:
            if st.button("✅ Concluído", key=f"done_{habit}"):
                # Lógica para registrar sucesso
                new_record = {'Data': today, 'Hábito': habit, 'Status': 'Concluído', 'Comentários': 'Nenhuma desculpa.'}
                st.session_state.records_df = pd.concat([st.session_state.records_df, pd.DataFrame([new_record])],
                                                        ignore_index=True)
                st.rerun()

        with col3:
            if st.button("❌ Falhou/Skip", key=f"fail_{habit}"):
                # Lógica para registrar falha
                comment = st.text_input("Qual a desculpa?",
                                        key=f"comment_{habit}") or "Nenhuma desculpa registrada, apenas falhou."
                new_record = {'Data': today, 'Hábito': habit, 'Status': 'Falhou', 'Comentários': comment}
                st.session_state.records_df = pd.concat([st.session_state.records_df, pd.DataFrame([new_record])],
                                                        ignore_index=True)
                st.rerun()

# --- TAB 2 e TAB 3 (Lógica Omitida para Concisão) ---
with tab2:
    st.header("Painel de Controle: O Espelho da Responsabilidade")
    st.write("Aqui você verá suas sequências (streaks) e taxas de sucesso.")
    # Adicionar gráficos e tabelas de streaks

with tab3:
    st.header("Gerenciar Hábitos")
    st.write("Defina seus novos desafios.")
    # Adicionar inputs para adicionar/remover hábitos
