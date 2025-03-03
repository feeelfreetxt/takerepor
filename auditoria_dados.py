import pandas as pd
import numpy as np
from datetime import datetime
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import os
import warnings
warnings.filterwarnings('ignore')

class AuditorDados:
    def __init__(self):
        self.arquivos = {
            'JULIO': "F:/okok/(JULIO) LISTAS INDIVIDUAIS.xlsx",
            'LEANDRO': "F:/okok/(LEANDRO_ADRIANO) LISTAS INDIVIDUAIS.xlsx"
        }
        self.relatorio_completo = {}
        
    def validar_arquivo(self, nome_arquivo, caminho):
        """Valida se o arquivo existe e pode ser lido"""
        if not os.path.exists(caminho):
            return False, f"Arquivo {nome_arquivo} não encontrado em {caminho}"
        try:
            pd.read_excel(caminho, sheet_name=None)
            return True, f"Arquivo {nome_arquivo} validado com sucesso"
        except Exception as e:
            return False, f"Erro ao ler arquivo {nome_arquivo}: {str(e)}"
    
    def analisar_aba(self, df, nome_aba):
        """Análise detalhada de uma aba específica"""
        analise = {
            'total_linhas': len(df),
            'total_colunas': len(df.columns),
            'colunas': list(df.columns),
            'tipos_dados': df.dtypes.to_dict(),
            'valores_nulos': df.isnull().sum().to_dict(),
            'valores_unicos': {col: df[col].nunique() for col in df.columns},
            'amostra_dados': df.head(5).to_dict('records'),
            'estatisticas': df.describe(include='all').to_dict(),
            'problemas_detectados': []
        }
        
        # Validações específicas
        if 'Data' in df.columns:
            try:
                pd.to_datetime(df['Data'])
            except:
                analise['problemas_detectados'].append("Erro na conversão de datas")
                
        if 'Status' in df.columns:
            status_invalidos = df[~df['Status'].isin(['VERIFICADO', 'ANÁLISE', 'PENDENTE', 'PRIORIDADE', 
                                                     'PRIORIDADE TOTAL', 'APROVADO', 'QUITADO', 'APREENDIDO', 'CANCELADO'])]['Status'].unique()
            if len(status_invalidos) > 0:
                analise['problemas_detectados'].append(f"Status inválidos encontrados: {status_invalidos}")
        
        return analise
    
    def gerar_relatorio_auditoria(self):
        """Gera relatório completo de auditoria"""
        for nome, caminho in self.arquivos.items():
            self.relatorio_completo[nome] = {
                'status_arquivo': self.validar_arquivo(nome, caminho)
            }
            
            if self.relatorio_completo[nome]['status_arquivo'][0]:
                try:
                    # Lê todas as abas
                    excel_file = pd.read_excel(caminho, sheet_name=None)
                    self.relatorio_completo[nome]['abas'] = {}
                    
                    for aba_nome, df in excel_file.items():
                        self.relatorio_completo[nome]['abas'][aba_nome] = self.analisar_aba(df, aba_nome)
                        
                except Exception as e:
                    self.relatorio_completo[nome]['erro_analise'] = str(e)
    
    def mostrar_dashboard_auditoria(self):
        """Exibe dashboard interativo com resultados da auditoria"""
        st.title("📊 Relatório de Auditoria de Dados")
        st.write("Análise detalhada das planilhas de dados")
        
        # Gera o relatório
        self.gerar_relatorio_auditoria()
        
        # Para cada arquivo
        for nome_arquivo, dados in self.relatorio_completo.items():
            st.header(f"📁 Arquivo: {nome_arquivo}")
            
            # Status do arquivo
            status_ok, mensagem = dados['status_arquivo']
            if status_ok:
                st.success(mensagem)
                
                # Para cada aba
                for nome_aba, analise_aba in dados['abas'].items():
                    with st.expander(f"📑 Aba: {nome_aba}"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Total de Linhas", analise_aba['total_linhas'])
                        with col2:
                            st.metric("Total de Colunas", analise_aba['total_colunas'])
                        with col3:
                            st.metric("Campos Únicos", 
                                    sum(analise_aba['valores_unicos'].values()))
                        
                        # Análise de colunas
                        st.subheader("📋 Estrutura de Dados")
                        df_estrutura = pd.DataFrame({
                            'Coluna': analise_aba['colunas'],
                            'Tipo': [str(analise_aba['tipos_dados'][col]) for col in analise_aba['colunas']],
                            'Valores Nulos': [analise_aba['valores_nulos'][col] for col in analise_aba['colunas']],
                            'Valores Únicos': [analise_aba['valores_unicos'][col] for col in analise_aba['colunas']]
                        })
                        st.dataframe(df_estrutura)
                        
                        # Problemas detectados
                        if analise_aba['problemas_detectados']:
                            st.error("⚠️ Problemas Detectados:")
                            for problema in analise_aba['problemas_detectados']:
                                st.write(f"- {problema}")
                        else:
                            st.success("✅ Nenhum problema crítico detectado")
                        
                        # Visualização de dados nulos
                        st.subheader("📉 Análise de Dados Nulos")
                        df_nulos = pd.DataFrame(list(analise_aba['valores_nulos'].items()), 
                                              columns=['Coluna', 'Valores Nulos'])
                        fig = px.bar(df_nulos, x='Coluna', y='Valores Nulos',
                                   title="Distribuição de Valores Nulos por Coluna")
                        st.plotly_chart(fig)
                        
                        # Amostra de dados
                        st.subheader("🔍 Amostra de Dados")
                        st.dataframe(pd.DataFrame(analise_aba['amostra_dados']))
                        
            else:
                st.error(mensagem)
        
        # Resumo geral
        st.header("📈 Resumo Geral da Auditoria")
        resumo = []
        for nome_arquivo, dados in self.relatorio_completo.items():
            if dados['status_arquivo'][0]:
                for nome_aba, analise_aba in dados['abas'].items():
                    resumo.append({
                        'Arquivo': nome_arquivo,
                        'Aba': nome_aba,
                        'Total Linhas': analise_aba['total_linhas'],
                        'Total Colunas': analise_aba['total_colunas'],
                        'Problemas': len(analise_aba['problemas_detectados'])
                    })
        
        if resumo:
            df_resumo = pd.DataFrame(resumo)
            st.dataframe(df_resumo)
            
            # Gráfico comparativo
            fig = px.bar(df_resumo, x='Aba', y='Total Linhas', 
                        color='Arquivo', barmode='group',
                        title="Comparativo de Volume de Dados por Aba")
            st.plotly_chart(fig)

if __name__ == "__main__":
    auditor = AuditorDados()
    auditor.mostrar_dashboard_auditoria()
