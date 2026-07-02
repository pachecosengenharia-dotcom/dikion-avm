import streamlit as st
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

st.set_page_config(page_title="AVM SaaS - Casas", layout="wide")

def treinar_modelo_casas(df):
    # 1. Limpeza dos nomes das colunas (remove espaços e converte para minúsculas)
    df.columns = df.columns.str.lower().str.strip()
    
    # 2. Filtragem estrita: Só usa linhas onde tipologia é CASA
    df['tipologia'] = df['tipologia'].astype(str).str.upper().str.strip()
    df_casas = df[df['tipologia'] == 'CASA'].copy()
    
    if df_casas.empty:
        st.error("Não foram encontrados dados de 'CASA' na sua planilha.")
        return None
    
    # 3. Seleção de colunas necessárias
    features = ['area_privativa', 'indice_fiscal', 'area_terreno', 'vagas_garagem', 'andar', 'pe_direito']
    
    # Validação de existência de colunas
    missing = [col for col in features if col not in df_casas.columns]
    if missing:
        st.error(f"Faltam colunas na planilha: {missing}")
        return None
    
    X = df_casas[features]
    y = df_casas['valor_total_declarado']
    
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    return model

# --- Interface ---
st.title("🏡 AVM Especialista: Casas")
uploaded_file = st.sidebar.file_uploader("Upload Planilha (Exclusivo Casas)", type=["csv", "xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    model = treinar_modelo_casas(df)
    
    if model:
        st.success("Modelo treinado com sucesso apenas com dados de casas!")
        
        # Inputs para predição
        col1, col2 = st.columns(2)
        area = col1.number_input("Área Construída", 100.0)
        indice = col2.number_input("Índice Fiscal", 1000.0)
        terreno = col1.number_input("Área Terreno", 200.0)
        vagas = col2.number_input("Vagas", 2.0)
        andar = 0 # Casas geralmente não têm andar
        pe_direito = col1.number_input("Pé Direito", 3.0)
        
        if st.button("Prever Valor"):
            input_data = pd.DataFrame([[area, indice, terreno, vagas, andar, pe_direito]], 
                                      columns=['area_privativa', 'indice_fiscal', 'area_terreno', 'vagas_garagem', 'andar', 'pe_direito'])
            valor = model.predict(input_data)[0]
            st.metric("Valor Estimado", f"R$ {valor:,.2f}")
