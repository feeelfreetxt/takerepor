import os

# Caminhos para verificar
caminhos = [
    "F:\\okok\\data",
    "F:\\okok\\data\\(JULIO) LISTAS INDIVIDUAIS.xlsx",
    "F:\\okok\\data\\(JULIO) LISTAS INDIVIDUAIS.xlsxm",  # Verificando as duas extensões possíveis
    "F:\\okok\\data\\(LEANDRO_ADRIANO) LISTAS INDIVIDUAIS.xlsx"
]

# Verificar cada caminho
for caminho in caminhos:
    existe = os.path.exists(caminho)
    tipo = "Pasta" if os.path.isdir(caminho) else "Arquivo" if os.path.isfile(caminho) else "Desconhecido"
    print(f"{tipo}: {caminho} - {'EXISTE' if existe else 'NÃO EXISTE'}")

# Listar arquivos na pasta, se existir
pasta = "F:\\okok\\data"
if os.path.exists(pasta) and os.path.isdir(pasta):
    print("\nArquivos na pasta:")
    for arquivo in os.listdir(pasta):
        print(f"- {arquivo}") 