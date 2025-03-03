import pandas as pd
import numpy as np
import os
import re
from datetime import datetime, timedelta
import warnings
import traceback
import json
import streamlit as st
import base64

# Suprimir avisos específicos do pandas
warnings.filterwarnings("ignore", category=pd.errors.SettingWithCopyWarning)

class AnalisadorExcel:
    def __init__(self, file_path):
        self.file_path = file_path
        self.colaboradores = {}
        self.erros = []
        print(f"Criando analisador para {os.path.basename(file_path)}")
        
    def normalizar_coluna(self, nome_coluna):
        """Normaliza o nome da coluna para um formato padrão"""
        if not isinstance(nome_coluna, str):
            return str(nome_coluna)
        
        # Remover espaços extras e converter para maiúsculas
        nome_normalizado = re.sub(r'\s+', ' ', nome_coluna).strip().upper()
        
        return nome_normalizado
    
    def corrigir_formato_data(self, valor):
        """Tenta converter um valor para data em formato padrão"""
        if pd.isna(valor) or valor is None:
            return None
            
        try:
            # Se já for datetime, retornar como está
            if isinstance(valor, (pd.Timestamp, datetime)):
                return valor
                
            # Se for string, tentar converter
            if isinstance(valor, str):
                # Remover caracteres não numéricos para análise
                valor_limpo = re.sub(r'[^\d/\-:]', '', valor).strip()
                
                # Se estiver vazio após limpeza, retornar None
                if not valor_limpo:
                    print(f"Erro ao converter data: {valor}")
                    return None
                
                # Tentar diferentes formatos de data
                formatos = [
                    '%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%d/%m/%y', 
                    '%d-%m-%y', '%Y/%m/%d', '%d/%m/%Y %H:%M:%S',
                    '%d-%m-%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S'
                ]
                
                for formato in formatos:
                    try:
                        return pd.to_datetime(valor_limpo, format=formato)
                    except:
                        continue
                
                # Se nenhum formato específico funcionar, deixar o pandas tentar inferir
                try:
                    return pd.to_datetime(valor)
                except:
                    print(f"Erro ao converter data: {valor}")
                    return None
            
            # Se for número, assumir que é um número de série do Excel
            if isinstance(valor, (int, float)):
                try:
                    # Converter número de série do Excel para datetime
                    # O Excel conta dias desde 01/01/1900 (com um bug para 1900 não ser bissexto)
                    return pd.to_datetime('1899-12-30') + pd.Timedelta(days=float(valor))
                except:
                    print(f"Erro ao converter número para data: {valor}")
                    return None
                    
            print(f"Tipo de data não reconhecido: {type(valor)} - {valor}")
            return None
        except Exception as e:
            print(f"Erro ao processar data '{valor}': {str(e)}")
            return None
    
    def calcular_metricas_colaborador(self, df, nome_colaborador):
        """Calcula métricas para um colaborador específico"""
        try:
            # Verificar se há dados suficientes
            if df.empty:
                print(f"Sem dados para {nome_colaborador}")
                return None
                
            # Verificar colunas necessárias
            colunas_necessarias = ['DATA', 'STATUS']
            colunas_presentes = [col for col in colunas_necessarias if col in df.columns]
            
            if len(colunas_presentes) < len(colunas_necessarias):
                colunas_faltantes = set(colunas_necessarias) - set(colunas_presentes)
                print(f"Erro ao processar dados de {nome_colaborador}: {colunas_faltantes}")
                return None
            
            # Criar cópia segura do DataFrame para evitar SettingWithCopyWarning
            df_analise = df.copy()
            
            # Converter colunas de data
            try:
                # Usar .loc para evitar SettingWithCopyWarning
                df_analise.loc[:, 'DATA'] = df_analise['DATA'].apply(self.corrigir_formato_data)
                
                # Verificar se a conversão funcionou
                if df_analise['DATA'].isna().all():
                    print(f"Erro: Todas as datas são nulas para {nome_colaborador}")
                    return None
                
                # Remover linhas com datas nulas
                df_analise = df_analise.dropna(subset=['DATA'])
                
                # Converter coluna RESOLUCAO se existir
                if 'RESOLUCAO' in df_analise.columns:
                    df_analise.loc[:, 'RESOLUCAO'] = df_analise['RESOLUCAO'].apply(self.corrigir_formato_data)
            except Exception as e:
                print(f"Erro ao processar datas para {nome_colaborador}: {str(e)}")
                traceback.print_exc()
                return None
            
            # Calcular total de registros
            total_registros = len(df_analise)
            
            # Calcular distribuição de status
            try:
                distribuicao_status = df_analise['STATUS'].value_counts().to_dict()
                # Converter para porcentagens
                distribuicao_percentual = {k: round(v / total_registros * 100, 1) for k, v in distribuicao_status.items()}
            except Exception as e:
                print(f"Erro ao calcular distribuição de status: {str(e)}")
                distribuicao_status = {}
                distribuicao_percentual = {}
            
            # Calcular tempo médio de resolução
            tempo_medio_resolucao = None
            tempo_mediano_resolucao = None
            outliers_resolucao = 0
            
            try:
                if 'RESOLUCAO' in df_analise.columns:
                    # Calcular diferença entre data de resolução e data de criação
                    df_resolvidos = df_analise.dropna(subset=['RESOLUCAO'])
                    
                    if not df_resolvidos.empty:
                        # Usar método seguro para calcular a diferença
                        try:
                            # Converter para datetime se ainda não for
                            if not pd.api.types.is_datetime64_dtype(df_resolvidos['DATA']):
                                df_resolvidos.loc[:, 'DATA'] = pd.to_datetime(df_resolvidos['DATA'])
                            if not pd.api.types.is_datetime64_dtype(df_resolvidos['RESOLUCAO']):
                                df_resolvidos.loc[:, 'RESOLUCAO'] = pd.to_datetime(df_resolvidos['RESOLUCAO'])
                            
                            # Calcular diferença em dias
                            df_resolvidos.loc[:, 'tempo_resolucao'] = (df_resolvidos['RESOLUCAO'] - df_resolvidos['DATA']).dt.days
                            
                            # Remover valores negativos ou extremamente altos (provavelmente erros)
                            df_resolvidos = df_resolvidos[(df_resolvidos['tempo_resolucao'] >= 0) & (df_resolvidos['tempo_resolucao'] <= 365)]
                            
                            if not df_resolvidos.empty:
                                tempo_medio_resolucao = round(df_resolvidos['tempo_resolucao'].mean(), 1)
                                tempo_mediano_resolucao = round(df_resolvidos['tempo_resolucao'].median(), 1)
                                
                                # Identificar outliers (método IQR)
                                Q1 = df_resolvidos['tempo_resolucao'].quantile(0.25)
                                Q3 = df_resolvidos['tempo_resolucao'].quantile(0.75)
                                IQR = Q3 - Q1
                                outliers_resolucao = len(df_resolvidos[(df_resolvidos['tempo_resolucao'] < (Q1 - 1.5 * IQR)) | 
                                                                      (df_resolvidos['tempo_resolucao'] > (Q3 + 1.5 * IQR))])
                        except Exception as e:
                            print(f"Erro ao calcular tempo de resolução: {str(e)}")
                            traceback.print_exc()
            except Exception as e:
                print(f"Erro ao processar tempos de resolução: {str(e)}")
                traceback.print_exc()
            
            # Calcular taxa de eficiência (registros resolvidos / total)
            taxa_eficiencia = None
            try:
                if 'STATUS' in df_analise.columns:
                    # Considerar como resolvidos os status diferentes de PENDENTE, ANÁLISE, PRIORIDADE
                    status_pendentes = ['PENDENTE', 'ANÁLISE', 'PRIORIDADE', 'PRIORIDADE TOTAL']
                    resolvidos = df_analise[~df_analise['STATUS'].isin(status_pendentes)]
                    taxa_eficiencia = round(len(resolvidos) / total_registros, 3) if total_registros > 0 else 0
            except Exception as e:
                print(f"Erro ao calcular taxa de eficiência: {str(e)}")
            
            # Calcular médias diárias por status
            medias_diarias = {}
            try:
                if 'DATA' in df_analise.columns and 'STATUS' in df_analise.columns:
                    # Agrupar por data e status
                    df_analise.loc[:, 'data_apenas'] = df_analise['DATA'].dt.date
                    agrupado = df_analise.groupby(['data_apenas', 'STATUS']).size().reset_index(name='contagem')
                    
                    # Calcular média por status
                    for status in df_analise['STATUS'].unique():
                        status_data = agrupado[agrupado['STATUS'] == status]
                        if not status_data.empty:
                            media = round(status_data['contagem'].mean(), 1)
                            medias_diarias[status] = media
            except Exception as e:
                print(f"Erro ao calcular médias diárias: {str(e)}")
                traceback.print_exc()
            
            # Analisar tendência
            tendencia = {}
            try:
                if 'DATA' in df_analise.columns:
                    # Agrupar por data
                    df_analise.loc[:, 'data_apenas'] = df_analise['DATA'].dt.date
                    contagem_diaria = df_analise.groupby('data_apenas').size().reset_index(name='contagem')
                    
                    if len(contagem_diaria) > 1:
                        # Converter datas para números (dias desde a primeira data)
                        primeira_data = contagem_diaria['data_apenas'].min()
                        contagem_diaria.loc[:, 'dias'] = (contagem_diaria['data_apenas'] - primeira_data).dt.days
                        
                        # Calcular coeficiente de correlação
                        corr = np.corrcoef(contagem_diaria['dias'], contagem_diaria['contagem'])[0, 1]
                        
                        # Determinar direção da tendência
                        if corr > 0.1:
                            direcao = 'crescente'
                        elif corr < -0.1:
                            direcao = 'decrescente'
                        else:
                            direcao = 'estável'
                            
                            # Calcular R²
                            if len(contagem_diaria) > 2:
                                x = contagem_diaria['dias'].values.reshape(-1, 1)
                                y = contagem_diaria['contagem'].values
                                
                                # Calcular regressão linear manualmente
                                n = len(x)
                                x_mean = np.mean(x)
                                y_mean = np.mean(y)
                                
                                numerator = np.sum((x - x_mean) * (y - y_mean))
                                denominator = np.sum((x - x_mean) ** 2)
                                
                                if denominator != 0:
                                    slope = numerator / denominator
                                    intercept = y_mean - slope * x_mean
                                    
                                    y_pred = slope * x + intercept
                                    r2 = max(0, 1 - np.sum((y - y_pred.flatten()) ** 2) / np.sum((y - y_mean) ** 2))
                                else:
                                    slope = 0
                                    intercept = y_mean
                                    r2 = 0
                            else:
                                slope = 0
                                intercept = 0
                                r2 = 0
                            
                            tendencia = {
                                'direcao': direcao,
                                'correlacao': round(corr, 2),
                                'r2': round(r2, 2),
                                'slope': round(float(slope), 4),
                                'intercept': round(float(intercept), 2)
                            }
            except Exception as e:
                print(f"Erro ao analisar tendência: {str(e)}")
                traceback.print_exc()
                tendencia = {'direcao': 'estável', 'r2': 0}
            
            # Analisar padrão semanal
            padrao_semanal = {}
            try:
                if 'DATA' in df_analise.columns:
                    # Extrair dia da semana
                    df_analise.loc[:, 'dia_semana'] = df_analise['DATA'].dt.day_name()
                    
                    # Contar registros por dia da semana
                    padrao_semanal = df_analise['dia_semana'].value_counts().to_dict()
            except Exception as e:
                print(f"Erro ao analisar padrão semanal: {str(e)}")
            
            # Compilar todas as métricas
            metricas = {
                'nome': nome_colaborador,
                'total_registros': total_registros,
                'distribuicao_status': distribuicao_status,
                'distribuicao_percentual': distribuicao_percentual,
                'tempo_medio_resolucao': tempo_medio_resolucao,
                'tempo_mediano_resolucao': tempo_mediano_resolucao,
                'outliers_resolucao': outliers_resolucao,
                'taxa_eficiencia': taxa_eficiencia,
                'medias_diarias': medias_diarias,
                'tendencia': tendencia,
                'padrao_semanal': padrao_semanal
            }
            
            return metricas
        except Exception as e:
            print(f"Erro ao calcular métricas para {nome_colaborador}: {str(e)}")
            traceback.print_exc()
            return None
    
    def exibir_metricas_colaborador(self, metricas):
        """Exibe as métricas calculadas para um colaborador"""
        if not metricas:
            return
            
        print(f"\n=== Análise Detalhada: {metricas['nome']} ===\n")
        
        # 1. Volumes e Distribuição
        print("1. Volumes e Distribuição")
        print(f"Total de Registros: {metricas['total_registros']}")
        
        if metricas['distribuicao_status']:
            print("\nDistribuição de Status:")
            for status, count in sorted(metricas['distribuicao_status'].items(), key=lambda x: x[1], reverse=True):
                percentual = metricas['distribuicao_percentual'].get(status, 0)
                print(f"  {status}: {count} ({percentual}%)")
        
        # 2. Tempos de Resolução
        print("\n2. Tempos de Resolução")
        if metricas['tempo_medio_resolucao'] is not None:
            print(f"Tempo Médio: {metricas['tempo_medio_resolucao']} dias")
            print(f"Tempo Mediano: {metricas['tempo_mediano_resolucao']} dias")
            print(f"Outliers: {metricas['outliers_resolucao']} casos")
        
        # 3. Indicadores de Eficiência
        print("\n3. Indicadores de Eficiência")
        if metricas['taxa_eficiencia'] is not None:
            print(f"Taxa de Eficiência: {metricas['taxa_eficiencia'] * 100:.1f}%")
        
        if metricas['medias_diarias']:
            print("\nMédias Diárias:")
            for status, media in sorted(metricas['medias_diarias'].items()):
                print(f"  {status}: {media}")
        
        # 4. Análise de Tendências
        print("\n4. Análise de Tendências")
        if metricas['tendencia']:
            direcao = metricas['tendencia'].get('direcao', 'estável')
            r2 = metricas['tendencia'].get('r2', 0)
            print(f"Tendência: {direcao} (R² = {r2:.2f})")
        
        # 5. Padrão Semanal
        print("\n5. Padrão Semanal")
        if metricas['padrao_semanal']:
            for dia, count in sorted(metricas['padrao_semanal'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {dia}: {count}")
    
    def analisar_arquivo(self):
        """Analisa todas as abas do arquivo Excel"""
        try:
            print(f"Analisando arquivo {self.file_path}")
            
            # Verificar se o arquivo existe
            if not os.path.exists(self.file_path):
                print(f"Arquivo não encontrado: {self.file_path}")
                self.erros.append({
                    'arquivo': os.path.basename(self.file_path),
                    'erro': 'Arquivo não encontrado'
                })
                return []
                
            # Ler o arquivo Excel com tratamento de erros
            try:
                xls = pd.ExcelFile(self.file_path)
            except Exception as e:
                print(f"Erro ao abrir arquivo Excel: {str(e)}")
                self.erros.append({
                    'arquivo': os.path.basename(self.file_path),
                    'erro': f'Erro ao abrir arquivo: {str(e)}'
                })
                return []
                
            # Processar cada aba
            nomes_colaboradores = []
            
            for sheet_name in xls.sheet_names:
                print(f"Analisando dados de: {sheet_name}")
                
                try:
                    # Ler a aba com tratamento de erros
                    try:
                        df = pd.read_excel(self.file_path, sheet_name=sheet_name)
                    except Exception as e:
                        print(f"Erro ao ler aba {sheet_name}: {str(e)}")
                        self.erros.append({
                            'aba': sheet_name,
                            'erro': f'Erro ao ler aba: {str(e)}'
                        })
                        continue
                    
                    # Verificar se há dados
                    if df.empty:
                        print(f"Aba {sheet_name} está vazia.")
                        continue
                        
                    # Normalizar nomes das colunas
                    df.columns = [self.normalizar_coluna(col) for col in df.columns]
                    
                    # Calcular métricas para o colaborador
                    metricas = self.calcular_metricas_colaborador(df, sheet_name)
                    
                    if metricas:
                        self.colaboradores[sheet_name] = metricas
                        nomes_colaboradores.append(sheet_name)
                        self.exibir_metricas_colaborador(metricas)
                        
                except Exception as e:
                    print(f"Erro ao processar aba {sheet_name}: {str(e)}")
                    traceback.print_exc()
                    self.erros.append({
                        'aba': sheet_name,
                        'erro': str(e)
                    })
                    continue
            
            # Calcular métricas comparativas
            self.calcular_metricas_comparativas()
            
            return nomes_colaboradores
        except Exception as e:
            print(f"Erro ao analisar arquivo: {str(e)}")
            traceback.print_exc()
            self.erros.append({
                'arquivo': os.path.basename(self.file_path),
                'erro': str(e)
            })
            return []
    
    def calcular_metricas_comparativas(self):
        """Calcula métricas comparativas entre colaboradores"""
        try:
            print("\n=== Análise Comparativa entre Colaboradores ===")
            
            # Verificar se há colaboradores suficientes
            if len(self.colaboradores) < 2:
                return
                
            # Extrair métricas para comparação
            eficiencias = {}
            tempos_resolucao = {}
            volumes = {}
            
            for nome, metricas in self.colaboradores.items():
                if metricas['taxa_eficiencia'] is not None:
                    eficiencias[nome] = metricas['taxa_eficiencia'] * 100
                    
                if metricas['tempo_medio_resolucao'] is not None:
                    tempos_resolucao[nome] = metricas['tempo_medio_resolucao']
                    
                volumes[nome] = metricas['total_registros']
            
            # Calcular rankings
            ranking_eficiencia = sorted(eficiencias.items(), key=lambda x: x[1], reverse=True)
            ranking_tempo = sorted(tempos_resolucao.items(), key=lambda x: x[1])
            ranking_volume = sorted(volumes.items(), key=lambda x: x[1], reverse=True)
            
            # Armazenar métricas comparativas
            self.metricas_comparativas = {
                'ranking_eficiencia': ranking_eficiencia,
                'ranking_tempo': ranking_tempo,
                'ranking_volume': ranking_volume,
                'media_eficiencia': np.mean(list(eficiencias.values())) if eficiencias else None,
                'media_tempo': np.mean(list(tempos_resolucao.values())) if tempos_resolucao else None,
                'media_volume': np.mean(list(volumes.values())) if volumes else None
            }
            
        except Exception as e:
            print(f"Erro ao calcular métricas comparativas: {str(e)}")
            traceback.print_exc()
    
    def obter_resultados(self):
        """Retorna os resultados da análise em formato JSON"""
        resultados = {
            'colaboradores': self.colaboradores,
            'metricas_comparativas': getattr(self, 'metricas_comparativas', {}),
            'erros': self.erros
        }
        
        return resultados

    def gerar_relatorio_html_completo(self):
        """Gera um relatório HTML completo com dados de todos os colaboradores"""
        try:
            if not st.session_state.analises:
                st.warning("Não há dados para gerar o relatório")
                return None
            
            # Iniciar HTML
            html = f"""
            <!DOCTYPE html>
            <html lang="pt-br">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Relatório Completo de Desempenho</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 1200px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    .header {{
                        text-align: center;
                        margin-bottom: 30px;
                        border-bottom: 2px solid #1976D2;
                        padding-bottom: 10px;
                    }}
                    .header h1 {{
                        color: #1976D2;
                        margin-bottom: 5px;
                    }}
                    .header p {{
                        color: #666;
                        font-size: 1.1em;
                    }}
                    .grupo-section {{
                        margin-bottom: 40px;
                    }}
                    .grupo-header {{
                        background-color: #1976D2;
                        color: white;
                        padding: 10px 15px;
                        border-radius: 5px;
                        margin-bottom: 20px;
                    }}
                    .card-container {{
                        display: flex;
                        flex-wrap: wrap;
                        gap: 20px;
                        margin-bottom: 30px;
                    }}
                    .card {{
                        background-color: #f8f9fa;
                        border-radius: 5px;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                        padding: 15px;
                        width: calc(33% - 20px);
                        min-width: 300px;
                    }}
                    .card h3 {{
                        color: #1976D2;
                        margin-top: 0;
                        border-bottom: 1px solid #ddd;
                        padding-bottom: 10px;
                    }}
                    .metric {{
                        margin-bottom: 15px;
                    }}
                    .metric-title {{
                        font-weight: bold;
                        margin-bottom: 5px;
                    }}
                    .metric-value {{
                        font-size: 1.2em;
                    }}
                    .good {{
                        color: #00C853;
                    }}
                    .medium {{
                        color: #FFD600;
                    }}
                    .bad {{
                        color: #FF3D00;
                    }}
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin-bottom: 20px;
                    }}
                    th, td {{
                        border: 1px solid #ddd;
                        padding: 8px 12px;
                        text-align: left;
                    }}
                    th {{
                        background-color: #f2f2f2;
                    }}
                    tr:nth-child(even) {{
                        background-color: #f9f9f9;
                    }}
                    .chart-container {{
                        margin: 20px 0;
                        text-align: center;
                    }}
                    .summary-section {{
                        background-color: #e3f2fd;
                        padding: 20px;
                        border-radius: 5px;
                        margin-bottom: 30px;
                    }}
                    .recommendations {{
                        background-color: #fff8e1;
                        padding: 15px;
                        border-left: 4px solid #ffc107;
                        margin-bottom: 20px;
                    }}
                    .footer {{
                        text-align: center;
                        margin-top: 50px;
                        padding-top: 20px;
                        border-top: 1px solid #ddd;
                        color: #666;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Relatório Completo de Desempenho</h1>
                    <p>Data de geração: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
                </div>
                
                <div class="summary-section">
                    <h2>Resumo Geral</h2>
                    <p>Este relatório apresenta uma análise detalhada do desempenho de todos os colaboradores registrados no sistema.</p>
                    
                    <table>
                        <tr>
                            <th>Grupo</th>
                            <th>Total de Colaboradores</th>
                            <th>Total de Registros</th>
                            <th>Eficiência Média</th>
                            <th>Tempo Médio de Resolução</th>
                        </tr>
            """
            
            # Adicionar resumo por grupo
            for grupo in ["julio", "leandro"]:
                if grupo in st.session_state.analises:
                    colaboradores = st.session_state.analises[grupo]
                    
                    # Calcular métricas do grupo
                    total_colaboradores = len(colaboradores)
                    total_registros = sum(c.get('total_registros', 0) for c in colaboradores.values())
                    
                    # Eficiência média
                    eficiencias = [c.get('taxa_eficiencia', 0) for c in colaboradores.values() if c.get('taxa_eficiencia') is not None]
                    eficiencia_media = sum(eficiencias) / len(eficiencias) * 100 if eficiencias else 0
                    
                    # Tempo médio
                    tempos = [c.get('tempo_medio_resolucao', 0) for c in colaboradores.values() if c.get('tempo_medio_resolucao') is not None]
                    tempo_medio = sum(tempos) / len(tempos) if tempos else 0
                    
                    html += f"""
                        <tr>
                            <td>{grupo.upper()}</td>
                            <td>{total_colaboradores}</td>
                            <td>{total_registros}</td>
                            <td>{eficiencia_media:.1f}%</td>
                            <td>{tempo_medio:.1f} dias</td>
                        </tr>
                    """
            
            html += """
                    </table>
                </div>
            """
            
            # Adicionar seções por grupo
            for grupo in ["julio", "leandro"]:
                if grupo in st.session_state.analises and st.session_state.analises[grupo]:
                    html += f"""
                    <div class="grupo-section">
                        <div class="grupo-header">
                            <h2>Grupo {grupo.upper()}</h2>
                        </div>
                        
                        <h3>Distribuição de Status</h3>
                        <table>
                            <tr>
                                <th>Colaborador</th>
                                <th>Total</th>
                                <th>VERIFICADOS</th>
                                <th>PENDENTE</th>
                                <th>QUITADO</th>
                                <th>ANÁLISE</th>
                                <th>APROVADO</th>
                                <th>Outros</th>
                            </tr>
                    """
                    
                    # Adicionar linhas da tabela para cada colaborador
                    for nome, metricas in st.session_state.analises[grupo].items():
                        total = metricas.get('total_registros', 0)
                        status_dist = metricas.get('distribuicao_status', {})
                        
                        verificados = status_dist.get("VERIFICADOS", 0)
                        pendente = status_dist.get("PENDENTE", 0)
                        quitado = status_dist.get("QUITADO", 0)
                        analise = status_dist.get("ANÁLISE", 0)
                        aprovado = status_dist.get("APROVADO", 0)
                        
                        # Calcular outros status
                        principais = ["VERIFICADOS", "PENDENTE", "QUITADO", "ANÁLISE", "APROVADO"]
                        outros = sum(v for k, v in status_dist.items() if k not in principais)
                        
                        html += f"""
                            <tr>
                                <td>{nome}</td>
                                <td>{total}</td>
                                <td>{verificados}</td>
                                <td>{pendente}</td>
                                <td>{quitado}</td>
                                <td>{analise}</td>
                                <td>{aprovado}</td>
                                <td>{outros}</td>
                            </tr>
                        """
                    
                    html += """
                        </table>
                        
                        <h3>Métricas de Desempenho</h3>
                        <div class="card-container">
                    """
                    
                    # Adicionar cards para cada colaborador
                    for nome, metricas in st.session_state.analises[grupo].items():
                        # Obter métricas
                        total_registros = metricas.get('total_registros', 0)
                        
                        taxa_eficiencia = metricas.get('taxa_eficiencia', 0)
                        if taxa_eficiencia is not None:
                            taxa_eficiencia = taxa_eficiencia * 100
                            eficiencia_class = "good" if taxa_eficiencia >= 80 else "medium" if taxa_eficiencia >= 60 else "bad"
                            eficiencia_texto = f"{taxa_eficiencia:.1f}%"
                        else:
                            eficiencia_class = ""
                            eficiencia_texto = "N/A"
                        
                        tempo_medio = metricas.get('tempo_medio_resolucao')
                        if tempo_medio is not None:
                            tempo_class = "good" if tempo_medio <= 1 else "medium" if tempo_medio <= 3 else "bad"
                            tempo_texto = f"{tempo_medio:.1f} dias"
                        else:
                            tempo_class = ""
                            tempo_texto = "N/A"
                        
                        # Tendência
                        tendencia = metricas.get('tendencia', {})
                        direcao = tendencia.get('direcao', 'estável')
                        
                        html += f"""
                            <div class="card">
                                <h3>{nome}</h3>
                                
                                <div class="metric">
                                    <div class="metric-title">Total de Registros</div>
                                    <div class="metric-value">{total_registros}</div>
                                </div>
                                
                                <div class="metric">
                                    <div class="metric-title">Taxa de Eficiência</div>
                                    <div class="metric-value {eficiencia_class}">{eficiencia_texto}</div>
                                </div>
                                
                                <div class="metric">
                                    <div class="metric-title">Tempo Médio de Resolução</div>
                                    <div class="metric-value {tempo_class}">{tempo_texto}</div>
                                </div>
                                
                                <div class="metric">
                                    <div class="metric-title">Tendência</div>
                                    <div class="metric-value">{direcao.capitalize()}</div>
                                </div>
                            </div>
                        """
                    
                    html += """
                        </div>
                    </div>
                    """
            
            # Adicionar seção de melhores desempenhos
            html += """
                <div class="summary-section">
                    <h2>Melhores Desempenhos</h2>
                    
                    <div class="card-container">
            """
            
            # Coletar dados de todos os colaboradores
            todos_colaboradores = {}
            for grupo, colaboradores in st.session_state.analises.items():
                for nome, dados in colaboradores.items():
                    todos_colaboradores[f"{grupo.upper()} - {nome}"] = dados
            
            # Top eficiência
            html += """
                <div class="card">
                    <h3>Top 5 - Eficiência</h3>
            """
            
            # Ordenar por eficiência
            top_eficiencia = sorted(
                [(nome, dados.get('taxa_eficiencia', 0) * 100) for nome, dados in todos_colaboradores.items() if dados.get('taxa_eficiencia') is not None],
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            for i, (nome, valor) in enumerate(top_eficiencia, 1):
                html += f"""
                    <div class="metric">
                        <div class="metric-title">{i}. {nome}</div>
                        <div class="metric-value good">{valor:.1f}%</div>
                    </div>
                """
            
            html += """
                </div>
            """
            
            # Top menor tempo
            html += """
                <div class="card">
                    <h3>Top 5 - Menor Tempo</h3>
            """
            
            # Ordenar por tempo (menor para maior)
            tempos_validos = [(nome, dados.get('tempo_medio_resolucao', float('inf'))) 
                           for nome, dados in todos_colaboradores.items() 
                           if dados.get('tempo_medio_resolucao') is not None]
            
            top_tempo = sorted(tempos_validos, key=lambda x: x[1])[:5]
            
            for i, (nome, valor) in enumerate(top_tempo, 1):
                html += f"""
                    <div class="metric">
                        <div class="metric-title">{i}. {nome}</div>
                        <div class="metric-value good">{valor:.1f} dias</div>
                    </div>
                """
            
            html += """
                </div>
            """
            
            # Top volume
            html += """
                <div class="card">
                    <h3>Top 5 - Volume</h3>
            """
            
            # Ordenar por volume
            top_volume = sorted(
                [(nome, dados.get('total_registros', 0)) for nome, dados in todos_colaboradores.items()],
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            for i, (nome, valor) in enumerate(top_volume, 1):
                html += f"""
                    <div class="metric">
                        <div class="metric-title">{i}. {nome}</div>
                        <div class="metric-value">{valor} registros</div>
                    </div>
                """
            
            html += """
                    </div>
                </div>
                </div>
            """
            
            # Adicionar recomendações gerais
            html += """
                <div class="recommendations">
                    <h2>Recomendações Gerais</h2>
                    <p>Com base na análise dos dados, recomendamos as seguintes ações:</p>
                    <ul>
                        <li><strong>Eficiência:</strong> Colaboradores com eficiência abaixo de 60% podem se beneficiar de treinamento adicional.</li>
                        <li><strong>Tempo de Resolução:</strong> Estabelecer metas de tempo máximo de resolução de 3 dias para melhorar a produtividade geral.</li>
                        <li><strong>Distribuição de Carga:</strong> Equilibrar a distribuição de tarefas entre colaboradores para evitar sobrecarga.</li>
                        <li><strong>Monitoramento Contínuo:</strong> Realizar análises periódicas para identificar tendências e ajustar estratégias.</li>
                    </ul>
                </div>
            """
            
            # Adicionar rodapé
            html += """
                <div class="footer">
                    <p>Relatório gerado automaticamente pelo Dashboard de Desempenho de Colaboradores</p>
                    <p>© 2023 - Todos os direitos reservados</p>
                </div>
            </body>
            </html>
            """
            
            # Salvar o HTML em um arquivo
            relatorio_path = os.path.join('resultados', f'relatorio_completo_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html')
            with open(relatorio_path, 'w', encoding='utf-8') as f:
                f.write(html)
            
            return relatorio_path
        
        except Exception as e:
            st.error(f"Erro ao gerar relatório HTML: {str(e)}")
            st.error(traceback.format_exc())
            return None

    def processar_arquivo_bytes(self, bytes_data, grupo, nome_arquivo):
        """Processa um arquivo Excel a partir de bytes"""
        try:
            # Criar diretório de uploads se não existir
            os.makedirs('uploads', exist_ok=True)
            
            # Salvar arquivo temporariamente
            temp_path = os.path.join('uploads', nome_arquivo)
            with open(temp_path, 'wb') as f:
                f.write(bytes_data)
            
            # Processar o arquivo
            analisador = AnalisadorExcel(temp_path)
            analisador.processar_arquivo()
            
            # Verificar se há colaboradores
            if not analisador.colaboradores:
                st.warning(f"Nenhum colaborador encontrado no arquivo {nome_arquivo}")
                return False
            
            # Inicializar o grupo se não existir
            if grupo not in st.session_state.analises:
                st.session_state.analises[grupo] = {}
            
            # Adicionar colaboradores ao grupo
            for nome, metricas in analisador.colaboradores.items():
                st.session_state.analises[grupo][nome] = metricas
            
            # Atualizar informações de sessão
            st.session_state.arquivos_analisados.append(nome_arquivo)
            st.session_state.ultima_analise = datetime.now().isoformat()
            
            # Salvar resultados
            self.salvar_resultados()
            
            return True
        except Exception as e:
            st.error(f"Erro ao processar arquivo {nome_arquivo}: {str(e)}")
            st.error(traceback.format_exc())
            return False

    def processar_arquivo(self):
        """Processa o arquivo Excel e extrai métricas por colaborador"""
        try:
            print(f"Analisando arquivo {os.path.basename(self.file_path)}")
            
            # Verificar se o arquivo existe
            if not os.path.exists(self.file_path):
                print(f"Arquivo não encontrado: {self.file_path}")
                return
            
            # Ler o arquivo Excel
            try:
                df = pd.read_excel(self.file_path)
            except Exception as e:
                print(f"Erro ao ler o arquivo Excel: {str(e)}")
                traceback.print_exc()
                return
            
            # Verificar se há dados
            if df.empty:
                print("Arquivo Excel vazio")
                return
            
            # Normalizar nomes de colunas
            df.columns = [self.normalizar_coluna(col) for col in df.columns]
            
            # Identificar coluna de colaborador
            coluna_colaborador = None
            for col in df.columns:
                if "COLABORADOR" in col or "RESPONSAVEL" in col:
                    coluna_colaborador = col
                    break
            
            if not coluna_colaborador:
                print("Coluna de colaborador não encontrada")
                return
            
            # Agrupar por colaborador
            colaboradores_unicos = df[coluna_colaborador].dropna().unique()
            
            for colaborador in colaboradores_unicos:
                # Filtrar dados do colaborador
                df_colaborador = df[df[coluna_colaborador] == colaborador]
                
                # Calcular métricas
                metricas = self.calcular_metricas_colaborador(df_colaborador, colaborador)
                
                if metricas:
                    self.colaboradores[colaborador] = metricas
            
            print(f"Processamento concluído. {len(self.colaboradores)} colaboradores encontrados.")
        
        except Exception as e:
            print(f"Erro ao processar arquivo: {str(e)}")
            traceback.print_exc()

# Classe para gerenciar o dashboard (deve estar fora do bloco if __name__)
class DashboardGerenciador:
    def __init__(self):
        self.analises = {}
    
    def carregar_arquivos_automaticamente(self):
        """Carrega automaticamente os arquivos Excel da pasta especificada"""
        try:
            # Caminho específico para a pasta de dados
            pasta_dados = "F:/okok/data"
            
            # Verificar se a pasta existe
            if not os.path.exists(pasta_dados):
                print(f"A pasta {pasta_dados} não foi encontrada.")
                return False
            
            # Arquivos específicos a serem carregados
            arquivos = [
                ("julio", os.path.join(pasta_dados, "(JULIO) LISTAS INDIVIDUAIS.xlsx")),
                ("leandro", os.path.join(pasta_dados, "(LEANDRO_ADRIANO) LISTAS INDIVIDUAIS.xlsx"))
            ]
            
            # Processar cada arquivo
            for grupo, caminho_arquivo in arquivos:
                if os.path.exists(caminho_arquivo):
                    print(f"Carregando arquivo: {caminho_arquivo}")
                    
                    # Criar analisador com o caminho completo
                    analisador = AnalisadorExcel(caminho_arquivo)
                    analisador.processar_arquivo()
                    
                    # Verificar se há colaboradores
                    if not analisador.colaboradores:
                        print(f"Nenhum colaborador encontrado no arquivo {caminho_arquivo}")
                        continue
                    
                    # Inicializar o grupo se não existir
                    if grupo not in self.analises:
                        self.analises[grupo] = {}
                    
                    # Adicionar colaboradores ao grupo
                    for nome, metricas in analisador.colaboradores.items():
                        self.analises[grupo][nome] = metricas
                    
                    print(f"Arquivo {caminho_arquivo} processado com sucesso!")
                else:
                    print(f"Arquivo não encontrado: {caminho_arquivo}")
            
            # Exibir lista de colaboradores
            print("\nLista de Colaboradores:")
            for grupo, colaboradores in self.analises.items():
                print(f"\nGrupo {grupo.upper()}:")
                for nome in colaboradores.keys():
                    print(f"- {nome}")
            
            return True
        
        except Exception as e:
            print(f"Erro ao carregar arquivos automaticamente: {str(e)}")
            traceback.print_exc()
            return False

# Executar diretamente para teste
if __name__ == "__main__":
    # Criar instância
    dashboard = DashboardGerenciador()
    
    # Carregar arquivos
    dashboard.carregar_arquivos_automaticamente()
