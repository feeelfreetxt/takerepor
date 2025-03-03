import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os

class AnalisadorExcel:
    def __init__(self, file_path):
        self.file_path = file_path
        self.xls = pd.ExcelFile(file_path)
        self.colaboradores = {}
        self.metricas_gerais = {}
        
    def normalizar_coluna(self, coluna):
        """Normaliza o nome da coluna para um formato consistente"""
        mapeamento = {
            'SITUAÇÂO': 'SITUACAO',
            'SITUAÇÃO': 'SITUACAO',
            'RESOLUCAO': 'RESOLUCAO',
            'RESOLUÇÃO': 'RESOLUCAO',
            'ANÁLISE': 'ANALISE',
            'DATA VENCIMENTO': 'DATA',
            'DT VENCIMENTO': 'DATA'
        }
        coluna = str(coluna).strip().upper()
        return mapeamento.get(coluna, coluna)
    
    def normalizar_data(self, data_str):
        """Normaliza diferentes formatos de data"""
        try:
            # Tenta diferentes formatos de data
            formatos = [
                '%d/%m/%Y',
                '%d%m/%Y',
                '%d/%m%Y',
                '%d%m%Y'
            ]
            
            for formato in formatos:
                try:
                    return pd.to_datetime(data_str, format=formato)
                except:
                    continue
                
            # Se nenhum formato funcionar, tenta o parse automático
            return pd.to_datetime(data_str)
        except:
            return None
    
    def calcular_metricas_colaborador(self, df, nome):
        """Calcula métricas avançadas para um colaborador"""
        try:
            # Normalização das datas
            if 'DATA' in df.columns:
                df['DATA'] = df['DATA'].apply(self.normalizar_data)
            if 'RESOLUCAO' in df.columns:
                df['RESOLUCAO'] = df['RESOLUCAO'].apply(self.normalizar_data)
            
            # Remove linhas com datas inválidas
            df = df.dropna(subset=['DATA'])
            
            metricas = {
                'nome': nome,
                'total_registros': len(df),
                'distribuicao_status': {},
                'tempo_medio_resolucao': None,
                'taxa_resolucao': 0,
                'eficiencia': {},
                'tendencias': {},
                'correlacoes': {},
                'outliers': {},
                'sazonalidade': {}
            }
            
            # 1. Distribuição de Status
            if 'SITUACAO' in df.columns:
                status_counts = df['SITUACAO'].value_counts()
                metricas['distribuicao_status'] = status_counts.to_dict()
                
                # Calcular percentuais
                metricas['percentuais'] = (status_counts / len(df) * 100).to_dict()
            
            # 2. Análise Temporal
            if 'DATA' in df.columns and 'RESOLUCAO' in df.columns:
                df['DATA'] = pd.to_datetime(df['DATA'])
                df['RESOLUCAO'] = pd.to_datetime(df['RESOLUCAO'])
                
                # Tempo médio de resolução
                tempo_resolucao = (df['RESOLUCAO'] - df['DATA']).dropna()
                if not tempo_resolucao.empty:
                    metricas['tempo_medio_resolucao'] = tempo_resolucao.mean().days
                    metricas['tempo_mediano_resolucao'] = tempo_resolucao.median().days
                    
                    # Identificar outliers no tempo de resolução
                    Q1 = tempo_resolucao.quantile(0.25)
                    Q3 = tempo_resolucao.quantile(0.75)
                    IQR = Q3 - Q1
                    outliers = tempo_resolucao[(tempo_resolucao < (Q1 - 1.5 * IQR)) | (tempo_resolucao > (Q3 + 1.5 * IQR))]
                    metricas['outliers']['tempo_resolucao'] = len(outliers)
            
            # 3. Eficiência
            if 'SITUACAO' in df.columns:
                status_positivos = ['VERIFICADO', 'APROVADO', 'QUITADO']
                total_positivos = df['SITUACAO'].isin(status_positivos).sum()
                metricas['taxa_eficiencia'] = total_positivos / len(df) if len(df) > 0 else 0
                
                # Análise diária
                if 'DATA' in df.columns:
                    df_diario = df.groupby(df['DATA'].dt.date)['SITUACAO'].value_counts().unstack(fill_value=0)
                    metricas['media_diaria'] = df_diario.mean().to_dict()
                    metricas['max_diario'] = df_diario.max().to_dict()
            
            # 4. Análise de Tendências
            if 'DATA' in df.columns and 'SITUACAO' in df.columns:
                # Tendência temporal de status
                df_trend = df.groupby(df['DATA'].dt.date)['SITUACAO'].count()
                if len(df_trend) > 1:
                    slope, intercept, r_value, p_value, std_err = stats.linregress(range(len(df_trend)), df_trend.values)
                    metricas['tendencias']['slope'] = slope
                    metricas['tendencias']['r_squared'] = r_value ** 2
            
            # 5. Análise de Prioridades
            prioridade_cols = [col for col in df.columns if 'PRIORIDADE' in col]
            if prioridade_cols:
                for col in prioridade_cols:
                    metricas['prioridades'] = df[col].value_counts().to_dict()
            
            # 6. Padrões de Trabalho
            if 'DATA' in df.columns:
                df['dia_semana'] = df['DATA'].dt.day_name()
                metricas['padrao_semanal'] = df.groupby('dia_semana')['SITUACAO'].count().to_dict()
            
            return metricas
        except Exception as e:
            print(f"Erro ao processar dados de {nome}: {str(e)}")
            return None
    
    def analisar_arquivo(self):
        """Analisa o arquivo Excel completo"""
        print("Iniciando análise detalhada do arquivo...")
        
        # Lista para armazenar nomes dos colaboradores
        nomes_colaboradores = []
        
        for sheet_name in self.xls.sheet_names:
            if sheet_name != "RELATÓRIO GERAL" and sheet_name not in ["", "TESTE"]:
                try:
                    print(f"\nAnalisando dados de: {sheet_name}")
                    df = pd.read_excel(self.xls, sheet_name=sheet_name)
                    
                    # Normalizar nomes das colunas
                    df.columns = [self.normalizar_coluna(col) for col in df.columns]
                    
                    # Calcular métricas para o colaborador
                    metricas = self.calcular_metricas_colaborador(df, sheet_name)
                    self.colaboradores[sheet_name] = metricas
                    nomes_colaboradores.append(sheet_name)
                    
                    # Exibir resumo das métricas
                    self.exibir_metricas_colaborador(metricas)
                    
                except Exception as e:
                    print(f"Erro ao processar aba {sheet_name}: {str(e)}")
        
        # Calcular métricas comparativas
        self.calcular_metricas_comparativas()
        
        return nomes_colaboradores
    
    def exibir_metricas_colaborador(self, metricas):
        """Exibe as métricas calculadas para um colaborador"""
        print(f"\n=== Análise Detalhada: {metricas['nome']} ===")
        
        print("\n1. Volumes e Distribuição")
        print(f"Total de Registros: {metricas['total_registros']}")
        
        if metricas['distribuicao_status']:
            print("\nDistribuição de Status:")
            for status, count in metricas['distribuicao_status'].items():
                percentual = metricas['percentuais'][status]
                print(f"  {status}: {count} ({percentual:.1f}%)")
        
        if metricas.get('tempo_medio_resolucao'):
            print("\n2. Tempos de Resolução")
            print(f"Tempo Médio: {metricas['tempo_medio_resolucao']:.1f} dias")
            print(f"Tempo Mediano: {metricas['tempo_mediano_resolucao']:.1f} dias")
            print(f"Outliers: {metricas['outliers'].get('tempo_resolucao', 0)} casos")
        
        if 'taxa_eficiencia' in metricas:
            print("\n3. Indicadores de Eficiência")
            print(f"Taxa de Eficiência: {metricas['taxa_eficiencia']*100:.1f}%")
            
            if 'media_diaria' in metricas:
                print("\nMédias Diárias:")
                for status, media in metricas['media_diaria'].items():
                    print(f"  {status}: {media:.1f}")
        
        if 'tendencias' in metricas and metricas['tendencias']:
            print("\n4. Análise de Tendências")
            slope = metricas['tendencias'].get('slope', 0)
            r_squared = metricas['tendencias'].get('r_squared', 0)
            tendencia = "crescente" if slope > 0 else "decrescente"
            print(f"Tendência: {tendencia} (R² = {r_squared:.2f})")
        
        if 'padrao_semanal' in metricas:
            print("\n5. Padrão Semanal")
            for dia, contagem in metricas['padrao_semanal'].items():
                print(f"  {dia}: {contagem}")
    
    def calcular_metricas_comparativas(self):
        """Calcula métricas comparativas entre colaboradores"""
        print("\n=== Análise Comparativa entre Colaboradores ===")
        
        # Comparar eficiência
        eficiencias = {nome: metricas['taxa_eficiencia'] 
                      for nome, metricas in self.colaboradores.items() 
                      if 'taxa_eficiencia' in metricas}
        
        if eficiencias:
            print("\nRanking de Eficiência:")
            for nome, taxa in sorted(eficiencias.items(), key=lambda x: x[1], reverse=True):
                print(f"{nome}: {taxa*100:.1f}%")
        
        # Comparar volumes
        volumes = {nome: metricas['total_registros'] 
                  for nome, metricas in self.colaboradores.items()}
        
        if volumes:
            print("\nDistribuição de Volume de Trabalho:")
            for nome, volume in sorted(volumes.items(), key=lambda x: x[1], reverse=True):
                print(f"{nome}: {volume} registros")
        
        # Identificar melhores práticas
        if eficiencias and volumes:
            print("\nDestaques de Produtividade:")
            for nome in eficiencias.keys():
                if (eficiencias[nome] > np.mean(list(eficiencias.values())) and 
                    volumes[nome] > np.mean(list(volumes.values()))):
                    print(f"* {nome} - Alta eficiência e alto volume")

# Uso do analisador
if __name__ == "__main__":
    try:
        # Caminho completo para os arquivos
        file_path_julio = "F:\\okok\\data\\(JULIO) LISTAS INDIVIDUAIS.xlsx"
        file_path_leandro = "F:\\okok\\data\\(LEANDRO_ADRIANO) LISTAS INDIVIDUAIS.xlsx"
        
        # Verificar se os arquivos existem
        if not os.path.exists(file_path_julio):
            print(f"ERRO: Arquivo não encontrado: {file_path_julio}")
        else:
            print(f"Analisando arquivo: {file_path_julio}")
            analisador = AnalisadorExcel(file_path_julio)
            nomes_colaboradores = analisador.analisar_arquivo()
            print("\nLista de Colaboradores (JULIO):")
            for nome in nomes_colaboradores:
                print(f"- {nome}")
        
        if not os.path.exists(file_path_leandro):
            print(f"ERRO: Arquivo não encontrado: {file_path_leandro}")
        else:
            print(f"Analisando arquivo: {file_path_leandro}")
            analisador = AnalisadorExcel(file_path_leandro)
            nomes_colaboradores = analisador.analisar_arquivo()
            print("\nLista de Colaboradores (LEANDRO_ADRIANO):")
            for nome in nomes_colaboradores:
                print(f"- {nome}")
                
    except Exception as e:
        print(f"Erro ao executar análise: {str(e)}")
        import traceback
        print(traceback.format_exc())