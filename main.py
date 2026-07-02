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
# FUNÇÕES DE LÓGICA E PDF
# =====================================================================
def executar_motor_ia(df_global, tipologia, area, indice_fiscal, atributos):
    df_tipo = df_global[df_global['tipologia'] == tipologia].copy()
    features = ['area_privativa', 'indice_fiscal', 'area_terreno', 'vagas_garagem', 'andar', 'pe_direito']
    
    if len(df_tipo) < 3:
        return None, "Amostras insuficientes (mínimo 3) para esta tipologia."

    X = df_tipo[features]
    y = df_tipo['valor_total_declarado']

    modelo = RandomForestRegressor(n_estimators=200, random_state=42)
    modelo.fit(X, y)
    r2 = round(modelo.score(X, y), 4)

    alvo = pd.DataFrame([{
        'area_privativa': area,
        'indice_fiscal': indice_fiscal,
        'area_terreno': atributos.get('area_terreno', 0),
        'vagas_garagem': atributos.get('vagas_garagem', 0),
        'andar': atributos.get('andar', 0),
        'pe_direito': atributos.get('pe_direito', 0),
    }])

    previsoes = np.array([arvore.predict(alvo.values)[0] for arvore in modelo.estimators_])
    return {'valores': {'v_min': np.percentile(previsoes, 15), 'v_medio': np.mean(previsoes), 'v_max': np.percentile(previsoes, 85)}, 'r2': r2, 'n_amostras': len(df_tipo)}, None

def gerar_laudo_pdf_ia(tenant, tipologia, area, valores, r2, n_amostras, status_juridico, score_juridico):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    story.append(Paragraph(f"LAUDO AVM - {tipologia}", styles['Heading1']))
    story.append(Paragraph(f"Valor Estimado: R$ {valores['v_medio']:,.2f}", styles['Normal']))
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# =====================================================================
# INTERFACE PRINCIPAL
# =====================================================================
st.title("🏢 Painel de Crédito - AVM")

if 'df' not in st.session_state:
    st.session_state.df = None

arquivo = st.file_uploader("Upload CSV ou Excel", type=["csv", "xlsx"])
if arquivo:
    st.session_state.df = pd.read_csv(arquivo) if arquivo.name.endswith('.csv') else pd.read_excel(arquivo)
    # Limpeza básica de colunas
    st.session_state.df.columns = [c.lower().strip().replace(" ", "_") for c in st.session_state.df.columns]
    st.success("Dados carregados!")

if st.session_state.df is not None:
    aba_avm, aba_jur = st.tabs(["AVM", "Jurídico"])
    
    with aba_avm:
        tipo = st.selectbox("Tipologia", ["CASA", "APARTAMENTO", "LOTE", "GALPAO"])
        area = st.number_input("Área", value=100.0)
        
        if st.button("Calcular"):
            res, erro = executar_motor_ia(st.session_state.df, tipo, area, 1000, {"area_terreno": 200, "vagas_garagem": 1, "andar": 0, "pe_direito": 3.0})
            if erro: st.error(erro)
            else: 
                st.write(f"Valor Médio: R$ {res['valores']['v_medio']:,.2f}")
                st.download_button("Baixar Laudo", gerar_laudo_pdf_ia("Banco", tipo, area, res['valores'], res['r2'], res['n_amostras'], True, "Baixo"), "laudo.pdf")
