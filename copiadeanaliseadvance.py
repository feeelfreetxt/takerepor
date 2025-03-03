import pandas as pd
import numpy as np
from debug_excel import AnalisadorExcel
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from datetime import datetime, timedelta
import warnings
import os
import json
warnings.filterwarnings('ignore')

class AnalisadorAvancado:
    def __init__(self):
        """Inicializa o analisador avançado"""
        try:
            # Inicializar estruturas de dados
            self.metricas_julio = {}
            self.metricas_leandro = {}
            self.gargalos = {}
            self.ultima_analise = None
            self.historico_analises = []
            self.resultados_preditivos = {}
            
        except Exception as e:
            raise RuntimeError(f"Erro ao inicializar analisador: {str(e)}")

    def analisar_arquivo(self, caminho_arquivo=None):
        """Realiza a análise detalhada do arquivo Excel"""
        if not caminho_arquivo:
            caminho_arquivo = 'dados_analise.xlsx'

        print("Iniciando análise detalhada do arquivo...")
        
        try:
            # Registrar data e hora da análise
            self.ultima_analise = datetime.now()
            
            # Ler todas as abas do arquivo Excel
            excel_file = pd.ExcelFile(caminho_arquivo)
            
            # Lista de colaboradores para processar
            colaboradores = [
                'ANA LIDIA', 'FELIPE', 'JULIANE', 'MATHEUS', 'ANA GESSICA', 
                'POLIANA', 'IGOR', 'ELISANGELA', 'NUNO', 'THALISSON', 
                'VICTOR ADRIANO', 'VITORIA', 'LEANDRO'
            ]
            
            # Processar cada aba
            for nome_aba in excel_file.sheet_names:
                if nome_aba not in colaboradores:
                    print(f"Pulando aba {nome_aba} - não é um colaborador")
                    continue
                    
                print(f"\nAnalisando dados de: {nome_aba}")
                
                try:
                    # Ler a aba atual
                    df = pd.read_excel(excel_file, sheet_name=nome_aba)
                    
                    # Verificar se temos pelo menos a coluna DATA
                    if 'DATA' not in df.columns:
                        print(f"Erro: Coluna DATA não encontrada na aba {nome_aba}")
                        continue
                    
                    # Processar os dados do colaborador
                    metricas = self.processar_dados_colaborador(nome_aba, df)
                    
                    if metricas:
                        # Adicionar às métricas do grupo apropriado
                        if nome_aba in ['ANA LIDIA', 'FELIPE', 'JULIANE', 'MATHEUS', 'ANA GESSICA', 'POLIANA', 'IGOR', 'ELISANGELA', 'NUNO', 'THALISSON', 'VICTOR ADRIANO']:
                            self.metricas_julio[nome_aba] = metricas
                        else:
                            self.metricas_leandro[nome_aba] = metricas
                
                except Exception as e:
                    print(f"Erro ao processar aba {nome_aba}: {str(e)}")
                    continue

            # Salvar histórico da análise se temos dados
            if self.metricas_julio or self.metricas_leandro:
                self.historico_analises.append({
                    'data': self.ultima_analise,
                    'metricas_julio': self.metricas_julio.copy(),
                    'metricas_leandro': self.metricas_leandro.copy()
                })

                # Manter apenas as últimas 10 análises
                if len(self.historico_analises) > 10:
                    self.historico_analises = self.historico_analises[-10:]

                # Realizar análises comparativas
                self.analisar_correlacoes()
                self.detectar_gargalos()
                self.analisar_tendencias()
                self.realizar_analise_preditiva()
                
                # Gerar o dashboard
                self.gerar_dashboard_html()
            else:
                print("\nNenhum dado válido encontrado para análise")
            
        except Exception as e:
            print(f"Erro ao analisar arquivo: {str(e)}")
            raise

    def calcular_correlacao_volume_eficiencia(self):
        """Calcula a correlação entre volume de casos e eficiência para cada grupo"""
        print("\n=== Análise de Correlação Volume vs Eficiência ===")
        
        resultados = {}
        for grupo, metricas in [("JULIO", self.metricas_julio), ("LEANDRO", self.metricas_leandro)]:
            volumes = []
            eficiencias = []
            
            for colab, dados in metricas.items():
                try:
                    volume = sum(dados['distribuicao_status'].values())
                    eficiencia = dados.get('taxa_eficiencia', 0)
                    if volume > 0:  # Evitar dados inválidos
                        volumes.append(volume)
                        eficiencias.append(eficiencia)
                except (KeyError, TypeError, ValueError) as e:
                    print(f"Aviso: Dados inválidos para {colab}: {str(e)}")
                    continue
            
            if len(volumes) >= 2:  # Precisamos de pelo menos 2 pontos para correlação
                try:
                    correlacao = stats.pearsonr(volumes, eficiencias)
                    resultados[grupo] = {
                        'coeficiente': correlacao[0],
                        'p_valor': correlacao[1]
                    }
                    
                    print(f"\nGrupo {grupo}:")
                    print(f"Coeficiente de correlação: {correlacao[0]:.3f}")
                    print(f"P-valor: {correlacao[1]:.3f}")
                    
                    if correlacao[1] < 0.05:
                        if correlacao[0] > 0:
                            print("=> Correlação positiva significativa: Maior volume está associado a maior eficiência")
                        else:
                            print("=> Correlação negativa significativa: Maior volume está associado a menor eficiência")
                    else:
                        print("=> Não há correlação significativa entre volume e eficiência")
                except Exception as e:
                    print(f"Erro ao calcular correlação para grupo {grupo}: {str(e)}")
            else:
                print(f"\nGrupo {grupo}: Dados insuficientes para análise de correlação")
        
        return resultados
    
    def analisar_correlacoes(self):
        """Analisa correlações entre diferentes métricas"""
        try:
            print("\n=== Análise de Correlações ===")
            
            # Analisar correlações para cada grupo
            for grupo_nome, metricas in [("Julio", self.metricas_julio), ("Leandro", self.metricas_leandro)]:
                if not metricas:
                    continue
                    
                print(f"\nGrupo {grupo_nome}:")
                
                # Coletar dados para análise
                dados_grupo = []
                for colaborador, dados in metricas.items():
                    if not dados:
                        continue
                        
                    total = dados['total_registros']
                    eficiencia = dados['taxa_eficiencia']
                    dados_grupo.append({
                        'colaborador': colaborador,
                        'total': total,
                        'eficiencia': eficiencia
                    })
                
                if not dados_grupo:
                    print("Sem dados suficientes para análise")
                    continue
                
                # Converter para DataFrame
                df_grupo = pd.DataFrame(dados_grupo)
                
                # Calcular correlação entre volume e eficiência
                if len(df_grupo) > 1:
                    corr = df_grupo['total'].corr(df_grupo['eficiencia'])
                    print(f"Correlação volume vs eficiência: {corr:.2f}")
                    
                    # Identificar padrões
                    if abs(corr) > 0.7:
                        if corr > 0:
                            print("Forte correlação positiva: maior volume tende a ter maior eficiência")
                        else:
                            print("Forte correlação negativa: maior volume tende a ter menor eficiência")
                    elif abs(corr) > 0.3:
                        print("Correlação moderada")
                    else:
                        print("Correlação fraca: volume e eficiência parecem ser independentes")
                else:
                    print("Dados insuficientes para calcular correlações")
        
        except Exception as e:
            print(f"Erro ao analisar correlações: {str(e)}")
            return None

    def detectar_gargalos(self):
        """Detecta gargalos no processo baseado em diversos indicadores"""
        try:
            print("\n=== Detecção de Gargalos ===")
            
            self.gargalos = {
                "Julio": [],
                "Leandro": []
            }
            
            # Analisar cada grupo
            for grupo_nome, metricas in [("Julio", self.metricas_julio), ("Leandro", self.metricas_leandro)]:
                if not metricas:
                    continue
                    
                print(f"\nGrupo {grupo_nome}:")
                
                # Calcular métricas médias do grupo
                total_registros = []
                taxa_eficiencia = []
                
                for dados in metricas.values():
                    if dados:
                        total_registros.append(dados['total_registros'])
                        taxa_eficiencia.append(dados['taxa_eficiencia'])
                
                if not total_registros:
                    continue
                    
                media_registros = np.mean(total_registros)
                media_eficiencia = np.mean(taxa_eficiencia)
                
                print(f"Média de registros: {media_registros:.2f}")
                print(f"Média de eficiência: {media_eficiencia:.2f}")
                
                # Identificar colaboradores com métricas significativamente abaixo da média
                for colaborador, dados in metricas.items():
                    if not dados:
                        continue
                        
                    # Verificar eficiência
                    if dados['taxa_eficiencia'] < media_eficiencia * 0.7:
                        gargalo = {
                            "colaborador": colaborador,
                            "tipo": "eficiência",
                            "valor": dados['taxa_eficiencia'],
                            "media_grupo": media_eficiencia,
                            "diferenca_percentual": ((dados['taxa_eficiencia'] / media_eficiencia) - 1) * 100
                        }
                        self.gargalos[grupo_nome].append(gargalo)
                        print(f"⚠️ Gargalo de eficiência detectado: {colaborador} ({dados['taxa_eficiencia']:.2f} vs média {media_eficiencia:.2f})")
                    
                    # Verificar volume desproporcional
                    if dados['total_registros'] > media_registros * 1.5:
                        gargalo = {
                            "colaborador": colaborador,
                            "tipo": "volume",
                            "valor": dados['total_registros'],
                            "media_grupo": media_registros,
                            "diferenca_percentual": ((dados['total_registros'] / media_registros) - 1) * 100
                        }
                        self.gargalos[grupo_nome].append(gargalo)
                        print(f"⚠️ Volume desproporcional detectado: {colaborador} ({dados['total_registros']} vs média {media_registros:.2f})")
                
                # Verificar distribuição de carga
                if len(total_registros) > 1:
                    cv = np.std(total_registros) / np.mean(total_registros)  # Coeficiente de variação
                    if cv > 0.5:  # Alta variabilidade
                        gargalo = {
                            "tipo": "distribuição",
                            "valor": cv,
                            "descricao": "Distribuição desigual de carga entre colaboradores"
                        }
                        self.gargalos[grupo_nome].append(gargalo)
                        print(f"⚠️ Distribuição desigual de carga detectada (CV={cv:.2f})")
            
            return self.gargalos
            
        except Exception as e:
            print(f"Erro ao detectar gargalos: {str(e)}")
            return None

    def prever_tendencias(self):
        """Analisa tendências e faz previsões simples"""
        print("\n=== Análise de Tendências e Previsões ===")
        
        for grupo, metricas in [("JULIO", self.metricas_julio), ("LEANDRO", self.metricas_leandro)]:
            print(f"\nGrupo {grupo}:")
            
            # Análise de tendências por colaborador
            for colab, dados in metricas.items():
                if 'tendencia' in dados:
                    tendencia = dados['tendencia']
                    print(f"\nColaborador: {colab}")
                    
                    # Interpretar coeficiente angular
                    slope = tendencia.get('direcao', '')
                    r2 = tendencia.get('r2', 0)
                    
                    if slope == "estável":
                        tendencia_str = "estável"
                    elif slope == "crescente":
                        tendencia_str = "crescente"
                    else:
                        tendencia_str = "decrescente"
                    
                    print(f"Tendência: {tendencia_str}")
                    print(f"R² = {r2:.3f}")
                    
                    # Fazer previsão para próxima semana
                    if r2 > 0.3:  # Só fazer previsão se o modelo tiver um ajuste razoável
                        ultima_eficiencia = dados['taxa_eficiencia']
                        previsao_proxima_semana = ultima_eficiencia + (slope * 7)  # 7 dias
                        print(f"Previsão de eficiência para próxima semana: {previsao_proxima_semana*100:.1f}%")
                        
                        if previsao_proxima_semana < ultima_eficiencia * 0.8:
                            print(" Alerta: Possível queda significativa na eficiência")
                        elif previsao_proxima_semana > ultima_eficiencia * 1.2:
                            print(" Expectativa de melhoria significativa na eficiência")

    def analisar_tendencias(self):
        """Analisa tendências nos dados"""
        try:
            print("\n=== Análise de Tendências ===")
            
            # Analisar tendências para cada grupo
            for grupo_nome, metricas in [("Julio", self.metricas_julio), ("Leandro", self.metricas_leandro)]:
                if not metricas:
                    continue
                    
                print(f"\nGrupo {grupo_nome}:")
                
                # Analisar tendências por colaborador
                for colaborador, dados in metricas.items():
                    if not dados or 'tendencia' not in dados:
                        continue
                        
                    tendencia = dados['tendencia']
                    print(f"\n{colaborador}:")
                    print(f"Direção: {tendencia['direcao']}")
                    print(f"R²: {tendencia['r2']:.3f}")
                    
                    # Interpretar a tendência
                    if tendencia['r2'] > 0.7:
                        print("Tendência forte e consistente")
                    elif tendencia['r2'] > 0.3:
                        print("Tendência moderada")
                    else:
                        print("Tendência fraca ou dados muito variáveis")
        
        except Exception as e:
            print(f"Erro ao analisar tendências: {str(e)}")
            return None

    def realizar_analise_preditiva(self):
        """
        Realiza análise preditiva avançada para prever métricas futuras com base em dados históricos.
        Utiliza modelos de regressão linear e análise de séries temporais para gerar previsões.
        """
        print("\n=== Análise Preditiva Avançada ===")
        
        # Verificar se temos dados históricos suficientes
        if len(self.historico_analises) < 2:
            print("Dados históricos insuficientes para análise preditiva. Necessário pelo menos 2 análises.")
            return None
        
        resultados_preditivos = {
            "Julio": {},
            "Leandro": {}
        }
        
        try:
            # Para cada grupo, realizar previsões
            for grupo_nome, grupo_metricas in [("Julio", self.metricas_julio), ("Leandro", self.metricas_leandro)]:
                if not grupo_metricas:
                    continue
                
                print(f"\nPrevisões para grupo {grupo_nome}:")
                
                # Para cada colaborador, construir modelo preditivo
                for colaborador in grupo_metricas.keys():
                    # Coletar dados históricos deste colaborador
                    dados_historicos = []
                    datas = []
                    
                    for idx, analise in enumerate(self.historico_analises):
                        if grupo_nome == "Julio":
                            metricas_grupo = analise.get('metricas_julio', {})
                        else:
                            metricas_grupo = analise.get('metricas_leandro', {})
                        
                        if colaborador in metricas_grupo and metricas_grupo[colaborador]:
                            dados_historicos.append(metricas_grupo[colaborador].get('taxa_eficiencia', 0))
                            datas.append(idx)  # Usar índice como proxy para tempo
                    
                    # Se temos pelo menos 3 pontos de dados, podemos fazer previsão
                    if len(dados_historicos) >= 3:
                        # Preparar dados para modelo
                        X = np.array(datas).reshape(-1, 1)
                        y = np.array(dados_historicos)
                        
                        # Criar e treinar modelo
                        modelo = LinearRegression()
                        modelo.fit(X, y)
                        
                        # Fazer previsão para próximos 3 períodos
                        proximos_periodos = np.array([len(datas), len(datas)+1, len(datas)+2]).reshape(-1, 1)
                        previsoes = modelo.predict(proximos_periodos)
                        
                        # Calcular qualidade do modelo
                        y_pred = modelo.predict(X)
                        r2 = r2_score(y, y_pred)
                        
                        # Armazenar resultados
                        resultados_preditivos[grupo_nome][colaborador] = {
                            "historico": dados_historicos,
                            "previsoes": previsoes.tolist(),
                            "r2": r2,
                            "tendencia": "crescente" if modelo.coef_[0] > 0 else "decrescente",
                            "coeficiente": float(modelo.coef_[0]),
                            "intercepto": float(modelo.intercept_)
                        }
                        
                        # Exibir resultados
                        print(f"\n{colaborador}:")
                        print(f"  Histórico de eficiência: {[f'{x:.2f}' for x in dados_historicos]}")
                        print(f"  Previsão próximos 3 períodos: {[f'{x:.2f}' for x in previsoes]}")
                        print(f"  Confiança do modelo (R²): {r2:.2f}")
                        print(f"  Tendência: {resultados_preditivos[grupo_nome][colaborador]['tendencia']}")
                        
                        # Alertas baseados na previsão
                        ultima_eficiencia = dados_historicos[-1]
                        proxima_previsao = previsoes[0]
                        
                        if proxima_previsao < ultima_eficiencia * 0.8 and r2 > 0.5:
                            print("  ⚠️ ALERTA: Possível queda significativa na eficiência")
                        elif proxima_previsao > ultima_eficiencia * 1.2 and r2 > 0.5:
                            print("  ✅ Expectativa de melhoria significativa na eficiência")
                    else:
                        print(f"\n{colaborador}: Dados históricos insuficientes para previsão")
            
            # Salvar resultados para uso no dashboard
            self.resultados_preditivos = resultados_preditivos
            return resultados_preditivos
            
        except Exception as e:
            print(f"Erro ao realizar análise preditiva: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def gerar_dashboard_html(self):
        """Gera um dashboard HTML com os resultados da análise"""
        
        # Criar o template HTML com chaves escapadas para estilo CSS
        html_template = """<!DOCTYPE html>
<html>
<head>
    <title>Dashboard de Atividades</title>
    <meta charset="UTF-8">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        .card {{ margin-bottom: 20px; }}
        .header {{ background-color: #f8f9fa; padding: 20px; margin-bottom: 20px; }}
        .metric-value {{ font-size: 24px; font-weight: bold; }}
        .metric-label {{ font-size: 14px; color: #6c757d; }}
        .trend-up {{ color: #28a745; }}
        .trend-down {{ color: #dc3545; }}
        .trend-stable {{ color: #6c757d; }}
        .alert {{ padding: 10px; margin-bottom: 10px; border-radius: 5px; }}
        .alert-warning {{ background-color: #fff3cd; color: #856404; }}
        .alert-success {{ background-color: #d4edda; color: #155724; }}
        .tab-content {{ padding: 20px; }}
        .nav-tabs {{ margin-bottom: 0; }}
        .prediction-card {{ background-color: #f8f9fa; border-left: 4px solid #007bff; }}
        .prediction-value {{ font-size: 18px; font-weight: bold; }}
        .prediction-date {{ font-size: 12px; color: #6c757d; }}
        .confidence {{ font-size: 12px; padding: 2px 5px; border-radius: 3px; }}
        .confidence-high {{ background-color: #d4edda; color: #155724; }}
        .confidence-medium {{ background-color: #fff3cd; color: #856404; }}
        .confidence-low {{ background-color: #f8d7da; color: #721c24; }}
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="header">
            <div class="row">
                <div class="col-md-8">
                    <h1>Dashboard de Atividades</h1>
                    <p>Análise detalhada de métricas e tendências</p>
                </div>
                <div class="col-md-4 text-end">
                    <p>Última atualização: <strong>{data_atualizacao}</strong></p>
                </div>
            </div>
        </div>
        
        <ul class="nav nav-tabs" id="myTab" role="tablist">
            <li class="nav-item" role="presentation">
                <button class="nav-link active" id="resumo-tab" data-bs-toggle="tab" data-bs-target="#resumo" type="button" role="tab" aria-controls="resumo" aria-selected="true">Resumo</button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="julio-tab" data-bs-toggle="tab" data-bs-target="#julio" type="button" role="tab" aria-controls="julio" aria-selected="false">Grupo Julio</button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="leandro-tab" data-bs-toggle="tab" data-bs-target="#leandro" type="button" role="tab" aria-controls="leandro" aria-selected="false">Grupo Leandro</button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="previsoes-tab" data-bs-toggle="tab" data-bs-target="#previsoes" type="button" role="tab" aria-controls="previsoes" aria-selected="false">Previsões</button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="historico-tab" data-bs-toggle="tab" data-bs-target="#historico" type="button" role="tab" aria-controls="historico" aria-selected="false">Histórico</button>
            </li>
        </ul>
        
        <div class="tab-content" id="myTabContent">
            <!-- Aba de Resumo -->
            <div class="tab-pane fade show active" id="resumo" role="tabpanel" aria-labelledby="resumo-tab">
                <div class="row">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5>Resumo Geral</h5>
                            </div>
                            <div class="card-body">
                                <div class="row">
                                    <div class="col-md-6 mb-3">
                                        <div class="metric-label">Total de Colaboradores</div>
                                        <div class="metric-value">{total_colaboradores}</div>
                                    </div>
                                    <div class="col-md-6 mb-3">
                                        <div class="metric-label">Total de Registros</div>
                                        <div class="metric-value">{total_registros}</div>
                                    </div>
                                    <div class="col-md-6 mb-3">
                                        <div class="metric-label">Eficiência Média</div>
                                        <div class="metric-value">{eficiencia_media:.2f}%</div>
                                    </div>
                                    <div class="col-md-6 mb-3">
                                        <div class="metric-label">Tendência Geral</div>
                                        <div class="metric-value {tendencia_class}">{tendencia_geral}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="card mt-3">
                            <div class="card-header">
                                <h5>Comparativo entre Grupos</h5>
                            </div>
                            <div class="card-body">
                                <div id="comparativo-grupos"></div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5>Alertas e Gargalos</h5>
                            </div>
                            <div class="card-body">
                                {alertas_html}
                            </div>
                        </div>
                        
                        <div class="card mt-3">
                            <div class="card-header">
                                <h5>Previsões para Próximo Período</h5>
                            </div>
                            <div class="card-body">
                                <div id="previsoes-resumo"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Aba do Grupo Julio -->
            <div class="tab-pane fade" id="julio" role="tabpanel" aria-labelledby="julio-tab">
                {metricas_julio_html}
            </div>
            
            <!-- Aba do Grupo Leandro -->
            <div class="tab-pane fade" id="leandro" role="tabpanel" aria-labelledby="leandro-tab">
                {metricas_leandro_html}
            </div>
            
            <!-- Aba de Previsões -->
            <div class="tab-pane fade" id="previsoes" role="tabpanel" aria-labelledby="previsoes-tab">
                <div class="row">
                    <div class="col-md-12 mb-4">
                        <div class="card">
                            <div class="card-header">
                                <h5>Análise Preditiva</h5>
                            </div>
                            <div class="card-body">
                                <p>Esta seção apresenta previsões baseadas em modelos estatísticos aplicados aos dados históricos. 
                                As previsões consideram a tendência atual e padrões identificados nas análises anteriores.</p>
                                
                                <div class="alert alert-info">
                                    <strong>Nota:</strong> A confiabilidade das previsões está diretamente relacionada à quantidade 
                                    de dados históricos disponíveis e à consistência dos padrões observados.
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5>Previsões - Grupo Julio</h5>
                            </div>
                            <div class="card-body">
                                {previsoes_julio_html}
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5>Previsões - Grupo Leandro</h5>
                            </div>
                            <div class="card-body">
                                {previsoes_leandro_html}
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-12 mt-4">
                        <div class="card">
                            <div class="card-header">
                                <h5>Visualização de Tendências</h5>
                            </div>
                            <div class="card-body">
                                <div id="grafico-previsoes"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Aba de Histórico -->
            <div class="tab-pane fade" id="historico" role="tabpanel" aria-labelledby="historico-tab">
                <div class="card">
                    <div class="card-header">
                        <h5>Histórico de Análises</h5>
                    </div>
                    <div class="card-body">
                        {historico_html}
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Scripts para gráficos Plotly
        {scripts_plotly}
        
        // Inicializar tooltips
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {{
            return new bootstrap.Tooltip(tooltipTriggerEl)
        }})
    </script>
</body>
</html>
"""
        
        try:
            # Preparar dados para o template
            data_atualizacao = self.ultima_analise.strftime("%d/%m/%Y %H:%M") if self.ultima_analise else "N/A"
            
            # Calcular métricas gerais
            total_colaboradores = len(self.metricas_julio) + len(self.metricas_leandro)
            
            total_registros = 0
            soma_eficiencia = 0
            count_eficiencia = 0
            
            for metricas in [self.metricas_julio, self.metricas_leandro]:
                for dados in metricas.values():
                    if dados:
                        total_registros += dados.get('total_registros', 0)
                        if 'taxa_eficiencia' in dados:
                            soma_eficiencia += dados['taxa_eficiencia']
                            count_eficiencia += 1
            
            eficiencia_media = soma_eficiencia / count_eficiencia if count_eficiencia > 0 else 0
            
            # Determinar tendência geral
            tendencia_geral = "Estável"
            tendencia_class = "trend-stable"
            
            tendencias_crescentes = 0
            tendencias_decrescentes = 0
            
            for metricas in [self.metricas_julio, self.metricas_leandro]:
                for dados in metricas.values():
                    if dados and 'tendencia' in dados:
                        if dados['tendencia']['direcao'] == 'crescente':
                            tendencias_crescentes += 1
                        elif dados['tendencia']['direcao'] == 'decrescente':
                            tendencias_decrescentes += 1
            
            if tendencias_crescentes > tendencias_decrescentes * 1.5:
                tendencia_geral = "Crescente ↑"
                tendencia_class = "trend-up"
            elif tendencias_decrescentes > tendencias_crescentes * 1.5:
                tendencia_geral = "Decrescente ↓"
                tendencia_class = "trend-down"
            
            # Gerar HTML para alertas e gargalos
            alertas_html = "<div class='alert alert-success'>Nenhum alerta crítico identificado.</div>"
            
            gargalos_encontrados = []
            for grupo, gargalos in self.gargalos.items():
                for gargalo in gargalos:
                    if 'colaborador' in gargalo:
                        if gargalo['tipo'] == 'eficiência':
                            gargalos_encontrados.append(
                                f"<div class='alert alert-warning'>"
                                f"<strong>{gargalo['colaborador']}</strong> - Eficiência abaixo da média do grupo "
                                f"({gargalo['valor']:.2f}% vs {gargalo['media_grupo']:.2f}%)"
                                f"</div>"
                            )
                        elif gargalo['tipo'] == 'volume':
                            gargalos_encontrados.append(
                                f"<div class='alert alert-warning'>"
                                f"<strong>{gargalo['colaborador']}</strong> - Volume de trabalho desproporcional "
                                f"({gargalo['valor']} registros vs média de {gargalo['media_grupo']:.0f})"
                                f"</div>"
                            )
                    elif gargalo.get('tipo') == 'distribuição':
                        gargalos_encontrados.append(
                            f"<div class='alert alert-warning'>"
                            f"<strong>Grupo {grupo}</strong> - {gargalo['descricao']} "
                            f"(CV = {gargalo['valor']:.2f})"
                            f"</div>"
                        )
            
            if gargalos_encontrados:
                alertas_html = "\n".join(gargalos_encontrados)
            
            # Gerar HTML para métricas de cada grupo
            metricas_julio_html = self.gerar_html_metricas(self.metricas_julio)
            metricas_leandro_html = self.gerar_html_metricas(self.metricas_leandro)
            
            # Gerar HTML para histórico
            historico_html = self.gerar_html_historico()
            
            # Gerar HTML para previsões
            previsoes_julio_html = self.gerar_html_previsoes("Julio")
            previsoes_leandro_html = self.gerar_html_previsoes("Leandro")
            
            # Gerar scripts para gráficos Plotly
            scripts_plotly = self.gerar_scripts_plotly()
            
            # Substituir placeholders no template
            html_final = html_template.format(
                data_atualizacao=data_atualizacao,
                total_colaboradores=total_colaboradores,
                total_registros=total_registros,
                eficiencia_media=eficiencia_media * 100,  # Converter para percentual
                tendencia_geral=tendencia_geral,
                tendencia_class=tendencia_class,
                alertas_html=alertas_html,
                metricas_julio_html=metricas_julio_html,
                metricas_leandro_html=metricas_leandro_html,
                historico_html=historico_html,
                previsoes_julio_html=previsoes_julio_html,
                previsoes_leandro_html=previsoes_leandro_html,
                scripts_plotly=scripts_plotly
            )
            
            # Salvar o HTML em um arquivo
            with open('dashboard_atividades.html', 'w', encoding='utf-8') as f:
                f.write(html_final)
            
            print(f"\nDashboard gerado com sucesso: dashboard_atividades.html")
            
        except Exception as e:
            print(f"Erro ao gerar dashboard HTML: {str(e)}")
            import traceback
            traceback.print_exc()

    def gerar_html_previsoes(self, grupo):
        """Gera o HTML para exibir as previsões de um grupo"""
        if grupo not in self.resultados_preditivos or not self.resultados_preditivos[grupo]:
            return "<p>Não há dados de previsão disponíveis para este grupo.</p>"
        
        html_partes = []
        
        for colaborador, dados in self.resultados_preditivos[grupo].items():
            # Determinar classe de confiança
            confianca_class = "confidence-low"
            confianca_texto = "Baixa"
            
            if dados['r2'] > 0.7:
                confianca_class = "confidence-high"
                confianca_texto = "Alta"
            elif dados['r2'] > 0.3:
                confianca_class = "confidence-medium"
                confianca_texto = "Média"
            
            # Formatar previsões
            previsoes = dados['previsoes']
            html_previsoes = ""
            
            for i, prev in enumerate(previsoes):
                periodo = i + 1
                html_previsoes += f"""
                <div class="col-md-4">
                    <div class="prediction-card p-2 mb-2">
                        <div class="prediction-date">Período {periodo}</div>
                        <div class="prediction-value">{prev:.2f}%</div>
                    </div>
                </div>
                """
            
            # Montar card do colaborador
            html_partes.append(f"""
            <div class="card mb-3">
                <div class="card-header">
                    <h6>{colaborador}</h6>
                </div>
                <div class="card-body">
                    <div class="row mb-2">
                        <div class="col-md-6">
                            <span class="metric-label">Tendência:</span>
                            <span class="{'trend-up' if dados['tendencia'] == 'crescente' else 'trend-down'}">
                                {dados['tendencia'].capitalize()}
                            </span>
                        </div>
                        <div class="col-md-6">
                            <span class="metric-label">Confiança:</span>
                            <span class="confidence {confianca_class}">{confianca_texto} (R²: {dados['r2']:.2f})</span>
                        </div>
                    </div>
                    
                    <div class="row">
                        {html_previsoes}
                    </div>
                </div>
            </div>
            """)
        
        return "\n".join(html_partes)

    def processar_dados_colaborador(self, nome, df):
        """Processa os dados de um colaborador específico"""
        try:
            # Converter datas para datetime
            df['Data'] = pd.to_datetime(df['DATA'], format='%d/%m/%Y', errors='coerce')
            
            # Remover registros com datas inválidas
            df = df.dropna(subset=['Data'])
            
            if len(df) == 0:
                print(f"Nenhum registro com data válida encontrado para {nome}")
                return None
            
            # Definir status com base nas colunas disponíveis
            df['Status'] = 'PENDENTE'  # Status padrão
            
            if 'RESOLUÇÃO' in df.columns:
                df.loc[df['RESOLUÇÃO'].notna(), 'Status'] = 'VERIFICADO'
            
            if 'ÚLTIMO PAGAMENTO' in df.columns:
                df.loc[df['ÚLTIMO PAGAMENTO'].notna(), 'Status'] = 'QUITADO'
            
            # Calcular distribuição de status
            distribuicao = df['Status'].value_counts().to_dict()
            total_registros = len(df)
            
            # Análise por data
            analise_diaria = {}
            for data, grupo in df.groupby('Data'):
                data_str = data.strftime('%Y-%m-%d')
                status_counts = grupo['Status'].value_counts().to_dict()
                analise_diaria[data_str] = status_counts

            # Calcular médias diárias
            dias_unicos = df['Data'].nunique()
            medias_diarias = {status: round(count/dias_unicos, 1) 
                            for status, count in distribuicao.items()}

            # Análise de tendências
            df_tendencia = df.groupby('Data').size().reset_index()
            if len(df_tendencia) > 1:
                X = np.arange(len(df_tendencia)).reshape(-1, 1)
                y = df_tendencia[0].values
                reg = LinearRegression().fit(X, y)
                r2 = reg.score(X, y)
                tendencia = 'crescente' if reg.coef_[0] > 0 else 'decrescente'
            else:
                tendencia = 'estável'
                r2 = 0

            # Análise semanal
            df['DiaSemana'] = df['Data'].dt.day_name()
            padrao_semanal = df['DiaSemana'].value_counts().to_dict()

            # Calcular taxa de eficiência
            total_processados = sum(v for k, v in distribuicao.items() 
                                  if k in ['VERIFICADO', 'QUITADO'])
            taxa_eficiencia = (total_processados / total_registros) * 100 if total_registros > 0 else 0

            return {
                'total_registros': total_registros,
                'distribuicao_status': distribuicao,
                'medias_diarias': medias_diarias,
                'tendencia': {
                    'direcao': tendencia,
                    'r2': round(r2, 3)
                },
                'padrao_semanal': padrao_semanal,
                'taxa_eficiencia': round(taxa_eficiencia, 1),
                'analise_diaria': analise_diaria
            }
        except Exception as e:
            print(f"Erro ao processar aba {nome}: {str(e)}")
            return None

if __name__ == "__main__":
    # Inicializar analisador
    analisador = AnalisadorAvancado()
    
    print("\nANÁLISE AVANÇADA DE DESEMPENHO")
    print("=" * 50 + "\n")
    
    # Analisar arquivo do grupo JULIO
    print("\nAnalisando grupo JULIO...")
    analisador.analisar_arquivo("(JULIO) LISTAS INDIVIDUAIS.xlsx")
    
    # Analisar arquivo do grupo LEANDRO
    print("\nAnalisando grupo LEANDRO...")
    analisador.analisar_arquivo("(LEANDRO_ADRIANO) LISTAS INDIVIDUAIS.xlsx")
