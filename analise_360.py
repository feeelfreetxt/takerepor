import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from debug_excel import AnalisadorExcel
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

class Analise360:
    def __init__(self):
        self.analisador_julio = None
        self.analisador_leandro = None
        self.data_atual = datetime.now().date()
        
    def configurar_arquivos(self, arquivos):
        """Configura os arquivos para análise"""
        for nome, caminho in arquivos.items():
            if 'JULIO' in nome.upper():
                self.analisador_julio = AnalisadorExcel(caminho)
            elif 'LEANDRO' in nome.upper():
                self.analisador_leandro = AnalisadorExcel(caminho)
                
    def calcular_score(self, metricas):
        """Calcula score baseado em múltiplos fatores"""
        score = 0
        
        # Fator 1: Taxa de eficiência (peso 40%)
        score += metricas['taxa_eficiencia'] * 40
        
        # Fator 2: Volume processado (peso 20%)
        total_processado = sum(v for k, v in metricas['distribuicao_status'].items() if k != 'PENDENTE')
        score += (total_processado / sum(metricas['distribuicao_status'].values())) * 20
        
        # Fator 3: Tempo médio de resolução (peso 20%)
        if metricas.get('tempo_medio_resolucao'):
            # Quanto menor o tempo, melhor o score
            tempo_score = max(0, (10 - metricas['tempo_medio_resolucao'])) / 10
            score += tempo_score * 20
            
        # Fator 4: Tendência de melhoria (peso 20%)
        if metricas.get('tendencias', {}).get('slope', 0) > 0:
            score += 20
        
        return score
        
    def gerar_ranking(self):
        """Gera ranking geral dos colaboradores"""
        ranking = []
        
        # Processar grupo JULIO se disponível
        if self.analisador_julio:
            try:
                dados_julio = self.analisador_julio.analisar_arquivo()
                for colab, metricas in self.analisador_julio.colaboradores.items():
                    score = self.calcular_score(metricas)
                    ranking.append({
                        'Colaborador': colab,
                        'Grupo': 'JULIO',
                        'Score': score,
                        'Taxa Eficiência': metricas['taxa_eficiencia'] * 100,
                        'Casos Pendentes': metricas['distribuicao_status'].get('PENDENTE', 0),
                        'Casos Processados': sum(v for k, v in metricas['distribuicao_status'].items() if k != 'PENDENTE'),
                        'Tempo Médio': metricas.get('tempo_medio_resolucao', 0)
                    })
            except Exception as e:
                st.error(f"Erro ao processar dados do grupo JULIO: {str(e)}")
            
        # Processar grupo LEANDRO se disponível
        if self.analisador_leandro:
            try:
                dados_leandro = self.analisador_leandro.analisar_arquivo()
                for colab, metricas in self.analisador_leandro.colaboradores.items():
                    score = self.calcular_score(metricas)
                    ranking.append({
                        'Colaborador': colab,
                        'Grupo': 'LEANDRO',
                        'Score': score,
                        'Taxa Eficiência': metricas['taxa_eficiencia'] * 100,
                        'Casos Pendentes': metricas['distribuicao_status'].get('PENDENTE', 0),
                        'Casos Processados': sum(v for k, v in metricas['distribuicao_status'].items() if k != 'PENDENTE'),
                        'Tempo Médio': metricas.get('tempo_medio_resolucao', 0)
                    })
            except Exception as e:
                st.error(f"Erro ao processar dados do grupo LEANDRO: {str(e)}")
        
        if not ranking:
            st.warning("⚠️ Nenhum arquivo de análise foi carregado ou os arquivos não contêm dados válidos")
            return pd.DataFrame()
            
        return pd.DataFrame(ranking).sort_values('Score', ascending=False)
    
    def overview_colaborador(self, colaborador, grupo):
        """Gera overview detalhado de um colaborador"""
        analisador = None
        if grupo == 'JULIO' and self.analisador_julio:
            analisador = self.analisador_julio
        elif grupo == 'LEANDRO' and self.analisador_leandro:
            analisador = self.analisador_leandro
            
        if not analisador:
            st.error(f"Analisador para o grupo {grupo} não está configurado")
            return None
            
        metricas = analisador.colaboradores.get(colaborador)
        if not metricas:
            st.error(f"Colaborador {colaborador} não encontrado no grupo {grupo}")
            return None
            
        # Dados diários (hoje)
        hoje = {status: 0 for status in metricas['distribuicao_status'].keys()}
        
        # Dados gerais
        geral = metricas['distribuicao_status']
        
        overview = {
            'Colaborador': colaborador,
            'Grupo': grupo,
            'Data': self.data_atual,
            'Relatório Diário': hoje,
            'Relatório Geral': geral,
            'Métricas Adicionais': {
                'Taxa de Eficiência': metricas['taxa_eficiencia'] * 100,
                'Tempo Médio de Resolução': metricas.get('tempo_medio_resolucao', 0),
                'Score': self.calcular_score(metricas),
                'Tendência': 'Crescente' if metricas.get('tendencias', {}).get('slope', 0) > 0 else 'Decrescente'
            }
        }
        
        return overview
        
    def mostrar_dashboard_360(self):
        """Interface principal do dashboard"""
        st.title("📊 Análise 360° de Performance")
        st.write("Visão completa do desempenho dos colaboradores")

        # CSS personalizado para melhorar o visual
        st.markdown("""
        <style>
        .metric-card {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 0.5rem 0;
            box-shadow: 0 0.125rem 0.25rem rgba(0,0,0,0.075);
        }
        .ranking-card {
            background-color: white;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 0.5rem 0;
            border-left: 4px solid #1f77b4;
        }
        </style>
        """, unsafe_allow_html=True)

        # Verificar se há dados para análise
        if not self.analisador_julio and not self.analisador_leandro:
            st.warning("⚠️ Nenhum arquivo foi carregado para análise. Por favor, carregue os arquivos Excel.")
            st.info("""
            **Arquivos esperados:**
            1. Arquivo do grupo JULIO (nome deve conter 'JULIO')
            2. Arquivo do grupo LEANDRO (nome deve conter 'LEANDRO')
            """)
            return

        # Sidebar mais limpa
        with st.sidebar:
            st.header("Filtros")
            
            # Criar lista de grupos disponíveis
            grupos_disponiveis = []
            if self.analisador_julio:
                grupos_disponiveis.append('JULIO')
            if self.analisador_leandro:
                grupos_disponiveis.append('LEANDRO')
            
            if grupos_disponiveis:
                grupo_selecionado = st.selectbox(
                    "Selecione o Grupo",
                    grupos_disponiveis
                )
                
                # Obter colaboradores do grupo selecionado
                analisador = self.analisador_julio if grupo_selecionado == 'JULIO' else self.analisador_leandro
                colaboradores = list(analisador.colaboradores.keys()) if analisador else []
                
                if colaboradores:
                    colaborador_selecionado = st.selectbox(
                        "Selecione o Colaborador",
                        colaboradores
                    )
                else:
                    st.warning("Nenhum colaborador encontrado neste grupo")
            else:
                st.warning("Nenhum grupo disponível")
                return

        # Gerar ranking
        df_ranking = self.gerar_ranking()
        
        if not df_ranking.empty:
            # Mostrar ranking geral
            st.header("🏆 Ranking Geral")
            st.dataframe(
                df_ranking.style.format({
                    'Score': '{:.2f}',
                    'Taxa Eficiência': '{:.2f}%',
                    'Tempo Médio': '{:.2f}'
                }),
                use_container_width=True
            )

            # Gráficos de desempenho
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📈 Score por Colaborador")
                fig = px.bar(df_ranking, 
                           x='Colaborador', 
                           y='Score',
                           color='Grupo',
                           title="Comparativo de Score")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("🎯 Taxa de Eficiência")
                fig = px.bar(df_ranking,
                           x='Colaborador',
                           y='Taxa Eficiência',
                           color='Grupo',
                           title="Comparativo de Eficiência")
                st.plotly_chart(fig, use_container_width=True)

            # Overview do colaborador selecionado
            if 'colaborador_selecionado' in locals() and 'grupo_selecionado' in locals():
                st.header(f"📋 Overview: {colaborador_selecionado}")
                overview = self.overview_colaborador(colaborador_selecionado, grupo_selecionado)
                
                if overview:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric(
                            "Score Geral",
                            f"{overview['Métricas Adicionais']['Score']:.2f}"
                        )
                    
                    with col2:
                        st.metric(
                            "Taxa de Eficiência",
                            f"{overview['Métricas Adicionais']['Taxa de Eficiência']:.2f}%"
                        )
                    
                    with col3:
                        st.metric(
                            "Tempo Médio de Resolução",
                            f"{overview['Métricas Adicionais']['Tempo Médio']:.2f} dias"
                        )
                    
                    # Distribuição de status
                    st.subheader("📊 Distribuição de Status")
                    df_status = pd.DataFrame(list(overview['Relatório Geral'].items()),
                                          columns=['Status', 'Quantidade'])
                    fig = px.pie(df_status,
                               values='Quantidade',
                               names='Status',
                               title="Distribuição por Status")
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Não foi possível gerar o ranking. Verifique se os arquivos contêm dados válidos.")
        
if __name__ == "__main__":
    analise = Analise360()
    arquivos = {
        "JULIO": "(JULIO) LISTAS INDIVIDUAIS.xlsx",
        "LEANDRO": "(LEANDRO_ADRIANO) LISTAS INDIVIDUAIS.xlsx"
    }
    analise.configurar_arquivos(arquivos)
    analise.mostrar_dashboard_360()
