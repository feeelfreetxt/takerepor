import os
import pandas as pd
import numpy as np
import json
import glob
import traceback
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, abort, flash, redirect, url_for

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave_secreta_para_flash_messages'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULTS_FOLDER'] = 'resultados'
app.config['DATA_FOLDER'] = 'data'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB limite de upload

# Criar diretórios se não existirem
for folder in [app.config['UPLOAD_FOLDER'], app.config['RESULTS_FOLDER'], app.config['DATA_FOLDER']]:
    os.makedirs(folder, exist_ok=True)

class AnaliseManager:
    def __init__(self):
        self.resultados = {}
        self.ultima_analise = None
        self.arquivos_analisados = []
        self.erros = []
        self.carregar_resultados_salvos()
        
    def carregar_resultados_salvos(self):
        """Carrega resultados salvos anteriormente"""
        try:
            relatorio_path = os.path.join(app.config['RESULTS_FOLDER'], 'relatorio_analise.json')
            if os.path.exists(relatorio_path):
                with open(relatorio_path, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                    
                    # Converter string de data para objeto datetime
                    if 'ultima_analise' in dados and dados['ultima_analise']:
                        try:
                            self.ultima_analise = datetime.fromisoformat(dados['ultima_analise'])
                        except:
                            self.ultima_analise = None
                    
                    if 'arquivos_analisados' in dados:
                        self.arquivos_analisados = dados['arquivos_analisados']
                        
                    if 'resultados' in dados:
                        self.resultados = dados['resultados']
                        
                    if 'erros' in dados:
                        self.erros = dados['erros']
                        
                print(f"Resultados carregados: {len(self.arquivos_analisados)} arquivos, {sum(len(grupo) for grupo in self.resultados.values())} colaboradores")
        except Exception as e:
            print(f"Erro ao carregar resultados salvos: {str(e)}")
        
    def analisar_arquivo(self, arquivo_path, grupo="default"):
        """Analisa um arquivo Excel e retorna os resultados"""
        print(f"Iniciando análise do arquivo: {arquivo_path} (grupo: {grupo})")
        
        try:
            # Verificar se o arquivo existe
            if not os.path.exists(arquivo_path):
                erro_msg = f"Arquivo não encontrado: {arquivo_path}"
                print(erro_msg)
                return {"status": "error", "mensagem": erro_msg}
                
            # Verificar extensão do arquivo
            if not arquivo_path.lower().endswith(('.xls', '.xlsx')):
                erro_msg = f"Formato de arquivo não suportado: {arquivo_path}"
                print(erro_msg)
                return {"status": "error", "mensagem": erro_msg}
            
            # Importar AnalisadorExcel
            try:
                from debug_excel import AnalisadorExcel
            except ImportError as e:
                erro_msg = f"Módulo debug_excel não encontrado: {str(e)}"
                print(erro_msg)
                return {"status": "error", "mensagem": erro_msg}
            
            # Criar analisador e processar arquivo
            try:
                print(f"Criando analisador para {arquivo_path}")
                analisador = AnalisadorExcel(arquivo_path)
                
                print(f"Analisando arquivo {arquivo_path}")
                colaboradores = analisador.analisar_arquivo()
                
                print(f"Análise concluída: {len(colaboradores)} colaboradores encontrados")
                
                # Verificar se colaboradores é None ou vazio
                if not colaboradores:
                    colaboradores = []
                    print("Aviso: Nenhum colaborador encontrado no arquivo")
                    
                # Armazenar resultados
                if grupo not in self.resultados:
                    self.resultados[grupo] = {}
                
                # Verificar se analisador.colaboradores existe e não é None
                if hasattr(analisador, 'colaboradores') and analisador.colaboradores:
                    self.resultados[grupo] = analisador.colaboradores
                    print(f"Resultados armazenados para o grupo {grupo}: {len(analisador.colaboradores)} colaboradores")
                else:
                    print("Aviso: analisador.colaboradores está vazio ou não existe")
                    self.resultados[grupo] = {}
                
                # Registrar arquivo analisado
                if arquivo_path not in self.arquivos_analisados:
                    self.arquivos_analisados.append(arquivo_path)
                
                self.ultima_analise = datetime.now()
                
                # Salvar resultados em JSON
                self.salvar_resultados()
                
                return {
                    "status": "success",
                    "colaboradores": colaboradores,
                    "metricas": analisador.colaboradores if hasattr(analisador, 'colaboradores') else {},
                    "arquivo": os.path.basename(arquivo_path)
                }
            except Exception as e:
                erro_msg = f"Erro ao analisar arquivo: {str(e)}"
                traceback_str = traceback.format_exc()
                print(f"{erro_msg}\n{traceback_str}")
                
                self.erros.append({
                    "arquivo": os.path.basename(arquivo_path),
                    "erro": str(e),
                    "traceback": traceback_str,
                    "data": datetime.now().isoformat()
                })
                
                return {
                    "status": "error",
                    "mensagem": erro_msg,
                    "detalhes": traceback_str
                }
        except Exception as e:
            erro_msg = f"Erro não tratado: {str(e)}"
            traceback_str = traceback.format_exc()
            print(f"{erro_msg}\n{traceback_str}")
            
            return {
                "status": "error",
                "mensagem": erro_msg,
                "detalhes": traceback_str
            }
    
    def analise_avancada(self):
        """Executa análise avançada nos dados coletados"""
        try:
            from analise_avancada import AnalisadorAvancado
            
            analisador = AnalisadorAvancado()
            
            # Transferir dados dos grupos para o analisador avançado
            if 'julio' in self.resultados:
                analisador.metricas_julio = self.resultados['julio']
            if 'leandro' in self.resultados:
                analisador.metricas_leandro = self.resultados['leandro']
            if 'default' in self.resultados:
                # Se não houver dados específicos, usar os dados padrão para ambos
                if 'julio' not in self.resultados:
                    analisador.metricas_julio = self.resultados['default']
                if 'leandro' not in self.resultados:
                    analisador.metricas_leandro = self.resultados['default']
            
            analisador.ultima_analise = self.ultima_analise or datetime.now()
            
            # Executar análises
            analisador.analisar_tendencias()
            analisador.identificar_gargalos()
            analisador.gerar_previsoes()
            
            # Gerar dashboard HTML
            html = analisador.gerar_dashboard_html()
            
            # Salvar HTML
            dashboard_path = os.path.join(app.config['RESULTS_FOLDER'], 'dashboard_analise.html')
            with open(dashboard_path, 'w', encoding='utf-8') as f:
                f.write(html)
            
            # Salvar dados da análise avançada
            analise_avancada_path = os.path.join(app.config['RESULTS_FOLDER'], 'analise_avancada.json')
            dados_analise = {
                "tendencias": analisador.tendencias,
                "gargalos": analisador.gargalos,
                "previsoes": analisador.previsoes,
                "ultima_analise": analisador.ultima_analise.isoformat() if analisador.ultima_analise else None
            }
            
            with open(analise_avancada_path, 'w', encoding='utf-8') as f:
                json.dump(dados_analise, f, indent=2, default=str)
            
            return {
                "status": "success",
                "dashboard": "dashboard_analise.html",
                "dados": "analise_avancada.json",
                "tendencias": analisador.tendencias,
                "gargalos": analisador.gargalos,
                "previsoes": analisador.previsoes
            }
        except Exception as e:
            erro_msg = f"Erro na análise avançada: {str(e)}"
            traceback_str = traceback.format_exc()
            print(f"{erro_msg}\n{traceback_str}")
            
            self.erros.append({
                "tipo": "analise_avancada",
                "erro": str(e),
                "traceback": traceback_str,
                "data": datetime.now().isoformat()
            })
            
            return {
                "status": "error",
                "mensagem": erro_msg,
                "detalhes": traceback_str
            }
    
    def salvar_resultados(self):
        """Salva os resultados em um arquivo JSON"""
        try:
            dados = {
                "ultima_analise": self.ultima_analise.isoformat() if self.ultima_analise else None,
                "arquivos_analisados": self.arquivos_analisados,
                "resultados": self.resultados,
                "erros": self.erros
            }
            
            relatorio_path = os.path.join(app.config['RESULTS_FOLDER'], 'relatorio_analise.json')
            
            with open(relatorio_path, 'w', encoding='utf-8') as f:
                json.dump(dados, f, indent=2, default=str)
                
            print(f"Resultados salvos em {relatorio_path}")
            return True
        except Exception as e:
            print(f"Erro ao salvar resultados: {str(e)}")
            return False
    
    def listar_arquivos_disponiveis(self):
        """Lista todos os arquivos Excel disponíveis para análise"""
        arquivos = []
        
        # Verificar na pasta de uploads
        for ext in ['*.xlsx', '*.xls']:
            arquivos.extend(glob.glob(os.path.join(app.config['UPLOAD_FOLDER'], ext)))
            
        # Verificar na pasta de dados
        for ext in ['*.xlsx', '*.xls']:
            arquivos.extend(glob.glob(os.path.join(app.config['DATA_FOLDER'], ext)))
            
        # Verificar na raiz do projeto
        for ext in ['*.xlsx', '*.xls']:
            arquivos.extend(glob.glob(ext))
            
        # Extrair apenas os nomes dos arquivos
        nomes_arquivos = [os.path.basename(arquivo) for arquivo in arquivos]
        
        return sorted(nomes_arquivos)

# Criar instância do gerenciador de análise
analise_manager = AnaliseManager()

@app.route('/')
def index():
    arquivos_disponiveis = analise_manager.listar_arquivos_disponiveis()
    return render_template('index.html', arquivos_disponiveis=arquivos_disponiveis)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"status": "error", "mensagem": "Nenhum arquivo enviado"})
        
    file = request.files['file']
    grupo = request.form.get('grupo', 'default')
    
    if file.filename == '':
        return jsonify({"status": "error", "mensagem": "Nenhum arquivo selecionado"})
        
    if file:
        try:
            # Salvar arquivo
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            
            print(f"Arquivo salvo em {filepath}")
            
            # Analisar arquivo
            resultado = analise_manager.analisar_arquivo(filepath, grupo)
            
            # Forçar atualização do dashboard após upload
            if resultado["status"] == "success":
                analise_manager.analise_avancada()
                
            return jsonify(resultado)
        except Exception as e:
            traceback_str = traceback.format_exc()
            print(f"Erro no upload: {str(e)}\n{traceback_str}")
            return jsonify({
                "status": "error", 
                "mensagem": f"Erro ao processar upload: {str(e)}",
                "detalhes": traceback_str
            })

@app.route('/analisar-existente', methods=['POST'])
def analisar_existente():
    arquivo = request.form.get('arquivo')
    grupo = request.form.get('grupo', 'default')
    
    if not arquivo:
        return jsonify({"status": "error", "mensagem": "Nenhum arquivo selecionado"})
    
    print(f"Analisando arquivo existente: {arquivo} (grupo: {grupo})")
    
    # Verificar em diferentes locais
    locais = [
        os.path.join(app.config['UPLOAD_FOLDER'], arquivo),
        os.path.join(app.config['DATA_FOLDER'], arquivo),
        arquivo  # Na raiz do projeto
    ]
    
    for caminho in locais:
        if os.path.exists(caminho):
            print(f"Arquivo encontrado em: {caminho}")
            resultado = analise_manager.analisar_arquivo(caminho, grupo)
            
            # Forçar atualização do dashboard após análise
            if resultado["status"] == "success":
                analise_manager.analise_avancada()
                
            return jsonify(resultado)
    
    return jsonify({"status": "error", "mensagem": f"Arquivo não encontrado: {arquivo}"})

@app.route('/analise-avancada', methods=['POST'])
def executar_analise_avancada():
    resultado = analise_manager.analise_avancada()
    return jsonify(resultado)

@app.route('/resultados/<path:filename>')
def download_resultado(filename):
    caminho = os.path.join(app.config['RESULTS_FOLDER'], filename)
    if os.path.exists(caminho):
        return send_file(caminho, as_attachment=False)
    else:
        # Se o arquivo não existir, criar um JSON vazio para evitar erros
        if filename == 'relatorio_analise.json':
            dados_vazios = {
                "ultima_analise": None,
                "arquivos_analisados": [],
                "resultados": {},
                "erros": []
            }
            caminho_temp = os.path.join(app.config['RESULTS_FOLDER'], filename)
            with open(caminho_temp, 'w', encoding='utf-8') as f:
                json.dump(dados_vazios, f, indent=4)
            return send_file(caminho_temp, as_attachment=False)
        else:
            abort(404)

@app.route('/dashboard')
def dashboard():
    # Verificar se existe um dashboard gerado
    dashboard_path = os.path.join(app.config['RESULTS_FOLDER'], 'dashboard_analise.html')
    if os.path.exists(dashboard_path):
        with open(dashboard_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        return html_content
    else:
        # Se não existir, redirecionar para a página inicial
        return render_template('dashboard.html')

@app.route('/erros')
def listar_erros():
    return jsonify(analise_manager.erros)

@app.route('/arquivos')
def listar_arquivos():
    arquivos = analise_manager.listar_arquivos_disponiveis()
    return jsonify(arquivos)

@app.route('/limpar-dados', methods=['POST'])
def limpar_dados():
    """Limpa todos os dados de análise"""
    try:
        analise_manager.resultados = {}
        analise_manager.arquivos_analisados = []
        analise_manager.erros = []
        analise_manager.ultima_analise = None
        analise_manager.salvar_resultados()
        
        return jsonify({"status": "success", "mensagem": "Dados limpos com sucesso"})
    except Exception as e:
        return jsonify({"status": "error", "mensagem": f"Erro ao limpar dados: {str(e)}"})

@app.route('/status')
def status():
    """Retorna o status atual do sistema"""
    return jsonify({
        "status": "online",
        "ultima_analise": analise_manager.ultima_analise.isoformat() if analise_manager.ultima_analise else None,
        "arquivos_analisados": len(analise_manager.arquivos_analisados),
        "colaboradores": sum(len(grupo) for grupo in analise_manager.resultados.values()),
        "erros": len(analise_manager.erros)
    })

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    traceback_str = traceback.format_exc()
    print(f"Erro 500: {str(e)}\n{traceback_str}")
    return render_template('500.html', error=str(e), traceback=traceback_str), 500

if __name__ == '__main__':
    # Criar arquivos iniciais se não existirem
    relatorio_path = os.path.join(app.config['RESULTS_FOLDER'], 'relatorio_analise.json')
    if not os.path.exists(relatorio_path):
        dados_vazios = {
            "ultima_analise": None,
            "arquivos_analisados": [],
            "resultados": {},
            "erros": []
        }
        with open(relatorio_path, 'w', encoding='utf-8') as f:
            json.dump(dados_vazios, f, indent=4)
    
    print("Servidor iniciado. Acesse http://127.0.0.1:5000")
    app.run(debug=True, port=5000) 