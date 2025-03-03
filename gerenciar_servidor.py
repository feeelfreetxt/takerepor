import os
import sys
import subprocess
import time
import signal
import psutil
import requests
import threading
import colorama
from colorama import Fore, Style

# Inicializar colorama para cores no terminal
colorama.init()

def print_info(mensagem):
    print(f"{Fore.BLUE}[INFO]{Style.RESET_ALL} {mensagem}")

def print_success(mensagem):
    print(f"{Fore.GREEN}[SUCESSO]{Style.RESET_ALL} {mensagem}")

def print_warning(mensagem):
    print(f"{Fore.YELLOW}[AVISO]{Style.RESET_ALL} {mensagem}")

def print_error(mensagem):
    print(f"{Fore.RED}[ERRO]{Style.RESET_ALL} {mensagem}")

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
            print_info(f"Servidor encerrado (PID: {pid})")
            
            # Esperar até 5 segundos para o processo encerrar
            for _ in range(10):
                if not psutil.pid_exists(pid):
                    break
                time.sleep(0.5)
                
            # Se ainda estiver rodando, forçar encerramento
            if psutil.pid_exists(pid):
                os.kill(pid, signal.SIGKILL)
                print_warning("Servidor forçado a encerrar")
            
            return True
        except Exception as e:
            print_error(f"Erro ao encerrar servidor: {str(e)}")
            return False
    else:
        print_warning("Nenhum servidor Flask encontrado rodando")
        return True  # Retorna True pois não há servidor para encerrar

def iniciar_servidor():
    """Inicia o servidor Flask"""
    try:
        # Verificar se o servidor já está rodando
        if encontrar_processo_flask():
            print_warning("Servidor já está rodando")
            return True
            
        # Verificar qual arquivo app usar
        if os.path.exists('app_fixed.py'):
            app_file = 'app_fixed.py'
        elif os.path.exists('app.py'):
            app_file = 'app.py'
        else:
            print_error("Nenhum arquivo app.py ou app_fixed.py encontrado")
            return False
        
        # Iniciar o servidor em um processo separado
        print_info(f"Iniciando servidor com {app_file}...")
        
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
            print_success("Servidor iniciado com sucesso")
            return True
        else:
            # Se o processo já terminou, algo deu errado
            stdout, stderr = processo.communicate()
            print_error(f"Erro ao iniciar servidor:\nSTDOUT: {stdout}\nSTDERR: {stderr}")
            return False
    except Exception as e:
        print_error(f"Erro ao iniciar servidor: {str(e)}")
        return False

def verificar_servidor():
    """Verifica se o servidor está respondendo"""
    try:
        response = requests.get('http://127.0.0.1:5000/status', timeout=2)
        if response.status_code == 200:
            print_success("Servidor está respondendo corretamente")
            return True
        else:
            print_warning(f"Servidor respondeu com código {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_warning("Não foi possível conectar ao servidor")
        return False
    except Exception as e:
        print_error(f"Erro ao verificar servidor: {str(e)}")
        return False

def reiniciar_servidor():
    """Reinicia o servidor Flask"""
    print_info("=== Reiniciando Servidor ===")
    
    # Encerrar servidor atual
    encerrar_servidor()
    
    # Aguardar um momento para garantir que a porta seja liberada
    time.sleep(2)
    
    # Iniciar novo servidor
    if iniciar_servidor():
        # Verificar se o servidor está respondendo
        time.sleep(3)
        if verificar_servidor():
            print_success("Servidor reiniciado com sucesso!")
            return True
        else:
            print_warning("Servidor iniciado, mas não está respondendo corretamente")
            return False
    else:
        print_error("Falha ao reiniciar servidor")
        return False

# Variável global para controlar o monitoramento
monitoramento_ativo = False
thread_monitoramento = None

def monitorar_servidor(intervalo=60):
    """Monitora o servidor e reinicia se necessário"""
    global monitoramento_ativo
    
    print_info(f"Monitorando servidor a cada {intervalo} segundos")
    
    while monitoramento_ativo:
        if not verificar_servidor():
            print_warning("Servidor não está respondendo. Reiniciando...")
            reiniciar_servidor()
        
        # Aguardar o intervalo especificado
        for _ in range(intervalo):
            if not monitoramento_ativo:
                break
            time.sleep(1)

def iniciar_monitoramento(intervalo=60):
    """Inicia o monitoramento em uma thread separada"""
    global monitoramento_ativo, thread_monitoramento
    
    if monitoramento_ativo:
        print_warning("Monitoramento já está ativo")
        return
    
    monitoramento_ativo = True
    thread_monitoramento = threading.Thread(target=monitorar_servidor, args=(intervalo,))
    thread_monitoramento.daemon = True
    thread_monitoramento.start()
    print_success("Monitoramento iniciado")

def parar_monitoramento():
    """Para o monitoramento"""
    global monitoramento_ativo, thread_monitoramento
    
    if not monitoramento_ativo:
        print_warning("Monitoramento não está ativo")
        return
    
    monitoramento_ativo = False
    if thread_monitoramento:
        thread_monitoramento.join(2)
    print_success("Monitoramento parado")

def abrir_navegador():
    """Abre o navegador na página do servidor"""
    import webbrowser
    try:
        webbrowser.open('http://127.0.0.1:5000')
        print_success("Navegador aberto")
        return True
    except Exception as e:
        print_error(f"Erro ao abrir navegador: {str(e)}")
        return False

def menu_interativo():
    """Exibe um menu interativo para gerenciar o servidor"""
    while True:
        print("\n" + "="*50)
        print(f"{Fore.CYAN}GERENCIADOR DE SERVIDOR FLASK{Style.RESET_ALL}")
        print("="*50)
        
        # Verificar status atual
        pid = encontrar_processo_flask()
        if pid:
            print(f"Status: {Fore.GREEN}ATIVO{Style.RESET_ALL} (PID: {pid})")
        else:
            print(f"Status: {Fore.RED}INATIVO{Style.RESET_ALL}")
            
        if monitoramento_ativo:
            print(f"Monitoramento: {Fore.GREEN}ATIVO{Style.RESET_ALL}")
        else:
            print(f"Monitoramento: {Fore.RED}INATIVO{Style.RESET_ALL}")
        
        print("\nOpções:")
        print("1. Iniciar servidor")
        print("2. Parar servidor")
        print("3. Reiniciar servidor")
        print("4. Verificar status")
        print("5. Iniciar monitoramento")
        print("6. Parar monitoramento")
        print("7. Abrir no navegador")
        print("8. Sair")
        
        opcao = input("\nEscolha uma opção (1-8): ")
        
        if opcao == '1':
            if not encontrar_processo_flask():
                confirmacao = input("Deseja iniciar o servidor? (s/n): ").lower()
                if confirmacao == 's':
                    iniciar_servidor()
            else:
                print_warning("Servidor já está rodando")
                
        elif opcao == '2':
            if encontrar_processo_flask():
                confirmacao = input("Deseja parar o servidor? (s/n): ").lower()
                if confirmacao == 's':
                    encerrar_servidor()
            else:
                print_warning("Servidor não está rodando")
                
        elif opcao == '3':
            confirmacao = input("Deseja reiniciar o servidor? (s/n): ").lower()
            if confirmacao == 's':
                reiniciar_servidor()
                
        elif opcao == '4':
            verificar_servidor()
            
        elif opcao == '5':
            if not monitoramento_ativo:
                try:
                    intervalo = int(input("Intervalo de monitoramento em segundos (padrão: 60): ") or "60")
                    iniciar_monitoramento(intervalo)
                except ValueError:
                    print_error("Intervalo inválido. Usando padrão de 60 segundos.")
                    iniciar_monitoramento(60)
            else:
                print_warning("Monitoramento já está ativo")
                
        elif opcao == '6':
            if monitoramento_ativo:
                parar_monitoramento()
            else:
                print_warning("Monitoramento não está ativo")
                
        elif opcao == '7':
            abrir_navegador()
            
        elif opcao == '8':
            confirmacao = input("Deseja encerrar o gerenciador? (s/n): ").lower()
            if confirmacao == 's':
                if monitoramento_ativo:
                    parar_monitoramento()
                
                if encontrar_processo_flask():
                    confirmacao_servidor = input("Deseja encerrar o servidor também? (s/n): ").lower()
                    if confirmacao_servidor == 's':
                        encerrar_servidor()
                
                print_info("Encerrando gerenciador. Até logo!")
                break
        else:
            print_error("Opção inválida. Tente novamente.")
        
        # Pequena pausa para ler as mensagens
        time.sleep(1)

if __name__ == "__main__":
    # Verificar se há argumentos de linha de comando
    if len(sys.argv) > 1:
        comando = sys.argv[1].lower()
        
        if comando == 'iniciar':
            iniciar_servidor()
        elif comando == 'parar':
            encerrar_servidor()
        elif comando == 'reiniciar':
            reiniciar_servidor()
        elif comando == 'status':
            verificar_servidor()
        elif comando == 'monitorar':
            intervalo = 60
            if len(sys.argv) > 2:
                try:
                    intervalo = int(sys.argv[2])
                except ValueError:
                    pass
            
            try:
                iniciar_monitoramento(intervalo)
                print_info("Pressione Ctrl+C para encerrar o monitoramento")
                while monitoramento_ativo:
                    time.sleep(1)
            except KeyboardInterrupt:
                print_info("\nEncerrando monitoramento")
                parar_monitoramento()
        else:
            print_error(f"Comando desconhecido: {comando}")
            print_info("Comandos disponíveis: iniciar, parar, reiniciar, status, monitorar")
    else:
        # Sem argumentos, iniciar o menu interativo
        menu_interativo() 