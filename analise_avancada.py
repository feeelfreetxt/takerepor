import pandas as pd
import numpy as np
from datetime import datetime
import json
import os

class AnalisadorAvancado:
    def __init__(self):
        self.metricas_julio = {}
        self.metricas_leandro = {}
        self.ultima_analise = None
        self.tendencias = {}
        self.gargalos = {
            'tempo_resolucao': [],
            'eficiencia_baixa': [],
            'volume_alto': [],
            'pendencias_altas': []
        }
        self.previsoes = {
            'carga_trabalho': {},
            'eficiencia_projetada': {},
            'tempo_resolucao_projetado': {}
        }
        
    def analisar_tendencias(self):
        """Analisa tendências nos dados de todos os colaboradores"""
        self.tendencias = {
            'eficiencia': {},
            'volume': {},
            'tempo_resolucao': {}
        }
        
        # Combinar dados de ambos os grupos
        todas_metricas = {}
        todas_metricas.update(self.metricas_julio)
        todas_metricas.update(self.metricas_leandro)
        
        # Extrair métricas para análise
        for nome, metricas in todas_metricas.items():
            if not metricas:
                continue
                
            # Eficiência
            if 'taxa_eficiencia' in metricas:
                self.tendencias['eficiencia'][nome] = metricas['taxa_eficiencia'] * 100
                
            # Volume
            if 'total_registros' in metricas:
                self.tendencias['volume'][nome] = metricas['total_registros']
                
            # Tempo de resolução
            if 'tempo_medio_resolucao' in metricas:
                self.tendencias['tempo_resolucao'][nome] = metricas['tempo_medio_resolucao']
        
        # Calcular médias e medianas
        for metrica, dados in self.tendencias.items():
            if dados:
                valores = list(dados.values())
                self.tendencias[f'{metrica}_media'] = np.mean(valores)
                self.tendencias[f'{metrica}_mediana'] = np.median(valores)
                self.tendencias[f'{metrica}_min'] = min(valores)
                self.tendencias[f'{metrica}_max'] = max(valores)
                
                # Identificar outliers
                Q1 = np.percentile(valores, 25)
                Q3 = np.percentile(valores, 75)
                IQR = Q3 - Q1
                
                outliers = [nome for nome, valor in dados.items() 
                           if valor < (Q1 - 1.5 * IQR) or valor > (Q3 + 1.5 * IQR)]
                
                self.tendencias[f'{metrica}_outliers'] = outliers
    
    def identificar_gargalos(self):
        """Identifica gargalos no processo"""
        self.gargalos = {
            'tempo_resolucao': [],
            'eficiencia_baixa': [],
            'volume_alto': [],
            'pendencias_altas': []
        }
        
        # Combinar dados de ambos os grupos
        todas_metricas = {}
        todas_metricas.update(self.metricas_julio)
        todas_metricas.update(self.metricas_leandro)
        
        # Calcular limiares
        tempos = [m.get('tempo_medio_resolucao', 0) for m in todas_metricas.values() if m and 'tempo_medio_resolucao' in m]
        eficiencias = [m.get('taxa_eficiencia', 0) for m in todas_metricas.values() if m and 'taxa_eficiencia' in m]
        volumes = [m.get('total_registros', 0) for m in todas_metricas.values() if m and 'total_registros' in m]
        
        if tempos:
            limiar_tempo = np.percentile(tempos, 75)  # 75º percentil
        else:
            limiar_tempo = 10  # valor padrão
            
        if eficiencias:
            limiar_eficiencia = np.percentile(eficiencias, 25)  # 25º percentil
        else:
            limiar_eficiencia = 0.15  # valor padrão
            
        if volumes:
            limiar_volume = np.percentile(volumes, 75)  # 75º percentil
        else:
            limiar_volume = 500  # valor padrão
        
        # Identificar gargalos
        for nome, metricas in todas_metricas.items():
            if not metricas:
                continue
                
            # Tempo de resolução alto
            if 'tempo_medio_resolucao' in metricas and metricas['tempo_medio_resolucao'] > limiar_tempo:
                self.gargalos['tempo_resolucao'].append({
                    'nome': nome,
                    'valor': metricas['tempo_medio_resolucao'],
                    'limiar': limiar_tempo
                })
                
            # Eficiência baixa
            if 'taxa_eficiencia' in metricas and metricas['taxa_eficiencia'] < limiar_eficiencia:
                self.gargalos['eficiencia_baixa'].append({
                    'nome': nome,
                    'valor': metricas['taxa_eficiencia'] * 100,  # percentual
                    'limiar': limiar_eficiencia * 100  # percentual
                })
                
            # Volume alto
            if 'total_registros' in metricas and metricas['total_registros'] > limiar_volume:
                self.gargalos['volume_alto'].append({
                    'nome': nome,
                    'valor': metricas['total_registros'],
                    'limiar': limiar_volume
                })
                
            # Pendências altas
            if 'distribuicao_status' in metricas and 'PENDENTE' in metricas['distribuicao_status']:
                pendentes = metricas['distribuicao_status']['PENDENTE']
                total = metricas['total_registros']
                
                if total > 0 and pendentes / total > 0.7:  # mais de 70% pendente
                    self.gargalos['pendencias_altas'].append({
                        'nome': nome,
                        'valor': pendentes,
                        'percentual': pendentes / total * 100
                    })
    
    def gerar_previsoes(self):
        """Gera previsões baseadas nos dados históricos"""
        self.previsoes = {
            'carga_trabalho': {},
            'eficiencia_projetada': {},
            'tempo_resolucao_projetado': {}
        }
        
        # Combinar dados de ambos os grupos
        todas_metricas = {}
        todas_metricas.update(self.metricas_julio)
        todas_metricas.update(self.metricas_leandro)
        
        # Gerar previsões para cada colaborador
        for nome, metricas in todas_metricas.items():
            if not metricas:
                continue
                
            # Carga de trabalho (baseada no padrão semanal)
            if 'padrao_semanal' in metricas and metricas['padrao_semanal']:
                total_semana = sum(metricas['padrao_semanal'].values())
                media_diaria = total_semana / 5  # considerando 5 dias úteis
                
                self.previsoes['carga_trabalho'][nome] = {
                    'diaria': media_diaria,
                    'semanal': total_semana,
                    'mensal': total_semana * 4
                }
                
            # Eficiência projetada
            if 'taxa_eficiencia' in metricas and 'tendencia' in metricas:
                eficiencia_atual = metricas['taxa_eficiencia']
                
                # Ajuste baseado na tendência
                if 'direcao' in metricas['tendencia']:
                    if metricas['tendencia']['direcao'] == 'crescente':
                        fator_ajuste = 1.05  # aumento de 5%
                    else:
                        fator_ajuste = 0.95  # redução de 5%
                else:
                    fator_ajuste = 1.0
                    
                eficiencia_projetada = min(eficiencia_atual * fator_ajuste, 1.0)
                
                self.previsoes['eficiencia_projetada'][nome] = {
                    'atual': eficiencia_atual * 100,
                    'projetada': eficiencia_projetada * 100,
                    'variacao': (eficiencia_projetada - eficiencia_atual) * 100
                }
                
            # Tempo de resolução projetado
            if 'tempo_medio_resolucao' in metricas:
                tempo_atual = metricas['tempo_medio_resolucao']
                
                # Ajuste baseado na eficiência
                if 'taxa_eficiencia' in metricas:
                    eficiencia = metricas['taxa_eficiencia']
                    
                    if eficiencia > 0.25:  # alta eficiência
                        fator_ajuste = 0.9  # redução de 10%
                    elif eficiencia < 0.15:  # baixa eficiência
                        fator_ajuste = 1.1  # aumento de 10%
                    else:
                        fator_ajuste = 1.0
                else:
                    fator_ajuste = 1.0
                    
                tempo_projetado = tempo_atual * fator_ajuste
                
                self.previsoes['tempo_resolucao_projetado'][nome] = {
                    'atual': tempo_atual,
                    'projetado': tempo_projetado,
                    'variacao': tempo_projetado - tempo_atual
                }
    
    def gerar_dashboard_html(self):
        """Gera um dashboard HTML com os resultados da análise"""
        # Combinar dados de ambos os grupos
        todas_metricas = {}
        todas_metricas.update(self.metricas_julio)
        todas_metricas.update(self.metricas_leandro)
        
        # Extrair dados para gráficos
        nomes = list(todas_metricas.keys())
        eficiencias = [todas_metricas[nome].get('taxa_eficiencia', 0) * 100 for nome in nomes]
        volumes = [todas_metricas[nome].get('total_registros', 0) for nome in nomes]
        tempos = [todas_metricas[nome].get('tempo_medio_resolucao', 0) for nome in nomes]
        
        # Ordenar dados por eficiência
        dados_combinados = list(zip(nomes, eficiencias, volumes, tempos))
        dados_ordenados = sorted(dados_combinados, key=lambda x: x[1], reverse=True)
        
        nomes_ordenados = [d[0] for d in dados_ordenados]
        eficiencias_ordenadas = [d[1] for d in dados_ordenados]
        volumes_ordenados = [d[2] for d in dados_ordenados]
        tempos_ordenados = [d[3] for d in dados_ordenados]
        
        # Preparar dados JSON para os gráficos
        nomes_json = json.dumps(nomes_ordenados[:10])
        eficiencias_json = json.dumps(eficiencias_ordenadas[:10])
        volumes_json = json.dumps(volumes_ordenados[:10])
        tempos_json = json.dumps(tempos_ordenados[:10])
        
        # Gerar HTML
        html = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Dashboard de Análise de Desempenho</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8f9fa; }}
                .card {{ border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }}
                .card-header {{ background-color: #2c3e50; color: white; border-radius: 10px 10px 0 0 !important; }}
                .stat-card {{ border-radius: 10px; padding: 20px; margin-bottom: 20px; background-color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .stat-value {{ font-size: 24px; font-weight: bold; margin-bottom: 5px; }}
                .stat-label {{ color: #6c757d; font-size: 14px; }}
                .trend-up {{ color: #2ecc71; }}
                .trend-down {{ color: #e74c3c; }}
                .trend-stable {{ color: #f1c40f; }}
                .alert-card {{ border-left: 4px solid; }}
                .alert-critical {{ border-color: #e74c3c; }}
                .alert-warning {{ border-color: #f1c40f; }}
                .alert-info {{ border-color: #3498db; }}
            </style>
        </head>
        <body>
            <div class="container-fluid py-4">
                <h1 class="mb-4">Dashboard de Análise de Desempenho</h1>
                <p class="text-muted">Última atualização: {self.ultima_analise.strftime('%d/%m/%Y %H:%M:%S') if self.ultima_analise else 'N/A'}</p>
                
                <div class="row">
                    <div class="col-md-4">
                        <div class="stat-card">
                            <div class="stat-value">{len(todas_metricas)}</div>
                            <div class="stat-label">Colaboradores Analisados</div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="stat-card">
                            <div class="stat-value">{sum(m.get('total_registros', 0) for m in todas_metricas.values())}</div>
                            <div class="stat-label">Total de Registros</div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="stat-card">
                            <div class="stat-value">{np.mean([m.get('taxa_eficiencia', 0) for m in todas_metricas.values() if m]) * 100:.1f}%</div>
                            <div class="stat-label">Eficiência Média</div>
                        </div>
                    </div>
                </div>
                
                <div class="row mt-4">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5 class="mb-0">Eficiência por Colaborador</h5>
                            </div>
                            <div class="card-body">
                                <canvas id="eficienciaChart" height="300"></canvas>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5 class="mb-0">Volume de Registros</h5>
                            </div>
                            <div class="card-body">
                                <canvas id="volumeChart" height="300"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row mt-4">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5 class="mb-0">Tempo Médio de Resolução</h5>
                            </div>
                            <div class="card-body">
                                <canvas id="tempoChart" height="300"></canvas>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5 class="mb-0">Gargalos Identificados</h5>
                            </div>
                            <div class="card-body">
                                <div class="alert alert-danger" role="alert">
                                    <h6>Tempo de Resolução Alto</h6>
                                    <ul>
                                        {' '.join([f'<li>{g["nome"]}: {g["valor"]:.1f} dias</li>' for g in self.gargalos['tempo_resolucao'][:5]])}
                                    </ul>
                                </div>
                                <div class="alert alert-warning" role="alert">
                                    <h6>Eficiência Baixa</h6>
                                    <ul>
                                        {' '.join([f'<li>{g["nome"]}: {g["valor"]:.1f}%</li>' for g in self.gargalos['eficiencia_baixa'][:5]])}
                                    </ul>
                                </div>
                                <div class="alert alert-info" role="alert">
                                    <h6>Volume Alto</h6>
                                    <ul>
                                        {' '.join([f'<li>{g["nome"]}: {g["valor"]} registros</li>' for g in self.gargalos['volume_alto'][:5]])}
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <script>
                // Gráfico de Eficiência
                const ctx1 = document.getElementById('eficienciaChart').getContext('2d');
                const eficienciaChart = new Chart(ctx1, {{
                    type: 'bar',
                    data: {{
                        labels: {nomes_json},
                        datasets: [{{
                            label: 'Eficiência (%)',
                            data: {eficiencias_json},
                            backgroundColor: 'rgba(52, 152, 219, 0.7)',
                            borderColor: 'rgba(52, 152, 219, 1)',
                            borderWidth: 1
                        }}]
                    }},
                    options: {{
                        indexAxis: 'y',
                        plugins: {{
                            legend: {{
                                display: false
                            }}
                        }},
                        scales: {{
                            x: {{
                                beginAtZero: true,
                                max: 100
                            }}
                        }}
                    }}
                }});
                
                // Gráfico de Volume
                const ctx2 = document.getElementById('volumeChart').getContext('2d');
                const volumeChart = new Chart(ctx2, {{
                    type: 'bar',
                    data: {{
                        labels: {nomes_json},
                        datasets: [{{
                            label: 'Volume de Registros',
                            data: {volumes_json},
                            backgroundColor: 'rgba(46, 204, 113, 0.7)',
                            borderColor: 'rgba(46, 204, 113, 1)',
                            borderWidth: 1
                        }}]
                    }},
                    options: {{
                        indexAxis: 'y',
                        plugins: {{
                            legend: {{
                                display: false
                            }}
                        }},
                        scales: {{
                            x: {{
                                beginAtZero: true
                            }}
                        }}
                    }}
                }});
                
                // Gráfico de Tempo
                const ctx3 = document.getElementById('tempoChart').getContext('2d');
                const tempoChart = new Chart(ctx3, {{
                    type: 'bar',
                    data: {{
                        labels: {nomes_json},
                        datasets: [{{
                            label: 'Tempo Médio (dias)',
                            data: {tempos_json},
                            backgroundColor: 'rgba(231, 76, 60, 0.7)',
                            borderColor: 'rgba(231, 76, 60, 1)',
                            borderWidth: 1
                        }}]
                    }},
                    options: {{
                        indexAxis: 'y',
                        plugins: {{
                            legend: {{
                                display: false
                            }}
                        }},
                        scales: {{
                            x: {{
                                beginAtZero: true
                            }}
                        }}
                    }}
                }});
            </script>
        </body>
        </html>
        """
        return html
    
    def analisar_dados(self, metricas_julio, metricas_leandro):
        """Executa a análise completa dos dados"""
        self.metricas_julio = metricas_julio or {}
        self.metricas_leandro = metricas_leandro or {}
        self.ultima_analise = datetime.now()
        
        # Executar análises
        self.analisar_tendencias()
        self.identificar_gargalos()
        self.gerar_previsoes()
        
        # Gerar dashboard
        dashboard_html = self.gerar_dashboard_html()
        
        return {
            "tendencias": self.tendencias,
            "gargalos": self.gargalos,
            "previsoes": self.previsoes,
            "dashboard_html": dashboard_html,
            "ultima_analise": self.ultima_analise.isoformat()
        }