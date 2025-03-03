import pkg_resources
import os

def criar_requirements_atualizado():
    """Cria um novo requirements.txt com as versões exatas instaladas"""
    
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
    print(f"\nDiretório atual: {os.getcwd()}")
    print("\nConteúdo do novo requirements.txt:")
    print(requirements)

if __name__ == "__main__":
    criar_requirements_atualizado()
