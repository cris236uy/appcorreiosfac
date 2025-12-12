import streamlit as st
import pandas as pd
from datetime import date, timedelta
from google import genai 
from google.genai.errors import APIError 
from io import BytesIO
import xlsxwriter

# --- 1. Funções de Suporte e Lógica de IA ---

def initialize_session_state():
    """Inicializa DataFrames e estados necessários."""
    if 'habits_df' not in st.session_state:
        st.session_state.habits_df = pd.DataFrame({
            'Hábito': pd.Series(dtype='str'),
            'Unidade Atômica': pd.Series(dtype='str'),
            'Ativo': pd.Series(dtype='bool')
        }) 
    if 'records_df' not in st.session_state:
        st.session_state.records_df = pd.DataFrame(columns=['Data', 'Hábito', 'Status', 'Comentários'])
        st.session_state.records_df['Data'] = pd.to_datetime(st.session_state.records_df['Data'])
    
    if 'suggestion' not in st.session_state:
        st.session_state.suggestion = None

def calculate_streak(records_df, habit_name):
    """Calcula a sequência atual e a melhor sequência."""
    successful_records = records_df[
        (records_df['Hábito'] == habit_name) & (records_df['Status'] == 'Concluído')
    ].sort_values(by='Data', ascending=True).copy()

    if successful_records.empty:
        return 0, 0

    dates_list = sorted(list(successful_records['Data'].dt.date.unique()))
    
    # Streak Atual
    current_streak = 0
    today = date.today()
    check_date = today if today in dates_list else today - timedelta(days=1)
    
    for i in range(len(dates_list) - 1, -1, -1):
        if dates_list[i] == check_date:
            current_streak += 1
            check_date -= timedelta(days=1)
        else: break
            
    # Melhor Streak
    max_streak, temp_max = 0, 1
    for i in range(1, len(dates_list)):
        if dates_list[i] == dates_list[i-1] + timedelta(days=1):
            temp_max += 1
        else:
            max_streak = max(max_streak, temp_max)
            temp_max = 1
    max_streak = max(max_streak, temp_max)
    
    return current_streak, max_streak

def call_gemini(prompt, api_key):
    """Função genérica para chamadas à API Gemini."""
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        return response.text
    except Exception as e:
        return f"ERRO: {e}"

def generate_next_level_suggestion(habit_name, api_key):
    """Gera uma sugestão de 'Level Up' após concluir um hábito."""
    prompt = f"""
    Você é David Goggins. O usuário concluiu: '{habit_name}'.
    Ele está ficando confortável. Sugira UMA nova missão complementar ou uma evolução MAIS DIFÍCIL.
    Responda em português.
    
    Formate estritamente assim:
    NOME: [Nome da nova missão]
    MINIMO: [Unidade atômica/mínima]
    MOTIVACAO: [Frase curta de impacto]
    """
    return call_gemini(prompt, api_key)

# --- 2. Interface e Layout ---

st.set_page_config(layout="wide", page_title="Atomic Goggins | Hardcore Discipline")
initialize_session_state()

st.title("🔥 Disciplina Implacável: O Desafio Goggins")
st.markdown("---")

# Login da API
if 'gemini_api_key' not in st.session_state:
    with st.container(border=True):
        st.subheader("🔑 Chave API Gemini")
        api_input = st.text_input("Insira sua API Key para ativar o modo Goggins:", type="password")
        if st.button("Ativar Protocolo"):
            st.session_state.gemini_api_key = api_input
            st.rerun()
    st.stop()

tab1, tab2, tab3 = st.tabs(["🎯 Missões de Hoje", "📈 O Espelho (Dashboard)", "⚙️ Arsenal (Config)"])

# --- TAB 1: REGISTRO DIÁRIO ---
with tab1:
    col_main, col_sug = st.columns([0.6, 0.4])
    
    with col_main:
        st.header("Não Pare Quando Estiver Cansado.")
        active_habits = st.session_state.habits_df[st.session_state.habits_df['Ativo'] == True]
        
        if active_habits.empty:
            st.info("Nenhuma missão ativa. Adicione hábitos na aba Arsenal.")
        
        for _, row in active_habits.iterrows():
            habit = row['Hábito']
            with st.expander(f"💪 {habit}", expanded=True):
                st.write(f"Mínimo aceitável: `{row['Unidade Atômica']}`")
                
                # Verifica se já registrou hoje
                reg_hoje = st.session_state.records_df[
                    (st.session_state.records_df['Data'].dt.date == date.today()) & 
                    (st.session_state.records_df['Hábito'] == habit)
                ]
                
                if not reg_hoje.empty:
                    st.success("Registrado!")
                else:
                    c1, c2 = st.columns(2)
                    if c1.button("✅ Concluído", key=f"done_{habit}"):
                        new_rec = {'Data': date.today(), 'Hábito': habit, 'Status': 'Concluído', 'Comentários': 'Trabalho feito.'}
                        st.session_state.records_df = pd.concat([st.session_state.records_df, pd.DataFrame([new_rec])], ignore_index=True)
                        # Gerar Upgrade
                        with st.spinner("Goggins está analisando seu progresso..."):
                            st.session_state.suggestion = generate_next_level_suggestion(habit, st.session_state.gemini_api_key)
                        st.rerun()
                        
                    if c2.button("❌ Falhei", key=f"fail_{habit}"):
                        motivo = st.text_input("Qual sua desculpa?", key=f"exc_{habit}")
                        if motivo:
                            prompt = f"Usuário falhou em '{habit}' porque '{motivo}'. Dê um sermão curto e uma punição física agressiva em português estilo Goggins."
                            sermon = call_gemini(prompt, st.session_state.gemini_api_key)
                            new_rec = {'Data': date.today(), 'Hábito': habit, 'Status': 'Falhou', 'Comentários': sermon}
                            st.session_state.records_df = pd.concat([st.session_state.records_df, pd.DataFrame([new_rec])], ignore_index=True)
                            st.rerun()

    with col_sug:
        if st.session_state.suggestion:
            st.subheader("⚡ PRÓXIMO NÍVEL")
            with st.container(border=True):
                st.markdown(st.session_state.suggestion)
                if st.button("🔥 ACEITAR NOVA MISSÃO"):
                    linhas = st.session_state.suggestion.split('\n')
                    n, m = "Nova Missão", "Mínimo"
                    for l in linhas:
                        if "NOME:" in l: n = l.split("NOME:")[1].strip()
                        if "MINIMO:" in l: m = l.split("MINIMO:")[1].strip()
                    
                    new_h = pd.DataFrame([{'Hábito': n, 'Unidade Atômica': m, 'Ativo': True}])
                    st.session_state.habits_df = pd.concat([st.session_state.habits_df, new_h], ignore_index=True)
                    st.session_state.suggestion = None
                    st.toast("Missão adicionada ao Arsenal!")
                    st.rerun()
                if st.button("Dispensar"):
                    st.session_state.suggestion = None
                    st.rerun()

# --- TAB 2: DASHBOARD ---
with tab2:
    st.header("📈 Estatísticas de Guerra")
    if not st.session_state.records_df.empty:
        # Streaks
        streak_data = []
        for h in st.session_state.habits_df['Hábito']:
            curr, best = calculate_streak(st.session_state.records_df, h)
            streak_data.append({"Hábito": h, "Atual 🔥": curr, "Recorde 🏆": best})
        st.table(pd.DataFrame(streak_data))
        
        # Relatório Semanal IA
        if st.button("Gerar Relatório de Elite"):
            prompt = f"Analise estes dados e dê um veredito brutal: {st.session_state.records_df.tail(20).to_string()}"
            st.code(call_gemini(prompt, st.session_state.gemini_api_key))
    else:
        st.info("Sem dados para exibir.")

# --- TAB 3: ARSENAL (GERENCIAMENTO) ---
with tab3:
    st.header("⚙️ Gerenciar Missões")
    
    # Adicionar novo
    with st.form("add_habit"):
        nome = st.text_input("Nome da Missão")
        unidade = st.text_input("Unidade Atômica (ex: Calçar o tênis)")
        if st.form_submit_button("Adicionar"):
            if nome:
                new_row = pd.DataFrame([{'Hábito': nome, 'Unidade Atômica': unidade, 'Ativo': True}])
                st.session_state.habits_df = pd.concat([st.session_state.habits_df, new_row], ignore_index=True)
                st.rerun()

    # Editor de dados
    if not st.session_state.habits_df.empty:
        st.subheader("Lista de Hábitos")
        # Correção do index para o data_editor
        df_edit = st.session_state.habits_df.copy()
        edited = st.data_editor(df_edit, num_rows="dynamic")
        if st.button("Salvar Alterações"):
            st.session_state.habits_df = edited
            st.rerun()
