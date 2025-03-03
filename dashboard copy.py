import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from debug_excel import AnalisadorExcel

class DashboardAnalise:
    def __init__(self):
        self.analisador = AnalisadorExcel("(JULIO) LISTAS INDIVIDUAIS.xlsx")
        self.dados = self.analisador.analisar_arquivo()
        self.metricas = self.analisador.colaboradores
        
    def gerar_alertas_desempenho(self, colaborador):
        """Gera alertas de desempenho para um colaborador específico"""
        alertas = []
        metricas = self.metricas[colaborador]
        
        # Alerta de eficiência
        media_eficiencia = np.mean([m['taxa_eficiencia'] for m in self.metricas.values()])
        if metricas['taxa_eficiencia'] < media_eficiencia * 0.8:
            alertas.append({
                'tipo': 'crítico',
                'mensagem': f'Eficiência abaixo da média (atual: {metricas["taxa_eficiencia"]*100:.1f}%, média: {media_eficiencia*100:.1f}%)'
            })
            
        # Alerta de volume pendente
        if metricas['distribuicao_status'].get('PENDENTE', 0) > 650:
            alertas.append({
                'tipo': 'atenção',
                'mensagem': f'Alto volume de casos pendentes: {metricas["distribuicao_status"].get("PENDENTE", 0)}'
            })
            
        # Alerta de tempo de resolução
        if metricas.get('tempo_medio_resolucao', 0) > 3:
            alertas.append({
                'tipo': 'atenção',
                'mensagem': f'Tempo médio de resolução alto: {metricas.get("tempo_medio_resolucao", 0):.1f} dias'
            })
            
        # Alerta de outliers
        if metricas['outliers'].get('tempo_resolucao', 0) > 10:
            alertas.append({
                'tipo': 'informativo',
                'mensagem': f'Alto número de casos com tempo de resolução atípico: {metricas["outliers"].get("tempo_resolucao", 0)}'
            })
            
        return alertas
    
    def gerar_recomendacoes(self, colaborador):
        """Gera recomendações personalizadas para um colaborador"""
        metricas = self.metricas[colaborador]
        recomendacoes = []
        
        # Recomendações baseadas na eficiência
        if metricas['taxa_eficiencia'] < 0.03:
            recomendacoes.append({
                'area': 'Eficiência',
                'recomendacao': 'Priorizar a resolução de casos mais antigos para melhorar a taxa de eficiência',
                'acao': 'Estabelecer meta diária de resolução de pelo menos 5 casos'
            })
            
        # Recomendações baseadas no tempo de resolução
        if metricas.get('tempo_medio_resolucao', 0) > 3:
            recomendacoes.append({
                'area': 'Tempo de Resolução',
                'recomendacao': 'Reduzir o tempo médio de resolução dos casos',
                'acao': 'Identificar e eliminar gargalos no processo de análise'
            })
            
        # Recomendações baseadas na distribuição de status
        if metricas['distribuicao_status'].get('ANALISE', 0) > metricas['distribuicao_status'].get('VERIFICADO', 0):
            recomendacoes.append({
                'area': 'Fluxo de Trabalho',
                'recomendacao': 'Melhorar a conversão de casos em análise para verificados',
                'acao': 'Revisar processo de análise para identificar pontos de melhoria'
            })
            
        # Recomendações baseadas no padrão semanal
        if 'padrao_semanal' in metricas:
            dias = metricas['padrao_semanal']
            if max(dias.values()) / (sum(dias.values())/len(dias)) > 2:
                recomendacoes.append({
                    'area': 'Distribuição de Trabalho',
                    'recomendacao': 'Melhorar a distribuição do trabalho ao longo da semana',
                    'acao': 'Estabelecer metas diárias mais equilibradas'
                })
        
        return recomendacoes
    
    def criar_dashboard(self):
        st.set_page_config(page_title="Dashboard de Análise de Desempenho", layout="wide")
        st.title("Dashboard de Análise de Desempenho")
        
        # Sidebar para seleção de colaborador
        colaborador = st.sidebar.selectbox(
            "Selecione o Colaborador",
            options=list(self.metricas.keys())
        )
        
        # Layout em colunas
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.header("Métricas Principais")
            metricas = self.metricas[colaborador]
            
            # Gráfico de distribuição de status
            fig_status = px.pie(
                values=list(metricas['distribuicao_status'].values()),
                names=list(metricas['distribuicao_status'].keys()),
                title="Distribuição de Status"
            )
            st.plotly_chart(fig_status)
            
            # Gráfico de tendência temporal
            if 'tendencias' in metricas:
                st.subheader("Tendência de Desempenho")
                st.write(f"Tendência: {'crescente' if metricas['tendencias'].get('slope', 0) > 0 else 'decrescente'}")
                st.write(f"R²: {metricas['tendencias'].get('r_squared', 0):.2f}")
            
            # Gráfico de padrão semanal
            if 'padrao_semanal' in metricas:
                fig_semanal = px.bar(
                    x=list(metricas['padrao_semanal'].keys()),
                    y=list(metricas['padrao_semanal'].values()),
                    title="Distribuição por Dia da Semana"
                )
                st.plotly_chart(fig_semanal)
        
        with col2:
            # Alertas
            st.header("Alertas de Desempenho")
            alertas = self.gerar_alertas_desempenho(colaborador)
            for alerta in alertas:
                if alerta['tipo'] == 'crítico':
                    st.error(alerta['mensagem'])
                elif alerta['tipo'] == 'atenção':
                    st.warning(alerta['mensagem'])
                else:
                    st.info(alerta['mensagem'])
            
            # Recomendações
            st.header("Recomendações")
            recomendacoes = self.gerar_recomendacoes(colaborador)
            for rec in recomendacoes:
                with st.expander(f"📌 {rec['area']}"):
                    st.write(f"**Recomendação:** {rec['recomendacao']}")
                    st.write(f"**Ação Sugerida:** {rec['acao']}")
            
            # Métricas de eficiência
            st.header("Métricas de Eficiência")
            col_ef1, col_ef2 = st.columns(2)
            with col_ef1:
                st.metric(
                    "Taxa de Eficiência",
                    f"{metricas['taxa_eficiencia']*100:.1f}%"
                )
            with col_ef2:
                if 'tempo_medio_resolucao' in metricas:
                    st.metric(
                        "Tempo Médio de Resolução",
                        f"{metricas['tempo_medio_resolucao']:.1f} dias"
                    )

if __name__ == "__main__":
    dashboard = DashboardAnalise()
    dashboard.criar_dashboard()
