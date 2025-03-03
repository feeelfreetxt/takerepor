import pandas as pd
from datetime import datetime
import os

STATUS_COLUMNS = [
    'VERIFICADO', 'ANÁLISE', 'PENDENTE', 'PRIORIDADE', 
    'PRIORIDADE TOTAL', 'APROVADO', 'QUITADO', 'APREENDIDO', 
    'CANCELADO'
]

class ProcessadorRelatorios:
    def __init__(self, file_path):
        self.file_path = file_path
        self.xls = pd.ExcelFile(file_path)
        self.dados_colaboradores = {}
        self.relatorio_geral = None
        self.data_atual = datetime.now().date()
        self.ordem_colaboradores = [
            "AMANDA SANTANA"  # Primeiro nome conforme solicitado
        ]
        
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
    
    def encontrar_coluna(self, df, possiveis_nomes):
        """Encontra uma coluna baseada em possíveis nomes"""
        for nome in possiveis_nomes:
            if nome in df.columns:
                return nome
        return None
    
    def carregar_dados(self):
        """Carrega e processa dados de todas as abas"""
        print("Carregando dados do arquivo...")
        
        # Primeiro, vamos coletar todos os nomes dos colaboradores das abas
        for sheet_name in self.xls.sheet_names:
            if sheet_name != "RELATÓRIO GERAL" and sheet_name not in ["", "TESTE"]:
                if sheet_name not in self.ordem_colaboradores:
                    self.ordem_colaboradores.append(sheet_name)
        
        # Agora carregamos os dados de cada aba
        for sheet_name in self.xls.sheet_names:
            if sheet_name == "RELATÓRIO GERAL":
                self.relatorio_geral = pd.read_excel(self.xls, sheet_name=sheet_name)
            elif sheet_name != "":
                try:
                    df = pd.read_excel(self.xls, sheet_name=sheet_name)
                    
                    # Normalizar nomes das colunas
                    df.columns = [self.normalizar_coluna(col) for col in df.columns]
                    
                    # Encontrar colunas importantes
                    data_col = self.encontrar_coluna(df, ['DATA', 'DT VENCIMENTO', 'DATA VENCIMENTO'])
                    situacao_col = self.encontrar_coluna(df, ['SITUACAO', 'SITUAÇÃO', 'STATUS'])
                    resolucao_col = self.encontrar_coluna(df, ['RESOLUCAO', 'RESOLUÇÃO', 'DATA RESOLUCAO'])
                    
                    # Converter datas
                    if data_col:
                        df[data_col] = pd.to_datetime(df[data_col], errors='coerce')
                    if resolucao_col:
                        df[resolucao_col] = pd.to_datetime(df[resolucao_col], errors='coerce')
                    
                    # Converter situação
                    if situacao_col:
                        df[situacao_col] = df[situacao_col].fillna('').str.strip().str.upper()
                    
                    self.dados_colaboradores[sheet_name] = {
                        'df': df,
                        'colunas': {
                            'data': data_col,
                            'situacao': situacao_col,
                            'resolucao': resolucao_col
                        }
                    }
                except Exception as e:
                    print(f"Erro ao processar aba {sheet_name}: {str(e)}")
    
    def gerar_relatorio_colaborador(self, colaborador, dados, tipo="GERAL"):
        """Gera relatório para um colaborador específico"""
        relatorio = {status: 0 for status in STATUS_COLUMNS}
        df = dados['df']
        colunas = dados['colunas']
        
        if tipo == "DIARIO" and colunas['data']:
            # Filtrar apenas registros do dia atual
            df_filtrado = df[df[colunas['data']].dt.date == self.data_atual]
        else:
            df_filtrado = df
        
        # Contar ocorrências de cada status
        if colunas['situacao']:
            contagem = df_filtrado[colunas['situacao']].value_counts()
            for status in STATUS_COLUMNS:
                relatorio[status] = int(contagem.get(status, 0))
        
        # Calcular total
        relatorio['TOTAL'] = sum(relatorio.values())
        
        return relatorio
    
    def gerar_relatorios_completos(self):
        """Gera relatórios diários e gerais para todos os colaboradores"""
        if not self.dados_colaboradores:
            self.carregar_dados()
        
        relatorios = {
            'DIARIO': {},
            'GERAL': {}
        }
        
        for colaborador in self.ordem_colaboradores:
            if colaborador in self.dados_colaboradores:
                dados = self.dados_colaboradores[colaborador]
                relatorios['DIARIO'][colaborador] = self.gerar_relatorio_colaborador(colaborador, dados, "DIARIO")
                relatorios['GERAL'][colaborador] = self.gerar_relatorio_colaborador(colaborador, dados, "GERAL")
        
        return relatorios
    
    def exibir_relatorios(self, relatorios):
        """Exibe os relatórios no formato especificado"""
        for colaborador in self.ordem_colaboradores:
            if colaborador in relatorios['DIARIO']:
                print(f"\n=== {colaborador} ===")
                
                print("\nRELATÓRIO DIÁRIO")
                for status in STATUS_COLUMNS + ['TOTAL']:
                    print(f"{status}\t{relatorios['DIARIO'][colaborador][status]}")
                
                print("\nRELATÓRIO GERAL")
                for status in STATUS_COLUMNS + ['TOTAL']:
                    print(f"{status}\t{relatorios['GERAL'][colaborador][status]}")
                
                # Adicionar informações de resolução se disponível
                dados = self.dados_colaboradores[colaborador]
                if dados['colunas']['resolucao']:
                    resolucoes = dados['df'][dados['colunas']['resolucao']].dropna()
                    if not resolucoes.empty:
                        print("\nINFORMAÇÕES DE RESOLUÇÃO:")
                        for data in resolucoes.dt.date.unique():
                            count = (resolucoes.dt.date == data).sum()
                            print(f"Data: {data.strftime('%d/%m/%Y')} - Resoluções: {count}")

# Uso do processador
if __name__ == "__main__":
    try:
        file_path = "(JULIO) LISTAS INDIVIDUAIS.xlsx"
        processador = ProcessadorRelatorios(file_path)
        relatorios = processador.gerar_relatorios_completos()
        processador.exibir_relatorios(relatorios)
    except Exception as e:
        print(f"Erro ao processar arquivo: {str(e)}")
        import traceback
        print(traceback.format_exc())