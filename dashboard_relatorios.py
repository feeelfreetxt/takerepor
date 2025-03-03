import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import json
import time
import tempfile
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import io
import base64
import traceback
from fpdf import FPDF
import uuid
import re

# Importações para processar os arquivos
from debug_excel_fixed import AnalisadorExcel

# Configuração da página
st.set_page_config(
    page_title="Dashboard Colaboradores",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #0D47A1;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .card {
        border-radius: 5px;
        padding: 1.5rem;
        background-color: #f8f9fa;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .metric-large {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
    }
    .metric-title {
        font-size: 1.1rem;
        text-align: center;
        color: #555;
    }
    .good-metric {
        color: #00C853;
    }
    .medium-metric {
        color: #FFD600;
    }
    .bad-metric {
        color: #FF3D00;
    }
    .highlight {
        background-color: #E3F2FD;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #1E88E5;
    }
    .footer {
        text-align: center;
        font-size: 0.8rem;
        color: #666;
        margin-top: 3rem;
    }
</style>
""", unsafe_allow_html=True)

class DashboardGerenciador:
    def __init__(self):
        # Inicializar estado da sessão se ainda não existir
        if 'analises' not in st.session_state:
            st.session_state.analises = {}
        
        if 'relatorios_individuais' not in st.session_state:
            st.session_state.relatorios_individuais = {}
            
        if 'arquivos_analisados' not in st.session_state:
            st.session_state.arquivos_analisados = []
            
        if 'ultima_analise' not in st.session_state:
            st.session_state.ultima_analise = None
            
        # Criar diretórios necessários
        os.makedirs('uploads', exist_ok=True)
        os.makedirs('resultados', exist_ok=True)
        
        # Carregar dados salvos, se existirem
        self.carregar_dados_salvos()
    
    def carregar_dados_salvos(self):
        """Carrega dados de análises anteriores se existirem"""
        relatorio_path = os.path.join('resultados', 'relatorio_analise.json')
        if os.path.exists(relatorio_path):
            try:
                with open(relatorio_path, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                
                # Atualizar estado da sessão com dados salvos
                if 'resultados' in dados:
                    for grupo, metricas in dados['resultados'].items():
                        if grupo not in st.session_state.analises:
                            st.session_state.analises[grupo] = {}
                        
                        st.session_state.analises[grupo].update(metricas)
                
                if 'arquivos_analisados' in dados:
                    st.session_state.arquivos_analisados = dados['arquivos_analisados']
                
                if 'ultima_analise' in dados and dados['ultima_analise']:
                    st.session_state.ultima_analise = dados['ultima_analise']
            except Exception as e:
                st.error(f"Erro ao carregar dados salvos: {str(e)}")
    
    def salvar_resultados(self):
        """Salva os resultados das análises em um arquivo JSON"""
        try:
            dados = {
                "ultima_analise": datetime.now().isoformat(),
                "arquivos_analisados": st.session_state.arquivos_analisados,
                "resultados": st.session_state.analises,
                "erros": []
            }
            
            relatorio_path = os.path.join('resultados', 'relatorio_analise.json')
            with open(relatorio_path, 'w', encoding='utf-8') as f:
                json.dump(dados, f, indent=2)
                
            return True
        except Exception as e:
            st.error(f"Erro ao salvar resultados: {str(e)}")
            return False
    
    def processar_arquivo(self, arquivo_carregado, grupo):
        """Processa um arquivo Excel carregado pelo usuário"""
        try:
            # Salvar o arquivo temporariamente
            arquivo_path = os.path.join('uploads', arquivo_carregado.name)
            with open(arquivo_path, 'wb') as f:
                f.write(arquivo_carregado.getbuffer())
            
            st.success(f"Arquivo salvo em {arquivo_path}")
            
            # Analisar o arquivo
            st.info(f"Iniciando análise do arquivo: {arquivo_path} (grupo: {grupo})")
            
            # Criar analisador
            analisador = AnalisadorExcel(arquivo_path)
            
            # Analisar arquivo
            colaboradores = analisador.analisar_arquivo()
            
            # Verificar se há colaboradores
            if not analisador.colaboradores:
                st.warning("Nenhum colaborador encontrado no arquivo.")
                return False
            
            # Atualizar estado da sessão
            if grupo not in st.session_state.analises:
                st.session_state.analises[grupo] = {}
            
            st.session_state.analises[grupo].update(analisador.colaboradores)
            
            if arquivo_path not in st.session_state.arquivos_analisados:
                st.session_state.arquivos_analisados.append(arquivo_path)
            
            st.session_state.ultima_analise = datetime.now().isoformat()
            
            # Salvar resultados
            self.salvar_resultados()
            
            st.success(f"Análise concluída! {len(analisador.colaboradores)} colaboradores encontrados.")
            return True
        except Exception as e:
            st.error(f"Erro ao processar arquivo: {str(e)}")
            st.error(traceback.format_exc())
            return False
    
    def analisar_desempenho(self, metricas):
        """Analisa o desempenho do colaborador com base nas métricas"""
        try:
            analise = {}
            
            # Eficiência
            taxa_eficiencia = metricas.get('taxa_eficiencia', 0)
            if taxa_eficiencia is not None:
                taxa_eficiencia = taxa_eficiencia * 100
            else:
                taxa_eficiencia = 0
                
            if taxa_eficiencia >= 80:
                nivel_eficiencia = "Excelente"
            elif taxa_eficiencia >= 60:
                nivel_eficiencia = "Bom"
            elif taxa_eficiencia >= 40:
                nivel_eficiencia = "Regular"
            else:
                nivel_eficiencia = "Precisa melhorar"
            
            analise["eficiencia"] = {
                "valor": taxa_eficiencia,
                "nivel": nivel_eficiencia
            }
            
            # Tempo médio de resolução
            tempo_medio = metricas.get('tempo_medio_resolucao')
            if tempo_medio is not None:
                if tempo_medio <= 1:
                    nivel_tempo = "Excelente"
                elif tempo_medio <= 3:
                    nivel_tempo = "Bom"
                elif tempo_medio <= 7:
                    nivel_tempo = "Regular"
                else:
                    nivel_tempo = "Demorado"
            else:
                nivel_tempo = "Não disponível"
            
            analise["tempo_resolucao"] = {
                "valor": tempo_medio,
                "nivel": nivel_tempo
            }
            
            # Volume de trabalho
            total_registros = metricas.get('total_registros', 0)
            if total_registros >= 100:
                nivel_volume = "Alto"
            elif total_registros >= 50:
                nivel_volume = "Médio"
            else:
                nivel_volume = "Baixo"
            
            analise["volume_trabalho"] = {
                "valor": total_registros,
                "nivel": nivel_volume
            }
            
            # Distribuição de status
            status_distribuicao = metricas.get('distribuicao_status', {})
            pendentes = status_distribuicao.get('PENDENTE', 0)
            concluidos = status_distribuicao.get('CONCLUIDO', 0) + status_distribuicao.get('QUITADO', 0)
            
            if (pendentes + concluidos) > 0:
                taxa_conclusao = concluidos / (pendentes + concluidos)
            else:
                taxa_conclusao = 0.0
            
            if taxa_conclusao >= 0.9:
                nivel_conclusao = "Excelente"
            elif taxa_conclusao >= 0.7:
                nivel_conclusao = "Bom"
            elif taxa_conclusao >= 0.5:
                nivel_conclusao = "Regular"
            else:
                nivel_conclusao = "Precisa melhorar"
            
            analise["taxa_conclusao"] = {
                "valor": taxa_conclusao * 100,
                "nivel": nivel_conclusao
            }
            
            return analise
        except Exception as e:
            st.error(f"Erro ao analisar desempenho: {str(e)}")
            return {}
    
    def gerar_recomendacoes(self, metricas):
        """Gera recomendações específicas com base nas métricas do colaborador"""
        recomendacoes = []
        
        try:
            # Verificar taxa de eficiência
            taxa_eficiencia = metricas.get('taxa_eficiencia', 0)
            if taxa_eficiencia is not None:
                taxa_eficiencia = taxa_eficiencia * 100
            else:
                taxa_eficiencia = 0
                
            if taxa_eficiencia < 60:
                recomendacoes.append({
                    "area": "Eficiência",
                    "recomendacao": "Aumente a taxa de conclusão de tarefas.",
                    "acao": "Priorize tarefas pendentes mais antigas e estabeleça metas diárias de conclusão."
                })
            
            # Verificar tempo médio de resolução
            tempo_medio = metricas.get('tempo_medio_resolucao')
            if tempo_medio is not None and tempo_medio > 5:
                recomendacoes.append({
                    "area": "Tempo de Resolução",
                    "recomendacao": "Reduza o tempo médio de resolução.",
                    "acao": "Identifique gargalos no processo e trabalhe em técnicas de otimização de tempo."
                })
            
            # Verificar pendências
            status_distribuicao = metricas.get('distribuicao_status', {})
            pendentes = status_distribuicao.get('PENDENTE', 0)
            total = sum(status_distribuicao.values()) if status_distribuicao else 0
            
            if pendentes > 0 and total > 0 and (pendentes / total > 0.3):
                recomendacoes.append({
                    "area": "Pendências",
                    "recomendacao": "Reduza o número de tarefas pendentes.",
                    "acao": "Dedique tempo específico diariamente para tratar pendências mais antigas."
                })
            
            # Recomendações gerais se não houver problemas específicos
            if not recomendacoes:
                recomendacoes.append({
                    "area": "Desempenho Geral",
                    "recomendacao": "Continue mantendo o bom desempenho.",
                    "acao": "Compartilhe suas práticas com a equipe para promover melhorias coletivas."
                })
            
            return recomendacoes
        except Exception as e:
            st.error(f"Erro ao gerar recomendações: {str(e)}")
            return [{
                "area": "Erro na Análise",
                "recomendacao": "Não foi possível gerar recomendações específicas.",
                "acao": "Verifique a qualidade dos dados no arquivo original."
            }]
    
    def gerar_graficos_colaborador(self, grupo, colaborador):
        """Gera gráficos para análise do colaborador"""
        graficos = {}
        
        try:
            if grupo not in st.session_state.analises or colaborador not in st.session_state.analises[grupo]:
                return graficos
            
            metricas = st.session_state.analises[grupo][colaborador]
            
            # 1. Gráfico de distribuição de status
            if 'distribuicao_status' in metricas:
                fig = plt.figure(figsize=(8, 5))
                status_data = metricas['distribuicao_status']
                
                # Filtrar status com valores > 0
                status_filtrado = {k: v for k, v in status_data.items() if v > 0}
                
                if status_filtrado:
                    plt.pie(
                        status_filtrado.values(),
                        labels=status_filtrado.keys(),
                        autopct='%1.1f%%',
                        startangle=90,
                        colors=plt.cm.Paired.colors
                    )
                    plt.axis('equal')
                    plt.title(f'Distribuição de Status - {colaborador}')
                    
                    # Converter para base64
                    buf = io.BytesIO()
                    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
                    buf.seek(0)
                    img_str = base64.b64encode(buf.read()).decode('utf-8')
                    plt.close(fig)
                    
                    graficos['distribuicao_status'] = img_str
            
            # 2. Gráfico de comparação com a média da equipe
            metricas_equipe = self.calcular_metricas_equipe(grupo)
            
            if metricas_equipe:
                fig = plt.figure(figsize=(10, 6))
                
                # Dados para comparação
                categorias = ['Eficiência', 'Tempo Médio', 'Volume']
                
                # Valores do colaborador (com tratamento para None)
                eficiencia_colab = metricas.get('taxa_eficiencia', 0)
                if eficiencia_colab is None:
                    eficiencia_colab = 0
                else:
                    eficiencia_colab = eficiencia_colab * 100
                    
                tempo_colab = metricas.get('tempo_medio_resolucao', 0)
                if tempo_colab is None:
                    tempo_colab = 0
                    
                volume_colab = metricas.get('total_registros', 0)
                
                colaborador_valores = [
                    eficiencia_colab,
                    tempo_colab,
                    volume_colab
                ]
                
                # Valores da equipe (com tratamento para None)
                eficiencia_equipe = metricas_equipe.get('eficiencia_media', 0)
                if eficiencia_equipe is None:
                    eficiencia_equipe = 0
                    
                tempo_equipe = metricas_equipe.get('tempo_medio_resolucao', 0)
                if tempo_equipe is None:
                    tempo_equipe = 0
                    
                volume_medio = metricas_equipe.get('total_registros', 0) / max(1, metricas_equipe.get('total_colaboradores', 1))
                
                medias_equipe = [
                    eficiencia_equipe,
                    tempo_equipe,
                    volume_medio
                ]
                
                # Calcular percentuais relativos (com tratamento para divisão por zero)
                percentuais = [
                    (colaborador_valores[0] / max(0.1, medias_equipe[0])) * 100 if medias_equipe[0] else 0,
                    (1 - colaborador_valores[1] / max(0.1, medias_equipe[1], colaborador_valores[1])) * 100 if medias_equipe[1] and colaborador_valores[1] else 0,
                    (colaborador_valores[2] / max(0.1, medias_equipe[2])) * 100 if medias_equipe[2] else 0
                ]
                
                # Criar gráfico de barras
                x = np.arange(len(categorias))
                width = 0.35
                
                fig, ax = plt.subplots(figsize=(10, 6))
                rects1 = ax.bar(x - width/2, [100, 100, 100], width, label='Média da Equipe', color='#1976D2')
                rects2 = ax.bar(x + width/2, percentuais, width, label=colaborador, color='#FFC107')
                
                ax.set_ylabel('Percentual (%)')
                ax.set_title(f'Comparação: {colaborador} vs. Média da Equipe')
                ax.set_xticks(x)
                ax.set_xticklabels(categorias)
                ax.legend()
                
                # Adicionar rótulos
                def autolabel(rects):
                    for rect in rects:
                        height = rect.get_height()
                        ax.annotate(f'{height:.0f}%',
                                    xy=(rect.get_x() + rect.get_width() / 2, height),
                                    xytext=(0, 3),
                                    textcoords="offset points",
                                    ha='center', va='bottom')
                
                autolabel(rects1)
                autolabel(rects2)
                
                # Converter para base64
                buf = io.BytesIO()
                plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
                buf.seek(0)
                img_str = base64.b64encode(buf.read()).decode('utf-8')
                plt.close(fig)
                
                graficos['comparacao_equipe'] = img_str
            
            return graficos
        except Exception as e:
            st.error(f"Erro ao gerar gráficos: {str(e)}")
            st.error(traceback.format_exc())
            return {}
    
    def gerar_relatorio_individual(self, grupo, colaborador):
        """Gera um relatório individual detalhado para um colaborador"""
        try:
            if grupo not in st.session_state.analises or colaborador not in st.session_state.analises[grupo]:
                return None
            
            # Obter métricas do colaborador
            metricas = st.session_state.analises[grupo][colaborador]
            
            # Analisar desempenho
            analise = self.analisar_desempenho(metricas)
            
            # Gerar recomendações
            recomendacoes = self.gerar_recomendacoes(metricas)
            
            # Gerar gráficos
            graficos = self.gerar_graficos_colaborador(grupo, colaborador)
            
            # Criar relatório
            relatorio = {
                "id": str(uuid.uuid4()),
                "nome": colaborador,
                "grupo": grupo,
                "data_geracao": datetime.now().isoformat(),
                "periodo": f"{datetime.now().strftime('%d/%m/%Y')}",
                "metricas": metricas,
                "analise": analise,
                "recomendacoes": recomendacoes,
                "graficos": graficos
            }
            
            # Salvar relatório na sessão
            chave_relatorio = f"{grupo}_{colaborador}"
            st.session_state.relatorios_individuais[chave_relatorio] = relatorio
            
            return relatorio
        except Exception as e:
            st.error(f"Erro ao gerar relatório individual: {str(e)}")
            st.error(traceback.format_exc())
            return None
    
    def exportar_relatorio_pdf(self, relatorio):
        """Exporta o relatório individual para PDF"""
        try:
            if not relatorio:
                return None
            
            # Criar PDF
            pdf = FPDF()
            pdf.add_page()
            
            # Configurar fonte
            pdf.set_font('Arial', 'B', 16)
            
            # Título
            pdf.cell(0, 10, f"Relatório de Desempenho: {relatorio['nome']}", 0, 1, 'C')
            pdf.set_font('Arial', '', 12)
            pdf.cell(0, 10, f"Grupo: {relatorio['grupo'].upper()}", 0, 1, 'C')
            pdf.cell(0, 10, f"Data: {relatorio['periodo']}", 0, 1, 'C')
            pdf.ln(10)
            
            # Métricas principais
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, "Métricas Principais", 0, 1)
            pdf.set_font('Arial', '', 12)
            
            metricas = relatorio['metricas']
            
            pdf.cell(0, 10, f"Total de Registros: {metricas.get('total_registros', 0)}", 0, 1)
            
            taxa_eficiencia = metricas.get('taxa_eficiencia', 0)
            if taxa_eficiencia is not None:
                pdf.cell(0, 10, f"Taxa de Eficiência: {taxa_eficiencia*100:.1f}%", 0, 1)
            else:
                pdf.cell(0, 10, f"Taxa de Eficiência: N/A", 0, 1)
            
            tempo_medio = metricas.get('tempo_medio_resolucao')
            if tempo_medio is not None:
                pdf.cell(0, 10, f"Tempo Médio de Resolução: {tempo_medio:.1f} dias", 0, 1)
            else:
                pdf.cell(0, 10, f"Tempo Médio de Resolução: N/A", 0, 1)
            
            pdf.ln(5)
            
            # Análise de desempenho
            if 'analise' in relatorio:
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(0, 10, "Análise de Desempenho", 0, 1)
                pdf.set_font('Arial', '', 12)
                
                analise = relatorio['analise']
                
                if 'eficiencia' in analise:
                    ef = analise['eficiencia']
                    pdf.cell(0, 10, f"Eficiência: {ef['valor']:.1f}% - {ef['nivel']}", 0, 1)
                
                if 'tempo_resolucao' in analise:
                    tr = analise['tempo_resolucao']
                    if tr['valor'] is not None:
                        pdf.cell(0, 10, f"Tempo de Resolução: {tr['valor']:.1f} dias - {tr['nivel']}", 0, 1)
                    else:
                        pdf.cell(0, 10, f"Tempo de Resolução: N/A", 0, 1)
                
                if 'volume_trabalho' in analise:
                    vt = analise['volume_trabalho']
                    pdf.cell(0, 10, f"Volume de Trabalho: {vt['valor']} registros - {vt['nivel']}", 0, 1)
                
                if 'taxa_conclusao' in analise:
                    tc = analise['taxa_conclusao']
                    pdf.cell(0, 10, f"Taxa de Conclusão: {tc['valor']:.1f}% - {tc['nivel']}", 0, 1)
                
                pdf.ln(5)
            
            # Recomendações
            if 'recomendacoes' in relatorio and relatorio['recomendacoes']:
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(0, 10, "Recomendações", 0, 1)
                pdf.set_font('Arial', '', 12)
                
                for rec in relatorio['recomendacoes']:
                    pdf.set_font('Arial', 'B', 12)
                    pdf.cell(0, 10, f"{rec['area']} - {rec['recomendacao']}", 0, 1)
                    pdf.set_font('Arial', '', 12)
                    pdf.cell(0, 10, f"Ação Recomendada: {rec['acao']}", 0, 1)
                    pdf.ln(5)
            
            # Gráficos
            if 'graficos' in relatorio and relatorio['graficos']:
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(0, 10, "Visualizações", 0, 1)
                
                graficos = relatorio['graficos']
                
                # Distribuição de status
                if 'distribuicao_status' in graficos:
                    pdf.set_font('Arial', 'B', 12)
                    pdf.cell(0, 10, "Distribuição de Status", 0, 1)
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                        tmp.write(base64.b64decode(graficos['distribuicao_status']))
                        tmp_path = tmp.name
                    
                    pdf.image(tmp_path, x=20, w=170)
                    os.unlink(tmp_path)
                    pdf.ln(10)
                
                if 'comparacao_equipe' in graficos:
                    pdf.set_font('Arial', 'B', 12)
                    pdf.cell(0, 10, "Comparação com a Média da Equipe", 0, 1)
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                        tmp.write(base64.b64decode(graficos['comparacao_equipe']))
                        tmp_path = tmp.name
                    
                    pdf.image(tmp_path, x=20, w=170)
                    os.unlink(tmp_path)
                
                # Salvar PDF em um buffer
                pdf_buffer = io.BytesIO()
                pdf.output(pdf_buffer)
                pdf_buffer.seek(0)
                
                return pdf_buffer
        except Exception as e:
            st.error(f"Erro ao exportar relatório para PDF: {str(e)}")
            st.error(traceback.format_exc())
            return None
    
    def calcular_metricas_equipe(self, grupo):
        """Calcula métricas agregadas para toda a equipe"""
        if grupo not in st.session_state.analises:
            return {}
        
        colaboradores = st.session_state.analises[grupo]
        if not colaboradores:
            return {}
        
        try:
            # Inicializar métricas
            metricas_equipe = {
                "total_colaboradores": len(colaboradores),
                "total_registros": 0,
                "eficiencia_media": 0,
                "tempo_medio_resolucao": 0,
                "distribuicao_status": {},
                "ranking_eficiencia": [],
                "ranking_tempo": [],
                "ranking_volume": []
            }
            
            # Coletar dados para cálculos
            eficiencias = []
            tempos = []
            volumes = []
            status_total = {}
            
            for nome, metricas in colaboradores.items():
                # Total de registros
                total_registros = metricas.get('total_registros', 0)
                metricas_equipe["total_registros"] += total_registros
                volumes.append((nome, total_registros))
                
                # Eficiência
                eficiencia = metricas.get('taxa_eficiencia', 0)
                if eficiencia is not None:
                    eficiencias.append((nome, eficiencia * 100))
                
                # Tempo médio
                tempo = metricas.get('tempo_medio_resolucao')
                if tempo is not None:
                    tempos.append((nome, tempo))
                
                # Distribuição de status
                for status, quantidade in metricas.get('distribuicao_status', {}).items():
                    if status in status_total:
                        status_total[status] += quantidade
                    else:
                        status_total[status] = quantidade
            
            # Calcular médias
            if eficiencias:
                metricas_equipe["eficiencia_media"] = sum(e[1] for e in eficiencias) / len(eficiencias)
            
            if tempos:
                metricas_equipe["tempo_medio_resolucao"] = sum(t[1] for t in tempos) / len(tempos)
            
            # Distribuição de status
            metricas_equipe["distribuicao_status"] = status_total
            
            # Rankings
            metricas_equipe["ranking_eficiencia"] = sorted(eficiencias, key=lambda x: x[1], reverse=True)
            metricas_equipe["ranking_tempo"] = sorted(tempos, key=lambda x: x[1])
            metricas_equipe["ranking_volume"] = sorted(volumes, key=lambda x: x[1], reverse=True)
            
            return metricas_equipe
        except Exception as e:
            st.error(f"Erro ao calcular métricas da equipe: {str(e)}")
            return {}

    def exibir_dashboard(self):
        """Exibe o dashboard principal"""
        st.markdown('<h1 class="main-header">Dashboard de Desempenho de Colaboradores</h1>', unsafe_allow_html=True)
        
        # Verificar se há dados para exibir
        if not any(st.session_state.analises.values()):
            st.info("Nenhum dado disponível. Faça upload de arquivos Excel para análise.")
            
            st.markdown("""
            ### Como usar este dashboard:
            1. **Faça upload de arquivos** Excel na barra lateral
            2. **Selecione o grupo** (Julio ou Leandro) para classificar os dados
            3. **Processe o arquivo** para extrair métricas de desempenho
            4. **Visualize o dashboard** com métricas e comparações
            5. **Gere relatórios individuais** para análise detalhada por colaborador
            """)
            return
        
        # Visão Geral
        tabs = st.tabs(["Visão Geral", "Análise Comparativa", "Relatórios Individuais"])
        
        with tabs[0]:
            st.markdown('<div class="card"><h2 class="sub-header">Visão Geral</h2>', unsafe_allow_html=True)
            
            # Métricas gerais por grupo
            col1, col2 = st.columns(2)
            
            for idx, grupo in enumerate(["julio", "leandro"]):
                if grupo in st.session_state.analises and st.session_state.analises[grupo]:
                    with col1 if idx == 0 else col2:
                        st.markdown(f'<h3>Grupo {grupo.upper()}</h3>', unsafe_allow_html=True)
                        
                        colaboradores = st.session_state.analises[grupo]
                        num_colaboradores = len(colaboradores)
                        
                        if num_colaboradores > 0:
                            # Calcular métricas gerais
                            eficiencias = [c.get('taxa_eficiencia', 0) for c in colaboradores.values()]
                            eficiencias = [e for e in eficiencias if e is not None]
                            
                            tempos = [c.get('tempo_medio_resolucao', 0) for c in colaboradores.values() if c.get('tempo_medio_resolucao') is not None]
                            volumes = [c.get('total_registros', 0) for c in colaboradores.values()]
                            
                            eficiencia_media = np.mean(eficiencias) * 100 if eficiencias else 0
                            tempo_medio = np.mean(tempos) if tempos else 0
                            volume_total = sum(volumes)
                            
                            # Exibir métricas em cards
                            mc1, mc2, mc3 = st.columns(3)
                            
                            with mc1:
                                st.metric("Colaboradores", num_colaboradores)
                            
                            with mc2:
                                st.metric("Eficiência Média", f"{eficiencia_media:.1f}%")
                            
                            with mc3:
                                st.metric("Tempo Médio", f"{tempo_medio:.1f} dias")
                            
                            # Gráfico de distribuição de status
                            st.subheader("Distribuição de Status")
                            
                            # Coletar dados de status de todos os colaboradores
                            status_total = {}
                            for c in colaboradores.values():
                                for status, quantidade in c.get('distribuicao_status', {}).items():
                                    if status in status_total:
                                        status_total[status] += quantidade
                                    else:
                                        status_total[status] = quantidade
                            
                            if status_total:
                                # Criar DataFrame para o gráfico
                                df_status = pd.DataFrame({
                                    'Status': list(status_total.keys()),
                                    'Quantidade': list(status_total.values())
                                })
                                
                                # Ordenar por quantidade
                                df_status = df_status.sort_values('Quantidade', ascending=False)
                                
                                # Criar gráfico de barras
                                fig = px.bar(
                                    df_status,
                                    x='Status',
                                    y='Quantidade',
                                    title=f"Distribuição de Status - Grupo {grupo.upper()}",
                                    color='Status',
                                    color_discrete_sequence=px.colors.qualitative.Pastel
                                )
                                
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.info("Não há dados de status disponíveis")
                        else:
                            st.info(f"Nenhum colaborador encontrado no grupo {grupo}")
                else:
                    with col1 if idx == 0 else col2:
                        st.info(f"Nenhum dado disponível para o grupo {grupo}")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Top colaboradores
            st.markdown('<div class="card"><h2 class="sub-header">Top Colaboradores</h2>', unsafe_allow_html=True)
            
            # Coletar dados de todos os colaboradores
            todos_colaboradores = {}
            for grupo, colaboradores in st.session_state.analises.items():
                for nome, dados in colaboradores.items():
                    todos_colaboradores[f"{grupo} - {nome}"] = dados
            
            if todos_colaboradores:
                tcol1, tcol2, tcol3 = st.columns(3)
                
                with tcol1:
                    st.subheader("Melhor Eficiência")
                    # Ordenar por eficiência
                    top_eficiencia = sorted(
                        [(nome, dados.get('taxa_eficiencia', 0) * 100) for nome, dados in todos_colaboradores.items() if dados.get('taxa_eficiencia') is not None],
                        key=lambda x: x[1],
                        reverse=True
                    )[:5]
                    
                    df_eficiencia = pd.DataFrame(top_eficiencia, columns=["Colaborador", "Eficiência (%)"])
                    st.dataframe(df_eficiencia, use_container_width=True, hide_index=True)
                
                with tcol2:
                    st.subheader("Menor Tempo Médio")
                    # Ordenar por tempo médio (do menor para o maior)
                    tempos_validos = [(nome, dados.get('tempo_medio_resolucao', float('inf'))) 
                                   for nome, dados in todos_colaboradores.items() 
                                   if dados.get('tempo_medio_resolucao') is not None]
                    
                    top_tempo = sorted(tempos_validos, key=lambda x: x[1])[:5]
                    
                    df_tempo = pd.DataFrame(top_tempo, columns=["Colaborador", "Tempo Médio (dias)"])
                    st.dataframe(df_tempo, use_container_width=True, hide_index=True)
                
                with tcol3:
                    st.subheader("Maior Volume")
                    # Ordenar por volume
                    top_volume = sorted(
                        [(nome, dados.get('total_registros', 0)) for nome, dados in todos_colaboradores.items()],
                        key=lambda x: x[1],
                        reverse=True
                    )[:5]
                    
                    df_volume = pd.DataFrame(top_volume, columns=["Colaborador", "Total de Registros"])
                    st.dataframe(df_volume, use_container_width=True, hide_index=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Análise Comparativa
        with tabs[1]:
            st.markdown('<h2 class="sub-header">Análise Comparativa</h2>', unsafe_allow_html=True)
            
            # Selecionar grupo para análise
            grupo_selecionado = st.selectbox(
                "Selecione o grupo para análise comparativa:",
                options=[g for g in st.session_state.analises.keys() if st.session_state.analises[g]],
                key="grupo_comparativo"
            )
            
            if grupo_selecionado and grupo_selecionado in st.session_state.analises:
                colaboradores = st.session_state.analises[grupo_selecionado]
                
                if colaboradores:
                    # Métricas da equipe
                    metricas_equipe = self.calcular_metricas_equipe(grupo_selecionado)
                    
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.subheader("Comparação de Eficiência")
                    
                    # Preparar dados para gráfico de barras
                    nomes = []
                    eficiencias = []
                    cores = []
                    
                    media_eficiencia = metricas_equipe.get("eficiencia_media", 0)
                    
                    for nome, metricas in colaboradores.items():
                        eficiencia = metricas.get('taxa_eficiencia', 0)
                        if eficiencia is not None:
                            eficiencia = eficiencia * 100
                            nomes.append(nome)
                            eficiencias.append(eficiencia)
                            
                            # Definir cor com base na comparação com a média
                            if eficiencia >= media_eficiencia * 1.1:  # 10% acima da média
                                cores.append('#00C853')  # Verde
                            elif eficiencia <= media_eficiencia * 0.9:  # 10% abaixo da média
                                cores.append('#FF3D00')  # Vermelho
                            else:
                                cores.append('#FFD600')  # Amarelo
                    
                    # Criar DataFrame para o gráfico
                    df_comp = pd.DataFrame({
                        'Colaborador': nomes,
                        'Eficiência (%)': eficiencias
                    })
                    
                    # Ordenar por eficiência
                    df_comp = df_comp.sort_values('Eficiência (%)', ascending=False)
                    
                    # Criar gráfico de barras
                    fig = px.bar(
                        df_comp,
                        x='Colaborador',
                        y='Eficiência (%)',
                        title=f"Comparação de Eficiência - Grupo {grupo_selecionado.upper()}",
                        color='Eficiência (%)',
                        color_continuous_scale=['#FF3D00', '#FFD600', '#00C853']
                    )
                    
                    # Adicionar linha para a média
                    fig.add_hline(
                        y=media_eficiencia,
                        line_dash="dash",
                        line_color="black",
                        annotation_text=f"Média: {media_eficiencia:.1f}%",
                        annotation_position="top right"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Comparação de tempo médio
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.subheader("Comparação de Tempo Médio de Resolução")
                    
                    # Preparar dados para gráfico de barras
                    nomes = []
                    tempos = []
                    cores = []
                    
                    tempos_validos = [(nome, metricas.get('tempo_medio_resolucao', None)) 
                                    for nome, metricas in colaboradores.items() 
                                    if metricas.get('tempo_medio_resolucao') is not None]
                    
                    if tempos_validos:
                        media_tempo = metricas_equipe.get("tempo_medio_resolucao", 0)
                        
                        for nome, tempo in tempos_validos:
                            nomes.append(nome)
                            tempos.append(tempo)
                            
                            # Definir cor com base na comparação com a média (para tempo, menor é melhor)
                            if tempo <= media_tempo * 0.9:  # 10% abaixo da média (melhor)
                                cores.append('#00C853')  # Verde
                            elif tempo >= media_tempo * 1.1:  # 10% acima da média (pior)
                                cores.append('#FF3D00')  # Vermelho
                            else:
                                cores.append('#FFD600')  # Amarelo
                        
                        # Criar DataFrame para o gráfico
                        df_tempo = pd.DataFrame({
                            'Colaborador': nomes,
                            'Tempo Médio (dias)': tempos
                        })
                        
                        # Ordenar por tempo (do menor para o maior)
                        df_tempo = df_tempo.sort_values('Tempo Médio (dias)', ascending=True)
                        
                        # Criar gráfico de barras
                        fig = px.bar(
                            df_tempo,
                            x='Colaborador',
                            y='Tempo Médio (dias)',
                            title=f"Comparação de Tempo Médio - Grupo {grupo_selecionado.upper()}",
                            color='Tempo Médio (dias)',
                            color_continuous_scale=['#00C853', '#FFD600', '#FF3D00']
                        )
                        
                        # Adicionar linha para a média
                        fig.add_hline(
                            y=media_tempo,
                            line_dash="dash",
                            line_color="black",
                            annotation_text=f"Média: {media_tempo:.1f} dias",
                            annotation_position="top right"
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Não há dados de tempo médio disponíveis para comparação")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Comparação de volume de trabalho
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.subheader("Comparação de Volume de Trabalho")
                    
                    # Preparar dados para gráfico de barras
                    nomes = []
                    volumes = []
                    
                    for nome, metricas in colaboradores.items():
                        nomes.append(nome)
                        volumes.append(metricas.get('total_registros', 0))
                    
                    # Criar DataFrame para o gráfico
                    df_volume = pd.DataFrame({
                        'Colaborador': nomes,
                        'Total de Registros': volumes
                    })
                    
                    # Ordenar por volume (do maior para o menor)
                    df_volume = df_volume.sort_values('Total de Registros', ascending=False)
                    
                    # Criar gráfico de barras
                    fig = px.bar(
                        df_volume,
                        x='Colaborador',
                        y='Total de Registros',
                        title=f"Comparação de Volume de Trabalho - Grupo {grupo_selecionado.upper()}",
                        color='Total de Registros',
                        color_continuous_scale=px.colors.sequential.Blues
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.info(f"Nenhum colaborador encontrado no grupo {grupo_selecionado}")
            else:
                st.info("Selecione um grupo para visualizar a análise comparativa")
        
        # Relatórios Individuais
        with tabs[2]:
            st.markdown('<h2 class="sub-header">Relatórios Individuais</h2>', unsafe_allow_html=True)
            
            # Selecionar grupo e colaborador
            col1, col2 = st.columns(2)
            
            with col1:
                grupo_relatorio = st.selectbox(
                    "Selecione o grupo:",
                    options=[g for g in st.session_state.analises.keys() if st.session_state.analises[g]],
                    key="grupo_relatorio"
                )
            
            colaboradores_disponiveis = []
            if grupo_relatorio and grupo_relatorio in st.session_state.analises:
                colaboradores_disponiveis = list(st.session_state.analises[grupo_relatorio].keys())
            
            with col2:
                colaborador_relatorio = st.selectbox(
                    "Selecione o colaborador:",
                    options=colaboradores_disponiveis,
                    key="colaborador_relatorio"
                )
            
            if grupo_relatorio and colaborador_relatorio:
                if colaborador_relatorio in st.session_state.analises[grupo_relatorio]:
                    # Botão para gerar relatório
                    if st.button("Gerar Relatório Individual", key="btn_gerar_relatorio"):
                        with st.spinner("Gerando relatório detalhado..."):
                            # Gerar relatório
                            relatorio = self.gerar_relatorio_individual(grupo_relatorio, colaborador_relatorio)
                            
                            if relatorio:
                                # Armazenar relatório na sessão
                                chave_relatorio = f"{grupo_relatorio}_{colaborador_relatorio}"
                                st.session_state.relatorios_individuais[chave_relatorio] = relatorio
                                
                                st.success(f"Relatório gerado com sucesso para {colaborador_relatorio}!")
                                
                                # Exibir relatório
                                self.exibir_relatorio_individual(relatorio)
                                
                                # Botão para exportar PDF
                                pdf_buffer = self.exportar_relatorio_pdf(relatorio)
                                if pdf_buffer:
                                    st.download_button(
                                        label="Baixar Relatório em PDF",
                                        data=pdf_buffer,
                                        file_name=f"Relatorio_{colaborador_relatorio}_{datetime.now().strftime('%Y%m%d')}.pdf",
                                        mime="application/pdf",
                                        key="btn_download_pdf"
                                    )
                            else:
                                st.error("Não foi possível gerar o relatório. Verifique os dados do colaborador.")
                    
                    # Exibir relatório existente, se disponível
                    chave_relatorio = f"{grupo_relatorio}_{colaborador_relatorio}"
                    if chave_relatorio in st.session_state.relatorios_individuais:
                        relatorio = st.session_state.relatorios_individuais[chave_relatorio]
                        
                        # Exibir relatório
                        self.exibir_relatorio_individual(relatorio)
                        
                        # Botão para exportar PDF
                        pdf_buffer = self.exportar_relatorio_pdf(relatorio)
                        if pdf_buffer:
                            st.download_button(
                                label="Baixar Relatório em PDF",
                                data=pdf_buffer,
                                file_name=f"Relatorio_{colaborador_relatorio}_{datetime.now().strftime('%Y%m%d')}.pdf",
                                mime="application/pdf",
                                key="btn_download_pdf_existente"
                            )
                else:
                    st.info(f"Colaborador {colaborador_relatorio} não encontrado no grupo {grupo_relatorio}")
            else:
                st.info("Selecione um grupo e um colaborador para gerar o relatório individual")
    
    def exibir_relatorio_individual(self, relatorio):
        """Exibe o relatório individual na interface"""
        try:
            if not relatorio:
                st.warning("Relatório vazio ou inválido")
                return
                
            # Exibir cabeçalho
            st.markdown(f"## Relatório de Desempenho: {relatorio['nome']}")
            st.markdown(f"**Grupo:** {relatorio['grupo']}")
            st.markdown(f"**Período:** {relatorio['periodo']}")
            
            # Métricas principais
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                valor = relatorio['metricas'].get('total_registros', 0)
                st.metric("Total de Registros", valor)
            
            with col2:
                valor = relatorio['metricas'].get('taxa_eficiencia', 0)
                if valor is not None:
                    valor_fmt = f"{valor*100:.1f}%"
                else:
                    valor_fmt = "N/A"
                st.metric("Taxa de Eficiência", valor_fmt)
            
            with col3:
                valor = relatorio['metricas'].get('tempo_medio_resolucao', 0)
                if valor is not None:
                    valor_fmt = f"{valor:.1f} dias"
                else:
                    valor_fmt = "N/A"
                st.metric("Tempo Médio", valor_fmt)
            
            with col4:
                tendencia = relatorio['metricas'].get('tendencia', {})
                direcao = tendencia.get('direcao', 'estável')
                st.metric("Tendência", direcao.capitalize())
            
            # Análise de desempenho
            st.subheader("Análise de Desempenho")
            
            if 'analise' in relatorio:
                analise = relatorio['analise']
                
                # Eficiência
                if 'eficiencia' in analise:
                    ef = analise['eficiencia']
                    valor = ef.get('valor', 0)
                    nivel = ef.get('nivel', 'N/A')
                    
                    st.markdown(f"**Eficiência:** {valor:.1f}% - {nivel}")
                
                # Tempo de resolução
                if 'tempo_resolucao' in analise:
                    tr = analise['tempo_resolucao']
                    valor = tr.get('valor', 0)
                    nivel = tr.get('nivel', 'N/A')
                    
                    if valor is not None:
                        st.markdown(f"**Tempo de Resolução:** {valor:.1f} dias - {nivel}")
                    else:
                        st.markdown(f"**Tempo de Resolução:** N/A")
                
                # Volume de trabalho
                if 'volume_trabalho' in analise:
                    vt = analise['volume_trabalho']
                    valor = vt.get('valor', 0)
                    nivel = vt.get('nivel', 'N/A')
                    
                    st.markdown(f"**Volume de Trabalho:** {valor} registros - {nivel}")
                
                # Taxa de conclusão
                if 'taxa_conclusao' in analise:
                    tc = analise['taxa_conclusao']
                    valor = tc.get('valor', 0)
                    nivel = tc.get('nivel', 'N/A')
                    
                    st.markdown(f"**Taxa de Conclusão:** {valor:.1f}% - {nivel}")
            
            # Recomendações
            if 'recomendacoes' in relatorio and relatorio['recomendacoes']:
                st.subheader("Recomendações")
                
                for rec in relatorio['recomendacoes']:
                    with st.expander(f"{rec['area']} - {rec['recomendacao']}"):
                        st.markdown(f"**Ação Recomendada:** {rec['acao']}")
            
            # Gráficos
            if 'graficos' in relatorio and relatorio['graficos']:
                st.subheader("Visualizações")
                
                graficos = relatorio['graficos']
                
                # Distribuição de status
                if 'distribuicao_status' in graficos:
                    st.image(base64.b64decode(graficos['distribuicao_status']))
                
                # Tendência de eficiência
                if 'tendencia_eficiencia' in graficos:
                    st.image(base64.b64decode(graficos['tendencia_eficiencia']))
                
                # Comparação com equipe
                if 'comparacao_equipe' in graficos:
                    st.image(base64.b64decode(graficos['comparacao_equipe']))
        
        except Exception as e:
            st.error(f"Erro ao exibir relatório: {str(e)}")
            st.error(traceback.format_exc())
    
    def exibir_sidebar(self):
        """Exibe a barra lateral com opções de upload e configuração"""
        with st.sidebar:
            st.image("https://img.icons8.com/color/96/000000/dashboard-layout.png", width=100)
            st.title("Configurações")
            
            st.subheader("Upload de Arquivos")
            
            # Seleção de grupo
            grupo = st.radio("Selecione o grupo:", ["julio", "leandro"])
            
            # Upload de arquivo
            arquivo_carregado = st.file_uploader("Selecione um arquivo Excel:", type=["xlsx", "xls"])
            
            if arquivo_carregado is not None:
                if st.button("Processar Arquivo"):
                    with st.spinner("Processando arquivo..."):
                        sucesso = self.processar_arquivo(arquivo_carregado, grupo)
                        if sucesso:
                            st.success("Arquivo processado com sucesso!")
                        else:
                            st.error("Erro ao processar arquivo.")
            
            st.divider()
            
            # Opções adicionais
            st.subheader("Opções")
            
            if st.button("Limpar Dados"):
                if st.session_state.analises:
                    st.session_state.analises = {}
                    st.session_state.relatorios_individuais = {}
                    st.session_state.arquivos_analisados = []
                    st.session_state.ultima_analise = None
                    
                    # Remover arquivo de resultados
                    relatorio_path = os.path.join('resultados', 'relatorio_analise.json')
                    if os.path.exists(relatorio_path):
                        os.remove(relatorio_path)
                    
                    st.success("Todos os dados foram limpos!")
                else:
                    st.info("Não há dados para limpar.")
            
            # Informações sobre a última análise
            if st.session_state.ultima_analise:
                st.divider()
                st.subheader("Informações")
                
                try:
                    data_analise = datetime.fromisoformat(st.session_state.ultima_analise)
                    st.info(f"Última análise: {data_analise.strftime('%d/%m/%Y %H:%M')}")
                except:
                    st.info(f"Última análise: {st.session_state.ultima_analise}")
                
                st.info(f"Arquivos analisados: {len(st.session_state.arquivos_analisados)}")
                
                total_colaboradores = sum(len(grupo_data) for grupo_data in st.session_state.analises.values())
                st.info(f"Total de colaboradores: {total_colaboradores}")

# Inicializar e executar o dashboard
if __name__ == "__main__":
    dashboard = DashboardGerenciador()
    dashboard.exibir_sidebar()
    dashboard.exibir_dashboard() 