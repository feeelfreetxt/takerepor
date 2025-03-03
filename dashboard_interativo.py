import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from collections import defaultdict, Counter
import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Dashboard Interativo de Colaboradores",
    page_icon="📊",
    layout="wide"
)

# Título principal
st.title("Dashboard Interativo de Colaboradores")
st.write(f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

# Função para normalizar nomes das colunas
def normalizar_coluna(coluna):
    coluna = str(coluna).strip().upper()
    mapeamento = {
        'SITUAÇÂO': 'SITUACAO',
        'SITUAÇÃO': 'SITUACAO',
    }
    return mapeamento.get(coluna, coluna)

# Função para carregar dados
@st.cache_data
def carregar_dados(arquivo):
    try:
        # Carregar todas as abas do arquivo Excel
        xls = pd.ExcelFile(arquivo)
        
        # Filtrar abas válidas (excluir abas de teste ou relatório geral)
        abas_validas = [aba for aba in xls.sheet_names if aba not in ["", "TESTE", "RELATÓRIO GERAL"]]
        
        dados_colaboradores = {}
        for aba in abas_validas:
            # Carregar dados da aba
            df = pd.read_excel(arquivo, sheet_name=aba)
            
            # Normalizar nomes das colunas
            df.columns = [normalizar_coluna(col) for col in df.columns]
            
            # Armazenar dados do colaborador
            dados_colaboradores[aba] = df
        
        return dados_colaboradores, abas_validas
    except Exception as e:
        st.error(f"Erro ao carregar dados do arquivo {os.path.basename(arquivo)}: {str(e)}")
        return {}, []

# Função para analisar dados de um colaborador
def analisar_colaborador(df, nome_colaborador):
    if df is None or len(df) == 0:
        st.warning(f"Não há dados para o colaborador {nome_colaborador}")
        return {}
    
    # Estatísticas básicas
    total_registros = len(df)
    
    # Análise da coluna SITUACAO
    situacao_counts = {}
    situacao_percentual = {}
    registros_vazios = 0
    valores_nao_padronizados = []
    
    if 'SITUACAO' in df.columns:
        situacao_counts = df['SITUACAO'].value_counts().to_dict()
        situacao_percentual = {k: v/total_registros*100 for k, v in situacao_counts.items()}
        
        # Valores vazios
        registros_vazios = df['SITUACAO'].isna().sum()
        
        # Valores padronizados
        valores_padronizados = ['PENDENTE', 'VERIFICADO', 'APROVADO', 'QUITADO', 'CANCELADO', 'EM ANÁLISE', 'ANÁLISE', 'PRIORIDADE']
        valores_unicos = [v for v in df['SITUACAO'].dropna().unique()]
        valores_nao_padronizados = [v for v in valores_unicos if v not in valores_padronizados]
    
    # Análise temporal
    analise_temporal = {}
    colunas_data = [col for col in df.columns if 'DATA' in col]
    
    for col_data in colunas_data:
        try:
            df[col_data] = pd.to_datetime(df[col_data], errors='coerce')
            datas_validas = df[col_data].dropna()
            
            if len(datas_validas) > 0:
                periodo = {
                    'min': datas_validas.min().date(),
                    'max': datas_validas.max().date(),
                    'registros': len(datas_validas),
                    'percentual': len(datas_validas)/total_registros*100
                }
                
                # Análise de transições se houver SITUACAO
                transicoes = []
                tempos_por_situacao = {}
                
                if 'SITUACAO' in df.columns:
                    df_ordenado = df.sort_values(by=col_data)
                    
                    # Verificar transições de estado
                    situacao_anterior = None
                    
                    for idx, row in df_ordenado.iterrows():
                        situacao_atual = row['SITUACAO']
                        if pd.notna(situacao_anterior) and pd.notna(situacao_atual) and situacao_anterior != situacao_atual:
                            transicoes.append((situacao_anterior, situacao_atual))
                        situacao_anterior = situacao_atual
                    
                    # Contar transições
                    contagem_transicoes = Counter(transicoes)
                    
                    # Tempo médio em cada situação
                    df_ordenado['data_anterior'] = df_ordenado[col_data].shift(1)
                    df_ordenado['tempo_no_estado'] = (df_ordenado[col_data] - df_ordenado['data_anterior']).dt.days
                    
                    # Calcular tempo médio por situação
                    tempos_por_situacao = df_ordenado.groupby('SITUACAO')['tempo_no_estado'].mean().to_dict()
                
                analise_temporal[col_data] = {
                    'periodo': periodo,
                    'transicoes': dict(contagem_transicoes),
                    'tempos_por_situacao': tempos_por_situacao
                }
        except Exception as e:
            analise_temporal[col_data] = {'erro': str(e)}
    
    # Calcular eficiência (baseado na proporção de registros não pendentes)
    eficiencia = 0
    if 'SITUACAO' in df.columns:
        total_nao_pendentes = sum(v for k, v in situacao_counts.items() if k != 'PENDENTE' and pd.notna(k))
        eficiencia = (total_nao_pendentes / total_registros) * 100 if total_registros > 0 else 0
    
    # Resultados da análise
    resultados = {
        'nome': nome_colaborador,
        'total_registros': total_registros,
        'situacao_counts': situacao_counts,
        'situacao_percentual': situacao_percentual,
        'registros_vazios': registros_vazios,
        'valores_nao_padronizados': valores_nao_padronizados,
        'analise_temporal': analise_temporal,
        'eficiencia': eficiencia
    }
    
    return resultados

# Função para exibir dashboard de um colaborador
def exibir_dashboard_colaborador(analise, grupo):
    if not analise:
        return
    
    # Criar card para o colaborador
    with st.container():
        st.subheader(f"{analise['nome']} ({grupo})")
        
        # Métricas principais
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Volume Total", analise['total_registros'])
        with col2:
            st.metric("Taxa de Eficiência", f"{analise['eficiencia']:.1f}%")
        
        # Distribuição de Status
        if analise['situacao_counts']:
            st.write("### Distribuição de Status")
            
            # Criar DataFrame para o gráfico
            df_situacao = pd.DataFrame({
                'Status': list(analise['situacao_counts'].keys()),
                'Quantidade': list(analise['situacao_counts'].values()),
                'Percentual': [f"{analise['situacao_percentual'].get(k, 0):.1f}%" for k in analise['situacao_counts'].keys()]
            })
            
            # Exibir tabela
            st.dataframe(df_situacao, hide_index=True)
            
            # Criar gráfico de pizza
            fig = px.pie(
                df_situacao, 
                values='Quantidade', 
                names='Status', 
                title=f"Distribuição de Status - {analise['nome']}",
                hole=0.4
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Análise Temporal
        if analise['analise_temporal']:
            st.write("### Análise Temporal")
            
            for col_data, dados in analise['analise_temporal'].items():
                if 'erro' in dados:
                    st.warning(f"Erro na análise da coluna {col_data}: {dados['erro']}")
                    continue
                
                st.write(f"#### Coluna: {col_data}")
                
                if 'periodo' in dados:
                    periodo = dados['periodo']
                    st.write(f"Período: {periodo['min']} a {periodo['max']}")
                    st.write(f"Registros com data: {periodo['registros']} ({periodo['percentual']:.1f}%)")
                
                # Transições de Estado
                if dados.get('transicoes'):
                    st.write("##### Transições de Estado mais comuns:")
                    
                    # Criar DataFrame para as transições
                    transicoes_list = [(f"{de} -> {para}", count) for (de, para), count in dados['transicoes'].items()]
                    transicoes_list.sort(key=lambda x: x[1], reverse=True)
                    
                    if transicoes_list:
                        df_transicoes = pd.DataFrame(transicoes_list[:5], columns=['Transição', 'Ocorrências'])
                        st.dataframe(df_transicoes, hide_index=True)
                
                # Tempo médio em cada situação
                if dados.get('tempos_por_situacao'):
                    st.write("##### Tempo Médio em cada Situação (dias):")
                    
                    # Criar DataFrame para os tempos
                    tempos_list = [(situacao, tempo) for situacao, tempo in dados['tempos_por_situacao'].items()]
                    tempos_list.sort(key=lambda x: x[1], reverse=True)
                    
                    if tempos_list:
                        df_tempos = pd.DataFrame(tempos_list, columns=['Situação', 'Tempo Médio (dias)'])
                        st.dataframe(df_tempos, hide_index=True)
                        
                        # Criar gráfico de barras
                        fig = px.bar(
                            df_tempos, 
                            x='Situação', 
                            y='Tempo Médio (dias)', 
                            title=f"Tempo Médio em cada Situação - {analise['nome']}",
                            color='Tempo Médio (dias)'
                        )
                        st.plotly_chart(fig, use_container_width=True)
        
        # Valores não padronizados
        if analise['valores_nao_padronizados']:
            st.warning(f"Valores não padronizados encontrados: {', '.join(analise['valores_nao_padronizados'])}")
        
        # Registros vazios
        if analise['registros_vazios'] > 0:
            st.warning(f"Registros com SITUACAO vazia: {analise['registros_vazios']} ({analise['registros_vazios']/analise['total_registros']*100:.1f}%)")

# Função para exibir comparação entre colaboradores
def exibir_comparacao_colaboradores(todas_analises):
    if not todas_analises:
        return
    
    st.header("Comparação entre Colaboradores")
    
    # Preparar dados para comparação
    dados_comparacao = []
    for grupo, analises in todas_analises.items():
        for nome, analise in analises.items():
            dados_comparacao.append({
                'Grupo': grupo,
                'Nome': nome,
                'Volume Total': analise['total_registros'],
                'Taxa de Eficiência (%)': analise['eficiencia']
            })
    
    # Criar DataFrame para comparação
    df_comparacao = pd.DataFrame(dados_comparacao)
    
    # Exibir tabela de comparação
    st.dataframe(df_comparacao, hide_index=True)
    
    # Gráfico de barras para volume total
    fig_volume = px.bar(
        df_comparacao, 
        x='Nome', 
        y='Volume Total', 
        color='Grupo',
        title="Volume Total por Colaborador",
        barmode='group'
    )
    st.plotly_chart(fig_volume, use_container_width=True)
    
    # Gráfico de barras para taxa de eficiência
    fig_eficiencia = px.bar(
        df_comparacao, 
        x='Nome', 
        y='Taxa de Eficiência (%)', 
        color='Grupo',
        title="Taxa de Eficiência por Colaborador",
        barmode='group'
    )
    st.plotly_chart(fig_eficiencia, use_container_width=True)

# Carregar dados dos arquivos Excel
arquivo_julio = "(JULIO) LISTAS INDIVIDUAIS.xlsx"
arquivo_leandro = "(LEANDRO_ADRIANO) LISTAS INDIVIDUAIS.xlsx"

# Sidebar para seleção
st.sidebar.title("Filtros")

# Carregar dados
with st.sidebar.expander("Arquivos Carregados", expanded=True):
    st.info(f"📊 {arquivo_julio}")
    st.info(f"📊 {arquivo_leandro}")

# Carregar dados dos arquivos
dados_julio, colaboradores_julio = carregar_dados(arquivo_julio)
dados_leandro, colaboradores_leandro = carregar_dados(arquivo_leandro)

# Opções de visualização
opcao_visualizacao = st.sidebar.radio(
    "Tipo de Visualização",
    ["Colaborador Específico", "Todos os Colaboradores", "Comparação entre Colaboradores"]
)

# Variáveis para armazenar análises
todas_analises = {
    "Grupo Julio": {},
    "Grupo Leandro": {}
}

# Visualização de colaborador específico
if opcao_visualizacao == "Colaborador Específico":
    grupo = st.sidebar.radio("Selecione o Grupo", ["Grupo Julio", "Grupo Leandro"])
    
    if grupo == "Grupo Julio":
        colaborador = st.sidebar.selectbox("Selecione o Colaborador", colaboradores_julio)
        if colaborador:
            df = dados_julio.get(colaborador)
            analise = analisar_colaborador(df, colaborador)
            exibir_dashboard_colaborador(analise, "Grupo Julio")
            todas_analises["Grupo Julio"][colaborador] = analise
    else:
        colaborador = st.sidebar.selectbox("Selecione o Colaborador", colaboradores_leandro)
        if colaborador:
            df = dados_leandro.get(colaborador)
            analise = analisar_colaborador(df, colaborador)
            exibir_dashboard_colaborador(analise, "Grupo Leandro")
            todas_analises["Grupo Leandro"][colaborador] = analise

# Visualização de todos os colaboradores
elif opcao_visualizacao == "Todos os Colaboradores":
    grupo = st.sidebar.radio("Selecione o Grupo", ["Grupo Julio", "Grupo Leandro", "Ambos os Grupos"])
    
    if grupo in ["Grupo Julio", "Ambos os Grupos"]:
        st.header("Grupo Julio")
        for colaborador in colaboradores_julio:
            df = dados_julio.get(colaborador)
            analise = analisar_colaborador(df, colaborador)
            exibir_dashboard_colaborador(analise, "Grupo Julio")
            todas_analises["Grupo Julio"][colaborador] = analise
            st.markdown("---")
    
    if grupo in ["Grupo Leandro", "Ambos os Grupos"]:
        st.header("Grupo Leandro")
        for colaborador in colaboradores_leandro:
            df = dados_leandro.get(colaborador)
            analise = analisar_colaborador(df, colaborador)
            exibir_dashboard_colaborador(analise, "Grupo Leandro")
            todas_analises["Grupo Leandro"][colaborador] = analise
            st.markdown("---")

# Comparação entre colaboradores
elif opcao_visualizacao == "Comparação entre Colaboradores":
    # Analisar todos os colaboradores
    for colaborador in colaboradores_julio:
        df = dados_julio.get(colaborador)
        analise = analisar_colaborador(df, colaborador)
        todas_analises["Grupo Julio"][colaborador] = analise
    
    for colaborador in colaboradores_leandro:
        df = dados_leandro.get(colaborador)
        analise = analisar_colaborador(df, colaborador)
        todas_analises["Grupo Leandro"][colaborador] = analise
    
    # Exibir comparação
    exibir_comparacao_colaboradores(todas_analises)

# Rodapé
st.sidebar.markdown("---")
st.sidebar.info("Dashboard desenvolvido para análise de dados dos colaboradores")
st.sidebar.write(f"Total de colaboradores: {len(colaboradores_julio) + len(colaboradores_leandro)}")
