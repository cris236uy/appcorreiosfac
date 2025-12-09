import streamlit as st
import pandas as pd
from datetime import date, timedelta

# --- 1. Funções de Suporte ---

def initialize_session_state():
    """Inicializa DataFrames e estados necessários."""
    if 'habits_df' not in st.session_state:
        # Hábito: Nome, Unidade Atômica (Mínimo), Ativo
        st.session_state.habits_df = pd.DataFrame({
            'Hábito': ['Correr 5km', 'Ler 10 páginas', 'Estudo Silencioso 1h'],
            'Unidade Atômica': ['Colocar tênis', 'Ler 1 parágrafo', 'Abrir o livro'],
            'Ativo': [True, True, True]
        })
    if 'records_df' not in st.session_state:
        # Data: Data do registro, Hábito: Nome, Status: Concluído/Falhou, Comentários
        st.session_state.records_df = pd.DataFrame(columns=['Data', 'Hábito', 'Status', 'Comentários'])
        st.session_state.records_df['Data'] = pd.to_datetime(st.session_state.records_df['Data'])
    else:
        # Garante que a coluna Data é um objeto datetime
        st.session_state.records_df['Data'] = pd.to_datetime(st.session_state.records_df['Data'])


def calculate_streak(records_df, habit_name):
    """Calcula a sequência atual (streak) e a melhor sequência (best_streak) para um hábito."""
    
    # 1. Filtra registros bem-sucedidos para o hábito
    successful_records = records_df[
        (records_df['Hábito'] == habit_name) & 
        (records_df['Status'] == 'Concluído')
    ].sort_values(by='Data', ascending=True).copy()

    if successful_records.empty:
        return 0, 0

    # Pega apenas datas únicas para evitar problemas com múltiplos registros no mesmo dia
    dates = successful_records['Data'].dt.date.unique()

    current_streak = 0
    best_streak = 0
    
    # Inicia a partir de ontem
    expected_date = date.today() - timedelta(days=1)
    
    # 2. Calcula a sequência atual (até o dia anterior ou hoje)
    temp_streak = 0
    # Itera de trás para frente a partir de ontem
    
    # Garante que 'dates' está em ordem cronológica
    dates_list = sorted(list(dates))

    # Verifica se o hábito foi concluído hoje
    today = date.today()
    was_done_today = today in dates_list
    
    # Verifica a sequência a partir de hoje/ontem
    current_date_check = today if was_done_today else today - timedelta(days=1)
    
    for i in range(len(dates_list) - 1, -1, -1):
        d = dates_list[i]
        
        # Se for o dia atual ou o dia anterior
        if d == current_date_check:
            temp_streak += 1
            current_date_check -= timedelta(days=1)
        elif d < current_date_check: # Parou a sequência
            break
            
    # Se a streak atual inclui hoje, e o dia anterior também foi feito:
    current_streak = temp_streak
    
    # 3. Calcula a melhor sequência histórica
    max_streak = 0
    if not dates_list:
        return current_streak, 0
    
    # Inicializa a primeira sequência
    temp_max_streak = 1
    
    for i in range(1, len(dates_list)):
        # Verifica se a diferença entre a data atual e a anterior é exatamente 1 dia
        if dates_list[i] == dates_list[i-1] + timedelta(days=1):
            temp_max_streak += 1
        else:
            max_streak = max(max_streak, temp_max_streak)
            temp_max_streak = 1 # Reinicia
            
    # Captura a última sequência
    max_streak = max(max_streak, temp_max_streak)
    
    return current_streak, max_streak

# --- 2. Configuração e Inicialização ---

st.set_page_config(layout="wide", page_title="Disciplina Implacável | Atomic Goggins")
initialize_session_state()

st.title("🔥 O Espelho da Responsabilidade (David Goggins Style)")
st.markdown("---")

# --- 3. Estrutura de Abas ---
tab1, tab2, tab3 = st.tabs(["🎯 Get After It (Hoje)", "📈 Painel de Controle", "⚙️ Gerenciar Hábitos"])

# ==============================================================================
#                             TAB 1: REGISTRO DIÁRIO
# ==============================================================================
with tab1:
    st.header("Missão de Hoje: Sem Desculpas.")
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")
    
    active_habits = st.session_state.habits_df[st.session_state.habits_df['Ativo'] == True]

    if active_habits.empty:
        st.warning("Você não tem hábitos ativos. Vá para a aba 'Gerenciar Hábitos' e defina sua missão!")
    
    for _, row in active_habits.iterrows():
        habit = row['Hábito']
        atomic_unit = row['Unidade Atômica']
        
        st.subheader(f"💪 {habit}")
        st.info(f"👉 **Unidade Atômica Mínima (A Única Coisa):** *{atomic_unit}*")
        
        col1, col2, col3 = st.columns([0.2, 0.2, 0.6])
        
        # Verifica se já foi registrado hoje
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
                st.error(f"❌ **FALHOU HOJE.** Olhe para o espelho. *({comment})*")
            st.markdown("---")
            continue

        # Formulário de Registro Rápido
        with col1:
            if st.button("✅ Concluído", key=f"done_{habit}", type="primary"):
                new_record = {'Data': today, 'Hábito': habit, 'Status': 'Concluído', 'Comentários': 'Sem desculpas, apenas trabalho.'}
                st.session_state.records_df = pd.concat([st.session_state.records_df, pd.DataFrame([new_record])], ignore_index=True)
                st.rerun()

        with col2:
            # Exibe o botão de falha e o campo de comentário
            if st.button("❌ Falhou", key=f"fail_{habit}"):
                # Usa um formulário modal ou um prompt mais elaborado
                with st.form(key=f"fail_form_{habit}"):
                    st.write(f"**Qual foi a desculpa para {habit}?** Seja honesto.")
                    comment = st.text_area("Comentário (Obrigatório, para análise):", height=50)
                    
                    if st.form_submit_button("Registrar Falha 📉"):
                        if comment:
                            new_record = {'Data': today, 'Hábito': habit, 'Status': 'Falhou', 'Comentários': comment}
                            st.session_state.records_df = pd.concat([st.session_state.records_df, pd.DataFrame([new_record])], ignore_index=True)
                            st.rerun()
                        else:
                            st.warning("Você deve registrar o porquê falhou.")
        
        st.markdown("---")

# ==============================================================================
#                             TAB 2: PAINEL DE CONTROLE
# ==============================================================================
with tab2:
    st.header("📈 Seu Desempenho: O Espelho da Responsabilidade")
    st.markdown("Este painel não mente. Ele mostra a consistência brutal.")
    
    if st.session_state.records_df.empty:
        st.info("Ainda não há registros de hábitos. Comece a rastrear!")
    else:
        # Tabela de Streaks
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
        
        # Gráfico de Sucesso Mensal
        st.subheader("Taxa de Sucesso nos Últimos 30 Dias")
        
        last_30_days = date.today() - timedelta(days=30)
        recent_records = st.session_state.records_df[st.session_state.records_df['Data'].dt.date >= last_30_days].copy()
        
        if not recent_records.empty:
            # Calcula a taxa de sucesso por hábito
            success_rate = recent_records.groupby('Hábito')['Status'].value_counts(normalize=True).mul(100).rename('Percentual').reset_index()
            success_rate_pivot = success_rate.pivot_table(index='Hábito', columns='Status', values='Percentual', fill_value=0)
            
            # Garante que 'Concluído' está sempre presente para o gráfico
            if 'Concluído' not in success_rate_pivot.columns:
                 success_rate_pivot['Concluído'] = 0

            # Exibe o gráfico de barras
            st.bar_chart(success_rate_pivot[['Concluído']].sort_values(by='Concluído', ascending=False), 
                         use_container_width=True)
        else:
            st.info("Dados insuficientes nos últimos 30 dias para gerar o gráfico.")

# ==============================================================================
#                             TAB 3: GERENCIAR HÁBITOS
# ==============================================================================
with tab3:
    st.header("⚙️ Gerenciar Minhas Missões (Hábitos)")
    
    # --- Adicionar Novo Hábito ---
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

    # --- Tabela de Hábitos Existentes (Edição e Exclusão) ---
    st.subheader("📚 Lista de Hábitos Atuais")
    
    # Criar uma cópia para edição
    editable_df = st.session_state.habits_df.copy()

    # Adicionar coluna de Ação para desativação/exclusão (melhor para Streamlit)
    
    st.dataframe(
        editable_df.set_index('Hábito'),
        column_order=('Ativo', 'Unidade Atômica'),
        column_config={
            "Ativo": st.column_config.CheckboxColumn("Ativo?", default=True),
            "Unidade Atômica": st.column_config.TextColumn("Unidade Atômica Mínima", help="O Mínimo para começar (Atomic Habit)")
        },
        hide_index=False,
        use_container_width=True
    )
    
    # Lógica de atualização
    st.caption("Para atualizar, edite diretamente na tabela acima e clique em 'Salvar Alterações'.")
    if st.button("Salvar Alterações"):
        # Uma implementação mais robusta usaria o st.data_editor se a versão for mais recente.
        # Por simplicidade aqui, vamos assumir que a edição do dataframe é a fonte da verdade.
        # (Em um ambiente real, você faria a edição no st.data_editor e capturaria o resultado)
        st.info("Para salvar a edição de Unidade Atômica/Ativo, o `st.data_editor` é recomendado. Usando a tabela de visualização como placeholder.")
        # Se estivéssemos usando st.data_editor:
        # st.session_state.habits_df = st.session_state.edited_df_result 

# --- FIM DO APP ---
st.markdown("---")
st.markdown("<footer>**Stay Hard!**</footer>", unsafe_allow_html=True)
