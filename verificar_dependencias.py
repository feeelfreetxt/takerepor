import pkg_resources
import subprocess
from packaging import version
import sys
import os
import importlib

def verificar_dependencias():
    """Verifica as dependências instaladas contra o requirements.txt"""
    try:
        # Ler requirements.txt
        with open('requirements.txt', 'r') as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        # Obter pacotes instalados
        installed_packages = {pkg.key: pkg.version for pkg in pkg_resources.working_set}
        
        print("\n=== Verificação de Dependências ===\n")
        
        status = {"instalados": [], "ausentes": [], "versao_incompativel": []}
        
        for req in requirements:
            if '>=' in req:
                package, version_req = req.split('>=')
                comparador = '>='
            elif '==' in req:
                package, version_req = req.split('==')
                comparador = '=='
            else:
                continue
                
            package = package.strip()
            version_req = version_req.strip()
            
            if package.lower() in installed_packages:
                installed_version = installed_packages[package.lower()]
                
                if comparador == '>=':
                    if version.parse(installed_version) >= version.parse(version_req):
                        status["instalados"].append(f"{package} {installed_version} (✓)")
                    else:
                        status["versao_incompativel"].append(
                            f"{package} {installed_version} (requer >={version_req})"
                        )
                else:  # ==
                    if version.parse(installed_version) == version.parse(version_req):
                        status["instalados"].append(f"{package} {installed_version} (✓)")
                    else:
                        status["versao_incompativel"].append(
                            f"{package} {installed_version} (requer =={version_req})"
                        )
            else:
                status["ausentes"].append(package)
        
        # Exibir resultados
        print("Pacotes Instalados Corretamente:")
        for pkg in status["instalados"]:
            print(f"✓ {pkg}")
        
        if status["versao_incompativel"]:
            print("\nPacotes com Versão Incompatível:")
            for pkg in status["versao_incompativel"]:
                print(f"⚠ {pkg}")
        
        if status["ausentes"]:
            print("\nPacotes Ausentes:")
            for pkg in status["ausentes"]:
                print(f"✗ {pkg}")
        
        return status

    except FileNotFoundError:
        print("Erro: Arquivo 'requirements.txt' não encontrado no diretório atual.")
        print(f"Diretório atual: {os.getcwd()}")
        return None
    except Exception as e:
        print(f"Erro ao verificar dependências: {str(e)}")
        return None

def criar_requirements_atualizado():
    """Cria um novo requirements.txt com as versões exatas instaladas"""
    import pkg_resources
    
    # Obter pacotes instalados
    installed_packages = {
        pkg.key: pkg.version 
        for pkg in pkg_resources.working_set
    }
    
    # Template com as dependências necessárias e suas versões
    requirements = f"""# Dependências principais
flask=={installed_packages.get('flask', '2.3.3')}
pandas=={installed_packages.get('pandas', '2.2.3')}
numpy=={installed_packages.get('numpy', '2.2.2')}
plotly=={installed_packages.get('plotly', '6.0.0')}
streamlit=={installed_packages.get('streamlit', '1.42.0')}

# Processamento de dados
openpyxl=={installed_packages.get('openpyxl', '3.1.5')}
python-dotenv=={installed_packages.get('python-dotenv', '1.0.0')}
scikit-learn=={installed_packages.get('scikit-learn', '1.6.1')}
scipy=={installed_packages.get('scipy', '1.15.2')}

# Visualização
matplotlib=={installed_packages.get('matplotlib', '3.10.0')}
seaborn=={installed_packages.get('seaborn', '0.13.2')}
statsmodels=={installed_packages.get('statsmodels', '0.14.0')}

# Web e Dashboard
dash=={installed_packages.get('dash', '2.13.0')}
dash-bootstrap-components=={installed_packages.get('dash-bootstrap-components', '1.5.0')}
gunicorn=={installed_packages.get('gunicorn', '21.2.0')}

# Banco de dados
SQLAlchemy=={installed_packages.get('sqlalchemy', '2.0.20')}

# Testes
pytest=={installed_packages.get('pytest', '8.3.4')}
"""
    
    # Salvar o novo requirements.txt
    with open('requirements.txt', 'w') as f:
        f.write(requirements)
    
    print("Novo arquivo requirements.txt criado com as versões exatas!")
    print("\nConteúdo do novo requirements.txt:")
    print(requirements)

def verificar_dependencia(pacote, versao_minima=None):
    try:
        modulo = importlib.import_module(pacote)
        if versao_minima:
            versao_atual = modulo.__version__
            if versao_atual < versao_minima:
                print(f"⚠️ {pacote} versão {versao_atual} instalada, mas a versão mínima recomendada é {versao_minima}")
                return False
        print(f"✅ {pacote} instalado corretamente")
        return True
    except ImportError:
        print(f"❌ {pacote} não está instalado")
        return False

def instalar_dependencias():
    dependencias = [
        "flask",
        "pandas",
        "numpy",
        "openpyxl",  # Para ler arquivos Excel
        "xlrd",      # Para ler arquivos Excel antigos (.xls)
    ]
    
    print("Verificando dependências...")
    faltando = []
    
    for dep in dependencias:
        if not verificar_dependencia(dep):
            faltando.append(dep)
    
    if faltando:
        print("\nAlgumas dependências estão faltando. Deseja instalá-las agora? (s/n)")
        resposta = input().lower()
        
        if resposta == 's':
            print("\nInstalando dependências...")
            for dep in faltando:
                print(f"Instalando {dep}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print("\nTodas as dependências foram instaladas!")
        else:
            print("\nVocê precisará instalar as dependências manualmente para usar o sistema.")
            print("Use o comando: pip install " + " ".join(faltando))
    else:
        print("\nTodas as dependências estão instaladas corretamente!")

if __name__ == "__main__":
    instalar_dependencias()