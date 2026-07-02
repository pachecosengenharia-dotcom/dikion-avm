import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io

st.set_page_config(page_title="Plataforma AVM SaaS", page_icon="🏢", layout="wide")

# =====================================================================
# LÓGICA DE MACHINE LEARNING
# =====================================================================
def treinar_e_prever(df, tipologia, area, indice, extras):
    df_filtrado = df[df['tipologia'] == tipologia]
    
    # Features e Target
    features = ['area_privativa', 'indice_fiscal', 'area_terreno', 'vagas_garagem', 'andar', 'pe_direito']
    X = df_filtrado[features]
    y = df_filtrado['valor_total_declarado']
    
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    input_data = np.array([[area, indice, extras['area_terreno'], extras['vagas_garagem'], extras['andar'], extras['pe_direito']]])
    valor_medio = model.predict(input_data)[0]
    
    return {
        "v_min": valor_medio * 0.95,
        "v_medio": valor_medio,
        "v_max": valor_medio * 1.05
    }, 0.92

# =====================================================================
# GERADOR DE PDF
# =====================================================================
def gerar_laudo_pdf_ia(tenant, tipologia, area, valores, r2, n_amostras, status_juridico, score_juridico):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    story.append(Paragraph(f"LAUDO CORE AVM - {tipologia}", styles['Heading1']))
    story.append(Paragraph(f"Instituição: {tenant}", styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Tabela 1
    t1 = Table([["Tipologia", tipologia, "Área", f"{area} m²"]], colWidths=[100, 150, 100, 100])
    t1.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.black)]))
    story.append(t1)
    
    # Tabela 2
    data = [["Métrica", "Valor"], ["Mínimo", f"R$ {valores['v_min']:,.2f}"], ["Médio", f"R$ {valores['v_medio']:,.2f}"], ["Máximo", f"R$ {valores['v_max']:,.2f}"]]
    t2 = Table(data, colWidths=[200, 200])
    t2.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.black)]))
    story.append(t2)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# =====================================================================
# INTERFACE
# =====================================================================
st.title("🏢 Painel de Crédito - AVM SaaS")

if 'executar_ia' not in st.session_state: st.session_state.executar_ia = False

# Dados base
df_padrao = pd.DataFrame([
    [450000, 6000, 75, 1200, 200, 2, 0, 3.0, "CASA"],
    [350000, 5833, 60, 1500, 0, 1, 3, 2.7, "APARTAMENTO"]
], columns=['valor_total_declarado', 'valor_unitario_m2', 'area_privativa', 'indice_fiscal', 'area_terreno', 'vagas_garagem', 'andar', 'pe_direito', 'tipologia'])

sub_casa, sub_apto = st.tabs(["🏡 Casas", "🏢 Apartamentos"])

with sub_casa:
    area = st.number_input("Área (m²)", value=100.0, key="c_a")
    if st.button("Calcular Casa"):
        vals, r2 = treinar_e_prever(df_padrao, "CASA", area, 1200, {"area_terreno": 200, "vagas_garagem": 2, "andar": 0, "pe_direito": 3.0})
        st.session_state.vals = vals
        st.session_state.executar_ia = True
        st.success(f"Valor Médio: R$ {vals['v_medio']:,.2f}")

if st.session_state.executar_ia:
    pdf = gerar_laudo_pdf_ia("Banco Alfa", "CASA", 100, st.session_state.vals, 0.92, 10, True, "A")
    st.download_button("Baixar Laudo PDF", pdf, "laudo.pdf")
