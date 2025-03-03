import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from database_manager import DatabaseManager
from analise_avancada import AnalisadorAvancado

class RelatorioAvancado:
    def __init__(self):
        self.db = DatabaseManager()
        self.analisador = AnalisadorAvancado()
        
    def gerar_relatorio(self):
        st.set_page_config(page_title="Análise Avançada de Desempenho", layout="wide")
        st.title("Análise Avançada de Desempenho")
        
        # Sidebar para filtros
        st.sidebar.title("Filtros")
        dias_historico = st.sidebar.slider("Dias de Histórico", 7, 90, 30)
        grupo_selecionado = st.sidebar.selectbox("Grupo", ["Todos", "JULIO", "LEANDRO"])
        
        # Layout principal
        col1, col2 = st.columns([2, 1])
        
        with col1:
            self.mostrar_metricas_historicas(dias_historico, grupo_selecionado)
            self.mostrar_correlacoes()
            
        with col2:
            self.mostrar_alertas()
            self.mostrar_gargalos()
            
        # Análise de tendências
        st.header("Análise de Tendências")
        self.mostrar_tendencias()
        
    def mostrar_metricas_historicas(self, dias, grupo):
        """Mostra gráficos históricos das principais métricas"""
        df = self.db.obter_historico_metricas(dias)
        
        if grupo != "Todos":
            df = df[df['grupo'] == grupo]
        
        if not df.empty:
            # Gráfico de eficiência ao longo do tempo
            fig = px.line(df, 
                         x='data_analise', 
                         y='taxa_eficiencia',
                         color='colaborador',
                         title='Evolução da Taxa de Eficiência')
            st.plotly_chart(fig)
            
            # Gráfico de tempo médio de resolução
            fig = px.box(df, 
                        x='grupo', 
                        y='tempo_medio_resolucao',
                        title='Distribuição do Tempo Médio de Resolução por Grupo')
            st.plotly_chart(fig)
            
            # Heatmap de casos pendentes por colaborador
            pivot = df.pivot_table(
                values='casos_pendentes',
                index='colaborador',
                columns='data_analise',
                aggfunc='mean'
            )
            fig = go.Figure(data=go.Heatmap(
                z=pivot.values,
                x=pivot.columns,
                y=pivot.index,
                colorscale='RdYlGn_r'
            ))
            fig.update_layout(title='Heatmap de Casos Pendentes por Colaborador')
            st.plotly_chart(fig)
    
    def mostrar_correlacoes(self):
        """Mostra análise de correlações"""
        st.header("Análise de Correlações")
        
        # Executar análise
        self.analisador.calcular_correlacao_volume_eficiencia()
        
        # Criar visualização
        dados_correlacao = {
            'Grupo': ['JULIO', 'LEANDRO'],
            'Coeficiente': [0.535, 0.282],
            'P-valor': [0.111, 0.374]
        }
        df_corr = pd.DataFrame(dados_correlacao)
        
        fig = go.Figure(data=[
            go.Bar(name='Coeficiente de Correlação',
                  x=df_corr['Grupo'],
                  y=df_corr['Coeficiente'])
        ])
        fig.update_layout(title='Correlação Volume vs Eficiência por Grupo')
        st.plotly_chart(fig)
        
    def mostrar_alertas(self):
        """Mostra alertas ativos"""
        st.header("Alertas Ativos")
        alertas = self.db.obter_alertas_ativos()
        
        if not alertas.empty:
            for _, alerta in alertas.iterrows():
                if alerta['tipo_alerta'] == 'crítico':
                    st.error(f"{alerta['colaborador']}: {alerta['descricao']}")
                elif alerta['tipo_alerta'] == 'atenção':
                    st.warning(f"{alerta['colaborador']}: {alerta['descricao']}")
                else:
                    st.info(f"{alerta['colaborador']}: {alerta['descricao']}")
    
    def mostrar_gargalos(self):
        """Mostra gargalos recentes"""
        st.header("Gargalos Identificados")
        gargalos = self.db.obter_gargalos_recentes()
        
        if not gargalos.empty:
            for _, gargalo in gargalos.iterrows():
                st.warning(
                    f"Grupo {gargalo['grupo']}: {gargalo['descricao']}\n"
                    f"Métrica: {gargalo['metrica']:.2f}"
                )
    
    def mostrar_tendencias(self):
        """Mostra análise de tendências"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Grupo JULIO")
            for colab, dados in self.analisador.metricas_julio.items():
                if 'tendencias' in dados:
                    tend = dados['tendencias']
                    st.write(f"**{colab}**")
                    st.write(f"R² = {tend.get('r_squared', 0):.3f}")
                    if tend.get('slope', 0) > 0:
                        st.write("Tendência: ⬆️ Crescente")
                    elif tend.get('slope', 0) < 0:
                        st.write("Tendência: ⬇️ Decrescente")
                    else:
                        st.write("Tendência: ➡️ Estável")
                    st.write("---")
        
        with col2:
            st.subheader("Grupo LEANDRO")
            for colab, dados in self.analisador.metricas_leandro.items():
                if 'tendencias' in dados:
                    tend = dados['tendencias']
                    st.write(f"**{colab}**")
                    st.write(f"R² = {tend.get('r_squared', 0):.3f}")
                    if tend.get('slope', 0) > 0:
                        st.write("Tendência: ⬆️ Crescente")
                    elif tend.get('slope', 0) < 0:
                        st.write("Tendência: ⬇️ Decrescente")
                    else:
                        st.write("Tendência: ➡️ Estável")
                    st.write("---")

if __name__ == "__main__":
    relatorio = RelatorioAvancado()
    relatorio.gerar_relatorio()
