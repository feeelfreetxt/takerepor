import os
import pandas as pd
import numpy as np
from datetime import datetime
import traceback
from pathlib import Path
import json
import webbrowser
from concurrent.futures import ThreadPoolExecutor

# Importando os módulos criados anteriormente
from validacao_metricas import validar_metricas_qualidade
from analise_detalhada import analisar_detalhes_colaborador
from analise_paralela import analisar_arquivo_paralelo
from debug_excel import AnalisadorExcel

class DashboardPipeline:
    def __init__(self):
        self.base_path = Path("F:\\okok")
        self.output_path = self.base_path / "dashboard_output"
        self.output_path.mkdir(exist_ok=True)
        
        # Arquivos de entrada
        self.arquivo_julio = self.base_path / "(JULIO) LISTAS INDIVIDUAIS.xlsx"
        self.arquivo_leandro = self.base_path / "(LEANDRO_ADRIANO) LISTAS INDIVIDUAIS.xlsx"
        
        # Configuração de estilo CSS
        self.css = """
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            .card {
                background: white;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .header {
                background: #2c3e50;
                color: white;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
            }
            .metric {
                display: inline-block;
                padding: 10px;
                margin: 5px;
                background: #ecf0f1;
                border-radius: 4px;
                min-width: 150px;
            }
            .good { color: #27ae60; }
            .warning { color: #f39c12; }
            .bad { color: #c0392b; }
            .chart-container {
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
                justify-content: space-between;
            }
            .chart {
                flex: 1;
                min-width: 300px;
                max-width: 600px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }
            th, td {
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            th {
                background-color: #2c3e50;
                color: white;
            }
            tr:nth-child(even) {
                background-color: #f2f2f2;
            }
            .nav {
                display: flex;
                gap: 10px;
                margin-bottom: 20px;
            }
            .nav-item {
                padding: 10px 20px;
                background: #2c3e50;
                color: white;
                border-radius: 4px;
                cursor: pointer;
                text-decoration: none;
            }
            .nav-item:hover {
                background: #34495e;
            }
        </style>
        """
    
    def executar_pipeline(self):
        """Executa o pipeline completo de análise"""
        try:
            print("Iniciando pipeline de análise...")
            
            # 1. Validação de métricas
            resultados_validacao = self.executar_validacao()
            
            # 2. Análise detalhada
            resultados_detalhados = self.executar_analise_detalhada()
            
            # 3. Análise paralela
            resultados_paralelos = self.executar_analise_paralela()
            
            # 4. Gerar dashboard
            self.gerar_dashboard(
                resultados_validacao,
                resultados_detalhados,
                resultados_paralelos
            )
            
            print("Pipeline concluído com sucesso!")
            
        except Exception as e:
            print(f"Erro no pipeline: {str(e)}")
            traceback.print_exc()
    
    def executar_validacao(self):
        """Executa a validação de métricas"""
        print("Executando validação de métricas...")
        return validar_metricas_qualidade(
            str(self.arquivo_julio),
            str(self.arquivo_leandro)
        )
    
    def executar_analise_detalhada(self):
        """Executa a análise detalhada"""
        print("Executando análise detalhada...")
        resultados = {}
        
        for arquivo in [self.arquivo_julio, self.arquivo_leandro]:
            if not arquivo.exists():
                print(f"Arquivo não encontrado: {arquivo}")
                continue
                
            xls = pd.ExcelFile(arquivo)
            for sheet in xls.sheet_names:
                if sheet.lower() not in ['resumo', 'índice', 'index', 'summary']:
                    df = pd.read_excel(arquivo, sheet_name=sheet)
                    resultados[sheet] = analisar_detalhes_colaborador(df, sheet)
        
        return resultados
    
    def executar_analise_paralela(self):
        """Executa a análise paralela"""
        print("Executando análise paralela...")
        try:
            # Criar um dicionário com os arquivos para análise
            arquivos = {
                'julio': str(self.arquivo_julio),
                'leandro': str(self.arquivo_leandro)
            }
            
            # Chamar a função com apenas um argumento (dicionário de arquivos)
            return analisar_arquivo_paralelo(arquivos)
            
        except Exception as e:
            print(f"Erro na análise paralela: {str(e)}")
            return {
                'status': 'erro',
                'mensagem': str(e),
                'resultados': {}
            }
    
    def gerar_dashboard(self, resultados_validacao, resultados_detalhados, resultados_paralelos):
        """Gera o dashboard HTML com todos os resultados"""
        print("Gerando dashboard...")
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Dashboard de Análise de Colaboradores</title>
            {self.css}
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Dashboard de Análise de Colaboradores</h1>
                    <p>Atualizado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                </div>
                
                <div class="nav">
                    <a href="#resumo" class="nav-item">Resumo</a>
                    <a href="#metricas" class="nav-item">Métricas</a>
                    <a href="#detalhes" class="nav-item">Detalhes</a>
                    <a href="#recomendacoes" class="nav-item">Recomendações</a>
                </div>
                
                <div id="resumo" class="card">
                    <h2>Resumo Geral</h2>
                    {self.gerar_secao_resumo(resultados_validacao)}
                </div>
                
                <div id="metricas" class="card">
                    <h2>Métricas por Colaborador</h2>
                    {self.gerar_secao_metricas(resultados_detalhados)}
                </div>
                
                <div id="detalhes" class="card">
                    <h2>Análise Detalhada</h2>
                    {self.gerar_secao_detalhes(resultados_paralelos)}
                </div>
                
                <div id="recomendacoes" class="card">
                    <h2>Recomendações</h2>
                    {self.gerar_secao_recomendacoes(resultados_validacao, resultados_detalhados)}
                </div>
            </div>
        </body>
        </html>
        """
        
        # Salvar o dashboard
        output_file = self.output_path / f"dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"Dashboard gerado em: {output_file}")
        
        # Abrir o dashboard no navegador
        webbrowser.open(str(output_file))
    
    def gerar_secao_resumo(self, resultados):
        """Gera a seção de resumo do dashboard"""
        # Implementar lógica de resumo
        return """
        <div class="chart-container">
            <div class="chart">
                <h3>Distribuição de Scores</h3>
                <!-- Adicionar gráfico de distribuição -->
            </div>
            <div class="chart">
                <h3>Top Performers</h3>
                <!-- Adicionar tabela de top performers -->
            </div>
        </div>
        """
    
    def gerar_secao_metricas(self, resultados):
        """Gera a seção de métricas do dashboard"""
        # Implementar lógica de métricas
        return """
        <table>
            <tr>
                <th>Colaborador</th>
                <th>Score</th>
                <th>Taxa Preenchimento</th>
                <th>Taxa Padronização</th>
                <th>Consistência</th>
            </tr>
            <!-- Adicionar linhas da tabela -->
        </table>
        """
    
    def gerar_secao_detalhes(self, resultados):
        """Gera a seção de detalhes do dashboard"""
        # Implementar lógica de detalhes
        return """
        <div class="chart-container">
            <!-- Adicionar gráficos detalhados -->
        </div>
        """
    
    def gerar_secao_recomendacoes(self, resultados_validacao, resultados_detalhados):
        """Gera a seção de recomendações do dashboard"""
        # Implementar lógica de recomendações
        return """
        <ul>
            <!-- Adicionar recomendações -->
        </ul>
        """

if __name__ == "__main__":
    pipeline = DashboardPipeline()
    pipeline.executar_pipeline() 