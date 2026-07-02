import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io

# 1. Configuração da Página
st.set_page_config(page_title="Plataforma AVM", layout="wide")

# 2. Inicialização do Estado (IMPEDE QUE O CÓDIGO QUEBRE AO INTERAGIR)
if 'df_global' not in st.session_state:
    st.session_state.df_global = None

# 3. Funções de Processamento
def limpar_dados(df):
    # Padroniza nomes para evitar KeyError
    df.columns = [c.lower().strip().replace(" ", "_").replace("á", "a").replace("í", "i").replace("é", "e").replace("ã", "a").replace("ç", "c") for c in df.columns]
    # Garante colunas mínimas
    cols_esperadas = ['valor_total_declarado', 'area_privativa', 'indice_fiscal', 'area_terreno', 'vagas_garagem', 'andar', 'pe_direito', 'tipologia']
    for col in cols_esperadas:
        if col not in df.columns:
            df[col] = 0.0
    return df

# 4. Interface de Upload
st.title("🏢 Painel de Crédito AVM - Versão Estável")
arquivo = st.file_uploader("Upload da base de imóveis (CSV ou Excel)", type=["csv", "xlsx"])

if arquivo is not None:
    try:
        if arquivo.name.endswith('.csv'):
            df = pd.read_csv(arquivo)
        else:
            df = pd.read_excel(arquivo)
        st.session_state.df_global = limpar_dados(df)
        st.success(f"Base carregada! {len(st.session_state.df_global)} registros.")
    except Exception as e:
        st.error(f"Erro ao ler arquivo: {e}")

# 5. Motor de IA (Executado apenas se a base existir)
if st.session_state.df_global is not None:
    aba_avm, aba_jur = st.tabs(["📊 1. Avaliação AVM", "📜 2. Análise Jurídica"])
    
    with aba_avm:
        st.subheader("Configuração da Avaliação")
        tipo = st.selectbox("Selecione a Tipologia", ["CASA", "APARTAMENTO", "LOTE", "GALPAO"])
        
        # Filtro de dados para a tipologia
        df_tipo = st.session_state.df_global[st.session_state.df_global['tipologia'].astype(str).str.upper() == tipo]
        
        if len(df_tipo) < 3:
            st.warning(f"Não há amostras suficientes para {tipo}. (Mínimo 3).")
        else:
            col1, col2 = st.columns(2)
            area = col1.number_input("Área Privativa (m²)", value=100.0)
            indice = col2.number_input("Índice Fiscal", value=1000.0)
            
            if st.button("Calcular Valor Estimado"):
                features = ['area_privativa', 'indice_fiscal', 'area_terreno', 'vagas_garagem', 'andar', 'pe_direito']
                X = df_tipo[features]
                y = df_tipo['valor_total_declarado']
                
                modelo = RandomForestRegressor(n_estimators=100, random_state=42)
                modelo.fit(X, y)
                
                # Predição
                alvo = pd.DataFrame({'area_privativa': [area], 'indice_fiscal': [indice], 'area_terreno': [0], 'vagas_garagem': [1], 'andar': [0], 'pe_direito': [2.8]})
                pred = modelo.predict(alvo)[0]
                
                st.metric("Valor Estimado de Mercado", f"R$ {pred:,.2f}")
                st.info(f"Modelo treinado com {len(df_tipo)} amostras.")

    with aba_jur:
        st.write("Módulo jurídico disponível.")
else:
    st.info("Por favor, faça o upload da base de dados para iniciar.")
