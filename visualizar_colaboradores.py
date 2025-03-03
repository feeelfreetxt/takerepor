#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Visualização de Dados dos Colaboradores
======================================
Este script exibe os dados de cada colaborador a partir dos arquivos Excel,
mostrando estatísticas detalhadas e métricas de desempenho.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict, Counter

# Importações locais
from debug_excel import AnalisadorExcel
from analise_360 import Analise360
from data_analysis_pipeline import DataAnalysisPipeline

def carregar_dados_colaborador(nome_arquivo, nome_aba):
    """
    Carrega os dados de um colaborador específico.
    
    Args:
        nome_arquivo (str): Caminho para o arquivo Excel
        nome_aba (str): Nome da aba/colaborador a ser analisada
        
    Returns:
        pandas.DataFrame: DataFrame com os dados do colaborador
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
        
        return df
    except Exception as e:
        print(f"Erro ao carregar dados do colaborador {nome_aba}: {str(e)}")
        return None

def analisar_colaborador(df, nome_aba):
    """
    Analisa os dados de um colaborador e exibe estatísticas.
    
    Args:
        df (pandas.DataFrame): DataFrame com os dados do colaborador
        nome_aba (str): Nome do colaborador
    """
    if df is None or len(df) == 0:
        print(f"Não há dados para o colaborador {nome_aba}")
        return
    
    print(f"\n{'='*80}")
    print(f"ANÁLISE DETALHADA: {nome_aba}")
    print(f"{'='*80}")
    
    # Estatísticas básicas
    total_registros = len(df)
    print(f"Total de registros: {total_registros}")
    
    # Análise da coluna SITUACAO
    if 'SITUACAO' in df.columns:
        situacao_counts = df['SITUACAO'].value_counts()
        print("\nDistribuição de SITUACAO:")
        for situacao, count in situacao_counts.items():
            print(f"  {situacao}: {count} ({count/total_registros*100:.1f}%)")
        
        # Valores vazios
        registros_vazios = df['SITUACAO'].isna().sum()
        if registros_vazios > 0:
            print(f"\nRegistros com SITUACAO vazia: {registros_vazios} ({registros_vazios/total_registros*100:.1f}%)")
        
        # Valores padronizados
        valores_padronizados = ['PENDENTE', 'VERIFICADO', 'APROVADO', 'QUITADO', 'CANCELADO', 'EM ANÁLISE']
        valores_unicos = df['SITUACAO'].dropna().unique()
        valores_nao_padronizados = [v for v in valores_unicos if v not in valores_padronizados]
        
        if valores_nao_padronizados:
            print(f"\nValores não padronizados: {', '.join(valores_nao_padronizados)}")
    
    # Análise temporal
    colunas_data = [col for col in df.columns if 'DATA' in col]
    if colunas_data:
        print("\nAnálise Temporal:")
        for col_data in colunas_data:
            try:
                df[col_data] = pd.to_datetime(df[col_data], errors='coerce')
                datas_validas = df[col_data].dropna()
                
                if len(datas_validas) > 0:
                    print(f"  Coluna: {col_data}")
                    print(f"  Período: {datas_validas.min().date()} a {datas_validas.max().date()}")
                    print(f"  Registros com data: {len(datas_validas)} ({len(datas_validas)/total_registros*100:.1f}%)")
                    
                    # Análise de transições se houver SITUACAO
                    if 'SITUACAO' in df.columns:
                        df_ordenado = df.sort_values(by=col_data)
                        
                        # Verificar transições de estado
                        transicoes = []
                        situacao_anterior = None
                        
                        for idx, row in df_ordenado.iterrows():
                            situacao_atual = row['SITUACAO']
                            if pd.notna(situacao_anterior) and pd.notna(situacao_atual) and situacao_anterior != situacao_atual:
                                transicoes.append((situacao_anterior, situacao_atual))
                            situacao_anterior = situacao_atual
                        
                        # Contar transições
                        contagem_transicoes = Counter(transicoes)
                        
                        if contagem_transicoes:
                            print("\n  Transições de Estado mais comuns:")
                            for (de, para), contagem in sorted(contagem_transicoes.items(), key=lambda x: x[1], reverse=True)[:5]:
                                print(f"    {de} -> {para}: {contagem} ocorrências")
                        
                        # Tempo médio em cada situação
                        df_ordenado['data_anterior'] = df_ordenado[col_data].shift(1)
                        df_ordenado['tempo_no_estado'] = (df_ordenado[col_data] - df_ordenado['data_anterior']).dt.days
                        
                        # Calcular tempo médio por situação
                        tempos_por_situacao = df_ordenado.groupby('SITUACAO')['tempo_no_estado'].mean()
                        
                        if not tempos_por_situacao.empty:
                            print("\n  Tempo Médio em cada Situação (dias):")
                            for situacao, tempo in sorted(tempos_por_situacao.items(), key=lambda x: x[1], reverse=True):
                                print(f"    {situacao}: {tempo:.1f} dias")
            except Exception as e:
                print(f"  Erro ao analisar coluna {col_data}: {str(e)}")
    
    # Gerar visualização
    try:
        if 'SITUACAO' in df.columns:
            plt.figure(figsize=(10, 6))
            situacao_counts = df['SITUACAO'].value_counts()
            sns.barplot(x=situacao_counts.index, y=situacao_counts.values)
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
            
            print(f"\nGráfico salvo em: {grafico_path}")
    except Exception as e:
        print(f"Erro ao gerar gráfico: {str(e)}")

def listar_colaboradores(nome_arquivo):
    """
    Lista todos os colaboradores em um arquivo Excel.
    
    Args:
        nome_arquivo (str): Caminho para o arquivo Excel
        
    Returns:
        list: Lista com os nomes das abas/colaboradores
    """
    try:
        xls = pd.ExcelFile(nome_arquivo)
        abas_validas = [aba for aba in xls.sheet_names if aba not in ["", "TESTE", "RELATÓRIO GERAL"]]
        return abas_validas
    except Exception as e:
        print(f"Erro ao listar colaboradores do arquivo {nome_arquivo}: {str(e)}")
        return []

def main():
    """Função principal para visualizar dados dos colaboradores"""
    print("Iniciando visualização de dados dos colaboradores...")
    
    # Definir caminhos dos arquivos
    arquivo_julio = "(JULIO) LISTAS INDIVIDUAIS.xlsx"
    arquivo_leandro = "(LEANDRO_ADRIANO) LISTAS INDIVIDUAIS.xlsx"
    
    # Listar colaboradores
    print(f"\nColaboradores do arquivo {arquivo_julio}:")
    colaboradores_julio = listar_colaboradores(arquivo_julio)
    for i, colab in enumerate(colaboradores_julio):
        print(f"{i+1}. {colab}")
    
    print(f"\nColaboradores do arquivo {arquivo_leandro}:")
    colaboradores_leandro = listar_colaboradores(arquivo_leandro)
    for i, colab in enumerate(colaboradores_leandro):
        print(f"{i+1}. {colab}")
    
    while True:
        print("\nOpções:")
        print("1. Analisar colaborador específico")
        print("2. Analisar todos os colaboradores")
        print("3. Sair")
        
        opcao = input("\nEscolha uma opção: ")
        
        if opcao == "1":
            arquivo = input("Qual arquivo? (1 para JULIO, 2 para LEANDRO): ")
            
            if arquivo == "1":
                arquivo_selecionado = arquivo_julio
                colaboradores = colaboradores_julio
            elif arquivo == "2":
                arquivo_selecionado = arquivo_leandro
                colaboradores = colaboradores_leandro
            else:
                print("Opção inválida!")
                continue
            
            print("\nColaboradores disponíveis:")
            for i, colab in enumerate(colaboradores):
                print(f"{i+1}. {colab}")
            
            try:
                indice = int(input("\nEscolha o número do colaborador: ")) - 1
                if 0 <= indice < len(colaboradores):
                    nome_aba = colaboradores[indice]
                    df = carregar_dados_colaborador(arquivo_selecionado, nome_aba)
                    analisar_colaborador(df, nome_aba)
                else:
                    print("Índice inválido!")
            except ValueError:
                print("Por favor, digite um número válido!")
        
        elif opcao == "2":
            arquivo = input("Qual arquivo? (1 para JULIO, 2 para LEANDRO, 3 para ambos): ")
            
            if arquivo == "1":
                arquivos_selecionados = [(arquivo_julio, colaboradores_julio)]
            elif arquivo == "2":
                arquivos_selecionados = [(arquivo_leandro, colaboradores_leandro)]
            elif arquivo == "3":
                arquivos_selecionados = [(arquivo_julio, colaboradores_julio), (arquivo_leandro, colaboradores_leandro)]
            else:
                print("Opção inválida!")
                continue
            
            for arquivo_selecionado, colaboradores in arquivos_selecionados:
                print(f"\nAnalisando arquivo: {arquivo_selecionado}")
                for nome_aba in colaboradores:
                    df = carregar_dados_colaborador(arquivo_selecionado, nome_aba)
                    analisar_colaborador(df, nome_aba)
        
        elif opcao == "3":
            print("Saindo...")
            break
        
        else:
            print("Opção inválida!")

if __name__ == "__main__":
    main()
