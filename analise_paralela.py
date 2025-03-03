#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Análise Paralela de Colaboradores
=================================
Este script executa análises em paralelo dos arquivos Excel e identifica melhorias
na qualidade da análise baseada na coluna "SITUAÇÃO" de cada colaborador.
"""

import os
import pandas as pd
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict, Counter
import traceback

# Importações locais
from debug_excel import AnalisadorExcel
from analise_360 import Analise360
from data_analysis_pipeline import DataAnalysisPipeline

def analisar_situacao_colaborador(nome_arquivo, nome_aba):
    """
    Analisa a qualidade dos registros na coluna SITUAÇÃO para um colaborador específico.
    
    Args:
        nome_arquivo (str): Caminho para o arquivo Excel
        nome_aba (str): Nome da aba/colaborador a ser analisada
        
    Returns:
        dict: Dicionário com métricas de qualidade dos registros
    """
    try:
        # Carregar dados do colaborador
        df = pd.read_excel(nome_arquivo, sheet_name=nome_aba)
        
        # Normalizar nomes das colunas
        colunas_normalizadas = []
        for col in df.columns:
            col_norm = str(col).strip().upper()
            if col_norm in ['SITUAÇÂO', 'SITUAÇÃO']:
                col_norm = 'SITUACAO'
            colunas_normalizadas.append(col_norm)
        
        df.columns = colunas_normalizadas
        
        # Verificar se a coluna SITUACAO existe
        if 'SITUACAO' not in df.columns:
            return {
                'colaborador': nome_aba,
                'arquivo': nome_arquivo,
                'erro': 'Coluna SITUACAO não encontrada',
                'status': 'FALHA'
            }
        
        # Análise de qualidade da coluna SITUACAO
        total_registros = len(df)
        registros_vazios = df['SITUACAO'].isna().sum()
        valores_unicos = df['SITUACAO'].dropna().unique()
        contagem_valores = df['SITUACAO'].value_counts().to_dict()
        
        # Verificar padrões de preenchimento
        valores_padronizados = ['PENDENTE', 'VERIFICADO', 'APROVADO', 'QUITADO', 'CANCELADO', 'EM ANÁLISE']
        valores_nao_padronizados = [v for v in valores_unicos if v not in valores_padronizados]
        
        # Verificar se há atualizações diárias
        tem_data = False
        atualizacoes_diarias = {}
        coluna_data = None
        
        # Verificar se há coluna de data
        for col in df.columns:
            if 'DATA' in col:
                tem_data = True
                coluna_data = col
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    # Agrupar por data e contar atualizações de status
                    atualizacoes = df.groupby(df[col].dt.date)['SITUACAO'].count()
                    atualizacoes_diarias = atualizacoes.to_dict()
                except:
                    pass
        
        # Calcular métricas de qualidade
        taxa_preenchimento = (total_registros - registros_vazios) / total_registros if total_registros > 0 else 0
        taxa_padronizacao = (len(valores_unicos) - len(valores_nao_padronizados)) / len(valores_unicos) if len(valores_unicos) > 0 else 0
        
        # Verificar consistência nas atualizações diárias
        consistencia_diaria = 0
        if atualizacoes_diarias:
            # Calcular desvio padrão das atualizações diárias
            std_atualizacoes = np.std(list(atualizacoes_diarias.values()))
            media_atualizacoes = np.mean(list(atualizacoes_diarias.values()))
            
            # Coeficiente de variação (menor é melhor)
            if media_atualizacoes > 0:
                consistencia_diaria = 1 - min(1, std_atualizacoes / media_atualizacoes)
        
        # Calcular score geral de qualidade
        score_qualidade = (
            0.4 * taxa_preenchimento +  # 40% para preenchimento
            0.3 * taxa_padronizacao +   # 30% para padronização
            0.3 * consistencia_diaria   # 30% para consistência diária
        ) * 100
        
        # Análise de transições de estado (se houver coluna de data)
        analise_transicoes = {}
        if tem_data and coluna_data and not df[coluna_data].isna().all():
            # Ordenar por data
            df_ordenado = df.sort_values(by=coluna_data)
            
            # Verificar transições de estado
            if 'SITUACAO' in df_ordenado.columns and len(df_ordenado) > 1:
                transicoes = []
                situacao_anterior = None
                
                for idx, row in df_ordenado.iterrows():
                    situacao_atual = row['SITUACAO']
                    if pd.notna(situacao_anterior) and pd.notna(situacao_atual) and situacao_anterior != situacao_atual:
                        transicoes.append((situacao_anterior, situacao_atual))
                    situacao_anterior = situacao_atual
                
                # Contar transições
                contagem_transicoes = Counter(transicoes)
                analise_transicoes = {f"{de} -> {para}": contagem for (de, para), contagem in contagem_transicoes.items()}
        
        # Análise de tempo médio em cada situação
        tempos_medios = {}
        if tem_data and coluna_data and not df[coluna_data].isna().all():
            # Agrupar por situação e calcular tempo médio
            df_ordenado = df.sort_values(by=coluna_data)
            df_ordenado['data_anterior'] = df_ordenado[coluna_data].shift(1)
            df_ordenado['tempo_no_estado'] = (df_ordenado[coluna_data] - df_ordenado['data_anterior']).dt.days
            
            # Calcular tempo médio por situação
            tempos_por_situacao = df_ordenado.groupby('SITUACAO')['tempo_no_estado'].mean()
            tempos_medios = tempos_por_situacao.to_dict()
        
        # Gerar visualização da distribuição de situações
        grafico_path = None
        try:
            if contagem_valores:
                plt.figure(figsize=(10, 6))
                sns.barplot(x=list(contagem_valores.keys()), y=list(contagem_valores.values()))
                plt.title(f'Distribuição de Situações - {nome_aba}')
                plt.xlabel('Situação')
                plt.ylabel('Quantidade')
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                # Salvar gráfico
                diretorio_graficos = 'graficos_situacao'
                if not os.path.exists(diretorio_graficos):
                    try:
                        os.makedirs(diretorio_graficos)
                    except FileExistsError:
                        # Diretório já existe, podemos continuar
                        pass
                
                # Garantir que o nome do arquivo seja único
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                nome_arquivo_grafico = f'situacao_{nome_aba.replace(" ", "_")}_{timestamp}.png'
                grafico_path = os.path.join(diretorio_graficos, nome_arquivo_grafico)
                plt.savefig(grafico_path)
                plt.close()
        except Exception as e:
            print(f"Erro ao gerar gráfico para {nome_aba}: {str(e)}")
        
        # Identificar problemas e sugestões
        problemas = []
        sugestoes = []
        
        if registros_vazios > 0:
            problemas.append(f"{registros_vazios} registros com SITUACAO vazia")
            sugestoes.append("Preencher todos os campos de SITUACAO")
            
        if valores_nao_padronizados:
            problemas.append(f"{len(valores_nao_padronizados)} valores não padronizados: {', '.join(valores_nao_padronizados)}")
            sugestoes.append("Padronizar valores de SITUACAO para: PENDENTE, VERIFICADO, APROVADO, QUITADO, CANCELADO, EM ANÁLISE")
            
        if not tem_data:
            problemas.append("Não há coluna de DATA para análise temporal")
            sugestoes.append("Adicionar coluna de DATA para permitir análise de atualizações diárias")
            
        if consistencia_diaria < 0.5 and atualizacoes_diarias:
            problemas.append("Baixa consistência nas atualizações diárias")
            sugestoes.append("Manter ritmo constante de atualizações diárias")
        
        return {
            'colaborador': nome_aba,
            'arquivo': nome_arquivo,
            'total_registros': total_registros,
            'registros_vazios': registros_vazios,
            'taxa_preenchimento': taxa_preenchimento * 100,
            'valores_unicos': list(valores_unicos),
            'valores_nao_padronizados': valores_nao_padronizados,
            'taxa_padronizacao': taxa_padronizacao * 100,
            'atualizacoes_diarias': atualizacoes_diarias,
            'consistencia_diaria': consistencia_diaria * 100,
            'score_qualidade': score_qualidade,
            'analise_transicoes': analise_transicoes,
            'tempos_medios': tempos_medios,
            'grafico_path': grafico_path,
            'problemas': problemas,
            'sugestoes': sugestoes,
            'status': 'SUCESSO'
        }
        
    except Exception as e:
        return {
            'colaborador': nome_aba,
            'arquivo': nome_arquivo,
            'erro': str(e),
            'status': 'FALHA'
        }

def analisar_arquivo_paralelo(arquivos):
    """
    Analisa os arquivos Excel em paralelo.
    
    Args:
        arquivos (dict): Dicionário com os caminhos dos arquivos
            {'julio': caminho_arquivo_julio, 'leandro': caminho_arquivo_leandro}
    
    Returns:
        dict: Resultados da análise
    """
    resultados = {}
    
    for nome, arquivo in arquivos.items():
        print(f"Analisando arquivo: {os.path.basename(arquivo)}")
        try:
            if not os.path.exists(arquivo):
                print(f"Arquivo não encontrado: {arquivo}")
                continue
                
            xls = pd.ExcelFile(arquivo)
            for sheet in xls.sheet_names:
                if sheet.lower() not in ['resumo', 'índice', 'index', 'summary']:
                    df = pd.read_excel(arquivo, sheet_name=sheet)
                    resultados[f"{nome}_{sheet}"] = {
                        'grupo': nome,
                        'colaborador': sheet,
                        'dados': analisar_situacao_colaborador(arquivo, sheet)
                    }
                    
        except Exception as e:
            print(f"Erro ao analisar {arquivo}: {str(e)}")
            traceback.print_exc()
    
    return resultados

def gerar_relatorio_melhorias(resultados_julio, resultados_leandro):
    """
    Gera um relatório consolidado de melhorias baseado nas análises.
    
    Args:
        resultados_julio (dict): Resultados da análise do grupo Julio
        resultados_leandro (dict): Resultados da análise do grupo Leandro
        
    Returns:
        str: Relatório formatado em texto
    """
    # Combinar resultados
    todos_resultados = {**resultados_julio, **resultados_leandro}
    
    # Calcular estatísticas gerais
    total_colaboradores = len(todos_resultados)
    
    # Verificar se os resultados são dicionários válidos
    colaboradores_com_problemas = 0
    todos_problemas = []
    todas_sugestoes = []
    todas_transicoes = {}
    todos_tempos_medios = defaultdict(list)
    
    for nome, r in todos_resultados.items():
        # Verificar se o resultado é um dicionário válido
        if isinstance(r, dict) and r.get('status') == 'SUCESSO':
            if r.get('problemas'):
                colaboradores_com_problemas += 1
                todos_problemas.extend(r.get('problemas', []))
            
            if r.get('sugestoes'):
                todas_sugestoes.extend(r.get('sugestoes', []))
            
            if r.get('analise_transicoes'):
                for transicao, contagem in r.get('analise_transicoes', {}).items():
                    if transicao in todas_transicoes:
                        todas_transicoes[transicao] += contagem
                    else:
                        todas_transicoes[transicao] = contagem
            
            if r.get('tempos_medios'):
                for situacao, tempo in r.get('tempos_medios', {}).items():
                    todos_tempos_medios[situacao].append(tempo)
    
    # Contar problemas e sugestões
    contagem_problemas = Counter(todos_problemas)
    contagem_sugestoes = Counter(todas_sugestoes)
    
    # Calcular média dos tempos médios
    tempos_medios_consolidados = {
        situacao: sum(tempos) / len(tempos) 
        for situacao, tempos in todos_tempos_medios.items() 
        if len(tempos) > 0
    }
    
    # Identificar colaboradores com melhor e pior qualidade
    colaboradores_validos = []
    for nome, r in todos_resultados.items():
        if isinstance(r, dict) and r.get('status') == 'SUCESSO' and 'score_qualidade' in r:
            colaboradores_validos.append((nome, r.get('score_qualidade', 0)))
    
    # Ordenar por score de qualidade
    colaboradores_validos.sort(key=lambda x: x[1], reverse=True)
    
    # Gerar relatório em texto
    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    relatorio = f"""
================================================================================
RELATÓRIO DE MELHORIAS NA QUALIDADE DA ANÁLISE
================================================================================
Data: {data_atual}
Total de Colaboradores Analisados: {total_colaboradores}
Colaboradores com Problemas Identificados: {colaboradores_com_problemas} ({colaboradores_com_problemas/total_colaboradores*100:.1f}%)
Gráficos Gerados: {sum(1 for r in todos_resultados.values() if isinstance(r, dict) and r.get('grafico_path'))}

--------------------------------------------------------------------------------
PROBLEMAS MAIS COMUNS
--------------------------------------------------------------------------------
"""
    
    for problema, contagem in contagem_problemas.most_common(10):
        relatorio += f"- {problema}: {contagem} ocorrências\n"
    
    relatorio += f"""
--------------------------------------------------------------------------------
SUGESTÕES DE MELHORIA
--------------------------------------------------------------------------------
"""
    
    for sugestao, contagem in contagem_sugestoes.most_common(10):
        relatorio += f"- {sugestao}: {contagem} ocorrências\n"
    
    relatorio += f"""
--------------------------------------------------------------------------------
TRANSIÇÕES DE ESTADO MAIS COMUNS
--------------------------------------------------------------------------------
"""
    
    for transicao, contagem in sorted(todas_transicoes.items(), key=lambda x: x[1], reverse=True)[:10]:
        relatorio += f"- {transicao}: {contagem} ocorrências\n"
    
    relatorio += f"""
--------------------------------------------------------------------------------
TEMPO MÉDIO EM CADA SITUAÇÃO
--------------------------------------------------------------------------------
"""
    
    for situacao, tempo in sorted(tempos_medios_consolidados.items(), key=lambda x: x[1]):
        relatorio += f"- {situacao}: {tempo:.1f} dias\n"
    
    relatorio += f"""
--------------------------------------------------------------------------------
TOP 5 COLABORADORES (MELHOR QUALIDADE)
--------------------------------------------------------------------------------
"""
    
    for i, (nome, score) in enumerate(colaboradores_validos[:5], 1):
        relatorio += f"{i}. {nome}: {score:.1f} pontos\n"
    
    relatorio += f"""
--------------------------------------------------------------------------------
COLABORADORES QUE PRECISAM DE ATENÇÃO (PIOR QUALIDADE)
--------------------------------------------------------------------------------
"""
    
    for i, (nome, score) in enumerate(colaboradores_validos[-5:], 1):
        relatorio += f"{i}. {nome}: {score:.1f} pontos\n"
    
    # Gerar relatório HTML
    gerar_relatorio_html(todos_resultados, colaboradores_validos, contagem_problemas, 
                         contagem_sugestoes, todas_transicoes, tempos_medios_consolidados)
    
    return relatorio

def gerar_relatorio_html(todos_resultados, colaboradores_validos, contagem_problemas, 
                         contagem_sugestoes, todas_transicoes, tempos_medios_consolidados):
    """
    Gera um relatório HTML detalhado com os resultados da análise.
    
    Args:
        todos_resultados (dict): Resultados combinados da análise
        colaboradores_validos (list): Lista de colaboradores ordenados por qualidade
        contagem_problemas (Counter): Contagem de problemas comuns
        contagem_sugestoes (Counter): Contagem de sugestões comuns
        todas_transicoes (dict): Contagem de transições de estado
        tempos_medios_consolidados (dict): Tempos médios em cada situação
    """
    try:
        # Criar diretório para relatórios se não existir
        os.makedirs('relatorios', exist_ok=True)
        
        # Nome do arquivo HTML
        data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_path = os.path.join('relatorios', f'relatorio_analise_{data_hora}.html')
        
        # Iniciar HTML
        html = f"""
        <!DOCTYPE html>
        <html lang="pt-br">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Relatório de Análise de Colaboradores</title>
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
                .metric-value.good {{
                    color: #28a745;
                }}
                .metric-value.bad {{
                    color: #dc3545;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 30px;
                }}
                th, td {{
                    padding: 10px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }}
                th {{
                    background-color: #f2f2f2;
                    font-weight: bold;
                }}
                tr:hover {{
                    background-color: #f5f5f5;
                }}
                .chart-container {{
                    margin-bottom: 30px;
                }}
                .recommendations {{
                    background-color: #e8f4fd;
                    padding: 20px;
                    border-radius: 5px;
                    margin-bottom: 30px;
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
                <h1>Relatório de Análise de Colaboradores</h1>
                <p>Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}</p>
            </div>
            
            <div class="summary-section">
                <h2>Resumo Geral</h2>
                
                <div class="card-container">
                    <div class="card">
                        <h3>Estatísticas Gerais</h3>
                        <div class="metric">
                            <div class="metric-title">Total de Colaboradores</div>
                            <div class="metric-value">{len(todos_resultados)}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-title">Colaboradores com Problemas</div>
                            <div class="metric-value">{sum(1 for r in todos_resultados.values() if isinstance(r, dict) and r.get('status') == 'SUCESSO' and r.get('problemas'))}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-title">Gráficos Gerados</div>
                            <div class="metric-value">{sum(1 for r in todos_resultados.values() if isinstance(r, dict) and r.get('grafico_path'))}</div>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>Problemas Mais Comuns</h3>
        """
        
        # Adicionar problemas mais comuns
        for problema, contagem in contagem_problemas.most_common(5):
            html += f"""
                        <div class="metric">
                            <div class="metric-title">{problema}</div>
                            <div class="metric-value">{contagem} ocorrências</div>
                        </div>
            """
        
        html += """
                    </div>
                    
                    <div class="card">
                        <h3>Sugestões de Melhoria</h3>
        """
        
        # Adicionar sugestões mais comuns
        for sugestao, contagem in contagem_sugestoes.most_common(5):
            html += f"""
                        <div class="metric">
                            <div class="metric-title">{sugestao}</div>
                            <div class="metric-value">{contagem} ocorrências</div>
                        </div>
            """
        
        html += """
                    </div>
                </div>
            </div>
            
            <h2>Análise por Grupo</h2>
        """
        
        # Separar colaboradores por grupo
        colaboradores_julio = {nome: r for nome, r in todos_resultados.items() 
                              if isinstance(r, dict) and r.get('arquivo', '').find('JULIO') >= 0}
        
        colaboradores_leandro = {nome: r for nome, r in todos_resultados.items() 
                               if isinstance(r, dict) and r.get('arquivo', '').find('LEANDRO') >= 0}
        
        # Adicionar seção para o grupo Julio
        html += """
            <div class="grupo-section">
                <div class="grupo-header">
                    <h2>Grupo JULIO</h2>
                </div>
                
                <h3>Métricas de Qualidade</h3>
                <table>
                    <tr>
                        <th>Colaborador</th>
                        <th>Total Registros</th>
                        <th>Registros Vazios</th>
                        <th>Taxa Preenchimento</th>
                        <th>Taxa Padronização</th>
                        <th>Score Qualidade</th>
                    </tr>
        """
        
        # Adicionar linhas da tabela para cada colaborador do grupo Julio
        for nome, metricas in colaboradores_julio.items():
            if not isinstance(metricas, dict) or metricas.get('status') != 'SUCESSO':
                continue
            
            html += f"""
                    <tr>
                        <td>{nome}</td>
                        <td>{metricas.get('total_registros', 0)}</td>
                        <td>{metricas.get('registros_vazios', 0)}</td>
                        <td>{metricas.get('taxa_preenchimento', 0):.1f}%</td>
                        <td>{metricas.get('taxa_padronizacao', 0):.1f}%</td>
                        <td>{metricas.get('score_qualidade', 0):.1f}</td>
                    </tr>
            """
        
        html += """
                </table>
            </div>
        """
        
        # Adicionar seção para o grupo Leandro
        html += """
            <div class="grupo-section">
                <div class="grupo-header">
                    <h2>Grupo LEANDRO</h2>
                </div>
                
                <h3>Métricas de Qualidade</h3>
                <table>
                    <tr>
                        <th>Colaborador</th>
                        <th>Total Registros</th>
                        <th>Registros Vazios</th>
                        <th>Taxa Preenchimento</th>
                        <th>Taxa Padronização</th>
                        <th>Score Qualidade</th>
                    </tr>
        """
        
        # Adicionar linhas da tabela para cada colaborador do grupo Leandro
        for nome, metricas in colaboradores_leandro.items():
            if not isinstance(metricas, dict) or metricas.get('status') != 'SUCESSO':
                continue
            
            html += f"""
                    <tr>
                        <td>{nome}</td>
                        <td>{metricas.get('total_registros', 0)}</td>
                        <td>{metricas.get('registros_vazios', 0)}</td>
                        <td>{metricas.get('taxa_preenchimento', 0):.1f}%</td>
                        <td>{metricas.get('taxa_padronizacao', 0):.1f}%</td>
                        <td>{metricas.get('score_qualidade', 0):.1f}</td>
                    </tr>
            """
        
        html += """
                </table>
            </div>
        """
        
        # Adicionar seção de melhores desempenhos
        html += """
            <h2>Melhores Desempenhos</h2>
            <div class="card-container">
        """
        
        # Top 5 colaboradores
        html += """
                <div class="card">
                    <h3>Top 5 - Melhor Qualidade</h3>
        """
        
        for i, (nome, score) in enumerate(colaboradores_validos[:5], 1):
            html += f"""
                    <div class="metric">
                        <div class="metric-title">{i}. {nome}</div>
                        <div class="metric-value good">{score:.1f} pontos</div>
                    </div>
            """
        
        html += """
                </div>
        """
        
        # Colaboradores que precisam de atenção
        html += """
                <div class="card">
                    <h3>Precisam de Atenção</h3>
        """
        
        for i, (nome, score) in enumerate(colaboradores_validos[-5:], 1):
            html += f"""
                    <div class="metric">
                        <div class="metric-title">{i}. {nome}</div>
                        <div class="metric-value bad">{score:.1f} pontos</div>
                    </div>
            """
        
        html += """
                </div>
        """
        
        # Tempo médio em cada situação
        html += """
                <div class="card">
                    <h3>Tempo Médio por Situação</h3>
        """
        
        for situacao, tempo in sorted(tempos_medios_consolidados.items(), key=lambda x: x[1]):
            html += f"""
                    <div class="metric">
                        <div class="metric-title">{situacao}</div>
                        <div class="metric-value">{tempo:.1f} dias</div>
                    </div>
            """
        
        html += """
                </div>
            </div>
        """
        
        # Adicionar recomendações gerais
        html += """
            <div class="recommendations">
                <h2>Recomendações Gerais</h2>
                <p>Com base na análise dos dados, recomendamos as seguintes ações:</p>
                <ul>
        """
        
        for sugestao, _ in contagem_sugestoes.most_common(10):
            html += f"""
                    <li>{sugestao}</li>
            """
        
        html += """
                </ul>
            </div>
        """
        
        # Adicionar rodapé
        html += """
            <div class="footer">
                <p>Relatório gerado automaticamente pelo sistema de Análise Paralela de Colaboradores</p>
                <p>© 2023 - Todos os direitos reservados</p>
            </div>
        </body>
        </html>
        """
        
        # Salvar o HTML em um arquivo
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"Relatório HTML gerado com sucesso: {html_path}")
        
    except Exception as e:
        print(f"Erro ao gerar relatório HTML: {str(e)}")
        traceback.print_exc()

def main():
    """Função principal para executar a análise em paralelo"""
    print("Iniciando análise paralela dos arquivos Excel...")
    
    # Definir caminhos dos arquivos
    arquivo_julio = "(JULIO) LISTAS INDIVIDUAIS.xlsx"
    arquivo_leandro = "(LEANDRO_ADRIANO) LISTAS INDIVIDUAIS.xlsx"
    
    print(f"Analisando arquivo: {arquivo_julio}")
    resultados_julio = analisar_arquivo_paralelo({
        'julio': arquivo_julio,
        'leandro': arquivo_leandro
    })
    
    # Gerar relatório de melhorias
    relatorio = gerar_relatorio_melhorias(resultados_julio, resultados_julio)
    
    # Salvar relatório em arquivo
    nome_arquivo = f"relatorio_melhorias_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(nome_arquivo, 'w', encoding='utf-8') as f:
        f.write(relatorio)
    
    print(f"Relatório de melhorias salvo em: {nome_arquivo}")
    print(relatorio)
    
    return {
        'resultados_julio': resultados_julio,
        'relatorio': relatorio
    }

if __name__ == "__main__":
    main()
