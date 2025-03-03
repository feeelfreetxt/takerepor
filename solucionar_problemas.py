import os
import sys
import subprocess
import time
import json
import socket
import requests
import traceback
import psutil
import shutil
import platform

def print_titulo(texto):
    """Imprime um título formatado"""
    print("\n" + "="*60)
    print(f" {texto} ".center(60, "="))
    print("="*60)

def print_sucesso(texto):
    """Imprime uma mensagem de sucesso"""
    print(f"✅ {texto}")

def print_erro(texto):
    """Imprime uma mensagem de erro"""
    print(f"❌ {texto}")

def print_aviso(texto):
    """Imprime uma mensagem de aviso"""
    print(f"⚠️ {texto}")

def print_info(texto):
    """Imprime uma mensagem informativa"""
    print(f"ℹ️ {texto}")

def verificar_porta_5000():
    """Verifica se a porta 5000 está em uso e por qual processo"""
    print_titulo("VERIFICAÇÃO DE PORTA")
    
    try:
        # Tentar criar um socket na porta 5000
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        resultado = sock.connect_ex(('127.0.0.1', 5000))
        sock.close()
        
        if resultado == 0:
            print_aviso("A porta 5000 está em uso")
            
            # Encontrar qual processo está usando a porta
            if platform.system() == "Windows":
                try:
                    # Usar netstat no Windows
                    output = subprocess.check_output("netstat -ano | findstr :5000", shell=True).decode()
                    linhas = output.strip().split('\n')
                    
                    if linhas:
                        for linha in linhas:
                            if "LISTENING" in linha:
                                partes = linha.strip().split()
                                if len(partes) > 4:
                                    pid = partes[-1]
                                    try:
                                        processo = psutil.Process(int(pid))
                                        print_info(f"Porta 5000 está sendo usada pelo processo: {processo.name()} (PID: {pid})")
                                    except:
                                        print_info(f"Porta 5000 está sendo usada pelo PID: {pid}")
                except:
                    print_erro("Não foi possível identificar o processo usando a porta 5000")
            else:
                try:
                    # Usar lsof em sistemas Unix
                    output = subprocess.check_output("lsof -i :5000", shell=True).decode()
                    linhas = output.strip().split('\n')
                    
                    if len(linhas) > 1:  # Pular o cabeçalho
                        for linha in linhas[1:]:
                            partes = linha.strip().split()
                            if len(partes) > 1:
                                processo = partes[0]
                                pid = partes[1]
                                print_info(f"Porta 5000 está sendo usada pelo processo: {processo} (PID: {pid})")
                except:
                    print_erro("Não foi possível identificar o processo usando a porta 5000")
            
            return False
        else:
            print_sucesso("A porta 5000 está disponível")
            return True
    except Exception as e:
        print_erro(f"Erro ao verificar porta: {str(e)}")
        return False

def liberar_porta_5000():
    """Tenta liberar a porta 5000 encerrando processos"""
    print_titulo("LIBERANDO PORTA 5000")
    
    try:
        if platform.system() == "Windows":
            # Método para Windows
            try:
                # Encontrar PID usando a porta 5000
                output = subprocess.check_output("netstat -ano | findstr :5000", shell=True).decode()
                linhas = output.strip().split('\n')
                
                pids = []
                for linha in linhas:
                    if "LISTENING" in linha:
                        partes = linha.strip().split()
                        if len(partes) > 4:
                            pids.append(partes[-1])
                
                if pids:
                    for pid in pids:
                        try:
                            print_info(f"Tentando encerrar processo com PID {pid}...")
                            subprocess.call(f"taskkill /F /PID {pid}", shell=True)
                            print_sucesso(f"Processo com PID {pid} encerrado")
                        except:
                            print_erro(f"Não foi possível encerrar o processo com PID {pid}")
                    
                    # Verificar novamente
                    time.sleep(1)
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    resultado = sock.connect_ex(('127.0.0.1', 5000))
                    sock.close()
                    
                    if resultado != 0:
                        print_sucesso("Porta 5000 liberada com sucesso")
                        return True
                    else:
                        print_erro("Não foi possível liberar a porta 5000")
                        return False
                else:
                    print_aviso("Nenhum processo encontrado usando a porta 5000")
                    return True
            except Exception as e:
                print_erro(f"Erro ao liberar porta no Windows: {str(e)}")
                return False
        else:
            # Método para Unix/Linux
            try:
                output = subprocess.check_output("lsof -i :5000 | grep LISTEN", shell=True).decode()
                linhas = output.strip().split('\n')
                
                pids = []
                for linha in linhas:
                    partes = linha.strip().split()
                    if len(partes) > 1:
                        pids.append(partes[1])
                
                if pids:
                    for pid in pids:
                        try:
                            print_info(f"Tentando encerrar processo com PID {pid}...")
                            os.kill(int(pid), 9)  # SIGKILL
                            print_sucesso(f"Processo com PID {pid} encerrado")
                        except:
                            print_erro(f"Não foi possível encerrar o processo com PID {pid}")
                    
                    # Verificar novamente
                    time.sleep(1)
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    resultado = sock.connect_ex(('127.0.0.1', 5000))
                    sock.close()
                    
                    if resultado != 0:
                        print_sucesso("Porta 5000 liberada com sucesso")
                        return True
                    else:
                        print_erro("Não foi possível liberar a porta 5000")
                        return False
                else:
                    print_aviso("Nenhum processo encontrado usando a porta 5000")
                    return True
            except Exception as e:
                print_erro(f"Erro ao liberar porta em Unix/Linux: {str(e)}")
                return False
    except Exception as e:
        print_erro(f"Erro ao tentar liberar porta: {str(e)}")
        return False

def verificar_arquivos_json():
    """Verifica e corrige arquivos JSON"""
    print_titulo("VERIFICAÇÃO DE ARQUIVOS JSON")
    
    arquivos_json = [
        os.path.join('resultados', 'relatorio_analise.json'),
        os.path.join('resultados', 'analise_avancada.json')
    ]
    
    todos_ok = True
    
    for arquivo in arquivos_json:
        if not os.path.exists(arquivo):
            print_aviso(f"Arquivo {arquivo} não encontrado. Criando...")
            
            # Criar diretório se não existir
            os.makedirs(os.path.dirname(arquivo), exist_ok=True)
            
            # Criar arquivo JSON vazio
            dados_vazios = {
                "ultima_analise": None,
                "arquivos_analisados": [],
                "resultados": {},
                "erros": []
            }
            
            try:
                with open(arquivo, 'w', encoding='utf-8') as f:
                    json.dump(dados_vazios, f, indent=4)
                print_sucesso(f"Arquivo {arquivo} criado com sucesso")
            except Exception as e:
                print_erro(f"Erro ao criar arquivo {arquivo}: {str(e)}")
                todos_ok = False
        else:
            # Verificar se o arquivo é um JSON válido
            try:
                with open(arquivo, 'r', encoding='utf-8') as f:
                    json.load(f)
                print_sucesso(f"Arquivo {arquivo} é um JSON válido")
            except json.JSONDecodeError:
                print_erro(f"Arquivo {arquivo} não é um JSON válido. Corrigindo...")
                
                # Fazer backup do arquivo corrompido
                backup_file = f"{arquivo}.bak"
                try:
                    shutil.copy2(arquivo, backup_file)
                    print_info(f"Backup criado em {backup_file}")
                except:
                    print_aviso("Não foi possível criar backup do arquivo corrompido")
                
                # Criar novo arquivo JSON
                dados_vazios = {
                    "ultima_analise": None,
                    "arquivos_analisados": [],
                    "resultados": {},
                    "erros": []
                }
                
                try:
                    with open(arquivo, 'w', encoding='utf-8') as f:
                        json.dump(dados_vazios, f, indent=4)
                    print_sucesso(f"Arquivo {arquivo} corrigido com sucesso")
                except Exception as e:
                    print_erro(f"Erro ao corrigir arquivo {arquivo}: {str(e)}")
                    todos_ok = False
            except Exception as e:
                print_erro(f"Erro ao verificar arquivo {arquivo}: {str(e)}")
                todos_ok = False
    
    return todos_ok

def verificar_permissoes_pastas():
    """Verifica permissões de escrita nas pastas necessárias"""
    print_titulo("VERIFICAÇÃO DE PERMISSÕES")
    
    pastas = ['uploads', 'resultados', 'data', 'templates', 'static']
    todas_ok = True
    
    for pasta in pastas:
        # Criar pasta se não existir
        if not os.path.exists(pasta):
            try:
                os.makedirs(pasta)
                print_sucesso(f"Pasta {pasta} criada com sucesso")
            except Exception as e:
                print_erro(f"Erro ao criar pasta {pasta}: {str(e)}")
                todas_ok = False
                continue
        
        # Verificar permissão de escrita
        try:
            arquivo_teste = os.path.join(pasta, 'teste_permissao.tmp')
            with open(arquivo_teste, 'w') as f:
                f.write('teste')
            os.remove(arquivo_teste)
            print_sucesso(f"Permissão de escrita na pasta {pasta} OK")
        except Exception as e:
            print_erro(f"Sem permissão de escrita na pasta {pasta}: {str(e)}")
            todas_ok = False
    
    return todas_ok

def verificar_dependencias():
    """Verifica se todas as dependências estão instaladas"""
    print_titulo("VERIFICAÇÃO DE DEPENDÊNCIAS")
    
    dependencias = [
        ('flask', 'Flask'),
        ('pandas', 'pandas'),
        ('numpy', 'numpy'),
        ('openpyxl', 'openpyxl'),
        ('psutil', 'psutil'),
        ('requests', 'requests')
    ]
    
    todas_ok = True
    faltando = []
    
    for modulo, nome in dependencias:
        try:
            __import__(modulo)
            print_sucesso(f"Dependência {nome} instalada")
        except ImportError:
            print_erro(f"Dependência {nome} não encontrada")
            faltando.append(nome)
            todas_ok = False
    
    if faltando:
        print_aviso("\nAlgumas dependências estão faltando. Deseja instalá-las agora? (s/n)")
        resposta = input().lower()
        
        if resposta == 's':
            for nome in faltando:
                try:
                    print_info(f"Instalando {nome}...")
                    subprocess.check_call([sys.executable, "-m", "pip", "install", nome])
                    print_sucesso(f"{nome} instalado com sucesso")
                except Exception as e:
                    print_erro(f"Erro ao instalar {nome}: {str(e)}")
    
    return todas_ok

def verificar_servidor_flask():
    """Verifica se o servidor Flask está rodando"""
    print_titulo("VERIFICAÇÃO DO SERVIDOR FLASK")
    
    try:
        response = requests.get('http://127.0.0.1:5000/status', timeout=2)
        if response.status_code == 200:
            print_sucesso("Servidor Flask está rodando e respondendo")
            return True
        else:
            print_aviso(f"Servidor Flask respondeu com código {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_erro("Servidor Flask não está rodando ou não está acessível")
        return False
    except Exception as e:
        print_erro(f"Erro ao verificar servidor Flask: {str(e)}")
        return False

def iniciar_servidor_flask():
    """Inicia o servidor Flask"""
    print_titulo("INICIANDO SERVIDOR FLASK")
    
    # Verificar se o servidor já está rodando
    try:
        response = requests.get('http://127.0.0.1:5000/status', timeout=1)
        if response.status_code == 200:
            print_aviso("Servidor Flask já está rodando")
            return True
    except:
        pass
    
    # Verificar qual arquivo app usar
    if os.path.exists('app_fixed.py'):
        app_file = 'app_fixed.py'
    elif os.path.exists('app.py'):
        app_file = 'app.py'
    else:
        print_erro("Nenhum arquivo app.py ou app_fixed.py encontrado")
        return False
    
    print_info(f"Iniciando servidor com {app_file}...")
    
    try:
        # Iniciar o servidor em um processo separado
        if platform.system() == "Windows":
            subprocess.Popen(
                [sys.executable, app_file],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            subprocess.Popen(
                [sys.executable, app_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
        
        # Esperar o servidor iniciar
        print_info("Aguardando servidor iniciar...")
        for _ in range(10):
            time.sleep(1)
            try:
                response = requests.get('http://127.0.0.1:5000/status', timeout=1)
                if response.status_code == 200:
                    print_sucesso("Servidor Flask iniciado com sucesso")
                    return True
            except:
                pass
        
        print_aviso("Servidor iniciado, mas não está respondendo ainda")
        return True
    except Exception as e:
        print_erro(f"Erro ao iniciar servidor Flask: {str(e)}")
        return False

def solucionar_problemas():
    """Executa todas as verificações e tenta solucionar problemas"""
    print_titulo("SOLUCIONADOR DE PROBLEMAS")
    print("Este script irá verificar e tentar corrigir problemas comuns.")
    
    # Verificar porta
    porta_ok = verificar_porta_5000()
    if not porta_ok:
        print_info("\nTentando liberar a porta 5000...")
        liberar_porta_5000()
    
    # Verificar arquivos JSON
    arquivos_ok = verificar_arquivos_json()
    
    # Verificar permissões
    permissoes_ok = verificar_permissoes_pastas()
    
    # Verificar dependências
    dependencias_ok = verificar_dependencias()
    
    # Verificar servidor
    servidor_ok = verificar_servidor_flask()
    
    # Resumo
    print_titulo("RESUMO DO DIAGNÓSTICO")
    print(f"Porta 5000: {'✅ OK' if porta_ok else '⚠️ Problemas detectados'}")
    print(f"Arquivos JSON: {'✅ OK' if arquivos_ok else '⚠️ Problemas detectados'}")
    print(f"Permissões: {'✅ OK' if permissoes_ok else '⚠️ Problemas detectados'}")
    print(f"Dependências: {'✅ OK' if dependencias_ok else '⚠️ Problemas detectados'}")
    print(f"Servidor: {'✅ Rodando' if servidor_ok else '⚠️ Não está rodando'}")
    
    # Perguntar se deseja iniciar o servidor
    if not servidor_ok:
        print_aviso("\nO servidor Flask não está rodando. Deseja iniciá-lo agora? (s/n)")
        resposta = input().lower()
        
        if resposta == 's':
            iniciar_servidor_flask()
    
    print_titulo("DIAGNÓSTICO CONCLUÍDO")
    print("Se ainda estiver enfrentando problemas, tente:")
    print("1. Reiniciar o computador")
    print("2. Verificar se há outros serviços usando a porta 5000")
    print("3. Verificar os logs do servidor em logs/app.log")
    print("4. Executar 'python gerenciar_servidor.py' para mais opções")

if __name__ == "__main__":
    solucionar_problemas() 