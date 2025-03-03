import os
import pandas as pd
import numpy as np
import json
import glob
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, abort, flash, redirect, url_for

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave_secreta_para_flash_messages'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULTS_FOLDER'] = 'resultados'
app.config['DATA_FOLDER'] = 'data'  # Nova pasta para arquivos salvos manualmente

# Criar diretórios se não existirem
for folder in [app.config['UPLOAD_FOLDER'], app.config['RESULTS_FOLDER'], app.config['DATA_FOLDER']]:
    os.makedirs(folder, exist_ok=True)

class AnaliseManager:
    def __init__(self):
        self.resultados = {}
        self.ultima_analise = None
        self.arquivos_analisados = []
        self.erros = []
        
    def analisar_arquivo(self, arquivo_path, grupo="default"):
        try:
            # Verificar se o arquivo existe
            if not os.path.exists(arquivo_path):
                return {
                    "status": "error",
                    "mensagem": f"Arquivo não encontrado: {arquivo_path}"
                }
                
            # Verificar extensão do arquivo
            if not arquivo_path.lower().endswith(('.xls', '.xlsx')):
                return {
                    "status": "error",
                    "mensagem": f"Formato de arquivo não suportado: {arquivo_path}"
                }
            
            # Tentar importar AnalisadorExcel
            try:
                from debug_excel import AnalisadorExcel
            except ImportError:
                return {
                    "status": "error",
                    "mensagem": "Módulo debug_excel não encontrado. Verifique se o arquivo está no diretório do projeto."
                }
            
            # Criar analisador com tratamento de erros
            try:
                analisador = AnalisadorExcel(arquivo_path)
                colaboradores = analisador.analisar_arquivo()
                
                # Verificar se colaboradores é None ou vazio
                if not colaboradores:
                    colaboradores = []
                    
                # Armazenar resultados
                if grupo not in self.resultados:
                    self.resultados[grupo] = {}
                    
                self.resultados[grupo] = analisador.colaboradores
                self.arquivos_analisados.append(arquivo_path)
                self.ultima_analise = datetime.now()
                
                # Salvar resultados em JSON
                self.salvar_resultados()
                
                return {
                    "status": "success",
                    "colaboradores": colaboradores,
                    "metricas": analisador.colaboradores
                }
            except Exception as e:
                self.erros.append({
                    "arquivo": os.path.basename(arquivo_path),
                    "erro": str(e),
                    "data": datetime.now().isoformat()
                })
                return {
                    "status": "error",
                    "mensagem": f"Erro ao analisar arquivo: {str(e)}"
                }
        except Exception as e:
            self.erros.append({
                "arquivo": os.path.basename(arquivo_path) if arquivo_path else "desconhecido",
                "erro": str(e),
                "data": datetime.now().isoformat()
            })
            return {
                "status": "error",
                "mensagem": f"Erro inesperado: {str(e)}"
            }
    
    def analise_avancada(self):
        try:
            # Tentar importar AnalisadorAvancado
            try:
                from analise_avancada import AnalisadorAvancado
            except ImportError:
                return {
                    "status": "error",
                    "mensagem": "Módulo analise_avancada não encontrado. Verifique se o arquivo está no diretório do projeto."
                }
            
            analisador = AnalisadorAvancado()
            
            # Verificar se há resultados para analisar
            if not self.resultados:
                return {
                    "status": "error",
                    "mensagem": "Nenhum resultado disponível para análise avançada. Analise pelo menos um arquivo primeiro."
                }
            
            # Configurar dados dos grupos
            if "julio" in self.resultados:
                analisador.metricas_julio = self.resultados["julio"]
            if "leandro" in self.resultados:
                analisador.metricas_leandro = self.resultados["leandro"]
            
            # Se não houver dados específicos, usar o grupo default
            if "default" in self.resultados and not hasattr(analisador, "metricas_julio"):
                analisador.metricas_julio = self.resultados["default"]
                
            analisador.ultima_analise = self.ultima_analise
            
            # Executar análises avançadas com tratamento de erros
            try:
                analisador.analisar_tendencias()
            except Exception as e:
                print(f"Erro ao analisar tendências: {e}")
                
            try:
                analisador.identificar_gargalos()
            except Exception as e:
                print(f"Erro ao identificar gargalos: {e}")
                
            try:
                analisador.gerar_previsoes()
            except Exception as e:
                print(f"Erro ao gerar previsões: {e}")
            
            # Gerar dashboard HTML
            html_path = os.path.join(app.config['RESULTS_FOLDER'], f"dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
            
            try:
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(analisador.gerar_dashboard_html())
            except Exception as e:
                return {
                    "status": "error",
                    "mensagem": f"Erro ao gerar dashboard HTML: {str(e)}"
                }
                
            return {
                "status": "success",
                "dashboard_path": html_path
            }
        except Exception as e:
            self.erros.append({
                "tipo": "analise_avancada",
                "erro": str(e),
                "data": datetime.now().isoformat()
            })
            return {
                "status": "error",
                "mensagem": f"Erro na análise avançada: {str(e)}"
            }
    
    def salvar_resultados(self):
        try:
            resultado_json = {
                "ultima_analise": self.ultima_analise.isoformat() if self.ultima_analise else None,
                "arquivos_analisados": self.arquivos_analisados,
                "resultados": {},
                "erros": self.erros
            }
            
            # Converter dados para formato serializável
            for grupo, metricas in self.resultados.items():
                resultado_json["resultados"][grupo] = {}
                for colaborador, dados in metricas.items():
                    if dados is not None:  # Verificar se dados não é None
                        resultado_json["resultados"][grupo][colaborador] = self.serializar_metricas(dados)
            
            # Salvar em arquivo JSON
            json_path = os.path.join(app.config['RESULTS_FOLDER'], "relatorio_analise.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(resultado_json, f, indent=4, ensure_ascii=False)
                
            return True
        except Exception as e:
            print(f"Erro ao salvar resultados: {e}")
            self.erros.append({
                "tipo": "salvar_resultados",
                "erro": str(e),
                "data": datetime.now().isoformat()
            })
            return False
    
    def serializar_metricas(self, metricas):
        """Converte objetos não serializáveis para formatos compatíveis com JSON"""
        if metricas is None:
            return {}
            
        resultado = {}
        
        for chave, valor in metricas.items():
            try:
                # Converter pandas Series/DataFrames para dicionários
                if isinstance(valor, (pd.Series, pd.DataFrame)):
                    resultado[chave] = valor.to_dict()
                # Converter numpy arrays para listas
                elif isinstance(valor, np.ndarray):
                    resultado[chave] = valor.tolist()
                # Converter numpy tipos para Python nativos
                elif isinstance(valor, (np.int64, np.int32, np.float64, np.float32)):
                    resultado[chave] = valor.item()
                # Converter datas
                elif isinstance(valor, (datetime, pd.Timestamp)):
                    resultado[chave] = valor.isoformat()
                # Processar dicionários recursivamente
                elif isinstance(valor, dict):
                    resultado[chave] = self.serializar_metricas(valor)
                # Manter outros tipos
                else:
                    resultado[chave] = valor
            except Exception as e:
                resultado[chave] = f"Erro ao serializar: {str(e)}"
                
        return resultado
        
    def listar_arquivos_disponiveis(self):
        """Lista todos os arquivos Excel disponíveis nas pastas do projeto"""
        arquivos = []
        
        # Buscar em uploads
        for ext in ['*.xlsx', '*.xls']:
            arquivos.extend(glob.glob(os.path.join(app.config['UPLOAD_FOLDER'], ext)))
            
        # Buscar em data (arquivos salvos manualmente)
        for ext in ['*.xlsx', '*.xls']:
            arquivos.extend(glob.glob(os.path.join(app.config['DATA_FOLDER'], ext)))
            
        # Buscar na raiz do projeto
        for ext in ['*.xlsx', '*.xls']:
            arquivos.extend(glob.glob(ext))
            
        return [os.path.basename(arquivo) for arquivo in arquivos]

# Instanciar gerenciador de análise
analise_manager = AnaliseManager()

@app.route('/')
def index():
    # Listar arquivos disponíveis
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
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            
            resultado = analise_manager.analisar_arquivo(filepath, grupo)
            return jsonify(resultado)
        except Exception as e:
            return jsonify({"status": "error", "mensagem": f"Erro ao processar arquivo: {str(e)}"})

@app.route('/analisar-existente', methods=['POST'])
def analisar_existente():
    arquivo = request.form.get('arquivo')
    grupo = request.form.get('grupo', 'default')
    
    if not arquivo:
        return jsonify({"status": "error", "mensagem": "Nenhum arquivo selecionado"})
    
    # Verificar em diferentes locais
    locais = [
        os.path.join(app.config['UPLOAD_FOLDER'], arquivo),
        os.path.join(app.config['DATA_FOLDER'], arquivo),
        arquivo  # Na raiz do projeto
    ]
    
    for caminho in locais:
        if os.path.exists(caminho):
            resultado = analise_manager.analisar_arquivo(caminho, grupo)
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
        return send_file(caminho)
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
            return send_file(caminho_temp)
        else:
            abort(404)

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/erros')
def listar_erros():
    return jsonify(analise_manager.erros)

@app.route('/arquivos')
def listar_arquivos():
    arquivos = analise_manager.listar_arquivos_disponiveis()
    return jsonify(arquivos)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html', error=str(e)), 500

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