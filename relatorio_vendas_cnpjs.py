import pandas as pd 
import sqlite3

# 1. Carregar os dados
file_name = 'nfe2025-08-04---extracao---2025.csv'
df = pd.read_csv(file_name, sep=';', encoding='utf-8-sig')

def limpando_e_filtrando_dados(df):
    df = df.copy()
    
    df.columns = df.columns.str.replace('.', ' ', regex=False).str.strip().str.replace(' ', '_').str.upper()
    
    df.columns = df.columns.str.replace('_+', '_', regex=True)
    print(df.columns)

    limite_nao_nulos = int(0.3 * len(df)) 
    df = df.dropna(thresh=limite_nao_nulos, axis=1)
    
    
    coluna_valor = 'VL_TOT_DO_PRODUTO_OU_SERVIÇO'
    coluna_data = 'DATA_DE_EMISSÃO_DA_NOTA'
    coluna_empresa = 'RAZÃO_SOCIAL_OU_NOME' 
    coluna_descricao = 'IDENTIF_DO_PRODUTO_OU_SERVIÇO' 
    
    
    if coluna_valor in df.columns:
        df[coluna_valor] = df[coluna_valor].astype(str).str.replace(',','.', regex=True)
        df[coluna_valor] = pd.to_numeric(df[coluna_valor], errors='coerce')

   
    if coluna_data in df.columns:
        df[coluna_data] = pd.to_datetime(df[coluna_data], errors='coerce')
        
        df = df.sort_values(by=coluna_data)
        df[coluna_data] = df[coluna_data].ffill()

   
    df = df.dropna(how='all')
    
    
    colunas_fundamentais = [coluna_data, coluna_empresa, coluna_descricao, coluna_valor]
    
    colunas_existentes = [col for col in colunas_fundamentais if col in df.columns]
    
    df_reduzido = df[colunas_existentes].copy()
    
   
    return df_reduzido.dropna(subset=[coluna_valor])


df_limpo = limpando_e_filtrando_dados(df)

print("--- Dados Prontos para Análise ---")
print(df_limpo.head())


coluna_empresa = 'RAZÃO_SOCIAL_OU_NOME'
coluna_valor = 'VL_TOT_DO_PRODUTO_OU_SERVIÇO'

if coluna_empresa in df_limpo.columns:
    relatorio_gastos = df_limpo.groupby(coluna_empresa)[coluna_valor].sum().reset_index()
    
    relatorio_gastos = relatorio_gastos.sort_values(by=coluna_valor, ascending=False)
    
    print("\n--- RELATÓRIO: Gastos Totais por Razão Social ---")
    print(relatorio_gastos.head(10)) 
    
   
    conn = sqlite3.connect('vendas_cnpjs.db')
    df_limpo.to_sql('vendas_totais_limpas', conn, if_exists='replace', index=False)
    relatorio_gastos.to_sql('resumo_gastos_empresas', conn, if_exists='replace', index=False)
    conn.close()
    print("\n[Sucesso] Tabelas salvas no SQLite!")
else:
    print(f"\n[Aviso] Coluna {coluna_empresa} não encontrada. Verifique o nome exato no CSV.")
