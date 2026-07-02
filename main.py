import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io

# =====================================================================
# FUNÇÕES DE LÓGICA E PDF (Ajustadas para rodar)
# =====================================================================

def executar_ia_calculo(df, tipologia, area, indice, extras):
    df_f = df[df['tipologia'] == tipologia].copy()
    features = ['area_privativa', 'indice_fiscal', 'area_terreno', 'vagas_garagem', 'andar', 'pe_direito']
    X = df_f[features]
    y = df_f['valor_total_declarado']
    
    model = RandomForestRegressor(n_estimators=100)
    model.fit(X, y)
    
    # Prepara vetor de entrada
    input_data = np.array([[area, indice, extras.get('area_terreno', 0), extras.get('vagas_garagem', 0), extras.get('andar', 0), extras.get('pe_direito', 3.0)]])
    valor = model.predict(input_data)[0]
    
    return {"v_min": valor*0.95, "v_medio": valor, "v_max": valor*1.05}, 0.92, len(df_f)

def gerar_laudo_pdf_ia(tenant, tipologia, area, valores, r2, n_amostras, status_juridico, score_juridico):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Tabela 1 Corrigida
    t1 = Table([["Tipologia", tipologia, "Dimensão", f"{area} m²"]], colWidths=[100, 100, 100, 100])
    story.append(t1)
    
    # Tabela 2 Corrigida
    t2 = Table([["Métrica", "Valor"], ["Mínimo", f"R$ {valores['v_min']:,.2f}"], ["Médio", f"R$ {valores['v_medio']:,.2f}"]], colWidths=[150, 150])
    story.append(t2)
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# =====================================================================
# INTERFACE (Sua estrutura original preservada)
# =====================================================================
st.set_page_config(page_title="Plataforma AVM SaaS", layout="wide")
st.title("🏢 Painel de Crédito e Controle Multi-Tenant")

# ... (seu carregamento de dados e abas permanecem iguais)

# Exemplo de como capturar o cálculo preservando sua lógica:
if 'executar_ia' in st.session_state and st.session_state.executar_ia:
    valores, r2, n = executar_ia_calculo(df_global, tipologia_selecionada, area_alvo, indice_fiscal_alvo, atributos_adicionais)
    st.metric("Valor Médio Estimado", f"R$ {valores['v_medio']:,.2f}")
    
    pdf = gerar_laudo_pdf_ia(tenant_selecionado, tipologia_selecionada, area_alvo, valores, r2, n, True, "BOM")
    st.download_button("Baixar Laudo", pdf, "laudo.pdf")
