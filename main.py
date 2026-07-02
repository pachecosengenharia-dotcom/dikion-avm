import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io

st.set_page_config(page_title="Plataforma AVM SaaS - Multi-Tipologia", page_icon="🏢", layout="wide")

# =====================================================================
# GERADOR DE PDF (Estrutura original ajustada para colWidths)
# =====================================================================
def gerar_laudo_pdf_ia(tenant, tipologia, area, valores, r2, n_amostras, status_juridico, score_juridico):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Definição dos estilos
    title_style = ParagraphStyle('T1', parent=styles['Heading1'], fontSize=16)
    subtitle_style = ParagraphStyle('T2', parent=styles['Heading2'], fontSize=12)
    
    story.append(Paragraph(f"LAUDO CORE AVM ({tipologia})", title_style))
    story.append(Paragraph(f"Instituição: {tenant}", styles['Normal']))
    
    # TABELA 1 - Ajustada com colWidths (correção do erro original)
    t1_data = [["Tipologia do Bem", tipologia, "Dimensão", f"{area} m²"]]
    t1 = Table(t1_data, colWidths=[120, 100, 100, 100])
    t1.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.black)]))
    story.append(t1)
    
    # TABELA 2
    t2_data = [["Métrica", "Valor"], ["Mínimo", f"R$ {valores['v_min']:,.2f}"], ["Médio", f"R$ {valores['v_medio']:,.2f}"]]
    t2 = Table(t2_data, colWidths=[200, 200])
    t2.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.black)]))
    story.append(t2)
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# =====================================================================
# LÓGICA DE TREINO (Isolando a Tipologia CASA)
# =====================================================================
def executar_modelo_casa(df, area, indice, terreno, vagas, pe_direito):
    # Filtro estrito para CASA e limpeza de nomes
    df.columns = df.columns.str.lower().str.strip()
    df['tipologia'] = df['tipologia'].astype(str).str.upper().str.strip()
    df_casas = df[df['tipologia'] == 'CASA']
    
    features = ['area_privativa', 'indice_fiscal', 'area_terreno', 'vagas_garagem', 'andar', 'pe_direito']
    X = df_casas[features]
    y = df_casas['valor_total_declarado']
    
    model = RandomForestRegressor(n_estimators=100)
    model.fit(X, y)
    
    # Predição
    valor = model.predict([[area, indice, terreno, vagas, 0, pe_direito]])[0]
    return {"v_min": valor*0.95, "v_medio": valor, "v_max": valor*1.05}

# =====================================================================
# INTERFACE (Mantendo sua estrutura original)
# =====================================================================
st.title("🏢 Painel de Crédito e Controle Multi-Tenant")

# ... (Seu carregamento de arquivo e abas continuam aqui) ...

if st.button("🚀 Calcular AVM de Casa"):
    # Chamada específica para a lógica de casa
    valores = executar_modelo_casa(df_global, area_casa, indice_casa, terreno_casa, quartos_casa, 3.0)
    st.session_state.valores = valores
    st.success(f"Valor Médio: R$ {valores['v_medio']:,.2f}")
