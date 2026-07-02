import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import io

st.set_page_config(page_title="AVM SaaS Pro", layout="wide")

# 1. Função de Base de Dados (Simulando uma carga de um banco de dados real)
@st.cache_data
def carregar_dados():
    data = {
        'valor_total_declarado': [450000, 480000, 510000, 350000, 380000, 420000, 150000, 210000],
        'area_privativa': [75, 78, 80, 60, 62, 65, 350, 400],
        'indice_fiscal': [1200, 1250, 1300, 1500, 1600, 1800, 800, 1100],
        'area_terreno': [200, 220, 250, 0, 0, 0, 350, 400],
        'vagas_garagem': [2, 2, 2, 1, 1, 2, 0, 0],
        'andar': [0, 0, 0, 3, 5, 8, 0, 0],
        'pe_direito': [3.0, 3.0, 3.2, 2.7, 2.7, 2.8, 0.0, 0.0],
        'tipologia': ['CASA', 'CASA', 'CASA', 'APARTAMENTO', 'APARTAMENTO', 'APARTAMENTO', 'LOTE', 'LOTE']
    }
    return pd.DataFrame(data)

# 2. Motor de IA
def executar_modelo(df, tipologia, params):
    df_f = df[df['tipologia'] == tipologia]
    features = ['area_privativa', 'indice_fiscal', 'area_terreno', 'vagas_garagem', 'andar', 'pe_direito']
    X = df_f[features]
    y = df_f['valor_total_declarado']
    
    model = RandomForestRegressor(n_estimators=200, random_state=42)
    model.fit(X, y)
    
    input_df = pd.DataFrame([params], columns=features)
    valor = model.predict(input_df)[0]
    return valor

# 3. Gerador de PDF (Com colunas definidas)
def gerar_pdf(valores, tipologia):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [Paragraph(f"Laudo Técnico - {tipologia}", styles['Heading1']), Spacer(1, 12)]
    
    t_data = [["Metrica", "Valor"], ["Valor Estimado", f"R$ {valores:,.2f}"]]
    t = Table(t_data, colWidths=[200, 200])
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black)]))
    story.append(t)
    
    doc.build(story)
    return buffer.getvalue()

# 4. Interface
df = carregar_dados()
st.title("Painel de Avaliação Imobiliária (AVM)")

tipo = st.selectbox("Escolha a Tipologia", ["CASA", "APARTAMENTO", "LOTE"])
col1, col2 = st.columns(2)

# Inputs dinâmicos simplificados para o exemplo
area = col1.number_input("Área Privativa", value=100.0)
indice = col1.number_input("Índice Fiscal", value=1000.0)
terreno = col2.number_input("Área Terreno", value=200.0)
vagas = col2.number_input("Vagas", value=1)
andar = col1.number_input("Andar", value=0)
pdireito = col2.number_input("Pé Direito", value=2.8)

if st.button("Calcular"):
    params = [area, indice, terreno, vagas, andar, pdireito]
    resultado = executar_modelo(df, tipo, params)
    st.metric("Valor Estimado", f"R$ {resultado:,.2f}")
    
    pdf_bytes = gerar_pdf(resultado, tipo)
    st.download_button("Baixar PDF", pdf_bytes, "laudo.pdf")
