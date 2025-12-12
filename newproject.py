import streamlit as st
import pandas as pd
from datetime import date, timedelta
from google import genai 
from google.genai.errors import APIError 
from io import BytesIO

# --- 1. Funções de Suporte e Lógica de IA ---

def initialize_session_state():
    """Inicializa DataFrames e estados necessários com tipos explícitos."""
    if 'habits_df' not in st.session_state:
        st.session_state.habits_df = pd.DataFrame({
            'Hábito': pd.Series(dtype='str'),
            'Unidade Atômica': pd.Series(dtype='str'),
            'Ativo': pd.Series(dtype='bool')
        }) 
    
    if 'records_df' not in st.session_state:
        st.session_state.records_df = pd.DataFrame(columns=['Data', 'Hábito', 'Status', 'Comentários'])
        # Força o tipo datetime na criação
        st.session_state.records_df['Data'] = pd.to_datetime(st.session_state.records_df['Data'])
    
    if 'suggestion' not in st.session_state:
        st.session_state.suggestion = None

def ensure_datetime():
    """Garante que a coluna Data seja sempre datetime para evitar o AttributeError."""
    if not st.session_state.records_df.empty:
        st.session_state.records_df['Data'] = pd.to_datetime(st.session_state.records_df['Data'])

def calculate_streak(records_df, habit_name):
    """Calcula a sequência atual e a melhor sequência."""
    if records_df.empty: return 0, 0
    
    # Filtra e garante que a data é objeto date para comparação
    successful_records = records_df[
        (records_df['Hábito'] == habit_name) & (records_df['Status'] == 'Concluído')
    ].copy()
    
    if successful_records.empty: return 0, 0

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
        return f"ERRO NA API: {e}"

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
        st.subheader("🔑 Configuração Inicial")
        api_input = st.text_input("Insira sua API Key do Gemini:", type="password")
        if st.button("Ativar Modo Goggins"):
            st.session_state.gemini_api_key = api_input
            st.rerun()
    st.stop()

tab1, tab2, tab3 = st.tabs(["🎯 Missões de Hoje", "📈 O Espelho (Stats)", "⚙️ Arsenal (Config)"])

# --- TAB 1: REGISTRO DIÁRIO ---
with tab1:
    col_main, col_sug = st.columns([0.6, 0.4])
    
    with col_main:
        st.header("Missão Diária")
        ensure_datetime() # Garante o tipo antes de filtrar
        active_habits = st.session_state.habits_df[st.session_state.habits_df['Ativo'] == True]
        
        if active_habits.empty:
            st.info("Nenhuma missão ativa no arsenal.")
        
        for _, row in active_habits.iterrows():
            habit = row['Hábito']
            with st.expander(f"💪 {habit}", expanded=True):
                st.write(f"Meta Mínima: `{row['Unidade Atômica']}`")
                
                # Filtragem segura usando dt.date
                df_records = st.session_state.records_df
                reg_hoje = df_records[
                    (pd.to_datetime(df_records['Data']).dt.date == date.today()) & 
                    (df_records['Hábito'] == habit)
                ]
                
                if not reg_hoje.empty:
                    status = reg_hoje.iloc[0]['Status']
                    if status == 'Concluído':
                        st.success("✅ Missão Cumprida!")
                    else:
                        st.error("❌ Você falhou nesta missão hoje.")
                else:
                    c1, c2 = st.columns(2)
                    if c1.button("✅ Concluído", key=f"done_{habit}"):
                        new_rec = pd.DataFrame([{
                            'Data': pd.Timestamp.now(), 
                            'Hábito': habit, 
                            'Status': 'Concluído', 
                            'Comentários': 'Sem desculpas.'
                        }])
                        st.session_state.records_df = pd.concat([st.session_state.records_df, new_rec], ignore_index=True)
                        with st.spinner("Goggins está de olho..."):
                            st.session_state.suggestion = generate_next_level_suggestion(habit, st.session_state.gemini_api_key)
                        st.rerun()
                        
                    if c2.button("❌ Falhei", key=f"fail_{habit}"):
                        motivo = st.text_input("Qual sua desculpa?", key=f"exc_input_{habit}")
                        if motivo:
                            sermon = call_gemini(f"Usuário falhou em '{habit}' por: '{motivo}'. Dê um sermão Goggins em PT-BR.", st.session_state.gemini_api_key)
                            new_rec = pd.DataFrame([{
                                'Data': pd.Timestamp.now(), 
                                'Hábito': habit, 
                                'Status': 'Falhou', 
                                'Comentários': sermon
                            }])
                            st.session_state.records_df = pd.concat([st.session_state.records_df, new_rec], ignore_index=True)
                            st.rerun()

    with col_sug:
        if st.session_state.suggestion:
            st.subheader("⚡ LEVEL UP?")
            with st.container(border=True):
                st.markdown(st.session_state.suggestion)
                if st.button("🔥 ACEITAR DESAFIO"):
                    linhas = st.session_state.suggestion.split('\n')
                    n, m = "Nova Missão", "Mínimo"
                    for l in linhas:
                        if "NOME:" in l: n = l.split("NOME:")[1].strip()
                        if "MINIMO:" in l: m = l.split("MINIMO:")[1].strip()
                    
                    new_h = pd.DataFrame([{'Hábito': n, 'Unidade Atômica': m, 'Ativo': True}])
                    st.session_state.habits_df = pd.concat([st.session_state.habits_df, new_h], ignore_index=True)
                    st.session_state.suggestion = None
                    st.rerun()
                if st.button("Dispensar"):
                    st.session_state.suggestion = None
                    st.rerun()

# --- TAB 2: DASHBOARD ---
with tab2:
    st.header("📈 Relatório de Guerra")
    ensure_datetime()
    if not st.session_state.records_df.empty:
        streak_data = []
        for h in st.session_state.habits_df['Hábito'].unique():
            curr, best = calculate_streak(st.session_state.records_df, h)
            streak_data.append({"Hábito": h, "Atual 🔥": curr, "Recorde 🏆": best})
        st.table(pd.DataFrame(streak_data))
    else:
        st.info("Nenhum dado registrado ainda.")

# --- TAB 3: CONFIG ---
with tab3:
    st.header("⚙️ Gerenciar Arsenal")
    with st.form("new_mission"):
        n = st.text_input("Nome do Hábito")
        u = st.text_input("Mínimo Atômico")
        if st.form_submit_button("Adicionar"):
            if n:
                new_row = pd.DataFrame([{'Hábito': n, 'Unidade Atômica': u, 'Ativo': True}])
                st.session_state.habits_df = pd.concat([st.session_state.habits_df, new_row], ignore_index=True)
                st.rerun()

    if not st.session_state.habits_df.empty:
        edited = st.data_editor(st.session_state.habits_df, num_rows="dynamic")
        if st.button("Salvar Arsenal"):
            st.session_state.habits_df = edited
            st.rerun()
