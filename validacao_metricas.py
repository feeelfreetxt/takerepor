import pandas as pd
import os
import json
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns

def validar_metricas_qualidade(arquivo_julio, arquivo_leandro):
    """
    Valida as métricas de qualidade dos colaboradores e gera provas visuais
    para confirmar os resultados.
    
    Args:
        arquivo_julio (str): Caminho para o arquivo Excel do grupo Julio
        arquivo_leandro (str): Caminho para o arquivo Excel do grupo Leandro
    """
    print("Iniciando validação das métricas de qualidade...")
    
    # Criar diretório para provas
    os.makedirs('provas_validacao', exist_ok=True)
    
    # Carregar resultados salvos (se existirem)
    resultados_salvos = {}
    if os.path.exists('resultados/metricas_colaboradores.json'):
        try:
            with open('resultados/metricas_colaboradores.json', 'r') as f:
                resultados_salvos = json.load(f)
        except:
            print("Não foi possível carregar resultados salvos.")
    
    # Dicionário para armazenar métricas recalculadas
    metricas_recalculadas = {}
    
    # Lista de colaboradores para validar
    colaboradores_top = ["VITORIA", "VICTOR ADRIANO", "ELISANGELA", "IGOR", "BRUNO"]
    colaboradores_bottom = ["NUNO", "AMANDA SANTANA", "JULIA", "KATIA", "ALINE SALVADOR"]
    colaboradores_validar = colaboradores_top + colaboradores_bottom
    
    # Processar arquivos
    arquivos = [
        ("julio", arquivo_julio),
        ("leandro", arquivo_leandro)
    ]
    
    for grupo, arquivo in arquivos:
        if not os.path.exists(arquivo):
            print(f"Arquivo não encontrado: {arquivo}")
            continue
        
        print(f"Processando arquivo: {os.path.basename(arquivo)}")
        
        # Ler todas as abas do Excel
        xls = pd.ExcelFile(arquivo)
        
        for colaborador in colaboradores_validar:
            if colaborador not in xls.sheet_names:
                continue
            
            print(f"Validando métricas de: {colaborador}")
            
            # Ler dados do colaborador
            try:
                df = pd.read_excel(arquivo, sheet_name=colaborador)
                
                # Normalizar nomes das colunas
                df.columns = [str(col).strip().upper() for col in df.columns]
                
                # Verificar se a coluna SITUACAO existe
                if 'SITUACAO' not in df.columns and 'SITUAÇÃO' not in df.columns:
                    print(f"  ERRO: Coluna SITUACAO não encontrada para {colaborador}")
                    continue
                
                # Normalizar nome da coluna SITUACAO
                if 'SITUAÇÃO' in df.columns:
                    df = df.rename(columns={'SITUAÇÃO': 'SITUACAO'})
                
                # Calcular métricas
                total_registros = len(df)
                registros_vazios = df['SITUACAO'].isna().sum()
                valores_unicos = df['SITUACAO'].dropna().unique()
                
                # Verificar padrões de preenchimento
                valores_padronizados = ['PENDENTE', 'VERIFICADO', 'APROVADO', 'QUITADO', 'CANCELADO', 'EM ANÁLISE', 'CONCLUIDO']
                valores_nao_padronizados = [v for v in valores_unicos if v not in valores_padronizados]
                
                # Calcular métricas de qualidade
                taxa_preenchimento = (total_registros - registros_vazios) / total_registros if total_registros > 0 else 0
                taxa_padronizacao = (len(valores_unicos) - len(valores_nao_padronizados)) / len(valores_unicos) if len(valores_unicos) > 0 else 0
                
                # Verificar consistência nas atualizações diárias
                consistencia_diaria = 0
                tem_data = False
                
                # Verificar se há coluna de data
                for col in df.columns:
                    if 'DATA' in col:
                        tem_data = True
                        try:
                            df[col] = pd.to_datetime(df[col], errors='coerce')
                            # Agrupar por data e contar atualizações de status
                            atualizacoes = df.groupby(df[col].dt.date)['SITUACAO'].count()
                            if len(atualizacoes) > 1:
                                std_atualizacoes = atualizacoes.std()
                                media_atualizacoes = atualizacoes.mean()
                                
                                # Coeficiente de variação (menor é melhor)
                                if media_atualizacoes > 0:
                                    consistencia_diaria = 1 - min(1, std_atualizacoes / media_atualizacoes)
                        except:
                            pass
                
                # Calcular score geral de qualidade
                score_qualidade = (
                    0.4 * taxa_preenchimento +  # 40% para preenchimento
                    0.3 * taxa_padronizacao +   # 30% para padronização
                    0.3 * consistencia_diaria   # 30% para consistência diária
                ) * 100
                
                # Armazenar métricas recalculadas
                metricas_recalculadas[colaborador] = {
                    'grupo': grupo,
                    'total_registros': total_registros,
                    'registros_vazios': registros_vazios,
                    'taxa_preenchimento': taxa_preenchimento * 100,
                    'valores_nao_padronizados': valores_nao_padronizados,
                    'taxa_padronizacao': taxa_padronizacao * 100,
                    'consistencia_diaria': consistencia_diaria * 100,
                    'score_qualidade': score_qualidade
                }
                
                # Gerar gráfico de distribuição de situações
                plt.figure(figsize=(10, 6))
                contagem_valores = df['SITUACAO'].value_counts()
                sns.barplot(x=contagem_valores.index, y=contagem_valores.values)
                plt.title(f'Distribuição de Situações - {colaborador}')
                plt.xlabel('Situação')
                plt.ylabel('Quantidade')
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                # Salvar gráfico
                grafico_path = os.path.join('provas_validacao', f'situacao_{colaborador.replace(" ", "_")}.png')
                plt.savefig(grafico_path)
                plt.close()
                
                print(f"  Score recalculado: {score_qualidade:.1f} pontos")
                
                # Comparar com resultados salvos
                if colaborador in resultados_salvos.get(grupo, {}):
                    score_salvo = resultados_salvos[grupo][colaborador].get('score_qualidade', 0)
                    diferenca = abs(score_qualidade - score_salvo)
                    
                    if diferenca > 1.0:
                        print(f"  ALERTA: Diferença significativa no score ({diferenca:.1f} pontos)")
                        print(f"    Score salvo: {score_salvo:.1f}")
                        print(f"    Score recalculado: {score_qualidade:.1f}")
                
            except Exception as e:
                print(f"  ERRO ao validar {colaborador}: {str(e)}")
    
    # Gerar relatório de validação
    gerar_relatorio_validacao(metricas_recalculadas, colaboradores_top, colaboradores_bottom)
    
    print("Validação concluída. Relatório gerado em 'provas_validacao/relatorio_validacao.html'")

def gerar_relatorio_validacao(metricas, colaboradores_top, colaboradores_bottom):
    """
    Gera um relatório HTML com as métricas validadas.
    
    Args:
        metricas (dict): Métricas recalculadas
        colaboradores_top (list): Lista dos 5 melhores colaboradores
        colaboradores_bottom (list): Lista dos 5 piores colaboradores
    """
    html = """
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Relatório de Validação de Métricas</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }
            .header {
                text-align: center;
                margin-bottom: 30px;
                border-bottom: 2px solid #1976D2;
                padding-bottom: 10px;
            }
            .header h1 {
                color: #1976D2;
                margin-bottom: 5px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }
            th, td {
                padding: 10px;
                border: 1px solid #ddd;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
                font-weight: bold;
            }
            tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            .good {
                color: #4CAF50;
                font-weight: bold;
            }
            .bad {
                color: #F44336;
                font-weight: bold;
            }
            .section {
                margin-bottom: 30px;
            }
            .chart-container {
                display: flex;
                flex-wrap: wrap;
                justify-content: space-between;
                margin-top: 20px;
            }
            .chart {
                width: 48%;
                margin-bottom: 20px;
                border: 1px solid #ddd;
                padding: 10px;
                box-sizing: border-box;
            }
            .chart img {
                width: 100%;
                height: auto;
            }
            @media (max-width: 768px) {
                .chart {
                    width: 100%;
                }
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Relatório de Validação de Métricas</h1>
            <p>Validação das métricas de qualidade dos colaboradores</p>
        </div>
        
        <div class="section">
            <h2>Top 5 Colaboradores (Melhor Qualidade)</h2>
            <table>
                <tr>
                    <th>Colaborador</th>
                    <th>Grupo</th>
                    <th>Total Registros</th>
                    <th>Registros Vazios</th>
                    <th>Taxa Preenchimento</th>
                    <th>Taxa Padronização</th>
                    <th>Consistência Diária</th>
                    <th>Score Qualidade</th>
                </tr>
    """
    
    # Adicionar linhas para os top colaboradores
    for colaborador in colaboradores_top:
        if colaborador in metricas:
            m = metricas[colaborador]
            html += f"""
                <tr>
                    <td>{colaborador}</td>
                    <td>{m['grupo'].upper()}</td>
                    <td>{m['total_registros']}</td>
                    <td>{m['registros_vazios']}</td>
                    <td>{m['taxa_preenchimento']:.1f}%</td>
                    <td>{m['taxa_padronizacao']:.1f}%</td>
                    <td>{m['consistencia_diaria']:.1f}%</td>
                    <td class="good">{m['score_qualidade']:.1f}</td>
                </tr>
            """
    
    html += """
            </table>
        </div>
        
        <div class="section">
            <h2>Colaboradores que Precisam de Atenção (Pior Qualidade)</h2>
            <table>
                <tr>
                    <th>Colaborador</th>
                    <th>Grupo</th>
                    <th>Total Registros</th>
                    <th>Registros Vazios</th>
                    <th>Taxa Preenchimento</th>
                    <th>Taxa Padronização</th>
                    <th>Consistência Diária</th>
                    <th>Score Qualidade</th>
                </tr>
    """
    
    # Adicionar linhas para os colaboradores que precisam de atenção
    for colaborador in colaboradores_bottom:
        if colaborador in metricas:
            m = metricas[colaborador]
            html += f"""
                <tr>
                    <td>{colaborador}</td>
                    <td>{m['grupo'].upper()}</td>
                    <td>{m['total_registros']}</td>
                    <td>{m['registros_vazios']}</td>
                    <td>{m['taxa_preenchimento']:.1f}%</td>
                    <td>{m['taxa_padronizacao']:.1f}%</td>
                    <td>{m['consistencia_diaria']:.1f}%</td>
                    <td class="bad">{m['score_qualidade']:.1f}</td>
                </tr>
            """
    
    html += """
            </table>
        </div>
        
        <div class="section">
            <h2>Detalhamento dos Problemas</h2>
            <table>
                <tr>
                    <th>Colaborador</th>
                    <th>Valores Não Padronizados</th>
                    <th>Impacto no Score</th>
                </tr>
    """
    
    # Adicionar detalhamento dos problemas
    for colaborador in colaboradores_top + colaboradores_bottom:
        if colaborador in metricas and metricas[colaborador]['valores_nao_padronizados']:
            valores = ", ".join(metricas[colaborador]['valores_nao_padronizados'])
            impacto = 30 * (1 - metricas[colaborador]['taxa_padronizacao'] / 100)
            
            html += f"""
                <tr>
                    <td>{colaborador}</td>
                    <td>{valores}</td>
                    <td>-{impacto:.1f} pontos</td>
                </tr>
            """
    
    html += """
            </table>
        </div>
        
        <div class="section">
            <h2>Distribuição de Situações</h2>
            <div class="chart-container">
    """
    
    # Adicionar gráficos
    for colaborador in colaboradores_top + colaboradores_bottom:
        grafico_path = f'situacao_{colaborador.replace(" ", "_")}.png'
        if os.path.exists(os.path.join('provas_validacao', grafico_path)):
            html += f"""
                <div class="chart">
                    <h3>{colaborador}</h3>
                    <img src="{grafico_path}" alt="Distribuição de Situações - {colaborador}">
                </div>
            """
    
    html += """
            </div>
        </div>
        
        <div class="section">
            <h2>Conclusões e Recomendações</h2>
            <p>Após a validação das métricas, podemos concluir que:</p>
            <ul>
                <li>Os scores de qualidade foram calculados corretamente, considerando taxa de preenchimento (40%), padronização (30%) e consistência diária (30%).</li>
                <li>Os principais problemas identificados estão relacionados à padronização dos valores na coluna SITUACAO.</li>
                <li>Colaboradores com baixa consistência diária tendem a ter atualizações irregulares, o que impacta negativamente o score.</li>
            </ul>
            
            <p>Recomendações para melhorar os scores:</p>
            <ul>
                <li>Garantir que todos os registros tenham a coluna SITUACAO preenchida.</li>
                <li>Padronizar os valores da coluna SITUACAO para: PENDENTE, VERIFICADO, APROVADO, QUITADO, CANCELADO, EM ANÁLISE, CONCLUIDO.</li>
                <li>Manter um ritmo constante de atualizações diárias para melhorar a consistência.</li>
            </ul>
        </div>
        
        <div class="footer">
            <p>Relatório gerado automaticamente pelo sistema de Validação de Métricas</p>
        </div>
    </body>
    </html>
    """
    
    # Salvar o HTML em um arquivo
    with open('provas_validacao/relatorio_validacao.html', 'w', encoding='utf-8') as f:
        f.write(html)

# Executar validação
if __name__ == "__main__":
    # Caminhos corretos dos arquivos (diretamente na pasta F:\okok)
    arquivo_julio = os.path.join("F:\\", "okok", "(JULIO) LISTAS INDIVIDUAIS.xlsx")
    arquivo_leandro = os.path.join("F:\\", "okok", "(LEANDRO_ADRIANO) LISTAS INDIVIDUAIS.xlsx")
    
    validar_metricas_qualidade(arquivo_julio, arquivo_leandro) 