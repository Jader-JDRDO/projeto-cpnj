import pandas as pd 
import sqlite3
import matplotlib.pyplot as plt

# 1. Carregar os dados
nome_arquivo = 'nfe2025-08-04---extracao---2025.csv' #arrumar aqui para colocar um caminho que possa ser lido sempre que tiver um csv novo
df = pd.read_csv(nome_arquivo, sep=';', encoding='utf-8-sig') #definindo o data frame com a separacao e a decodificação para nao dar erro de interpretação

def limpando_e_filtrando_dados(df): #funcao de limpeza de dados

    #rescrevendo as colunas para tirar os pontos nas legendas e adicionar espaços vazios e depois nesses espaços vazios adicionar o subinhado
    df.columns = df.columns.str.replace('.', ' ', regex=False).str.strip().str.replace(' ', '_').str.upper()
    df.columns = df.columns.str.replace('_+', '_', regex=True) #se tiver mais de um sublinhado junto, adicionar trasnforma em apenas um sublinhado
    print(df.columns) #exibir os nomes das colunas

    limite_nao_nulos = int(0.3 * len(df)) #contando o total de linhas no arquivo e multiplicando por 30% definindo limite de linhas nulas
    df = df.dropna(thresh=limite_nao_nulos, axis=1) #df refeito e excluindo as colunas no qual tem mais de 30% de linhas nulas
    
    
    coluna_valor = 'VL_TOT_DO_PRODUTO_OU_SERVIÇO' #definindo valor das variaveis com um dicionario de acordo com as colunas
    coluna_data = 'DATA_DE_EMISSÃO_DA_NOTA'
    coluna_empresa = 'RAZÃO_SOCIAL_OU_NOME' 
    coluna_descricao = 'IDENTIF_DO_PRODUTO_OU_SERVIÇO' 
    
    
    if coluna_valor in df.columns: #se a coluna com valor esta entre as colunas que nao foram excluidas entao
        df[coluna_valor] = df[coluna_valor].astype(str).str.replace(',','.', regex=True)#tirar as , e deixar os pontos e colocar tudo como texto
        df[coluna_valor] = pd.to_numeric(df[coluna_valor], errors='coerce') #assim, padronizando tudo para numero depois

   
    if coluna_data in df.columns: #se a coluna com data esta entre as colunas que nao foram excluidas entao
        df[coluna_data] = pd.to_datetime(df[coluna_data], errors='coerce') #padronizar a coluna com formato de data
        
        df = df.sort_values(by=coluna_data) #ordem cronológica crescente baseada na data de emissão da nota fiscal.
        df[coluna_data] = df[coluna_data].ffill() #preenchenco datas que estao nulas de acordo com a linha de cima

   
    df = df.dropna(how='all') #vai deletar a coluna se todas as linhas estiverem vazias
    
    
    colunas_fundamentais = [coluna_data, coluna_empresa, coluna_descricao, coluna_valor] #colunas que sao obrigatorias
    
    colunas_existentes = [col for col in colunas_fundamentais if col in df.columns] #verifica se nas colunas existentes, contem as colunas obrigatorias
    
    df_reduzido = df[colunas_existentes].copy()
    
   
    return df_reduzido.dropna(subset=[coluna_valor])


df_limpo = limpando_e_filtrando_dados(df) #funçao sendo execultada

print("--- Dados Prontos para Análise ---") #se der td certo, aparece essa mensagem
print(df_limpo.head()) #exibe só os primeiros dados da df

# 2. Exibindo dados
coluna_empresa = 'RAZÃO_SOCIAL_OU_NOME' #coluna com os nomes das empresas
coluna_valor = 'VL_TOT_DO_PRODUTO_OU_SERVIÇO' #coluna com o valor total do produto ou serviço

if coluna_empresa in df_limpo.columns: #se a coluna com as empresas estiver dentro do df que foi limpo
    relatorio_gastos = df_limpo.groupby(coluna_empresa)[coluna_valor].sum().reset_index() #relatorio de dados totais gastos de acordo com a empresa
    
    relatorio_gastos = relatorio_gastos.sort_values(by=coluna_valor, ascending=False)#relatorio de gastos organizado em ordem crescente
    
    print("\n--- RELATÓRIO: Gastos Totais por Razão Social ---")
    print(relatorio_gastos.head(10)) 
    
   #jogando tudo para um banco de dados
    conn = sqlite3.connect('vendas_cnpjs.db')
    df_limpo.to_sql('vendas_totais_limpas', conn, if_exists='replace', index=False)
    relatorio_gastos.to_sql('resumo_gastos_empresas', conn, if_exists='replace', index=False)
    conn.close()
    print("\n[Sucesso] Tabelas salvas no SQLite!")
else:
    print(f"\n[Aviso] Coluna {coluna_empresa} não encontrada. Verifique o nome exato no CSV.")

top_empresas = relatorio_gastos.head(10)
plt.figure(figsize=(10, 5))
plt.barh(top_empresas[coluna_empresa],top_empresas[coluna_valor] / 1e6, color='skyblue')
plt.xlabel('Gasto Total em milhões(R$)')
plt.ylabel('Empresa')
plt.title('Top 10 Maiores Gastos por Empresa')
plt.gca().invert_yaxis() # Maior gasto fica no topo
plt.tight_layout()
plt.savefig('10_empresas_que_mais_gastam.png')


