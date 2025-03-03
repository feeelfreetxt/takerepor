import os
import sys
import requests
import json
import time
import traceback

def verificar_servidor():
    """Verifica se o servidor Flask está respondendo"""
    try:
        response = requests.get('http://127.0.0.1:5000/status', timeout=5)
        if response.status_code == 200:
            print("✅ Servidor está online e respondendo")
            return True
        else:
            print(f"❌ Servidor respondeu com código {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Não foi possível conectar ao servidor")
        return False
    except Exception as e:
        print(f"❌ Erro ao verificar servidor: {str(e)}")
        return False

def verificar_arquivos_json():
    """Verifica se os arquivos JSON estão corretos"""
    resultados_path = os.path.join('resultados', 'relatorio_analise.json')
    
    if not os.path.exists(resultados_path):
        print(f"❌ Arquivo {resultados_path} não encontrado")
        return False
    
    try:
        with open(resultados_path, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        print(f"✅ Arquivo {resultados_path} está em formato JSON válido")
        return True
    except json.JSONDecodeError:
        print(f"❌ Arquivo {resultados_path} não é um JSON válido")
        return False
    except Exception as e:
        print(f"❌ Erro ao ler arquivo {resultados_path}: {str(e)}")
        return False

def verificar_permissoes():
    """Verifica permissões de escrita nas pastas necessárias"""
    for pasta in ['uploads', 'resultados', 'data']:
        if not os.path.exists(pasta):
            try:
                os.makedirs(pasta)
                print(f"✅ Pasta {pasta} criada com sucesso")
            except Exception as e:
                print(f"❌ Não foi possível criar a pasta {pasta}: {str(e)}")
                return False
        
        # Verificar permissão de escrita
        try:
            test_file = os.path.join(pasta, 'test_write.tmp')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            print(f"✅ Permissão de escrita na pasta {pasta} OK")
        except Exception as e:
            print(f"❌ Sem permissão de escrita na pasta {pasta}: {str(e)}")
            return False
    
    return True

def corrigir_json():
    """Corrige o arquivo JSON de resultados se estiver corrompido"""
    resultados_path = os.path.join('resultados', 'relatorio_analise.json')
    
    try:
        # Tentar ler o arquivo
        try:
            with open(resultados_path, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            print("✅ Arquivo JSON já está correto")
            return True
        except:
            # Se falhar, criar um novo arquivo
            dados_vazios = {
                "ultima_analise": None,
                "arquivos_analisados": [],
                "resultados": {},
                "erros": []
            }
            
            with open(resultados_path, 'w', encoding='utf-8') as f:
                json.dump(dados_vazios, f, indent=4)
            
            print("✅ Arquivo JSON recriado com sucesso")
            return True
    except Exception as e:
        print(f"❌ Não foi possível corrigir o arquivo JSON: {str(e)}")
        return False

def executar_diagnostico():
    """Executa diagnóstico completo e tenta corrigir problemas"""
    print("=== Diagnóstico do Sistema ===\n")
    
    # Verificar servidor
    servidor_ok = verificar_servidor()
    
    # Verificar arquivos JSON
    json_ok = verificar_arquivos_json()
    
    # Verificar permissões
    permissoes_ok = verificar_permissoes()
    
    print("\n=== Resultado do Diagnóstico ===")
    if servidor_ok and json_ok and permissoes_ok:
        print("✅ Sistema está funcionando corretamente")
        return True
    
    print("\n=== Tentando corrigir problemas ===")
    
    # Corrigir JSON se necessário
    if not json_ok:
        corrigir_json()
    
    print("\nDiagnóstico concluído. Execute novamente o sistema.")
    return False

if __name__ == "__main__":
    executar_diagnostico() 