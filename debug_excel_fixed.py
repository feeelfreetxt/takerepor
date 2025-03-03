import pandas as pd
import numpy as np
import os
import re
from datetime import datetime, timedelta
import warnings
import traceback
import json

# Suprimir avisos específicos do pandas
warnings.filterwarnings("ignore", category=pd.errors.SettingWithCopyWarning)

class AnalisadorExcel:
    def __init__(self, file_path):
        self.file_path = file_path
        self.colaboradores = {}
        self.erros = []
        print(f"Criando analisador para {file_path}")
        
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
                    return None
            
            # Se for número, assumir que é um número de série do Excel
            if isinstance(valor, (int, float)):
                try:
                    # Converter número de série do Excel para datetime
                    # O Excel conta dias desde 01/01/1900 (com um bug para 1900 não ser bissexto)
                    return pd.to_datetime('1899-12-30') + pd.Timedelta(days=float(valor))
                except:
                    return None
                    
            return None
        except Exception as e:
            return None
    
    def detectar_colunas_necessarias(self, df):
        """Detecta e mapeia colunas necessárias no DataFrame"""
        colunas_mapeadas = {}
        colunas_df = [self.normalizar_coluna(col) for col in df.columns]
        
        # Mapeamento de possíveis nomes para cada tipo de coluna
        mapeamentos = {
            'data': ['DATA', 'DT', 'DATE', 'DATA CRIACAO', 'DATA CRIAÇÃO', 'DATA DE CRIACAO', 'DATA DE CRIAÇÃO'],
            'status': ['STATUS', 'SITUACAO', 'SITUAÇÃO', 'ESTADO'],
            'responsavel': ['RESPONSAVEL', 'RESPONSÁVEL', 'ATRIBUIDO', 'ATRIBUÍDO', 'ATENDENTE'],
            'id': ['ID', 'CODIGO', 'CÓDIGO', 'NUMERO', 'NÚMERO', '#'],
            'descricao': ['DESCRICAO', 'DESCRIÇÃO', 'ASSUNTO', 'TEMA', 'TITULO', 'TÍTULO']
        }
        
        # Tentar encontrar cada tipo de coluna
        for tipo, possiveis_nomes in mapeamentos.items():
            for nome in possiveis_nomes:
                if nome in colunas_df:
                    colunas_mapeadas[tipo] = df.columns[colunas_df.index(nome)]
                    break
        
        # Se não encontrou colunas essenciais, tentar inferir
        if 'data' not in colunas_mapeadas:
            # Tentar encontrar coluna de data por tipo
            for col in df.columns:
                if df[col].dtype == 'datetime64[ns]' or (
                    isinstance(df[col].iloc[0], str) and 
                    any(c in df[col].iloc[0].lower() for c in ['/', '-']) and
                    sum(c.isdigit() for c in df[col].iloc[0]) >= 4
                ):
                    colunas_mapeadas['data'] = col
                    break
        
        if 'status' not in colunas_mapeadas:
            # Tentar encontrar coluna de status por conteúdo
            status_keywords = ['CONCLUIDO', 'PENDENTE', 'EM ANDAMENTO', 'CANCELADO', 'ABERTO', 'FECHADO']
            for col in df.columns:
                valores = df[col].astype(str).str.upper()
                if valores.isin(status_keywords).any():
                    colunas_mapeadas['status'] = col
                    break
        
        return colunas_mapeadas
    
    def calcular_metricas_colaborador(self, df, nome_colaborador):
        """Calcula métricas para um colaborador específico"""
        try:
            # Verificar se há dados suficientes
            if df.empty:
                print(f"Sem dados para {nome_colaborador}")
                return None
            
            # Detectar colunas necessárias
            colunas = self.detectar_colunas_necessarias(df)
            
            # Verificar se encontrou as colunas essenciais
            colunas_faltantes = []
            if 'data' not in colunas:
                colunas_faltantes.append('DATA')
            if 'status' not in colunas:
                colunas_faltantes.append('STATUS')
            
            if colunas_faltantes:
                print(f"Erro ao processar dados de {nome_colaborador}: {set(colunas_faltantes)}")
                return None
            
            # Extrair colunas mapeadas
            coluna_data = colunas.get('data')
            coluna_status = colunas.get('status')
            
            # Converter coluna de data para datetime
            df_processado = df.copy()
            df_processado[coluna_data] = df_processado[coluna_data].apply(self.corrigir_formato_data)
            
            # Remover linhas com data inválida
            df_processado = df_processado.dropna(subset=[coluna_data])
            
            if df_processado.empty:
                print(f"Sem dados válidos para {nome_colaborador} após processamento")
                return None
            
            # Normalizar valores de status
            df_processado[coluna_status] = df_processado[coluna_status].astype(str).str.upper()
            
            # Mapear status para categorias padrão
            mapeamento_status = {
                'CONCLUIDO': 'CONCLUIDO',
                'CONCLUÍDO': 'CONCLUIDO',
                'FINALIZADO': 'CONCLUIDO',
                'FECHADO': 'CONCLUIDO',
                'RESOLVIDO': 'CONCLUIDO',
                'PENDENTE': 'PENDENTE',
                'ABERTO': 'PENDENTE',
                'EM ANDAMENTO': 'EM ANDAMENTO',
                'EM ANÁLISE': 'EM ANDAMENTO',
                'EM ANALISE': 'EM ANDAMENTO',
                'CANCELADO': 'CANCELADO',
                'SUSPENSO': 'CANCELADO'
            }
            
            # Aplicar mapeamento, mantendo valores não mapeados como estão
            df_processado['STATUS_NORMALIZADO'] = df_processado[coluna_status].apply(
                lambda x: next((v for k, v in mapeamento_status.items() if k in x), x)
            )
            
            # Calcular distribuição de status
            distribuicao_status = df_processado['STATUS_NORMALIZADO'].value_counts().to_dict()
            
            # Garantir que todos os status padrão estejam presentes
            for status in ['CONCLUIDO', 'PENDENTE', 'EM ANDAMENTO', 'CANCELADO']:
                if status not in distribuicao_status:
                    distribuicao_status[status] = 0
            
            # Calcular total de registros
            total_registros = len(df_processado)
            
            # Calcular taxa de eficiência (concluídos / total)
            concluidos = distribuicao_status.get('CONCLUIDO', 0)
            taxa_eficiencia = concluidos / total_registros if total_registros > 0 else 0
            
            # Calcular tempo médio de resolução para itens concluídos
            tempo_medio_resolucao = None
            
            if 'responsavel' in colunas and concluidos > 0:
                # Se tiver coluna de responsável, calcular tempo médio
                df_concluidos = df_processado[df_processado['STATUS_NORMALIZADO'] == 'CONCLUIDO']
                
                # Ordenar por data
                df_concluidos = df_concluidos.sort_values(by=coluna_data)
                
                # Calcular diferença entre datas consecutivas (em dias)
                if len(df_concluidos) > 1:
                    datas = df_concluidos[coluna_data].tolist()
                    diferencas = [(datas[i] - datas[i-1]).days for i in range(1, len(datas))]
                    diferencas = [d for d in diferencas if d > 0]  # Remover valores negativos
                    
                    if diferencas:
                        tempo_medio_resolucao = sum(diferencas) / len(diferencas)
            
            # Calcular tendência
            tendencia = {
                'direcao': 'estável',
                'valor': 0
            }
            
            if len(df_processado) > 5:
                # Agrupar por mês e contar
                df_processado['MES'] = df_processado[coluna_data].dt.to_period('M')
                contagem_mensal = df_processado.groupby('MES').size()
                
                if len(contagem_mensal) > 1:
                    # Calcular tendência linear
                    x = np.arange(len(contagem_mensal))
                    y = contagem_mensal.values
                    
                    # Regressão linear simples
                    slope = np.polyfit(x, y, 1)[0]
                    
                    # Determinar direção da tendência
                    if slope > 0.1 * np.mean(y):
                        tendencia['direcao'] = 'crescente'
                    elif slope < -0.1 * np.mean(y):
                        tendencia['direcao'] = 'decrescente'
                    
                    tendencia['valor'] = slope
            
            # Compilar métricas
            metricas = {
                'nome': nome_colaborador,
                'total_registros': total_registros,
                'distribuicao_status': distribuicao_status,
                'taxa_eficiencia': taxa_eficiencia,
                'tempo_medio_resolucao': tempo_medio_resolucao,
                'tendencia': tendencia,
                'ultima_atualizacao': datetime.now().isoformat()
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
        
        print(f"\n=== Métricas para {metricas['nome']} ===")
        print(f"Total de registros: {metricas['total_registros']}")
        print(f"Distribuição de status: {metricas['distribuicao_status']}")
        print(f"Taxa de eficiência: {metricas['taxa_eficiencia']:.2%}")
        
        if metricas['tempo_medio_resolucao']:
            print(f"Tempo médio de resolução: {metricas['tempo_medio_resolucao']:.2f} dias")
        else:
            print("Tempo médio de resolução: N/A")
        
        print(f"Tendência: {metricas['tendencia']['direcao']} ({metricas['tendencia']['valor']:.2f})")
    
    def analisar_arquivo(self):
        """Analisa o arquivo Excel e extrai métricas para cada colaborador"""
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
            
            # Verificar extensão do arquivo
            if not self.file_path.lower().endswith(('.xlsx', '.xls')):
                print(f"Formato de arquivo não suportado: {self.file_path}")
                self.erros.append({
                    'arquivo': os.path.basename(self.file_path),
                    'erro': 'Formato de arquivo não suportado'
                })
                return []
            
            # Ler todas as abas do arquivo Excel
            try:
                # Primeiro tentar com openpyxl (para .xlsx)
                excel_file = pd.ExcelFile(self.file_path, engine='openpyxl')
            except:
                try:
                    # Se falhar, tentar com xlrd (para .xls)
                    excel_file = pd.ExcelFile(self.file_path, engine='xlrd')
                except Exception as e:
                    print(f"Erro ao abrir arquivo Excel: {str(e)}")
                    self.erros.append({
                        'arquivo': os.path.basename(self.file_path),
                        'erro': f'Erro ao abrir arquivo: {str(e)}'
                    })
                    return []
            
            # Processar cada aba como um colaborador separado
            nomes_colaboradores = []
            
            for sheet_name in excel_file.sheet_names:
                try:
                    print(f"Analisando dados de: {sheet_name}")
                    
                    # Ler dados da aba
                    try:
                        df = excel_file.parse(sheet_name)
                    except Exception as e:
                        print(f"Erro ao ler aba {sheet_name}: {str(e)}")
                        continue
                    
                    # Verificar se há dados
                    if df.empty:
                        print(f"Aba {sheet_name} está vazia.")
                        continue
                        
                    # Normalizar nomes das colunas
                    df.columns = [col if isinstance(col, str) else str(col) for col in df.columns]
                    
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
            if len(self.colaboradores) < 1:
                print(f"Análise concluída: {len(self.colaboradores)} colaboradores encontrados")
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
            
            print(f"Análise concluída: {len(self.colaboradores)} colaboradores encontrados")
            
        except Exception as e:
            print(f"Erro ao calcular métricas comparativas: {str(e)}")
            traceback.print_exc()
    
    def obter_resultados(self):
        """Retorna os resultados da análise em formato JSON"""
        if not self.colaboradores:
            print("Aviso: Nenhum colaborador encontrado no arquivo")
            
            # Criar um colaborador padrão com dados mínimos
            self.colaboradores["RELATÓRIO GERAL"] = {
                'nome': "RELATÓRIO GERAL",
                'total_registros': 0,
                'distribuicao_status': {
                    'CONCLUIDO': 0,
                    'PENDENTE': 0,
                    'EM ANDAMENTO': 0,
                    'CANCELADO': 0
                },
                'taxa_eficiencia': 0,
                'tempo_medio_resolucao': 0,
                'tendencia': {
                    'direcao': 'estável',
                    'valor': 0
                },
                'ultima_atualizacao': datetime.now().isoformat()
            }
        
        resultados = {
            'colaboradores': self.colaboradores,
            'metricas_comparativas': getattr(self, 'metricas_comparativas', {}),
            'erros': self.erros
        }
        
        return resultados 