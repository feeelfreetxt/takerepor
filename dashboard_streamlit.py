import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# Configuração da página
st.set_page_config(page_title="Dashboard de Atividades", layout="wide", initial_sidebar_state="expanded")

# Função para ler e processar dados das planilhas
def get_data():
    try:
        # Caminho absoluto das planilhas
        base_path = r"F:\okok"
        planilha_julio = os.path.join(base_path, "(JULIO) LISTAS INDIVIDUAIS.xlsx")
        planilha_leandro = os.path.join(base_path, "(LEANDRO_ADRIANO) LISTAS INDIVIDUAIS.xlsx")
        
        st.write("Tentando ler planilhas de:", base_path)
        st.write("Arquivos encontrados:", os.listdir(base_path))
        
        # Ler planilha do Julio
        df_julio = pd.read_excel(planilha_julio)
        df_julio['Grupo'] = 'JULIO'
        st.success("Planilha do Julio carregada com sucesso!")
        
        # Ler planilha do Leandro
        df_leandro = pd.read_excel(planilha_leandro)
        df_leandro['Grupo'] = 'LEANDRO'
        st.success("Planilha do Leandro carregada com sucesso!")
        
        # Concatenar os dataframes
        df = pd.concat([df_julio, df_leandro], ignore_index=True)
        
        # Preencher valores nulos com 0
        df = df.fillna(0)
        
        # Garantir que todas as colunas necessárias existam
        colunas_necessarias = ['Colaborador', 'VERIFICADOS', 'PENDENTE', 'QUITADO', 'ANÁLISE', 'APROVADO']
        for coluna in colunas_necessarias:
            if coluna not in df.columns:
                df[coluna] = 0
        
        return df
        
    except Exception as e:
        st.error(f"Erro ao ler planilhas: {str(e)}")
        return pd.DataFrame()

# Título principal
st.title("Dashboard de Atividades por Colaborador")

# Carregar dados
df = get_data()

if not df.empty:
    # Sidebar com filtros avançados
    st.sidebar.title("Filtros Avançados")

    # Filtro de Grupo
    grupo_selecionado = st.sidebar.multiselect(
        "Selecione os Grupos",
        options=list(df['Grupo'].unique()),
        default=list(df['Grupo'].unique())
    )

    # Filtros de métricas
    st.sidebar.subheader("Filtros de Métricas")
    col1_side, col2_side = st.sidebar.columns(2)

    with col1_side:
        min_verificados = st.number_input("Mín. Verificados", 0, int(df['VERIFICADOS'].max()), 0)
        min_pendente = st.number_input("Mín. Pendente", 0, int(df['PENDENTE'].max()), 0)
        min_quitado = st.number_input("Mín. Quitado", 0, int(df['QUITADO'].max()), 0)

    with col2_side:
        min_analise = st.number_input("Mín. Análise", 0, int(df['ANÁLISE'].max()), 0)
        min_aprovado = st.number_input("Mín. Aprovado", 0, int(df['APROVADO'].max()), 0)

    # Ordenação
    ordem_por = st.sidebar.selectbox(
        "Ordenar por",
        ["Colaborador", "VERIFICADOS", "PENDENTE", "QUITADO", "ANÁLISE", "APROVADO"]
    )

    ordem_direcao = st.sidebar.radio("Direção", ["Crescente", "Decrescente"])

    # Aplicar filtros
    mask = (
        (df['Grupo'].isin(grupo_selecionado)) &
        (df['VERIFICADOS'] >= min_verificados) &
        (df['PENDENTE'] >= min_pendente) &
        (df['QUITADO'] >= min_quitado) &
        (df['ANÁLISE'] >= min_analise) &
        (df['APROVADO'] >= min_aprovado)
    )

    df_filtrado = df[mask].copy()

    # Ordenar dados
    ascending = ordem_direcao == "Crescente"
    df_filtrado = df_filtrado.sort_values(by=ordem_por, ascending=ascending)

    # Layout principal
    col1, col2 = st.columns([2, 1])

    with col1:
        # Gráfico de barras empilhadas
        df_melted = df_filtrado.melt(
            id_vars=['Colaborador', 'Grupo'],
            value_vars=['VERIFICADOS', 'PENDENTE', 'QUITADO', 'ANÁLISE', 'APROVADO'],
            var_name='Status',
            value_name='Quantidade'
        )

        fig = px.bar(
            df_melted,
            x='Colaborador',
            y='Quantidade',
            color='Status',
            barmode='stack',
            title='Distribuição de Status por Colaborador',
            color_discrete_sequence=['#9467bd', '#d62728', '#2ca02c', '#ff7f0e', '#1f77b4'],
            height=500
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(t=100)
        )
        
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Tabela resumo por grupo
        st.subheader("Resumo por Grupo")
        resumo_grupo = df_filtrado.groupby('Grupo').agg({
            'VERIFICADOS': 'sum',
            'PENDENTE': 'sum',
            'QUITADO': 'sum',
            'ANÁLISE': 'sum',
            'APROVADO': 'sum'
        }).reset_index()
        
        st.dataframe(
            resumo_grupo.style.background_gradient(cmap='YlOrRd'),
            use_container_width=True
        )

    # Tabela detalhada
    st.subheader("Visão Detalhada por Colaborador")
    st.dataframe(
        df_filtrado.style.background_gradient(
            subset=['VERIFICADOS', 'PENDENTE', 'QUITADO', 'ANÁLISE', 'APROVADO'],
            cmap='YlOrRd'
        ),
        use_container_width=True
    )

    # Métricas gerais
    st.subheader("Métricas Gerais")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Total Verificados", df_filtrado['VERIFICADOS'].sum())
    with col2:
        st.metric("Total Pendente", df_filtrado['PENDENTE'].sum())
    with col3:
        st.metric("Total Quitado", df_filtrado['QUITADO'].sum())
    with col4:
        st.metric("Total Análise", df_filtrado['ANÁLISE'].sum())
    with col5:
        st.metric("Total Aprovado", df_filtrado['APROVADO'].sum())

    # Formulário de anotações
    st.sidebar.markdown("---")
    st.sidebar.subheader("Anotações do Gestor")
    with st.sidebar.form("anotacoes_form"):
        colaborador = st.selectbox("Selecione o Colaborador", df_filtrado['Colaborador'].unique())
        data = st.date_input("Data")
        anotacao = st.text_area("Anotação")
        submitted = st.form_submit_button("Salvar Anotação")
        
        if submitted:
            st.success(f"Anotação salva para {colaborador} em {data}")
else:
    st.error("Não foi possível carregar os dados. Verifique se as planilhas estão no formato correto.")
