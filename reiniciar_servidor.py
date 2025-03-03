import os
import sys
import subprocess
import time
import signal
import psutil

def encontrar_processo_flask():
    """Encontra o processo do Flask rodando na porta 5000"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Verificar se é um processo Python
            if 'python' in proc.info['name'].lower():
                cmdline = proc.info['cmdline']
                # Verificar se está executando app.py ou app_fixed.py
                if cmdline and any(app in cmdline for app in ['app.py', 'app_fixed.py']):
                    return proc.pid
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return None

def encerrar_servidor():
    """Encerra o servidor Flask se estiver rodando"""
    pid = encontrar_processo_flask()
    if pid:
        try:
            # Enviar sinal SIGTERM para encerrar graciosamente
            os.kill(pid, signal.SIGTERM)
            print(f"Servidor encerrado (PID: {pid})")
            
            # Esperar até 5 segundos para o processo encerrar
            for _ in range(10):
                if not psutil.pid_exists(pid):
                    break
                time.sleep(0.5)
                
            # Se ainda estiver rodando, forçar encerramento
            if psutil.pid_exists(pid):
                os.kill(pid, signal.SIGKILL)
                print("Servidor forçado a encerrar")
            
            return True
        except Exception as e:
            print(f"Erro ao encerrar servidor: {str(e)}")
            return False
    else:
        print("Nenhum servidor Flask encontrado rodando")
        return True  # Retorna True pois não há servidor para encerrar

def iniciar_servidor():
    """Inicia o servidor Flask"""
    try:
        # Verificar qual arquivo app usar
        if os.path.exists('app_fixed.py'):
            app_file = 'app_fixed.py'
        elif os.path.exists('app.py'):
            app_file = 'app.py'
        else:
            print("Erro: Nenhum arquivo app.py ou app_fixed.py encontrado")
            return False
        
        # Iniciar o servidor em um processo separado
        print(f"Iniciando servidor com {app_file}...")
        
        # Usar subprocess.Popen para iniciar o servidor em background
        processo = subprocess.Popen(
            [sys.executable, app_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Esperar um pouco para o servidor iniciar
        time.sleep(3)
        
        # Verificar se o processo ainda está rodando
        if processo.poll() is None:
            print("Servidor iniciado com sucesso")
            return True
        else:
            # Se o processo já terminou, algo deu errado
            stdout, stderr = processo.communicate()
            print(f"Erro ao iniciar servidor:\nSTDOUT: {stdout}\nSTDERR: {stderr}")
            return False
    except Exception as e:
        print(f"Erro ao iniciar servidor: {str(e)}")
        return False

def verificar_servidor():
    """Verifica se o servidor está respondendo"""
    import requests
    
    try:
        response = requests.get('http://127.0.0.1:5000/status', timeout=2)
        if response.status_code == 200:
            print("Servidor está respondendo corretamente")
            return True
        else:
            print(f"Servidor respondeu com código {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("Não foi possível conectar ao servidor")
        return False
    except Exception as e:
        print(f"Erro ao verificar servidor: {str(e)}")
        return False

def reiniciar_servidor():
    """Reinicia o servidor Flask"""
    print("=== Reiniciando Servidor ===")
    
    # Encerrar servidor atual
    encerrar_servidor()
    
    # Aguardar um momento para garantir que a porta seja liberada
    time.sleep(2)
    
    # Iniciar novo servidor
    if iniciar_servidor():
        # Verificar se o servidor está respondendo
        time.sleep(3)
        if verificar_servidor():
            print("Servidor reiniciado com sucesso!")
            return True
        else:
            print("Servidor iniciado, mas não está respondendo corretamente")
            return False
    else:
        print("Falha ao reiniciar servidor")
        return False

def monitorar_servidor(intervalo=60):
    """Monitora o servidor e reinicia se necessário"""
    print(f"Monitorando servidor a cada {intervalo} segundos. Pressione Ctrl+C para encerrar.")
    
    try:
        while True:
            if not verificar_servidor():
                print("Servidor não está respondendo. Reiniciando...")
                reiniciar_servidor()
            
            time.sleep(intervalo)
    except KeyboardInterrupt:
        print("\nMonitoramento encerrado pelo usuário")
        encerrar_servidor()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Gerenciador de servidor Flask")
    parser.add_argument('acao', choices=['iniciar', 'encerrar', 'reiniciar', 'monitorar'], 
                        help='Ação a ser executada')
    parser.add_argument('--intervalo', type=int, default=60,
                        help='Intervalo de monitoramento em segundos (padrão: 60)')
    
    args = parser.parse_args()
    
    if args.acao == 'iniciar':
        iniciar_servidor()
    elif args.acao == 'encerrar':
        encerrar_servidor()
    elif args.acao == 'reiniciar':
        reiniciar_servidor()
    elif args.acao == 'monitorar':
        monitorar_servidor(args.intervalo) 