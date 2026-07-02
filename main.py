import streamlit as st
import pandas as pd
import numpy as np
import io
from sklearn.ensemble import RandomForestRegressor
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

st.set_page_config(page_title="AVM SaaS Pro", layout="wide")

# =====================================================================
# FUNÇÕES DE LÓGICA E PDF
# =====================================================================
def treinar_e_prever(df, tipologia, params):
    df_f = df[df['tipologia'] == tipologia].copy()
    features = ['area_privativa', 'indice_fiscal', 'area_terreno', 'vagas_garagem', 'andar', 'pe_direito']
    X = df_f[features]
    y = df_f['valor_total_declarado']
    
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    return model.predict(np.array([params]))[0]

def gerar_pdf(tenant, tipologia, valor, juridico):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [Paragraph(f"Laudo AVM - Cliente: {tenant}", styles['Title']), Spacer(1, 12)]
    
    data = [["Item", "Detalhe"], ["Tipologia", tipologia], ["Valor Estimado", f"R$ {valor:,.2f}"], ["Status Jurídico", juridico]]
    t = Table(data, colWidths=[200, 200])
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black)]))
    story.append(t)
    
    doc.build(story)
    return buffer.getvalue()

# =====================================================================
# INTERFACE PRINCIPAL
# =====================================================================
st.sidebar.header("⚙️ Configurações")
tenant = st.sidebar.selectbox("Cliente Institucional", ["Banco Alfa", "Imobiliária Beta"])

# Upload de arquivos (Suporta CSV e XLSX)
uploaded_file = st.sidebar.file_uploader("Upload Base de Dados", type=["csv", "xlsx"])

if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    st.sidebar.success("Base carregada com sucesso!")
else:
    # Base padrão para demonstração
    df = pd.DataFrame({
        'valor_total_declarado': [500000, 350000],
        'area_privativa': [100, 60],
        'indice_fiscal': [1000, 1500],
        'area_terreno': [200, 0],
        'vagas_garagem': [2, 1],
        'andar': [0, 3],
        'pe_direito': [2.8, 2.7],
        'tipologia': ['CASA', 'APARTAMENTO']
    })

# Abas Principais
tab1, tab2 = st.tabs(["📊 Avaliação AVM", "⚖️ Análise Jurídica"])

with tab1:
    st.subheader("Configuração da Avaliação")
    tipo = st.selectbox("Tipologia", ["CASA", "APARTAMENTO", "LOTE"])
    c1, c2 = st.columns(2)
    area = c1.number_input("Área Privativa (m²)", value=100.0)
    indice = c2.number_input("Índice Fiscal", value=1000.0)
    terreno = c1.number_input("Área Terreno (m²)", value=200.0)
    vagas = c2.number_input("Vagas", value=2)
    andar = c1.number_input("Andar", value=0)
    pdireito = c2.number_input("Pé Direito", value=2.8)
    
    if st.button("Executar Precificação"):
        params = [area, indice, terreno, vagas, andar, pdireito]
        resultado = treinar_e_prever(df, tipo, params)
        st.session_state.res = resultado
        st.session_state.tipo = tipo
        st.metric("Valor Estimado", f"R$ {resultado:,.2f}")

with tab2:
    st.subheader("Status Documental")
    doc_status = st.radio("Aprovar Matrícula?", ["APROVADO", "PENDENTE", "REPROVADO"])
    st.session_state.juridico = doc_status
    st.info(f"Status para {tenant}: {doc_status}")

# Download final
if 'res' in st.session_state:
    if st.button("Gerar Laudo PDF Final"):
        pdf = gerar_pdf(tenant, st.session_state.tipo, st.session_state.res, st.session_state.juridico)
        st.download_button("📥 Download Laudo PDF", pdf, "laudo_final.pdf")
