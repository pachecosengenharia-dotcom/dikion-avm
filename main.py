import streamlit as st
import pandas as pd
import numpy as np
import io
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# 1. SETUP DA PÁGINA
st.set_page_config(page_title="AVM SaaS", layout="wide")

# 2. FUNÇÕES DE SUPORTE
def treinar_e_prever(df, tipologia, params):
    # Filtro e limpeza
    df['tipologia'] = df['tipologia'].astype(str).str.upper().str.strip()
    df_f = df[df['tipologia'] == tipologia].copy()
    
    features = ['area_privativa', 'indice_fiscal', 'area_terreno', 'vagas_garagem', 'andar', 'pe_direito']
    X = df_f[features]
    y = df_f['valor_total_declarado']
    
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    # Importância para o gráfico
    importancia = pd.DataFrame({'feature': features, 'importancia': model.feature_importances_}).sort_values('importancia')
    valor = model.predict(np.array([params]))[0]
    return valor, importancia

# 3. INTERFACE E CARGA DE DADOS
st.sidebar.header("⚙️ Configurações")
tenant = st.sidebar.selectbox("Cliente", ["Banco Alfa", "Imobiliária Beta"])
uploaded_file = st.sidebar.file_uploader("Upload Base (.csv ou .xlsx)", type=["csv", "xlsx"])

# Inicializa base (Demo ou Upload)
if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
else:
    df = pd.DataFrame({
        'valor_total_declarado': [500000, 350000], 'area_privativa': [100, 60], 
        'indice_fiscal': [1000, 1500], 'area_terreno': [200, 0], 
        'vagas_garagem': [2, 1], 'andar': [0, 3], 'pe_direito': [2.8, 2.7], 
        'tipologia': ['CASA', 'APARTAMENTO']
    })

# 4. ABAS E INPUTS
tab1, tab2 = st.tabs(["📊 Avaliação", "⚖️ Jurídico"])

with tab1:
    tipo = st.selectbox("Tipologia", ["CASA", "APARTAMENTO", "LOTE"])
    col1, col2 = st.columns(2)
    p = [col1.number_input("Área (m²)", 100.0), col2.number_input("Índice", 1000.0), 
         col1.number_input("Terreno", 200.0), col2.number_input("Vagas", 2.0), 
         col1.number_input("Andar", 0.0), col2.number_input("Pé Direito", 2.8)]
    
    if st.button("Executar Precificação"):
        valor, imp = treinar_e_prever(df, tipo, p)
        st.session_state.res = valor
        st.session_state.imp = imp
        st.session_state.tipo = tipo

# 5. EXIBIÇÃO DE RESULTADOS
if 'res' in st.session_state:
    st.metric("Valor Estimado", f"R$ {st.session_state.res:,.2f}")
    fig, ax = plt.subplots()
    ax.barh(st.session_state.imp['feature'], st.session_state.imp['importancia'])
    st.pyplot(fig)
