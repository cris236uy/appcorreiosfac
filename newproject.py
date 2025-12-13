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
        # Garante que a coluna Data é um objeto Datetime na criação
        st.session_state.records_df['Data'] = pd.to_datetime(st.session_state.records_df['Data'])
    else:
        # Garante que a coluna Data é um objeto Datetime em sessões subsequentes
        ensure_datetime() 
    
    if 'suggestion' not in st.session_state:
        st.session_state.suggestion = None

def ensure_datetime():
    """Garante que a coluna Data seja sempre datetime para evitar o AttributeError."""
    if not st.session_state.records_df.empty:
        # Usa errors='coerce' para lidar com qualquer valor não-data, transformando-o em NaT (Not a Time)
        st.session_state.records_df['Data'] = pd.to_datetime(st.session_state.records_df['Data'], errors='coerce')
        # Opcional: remover linhas com data inválida
        st.session_state.records_df.dropna(subset=['Data'], inplace=True)

def calculate_streak(records_df, habit_name):
    """Calcula a sequência atual e a melhor sequência."""
    if records_df.empty: return 0, 0
    
    successful_records = records_df[
        (records_df['Hábito'] == habit_name) & (records_df['Status'] == 'Concluído')
    ].copy()
    
    if successful_records.empty: return 0, 0

    dates_list = sorted(list(successful_records['Data'].dt.date.unique()))
    
    # Lógica de Streak Atual (mantida para robustez)
    current_streak = 0
    today = date.today()
    # Verifica se o último registro foi hoje ou ontem para iniciar a contagem da streak atual
    check_date = today if today in dates_list else today - timedelta(days=1)
    
    for i in range(len(dates_list) - 1, -1, -1):
        if dates_list[i] == check_date:
            current_streak += 1
            check_date -= timedelta(days=1)
        else: break
            
    # Lógica de Melhor Streak (mantida para robustez)
    max_streak, temp_max = 0, 1
    if dates_list:
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
        # --- ONDE A CONEXÃO É FEITA ---
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        return response.text
    except APIError as e:
        # Captura erros específicos da API para um feedback melhor
        return f"ERRO NA API (APIError): Falha ao se comunicar. Verifique a chave ou o limite. Detalhes: {e}"
    except Exception as e:
        return f"ERRO NA API (Geral): {e}"

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

# ==============================================================================
#                      CONFIGURAÇÃO E AUTENTICAÇÃO DA API
# ==============================================================================

if 'gemini_api_key' not in st.session_state or not st.session_state.gemini_api_key:
    with st.container(border=True):
        st.subheader("🔑 Configuração Inicial: Chave Gemini")
        st.info("A chave API é necessária para o 'Sermão' e o 'Level Up' de David Goggins.")
        
        api_input = st.text_input(
            "Insira sua API Key do Gemini:", 
            type="password",
            key="api_key_input"
        )
        
        if st.button("Ativar Modo Goggins"):
            if api_input:
                st.session_state.gemini_api_key = api_input
                st.success("Chave salva! Prepare-se para sofrer.")
                st.rerun()
            else:
                st.error("Por favor, insira uma chave válida.")
    st.stop()
else:
    api_key = st.session_state.gemini_api_key

# --- 3. Estrutura de Abas ---
tab1, tab2, tab3 = st.tabs(["🎯 Missões de Hoje", "📈 O Espelho (Stats)", "⚙️ Arsenal (Config)"])

# --- TAB 1: REGISTRO DIÁRIO ---
with tab1:
    col_main, col_sug = st.columns([0.6, 0.4])
    
    with col_main:
        st.header("Missão Diária")
        active_habits = st.session_state.habits_df[st.session_state.habits_df['Ativo'] == True]
        
        if active_habits.empty:
            st.info("Nenhuma missão ativa no arsenal. Vá para a aba 'Arsenal' e comece a sofrer.")
        
        for _, row in active_habits.iterrows():
            habit = row['Hábito']
            with st.expander(f"💪 {habit}", expanded=True):
                st.write(f"Meta Mínima: `{row['Unidade Atômica']}`")
                
                df_records = st.session_state.records_df
                # Filtragem segura
                reg_hoje = df_records[
                    (df_records['Data'].dt.date == date.today()) & 
                    (df_records['Hábito'] == habit)
                ]
                
                if not reg_hoje.empty:
                    status = reg_hoje.iloc[0]['Status']
                    comment = reg_hoje.iloc[0]['Comentários']
                    if status == 'Concluído':
                        st.success(f"✅ Missão Cumprida! ({comment})")
                    else:
                        st.error("❌ Você falhou nesta missão hoje. Leia seu sermão abaixo:")
                        st.code(comment, language="markdown")
                else:
                    c1, c2 = st.columns(2)
                    
                    # Ação de Concluído (Gera Upgrade)
                    if c1.button("✅ Concluído", key=f"done_{habit}", type="primary"):
                        new_rec = pd.DataFrame([{
                            'Data': pd.Timestamp.now(), 
                            'Hábito': habit, 
                            'Status': 'Concluído', 
                            'Comentários': 'Sem desculpas.'
                        }])
                        st.session_state.records_df = pd.concat([st.session_state.records_df, new_rec], ignore_index=True)
                        with st.spinner("Goggins está analisando seu progresso para o próximo nível..."):
                            st.session_state.suggestion = generate_next_level_suggestion(habit, api_key) # Usa a chave
                        st.rerun()
                        
                    # Ação de Falha (Gera Sermão)
                    with c2:
                        with st.form(key=f"fail_form_{habit}"):
                            motivo = st.text_input("Qual sua desculpa?", key=f"exc_input_{habit}")
                            if st.form_submit_button("❌ Gerar Sermão e Registrar Falha"):
                                if motivo:
                                    with st.spinner("Preparando o Sermão e a Punição..."):
                                        prompt_sermon = f"""
                                        Você é David Goggins. O usuário falhou em '{habit}' por: '{motivo}'. 
                                        Dê um sermão curto, brutal e motivacional, seguido de uma punição física clara (ex: 50 flexões, 1 hora de corrida extra) em português.
                                        """
                                        sermon = call_gemini(prompt_sermon, api_key) # Usa a chave
                                    
                                    new_rec = pd.DataFrame([{
                                        'Data': pd.Timestamp.now(), 
                                        'Hábito': habit, 
                                        'Status': 'Falhou', 
                                        'Comentários': sermon
                                    }])
                                    st.session_state.records_df = pd.concat([st.session_state.records_df, new_rec], ignore_index=True)
                                    st.rerun()
                                else:
                                    st.warning("Você deve fornecer uma desculpa para o David Goggins te punir.")

    # Cartão de Sugestão de Level Up
    with col_sug:
        if st.session_state.suggestion:
            st.subheader("⚡ LEVEL UP DETECTADO")
            with st.container(border=True):
                st.markdown(st.session_state.suggestion)
                
                col_s1, col_s2 = st.columns(2)
                
                if col_s1.button("🔥 ACEITAR NOVO DESAFIO", use_container_width=True):
                    linhas = st.session_state.suggestion.split('\n')
                    n, m = "Nova Missão (Nome não encontrado)", "Mínimo (Não encontrado)"
                    for l in linhas:
                        if "NOME:" in l: n = l.split("NOME:")[1].strip()
                        if "MINIMO:" in l: m = l.split("MINIMO:")[1].strip()
                    
                    new_h = pd.DataFrame([{'Hábito': n, 'Unidade Atômica': m, 'Ativo': True}])
                    st.session_state.habits_df = pd.concat([st.session_state.habits_df, new_h], ignore_index=True)
                    st.session_state.suggestion = None
                    st.toast(f"Missão '{n}' adicionada ao seu arsenal!", icon="💥")
                    st.rerun()
                
                if col_s2.button("Dispensar (Vou descansar)", use_container_width=True):
                    st.session_state.suggestion = None
                    st.rerun()

# --- TAB 2: DASHBOARD ---
with tab2:
    st.header("📈 O Espelho da Realidade")
    
    if not st.session_state.records_df.empty:
        st.subheader("Sequências Atuais (Streaks)")
        streak_data = []
        for h in st.session_state.habits_df['Hábito'].unique():
            curr, best = calculate_streak(st.session_state.records_df, h)
            streak_data.append({"Hábito": h, "Atual 🔥": curr, "Recorde 🏆": best})
        st.table(pd.DataFrame(streak_data))
        
        st.subheader("Resumo de Sucesso (Últimos 30 Dias)")
        # Lógica de Gráfico de Sucesso (Implementação Adicional)
        last_30_days = date.today() - timedelta(days=30)
        recent_records = st.session_state.records_df[st.session_state.records_df['Data'].dt.date >= last_30_days].copy()
        
        if not recent_records.empty:
            success_rate = recent_records.groupby('Hábito')['Status'].value_counts(normalize=True).mul(100).rename('Percentual').reset_index()
            success_rate_pivot = success_rate.pivot_table(index='Hábito', columns='Status', values='Percentual', fill_value=0)
            
            if 'Concluído' not in success_rate_pivot.columns:
                 success_rate_pivot['Concluído'] = 0

            st.bar_chart(success_rate_pivot[['Concluído']].sort_values(by='Concluído', ascending=False), 
                         use_container_width=True)
        else:
            st.info("Dados insuficientes nos últimos 30 dias para gerar o gráfico.")
            
    else:
        st.info("Nenhum dado registrado ainda.")

# --- TAB 3: CONFIG ---
with tab3:
    st.header("⚙️ Gerenciar Arsenal de Missões")
    
    st.subheader("➕ Adicionar Nova Missão")
    with st.form("new_mission"):
        n = st.text_input("Nome do Hábito/Missão")
        u = st.text_input("Unidade Atômica (O mínimo aceitável)")
        if st.form_submit_button("Adicionar Hábito"):
            if n:
                new_row = pd.DataFrame([{'Hábito': n, 'Unidade Atômica': u, 'Ativo': True}])
                st.session_state.habits_df = pd.concat([st.session_state.habits_df, new_row], ignore_index=True)
                st.toast(f"Hábito '{n}' adicionado!", icon="➕")
                st.rerun()

    st.subheader("📝 Editar Hábitos Existentes")
    if not st.session_state.habits_df.empty:
        edited = st.data_editor(st.session_state.habits_df, num_rows="dynamic", key="habit_data_editor")
        if st.button("Salvar Alterações no Arsenal"):
            st.session_state.habits_df = edited
            st.toast("Arsenal salvo!", icon="💾")
            st.rerun()
