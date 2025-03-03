import pandas as pd
import os

def analisar_detalhes_colaborador(df, colaborador):
    """
    Analisa detalhadamente as colunas do Excel para um colaborador específico.
    
    Args:
        df (DataFrame): DataFrame com os dados do colaborador
        colaborador (str): Nome do colaborador
    """
    print(f"\n{'='*80}")
    print(f"Análise Detalhada: {colaborador}")
    print(f"{'='*80}")

    # 1. Análise de Preenchimento
    print("\n1. ANÁLISE DE PREENCHIMENTO:")
    print(f"Total de registros: {len(df)}")
    for coluna in df.columns:
        vazios = df[coluna].isna().sum()
        taxa_preenchimento = ((len(df) - vazios) / len(df)) * 100
        print(f"Coluna {coluna:20}: {taxa_preenchimento:6.2f}% preenchido ({vazios} vazios)")

    # 2. Análise de Status/Situação
    print("\n2. ANÁLISE DE STATUS/SITUAÇÃO:")
    # Verificar se existe a coluna SITUAÇÃO ou SITUACAO
    situacao_col = None
    if 'SITUAÇÃO' in df.columns:
        situacao_col = 'SITUAÇÃO'
    elif 'SITUACAO' in df.columns:
        situacao_col = 'SITUACAO'
    
    if situacao_col:
        status_counts = df[situacao_col].value_counts()
        print("\nDistribuição de Status:")
        for status, count in status_counts.items():
            print(f"{status:20}: {count:4d} registros ({count/len(df)*100:6.2f}%)")

    # 3. Análise Temporal
    print("\n3. ANÁLISE TEMPORAL:")
    if 'DATA' in df.columns:
        df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce')
        print("\nDistribuição por Mês:")
        monthly = df.groupby(df['DATA'].dt.to_period('M')).size()
        for month, count in monthly.items():
            print(f"{month}: {count} registros")

    # 4. Análise de Tempo de Resolução
    print("\n4. ANÁLISE DE TEMPO DE RESOLUÇÃO:")
    resolucao_col = 'RESOLUCAO' if 'RESOLUCAO' in df.columns else 'RESOLUÇÃO'
    if 'DATA' in df.columns and resolucao_col in df.columns:
        df[resolucao_col] = pd.to_datetime(df[resolucao_col], errors='coerce')
        df['tempo_resolucao'] = (df[resolucao_col] - df['DATA']).dt.days
        
        print(f"\nTempo médio de resolução: {df['tempo_resolucao'].mean():.1f} dias")
        print(f"Tempo mínimo: {df['tempo_resolucao'].min()} dias")
        print(f"Tempo máximo: {df['tempo_resolucao'].max()} dias")

    # 5. Métricas de Qualidade
    print("\n5. MÉTRICAS DE QUALIDADE:")
    
    if situacao_col:
        # Taxa de preenchimento
        taxa_preenchimento = df[situacao_col].notna().mean() * 100
        print(f"Taxa de preenchimento: {taxa_preenchimento:.1f}%")
        
        # Taxa de padronização
        valores_padronizados = ['PENDENTE', 'VERIFICADO', 'APROVADO', 'QUITADO', 'CANCELADO', 'EM ANÁLISE', 'CONCLUIDO']
        valores_unicos = df[situacao_col].dropna().unique()
        valores_nao_padronizados = [v for v in valores_unicos if v not in valores_padronizados]
        taxa_padronizacao = ((len(valores_unicos) - len(valores_nao_padronizados)) / len(valores_unicos)) * 100 if len(valores_unicos) > 0 else 0
        print(f"Taxa de padronização: {taxa_padronizacao:.1f}%")
        
        if valores_nao_padronizados:
            print("\nValores não padronizados encontrados:")
            for valor in valores_nao_padronizados:
                count = df[situacao_col].value_counts()[valor]
                print(f"- {valor}: {count} ocorrências")

        # 6. Score Final
        print("\n6. SCORE FINAL:")
        consistencia_diaria = calcular_consistencia_diaria(df, situacao_col)
        score_final = (
            0.4 * taxa_preenchimento/100 +  # 40% preenchimento
            0.3 * taxa_padronizacao/100 +   # 30% padronização
            0.3 * consistencia_diaria       # 30% consistência
        ) * 100
        
        print(f"Score Final: {score_final:.1f} pontos")
        print(f"- Componente Preenchimento: {taxa_preenchimento * 0.4:.1f} pontos")
        print(f"- Componente Padronização: {taxa_padronizacao * 0.3:.1f} pontos")
        print(f"- Componente Consistência: {consistencia_diaria * 30:.1f} pontos")

def calcular_consistencia_diaria(df, situacao_col):
    """Calcula a consistência diária das atualizações"""
    if 'DATA' not in df.columns:
        return 0
    
    try:
        atualizacoes = df.groupby(df['DATA'].dt.date)[situacao_col].count()
        if len(atualizacoes) > 1:
            std_atualizacoes = atualizacoes.std()
            media_atualizacoes = atualizacoes.mean()
            return 1 - min(1, std_atualizacoes / media_atualizacoes)
    except:
        pass
    return 0

# Executar análise
if __name__ == "__main__":
    arquivo_julio = os.path.join("F:\\", "okok", "(JULIO) LISTAS INDIVIDUAIS.xlsx")
    arquivo_leandro = os.path.join("F:\\", "okok", "(LEANDRO_ADRIANO) LISTAS INDIVIDUAIS.xlsx")
    
    # Lista de colaboradores para análise
    colaboradores = [
        "VITORIA", "VICTOR ADRIANO", "ELISANGELA", "IGOR", "BRUNO",
        "NUNO", "AMANDA SANTANA", "JULIA", "KATIA", "ALINE SALVADOR"
    ]
    
    # Analisar cada arquivo
    for arquivo in [arquivo_julio, arquivo_leandro]:
        print(f"\nAnalisando arquivo: {os.path.basename(arquivo)}")
        xls = pd.ExcelFile(arquivo)
        
        for colaborador in colaboradores:
            if colaborador in xls.sheet_names:
                df = pd.read_excel(arquivo, sheet_name=colaborador)
                analisar_detalhes_colaborador(df, colaborador)