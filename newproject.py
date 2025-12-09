import streamlit as st
import pandas as pd
from datetime import date, timedelta
# Importe a biblioteca do Gemini (o nome exato pode variar dependendo da versão)
from google import genai 
from google.genai.errors import APIError 

# --- 1. Funções de Suporte ---

def initialize_session_state():
    """Inicializa DataFrames e estados necessários."""
    if 'habits_df' not in st.session_state:
        st.session_state.habits_df = pd.DataFrame({
            'Hábito': ['Correr 5km', 'Ler 10 páginas', 'Estudo Silencioso 1h'],
            'Unidade Atômica': ['Colocar tênis', 'Ler 1 parágrafo', 'Abrir o livro'],
            'Ativo': [True, True, True]
        })
    if 'records_df' not in st.session_state:
        st.session_state.records_df = pd.DataFrame(columns=['Data', 'Hábito', 'Status', 'Comentários'])
        st.session_state.records_df['Data'] = pd.to_datetime(st.session_state.records_df['Data'])
    else:
        st.session_state.records_df['Data'] = pd.to_datetime(st.session_state.records_df['Data'])


def calculate_streak(records_df, habit_name):
    """Calcula a sequência atual (streak) e a melhor sequência (best_streak) para um hábito."""
    # Lógica de calculate_streak (A mesma da versão anterior, omitida aqui por concisão)
    successful_records = records_df[
        (records_df['Hábito'] == habit_name) & 
        (records_df['Status'] == 'Concluído')
    ].sort_values(by='Data', ascending=True).copy()

    if successful_records.empty:
        return 0, 0

    dates = successful_records['Data'].dt.date.unique()
    dates_list = sorted(list(dates))

    current_streak = 0
    best_streak = 0
    
    today = date.today()
    was_done_today = today in dates_list
    
    current_date_check = today if was_done_today else today - timedelta(days=1)
    
    temp_streak = 0
    for i in range(len(dates_list) - 1, -1, -1):
        d = dates_list[i]
        
        if d == current_date_check:
            temp_streak += 1
            current_date_check -= timedelta(days=1)
        elif d < current_date_check:
            break
            
    current_streak = temp_streak
    
    max_streak = 0
    if not dates_list:
        return current_streak, 0
    
    temp_max_streak = 1
    
    for i in range(1, len(dates_list)):
        if dates_list[i] == dates_list[i-1] + timedelta(days=1):
            temp_max_streak += 1
        else:
            max_streak = max(max_streak, temp_max_streak)
            temp_max_streak = 1
            
    max_streak = max(max_streak, temp_max_streak)
    
    return current_streak, max_streak


def generate_sermon(habit_name, excuse_text, api_key):
    """Gera um sermão e punição usando a API do Gemini."""
    
    try:
        # Configura o cliente Gemini
        client = genai.Client(api_key=api_key)
        
        # O prompt do Goggins
        prompt = f"""
        Você é um assistente de responsabilidade e disciplina no estilo de David Goggins.
        Sua tarefa é ser brutalmente honesto, motivacional e punitivo.
        
        O usuário falhou na tarefa: '{habit_name}'.
        A desculpa dada foi: '{excuse_text}'.
        
        Gere uma resposta em português que contenha:
        1. Um 'Sermão no Espelho' curto e direto, criticando a fraqueza do usuário e a desculpa.
        2. Uma 'Punição Física' clara e mensurável (algo como flexões, corrida extra, ou banho gelado) para ser feita IMEDIATAMENTE.
        
        Formate a resposta estritamente da seguinte maneira:
        ---
        🚨 SERMÃO NO ESPELHO
        [Seu Sermão de Crítica Aqui]
        
        ⚖️ PUNIÇÃO IMEDIATA
        [Sua Punição Clara Aqui]
        ---
        """

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        return response.text
    
    except APIError as e:
        return f"ERRO NA API GEMINI: Falha na comunicação. Verifique a chave e o status da API. Detalhes: {e}"
    except Exception as e:
        return f"ERRO INESPERADO: {e}"

# --- 2. Configuração e Inicialização ---

st.set_page_config(layout="wide", page_title="Disciplina Implacável | Atomic Goggins")
initialize_session_state()

st.title("🔥 O Espelho da Responsabilidade (David Goggins Style)")
st.markdown("---")

# ==============================================================================
#                             CONFIGURAÇÃO DE CHAVE API
# ==============================================================================

if 'gemini_api_key' not in st.session_state or not st.session_state.gemini_api_key:
    st.subheader("🔑 Chave API Gemini - Necessária para o Sermão")
    st.info("Insira sua chave API do Gemini para habilitar o modo 'Accountability Mirror'. Sua chave não será salva além desta sessão.")
    
    api_key_input = st.text_input(
        "Sua Chave API do Gemini:", 
        type="password", 
        key="api_key_input_field"
    )
    
    if st.button("Salvar Chave e Continuar"):
        if api_key_input.strip():
            st.session_state.gemini_api_key = api_key_input.strip()
            st.toast("Chave API salva! O modo Goggins está ativado.", icon="🔥")
            st.rerun() # Recarrega para limpar o campo de input
        else:
            st.error("Por favor, insira uma chave válida.")
            
    # Se a chave não estiver configurada, pare o resto do aplicativo
    st.stop() 

# --- 3. Estrutura de Abas (Só aparece após a chave ser salva) ---
tab1, tab2, tab3 = st.tabs(["🎯 Get After It (Hoje)", "📈 Painel de Controle", "⚙️ Gerenciar Hábitos"])

# ==============================================================================
#                             TAB 1: REGISTRO DIÁRIO
# ==============================================================================
with tab1:
    st.header("Missão de Hoje: Sem Desculpas.")
    today = date.today()
    
    active_habits = st.session_state.habits_df[st.session_state.habits_df['Ativo'] == True]

    if active_habits.empty:
        st.warning("Você não tem hábitos ativos. Vá para a aba 'Gerenciar Hábitos' e defina sua missão!")
    
    for _, row in active_habits.iterrows():
        habit = row['Hábito']
        atomic_unit = row['Unidade Atômica']
        
        st.subheader(f"💪 {habit}")
        st.info(f"👉 **Unidade Atômica Mínima:** *{atomic_unit}*")
        
        col1, col2 = st.columns([0.2, 0.8])
        
        existing_record = st.session_state.records_df[
            (st.session_state.records_df['Data'].dt.date == today) & 
            (st.session_state.records_df['Hábito'] == habit)
        ]
        
        if not existing_record.empty:
            status = existing_record['Status'].iloc[0]
            comment = existing_record['Comentários'].iloc[0]
            
            if status == 'Concluído':
                st.success(f"✅ **CONCLUÍDO HOJE!** Você fez o que devia. *({comment})*")
            else:
                st.error(f"❌ **FALHOU HOJE.** Olhe para o espelho. Seu sermão está abaixo.")
                st.code(comment, language='markdown') # Exibe o sermão gerado
            st.markdown("---")
            continue

        # Formulário de Registro Rápido
        with col1:
            if st.button("✅ Concluído", key=f"done_{habit}", type="primary"):
                new_record = {'Data': today, 'Hábito': habit, 'Status': 'Concluído', 'Comentários': 'Nenhuma desculpa, apenas trabalho.'}
                st.session_state.records_df = pd.concat([st.session_state.records_df, pd.DataFrame([new_record])], ignore_index=True)
                st.rerun()

        with col2:
            # Formulário de Falha com Geração de Sermão
            with st.expander("❌ Registrar Falha e Receber Sermão"):
                with st.form(key=f"fail_form_{habit}"):
                    st.write(f"**Qual foi a desculpa para não fazer {habit}?** Seja brutalmente honesto.")
                    excuse_input = st.text_area("Desculpa (Obrigatório):", height=50)
                    
                    if st.form_submit_button("Gerar Sermão e Registrar Falha 📉"):
                        if excuse_input:
                            # Chama o Gemini para gerar o sermão
                            with st.spinner("Gerando Sermão e Punição..."):
                                sermon_and_punishment = generate_sermon(
                                    habit, 
                                    excuse_input, 
                                    st.session_state.gemini_api_key
                                )
                            
                            # Registra o resultado do Gemini como o 'Comentário'
                            new_record = {'Data': today, 'Hábito': habit, 'Status': 'Falhou', 'Comentários': sermon_and_punishment}
                            st.session_state.records_df = pd.concat([st.session_state.records_df, pd.DataFrame([new_record])], ignore_index=True)
                            st.rerun()
                        else:
                            st.warning("Você deve registrar o porquê falhou para receber a punição.")
        
        st.markdown("---")


# ==============================================================================
#                             TAB 2 E 3 (Inalteradas)
# ==============================================================================
with tab2:
    st.header("📈 Seu Desempenho: O Espelho da Responsabilidade")
    st.markdown("Este painel não mente. Ele mostra a consistência brutal.")
    
    if st.session_state.records_df.empty:
        st.info("Ainda não há registros de hábitos. Comece a rastrear!")
    else:
        st.subheader("Sequências (Streaks)")
        streak_data = []
        for habit in st.session_state.habits_df[st.session_state.habits_df['Ativo'] == True]['Hábito']:
            current_s, best_s = calculate_streak(st.session_state.records_df, habit)
            streak_data.append({
                'Hábito': habit,
                '🔥 Sequência Atual': current_s,
                '🏆 Melhor Sequência': best_s
            })

        st.table(pd.DataFrame(streak_data).set_index('Hábito'))
        
        st.markdown("---")
        
        st.subheader("Taxa de Sucesso nos Últimos 30 Dias")
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

with tab3:
    st.header("⚙️ Gerenciar Minhas Missões (Hábitos)")
    
    st.subheader("➕ Adicionar Nova Missão")
    with st.form("new_habit_form"):
        new_habit_name = st.text_input("Nome do Hábito/Missão (Ex: Meditar 10min)")
        new_atomic_unit = st.text_input("Unidade Atômica (O Mínimo para não quebrar a corrente. Ex: Sentar no tapete)")
        
        submitted = st.form_submit_button("Adicionar Hábito")
        if submitted and new_habit_name:
            if new_habit_name in st.session_state.habits_df['Hábito'].values:
                st.warning("Este hábito já existe.")
            else:
                new_row = pd.DataFrame([{'Hábito': new_habit_name, 'Unidade Atômica': new_atomic_unit, 'Ativo': True}])
                st.session_state.habits_df = pd.concat([st.session_state.habits_df, new_row], ignore_index=True)
                st.success(f"Hábito '{new_habit_name}' adicionado! Agora vá executá-lo.")
                st.rerun()

    st.markdown("---")

    st.subheader("📚 Lista de Hábitos Atuais")
    
    st.dataframe(
        st.session_state.habits_df.set_index('Hábito'),
        column_order=('Ativo', 'Unidade Atômica'),
        column_config={
            "Ativo": st.column_config.CheckboxColumn("Ativo?", default=True),
            "Unidade Atômica": st.column_config.TextColumn("Unidade Atômica Mínima", help="O Mínimo para começar (Atomic Habit)")
        },
        hide_index=False,
        use_container_width=True
    )
    
    st.caption("Para atualização persistente, você precisará salvar o DataFrame em um arquivo (ex: CSV) e recarregá-lo na inicialização do app.")

# --- FIM DO APP ---
st.markdown("---")
st.markdown("<footer>**Stay Hard!**</footer>", unsafe_allow_html=True)
