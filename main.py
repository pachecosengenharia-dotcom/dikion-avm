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

st.set_page_config(page_title="AVM SaaS Pro", layout="wide")

# =====================================================================
# FUNÇÕES DE LÓGICA E PDF
# =====================================================================
def treinar_e_prever(df, tipologia, params):
    df['tipologia'] = df['tipologia'].astype(str).str.upper().str.strip()
    df_f = df[df['tipologia'] == tipologia].copy()
    
    if len(df_f) < 2: return None, None, "Dados insuficientes."
    
    features = ['area_privativa', 'indice_fiscal', 'area_terreno', 'vagas_garagem', 'andar', 'pe_direito']
    X = df_f[features]; y = df_f['valor_total_declarado']
    
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    imp = pd.DataFrame({'feature': features, 'importancia': model.feature_importances_}).sort_values('importancia')
    valor = model.predict(np.array([params]))[0]
    return valor, imp, None

def gerar_pdf(tenant, tipologia, valor, juridico, img_buffer):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [Paragraph(f"Laudo AVM - {tenant}", styles['Title']), Spacer(1, 12)]
    
    data = [["Item", "Detalhe"], ["Tipologia", tipologia], ["Valor Estimado", f"R$ {valor:,.2f}"], ["Status", juridico]]
    t = Table(data, colWidths=[200, 200])
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black)]))
    story.append(t); story.append(Spacer(1, 20))
    
    # Inserção do Gráfico
    story.append(Paragraph("Importância das Variáveis:", styles['Heading2']))
    story.append(Image(img_buffer, width=400, height=200))
    
    doc.build(story)
    return buffer.getvalue()

# =====================================================================
# INTERFACE
# =====================================================================
st.title("📊 AVM SaaS - Avaliação Inteligente")
# [Carga de Dados omitida para brevidade - utilize o mesmo carregador anterior]
# ...

if st.button("Executar Precificação"):
    resultado, imp_df, erro = treinar_e_prever(df, tipo, params)
    if not erro:
        st.metric("Valor Estimado", f"R$ {resultado:,.2f}")
        
        # Gerar Gráfico no Buffer
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.barh(imp_df['feature'], imp_df['importancia'], color='#2B6CB0')
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png'); img_buffer.seek(0)
        st.pyplot(fig)
        
        st.session_state.res = resultado; st.session_state.tipo = tipo; st.session_state.img = img_buffer

if 'res' in st.session_state and st.button("Gerar PDF"):
    pdf = gerar_pdf(tenant, st.session_state.tipo, st.session_state.res, "APROVADO", st.session_state.img)
    st.download_button("📥 Baixar Laudo com Gráfico", pdf, "laudo_final.pdf")
