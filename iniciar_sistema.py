import os
import sys
import webbrowser
import time
import subprocess

def verificar_ambiente():
    """Verifica se o ambiente está configurado corretamente"""
    print("Verificando ambiente...")
    
    # Verificar se as pastas necessárias existem
    for pasta in ['uploads', 'resultados', 'data']:
        if not os.path.exists(pasta):
            os.makedirs(pasta)
            print(f"✅ Pasta '{pasta}' criada")
        else:
            print(f"✅ Pasta '{pasta}' já existe")
    
    # Verificar dependências
    try:
        import verificar_dependencias
        verificar_dependencias.instalar_dependencias()
    except ImportError:
        print("❌ Arquivo verificar_dependencias.py não encontrado")
        return False
    
    return True

def iniciar_servidor():
    """Inicia o servidor Flask"""
    print("\nIniciando servidor...")
    
    # Verificar qual arquivo app usar
    if os.path.exists('app_fixed.py'):
        app_file = 'app_fixed.py'
    elif os.path.exists('app.py'):
        app_file = 'app.py'
    else:
        print("❌ Nenhum arquivo app.py encontrado")
        return False
    
    # Iniciar o servidor em um processo separado
    try:
        processo = subprocess.Popen([sys.executable, app_file])
        print(f"✅ Servidor iniciado com {app_file}")
        return processo
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor: {str(e)}")
        return None

def abrir_navegador():
    """Abre o navegador na página inicial do sistema"""
    print("\nAbrindo navegador...")
    time.sleep(2)  # Esperar o servidor iniciar
    
    try:
        webbrowser.open('http://127.0.0.1:5000')
        print("✅ Navegador aberto")
        return True
    except Exception as e:
        print(f"❌ Erro ao abrir navegador: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== Sistema de Análise de Desempenho ===\n")
    
    if verificar_ambiente():
        processo_servidor = iniciar_servidor()
        
        if processo_servidor:
            abrir_navegador()
            
            print("\nServidor rodando. Pressione Ctrl+C para encerrar.")
            try:
                # Manter o script rodando
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nEncerrando servidor...")
                processo_servidor.terminate()
                print("Servidor encerrado. Até logo!") 