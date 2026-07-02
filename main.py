import streamlit as st
import pandas as pd
import numpy as np
import json
from sklearn.ensemble import RandomForestRegressor
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io

st.set_page_config(page_title="Plataforma AVM SaaS - Multi-Tipologia", page_icon="🏢", layout="wide")

# ... (Sua função carregar_base_multitipologia_padrao permanece idêntica) ...
def carregar_base_multitipologia_padrao():
    dados = [
        (450000, 6000, 75, 1200, 200, 2, 0, 3.0, "CASA"),
        (480000, 6153, 78, 1250, 220, 2, 0, 3.0, "CASA"),
        (510000, 6375, 80, 1300, 250, 2, 0, 3.2, "CASA"),
        (350000, 5833, 60, 1500, 0, 1, 3, 2.7, "APARTAMENTO"),
        (150000, 428, 350, 800, 350, 0, 0, 0, "LOTE"),
        (1200000, 2400, 500, 900, 800, 0, 0, 6.0, "GALPAO")
    ]
    return pd.DataFrame(dados, columns=['valor_total_declarado', 'valor_unitario_m2', 'area_privativa', 'indice_fiscal', 'area_terreno', 'vagas_garagem', 'andar', 'pe_direito', 'tipologia'])

# =====================================================================
# GERADOR DE PDF CUSTOMIZADO (Correção de colWidths)
# =====================================================================
def gerar_laudo_pdf_ia(tenant, tipologia, area, valores, r2, n_amostras, status_juridico, score_juridico):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('T1', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor("#1A365D"), spaceAfter=15)
    subtitle_style = ParagraphStyle('T2', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor("#2B6CB0"), spaceAfter=8)
    text_style = ParagraphStyle('T3', parent=styles['Normal'], fontSize=9, leading=13, spaceAfter=6)
    
    story.append(Paragraph(f"LAUDO CORE AVM - INTELIGÊNCIA ARTIFICIAL ({tipologia})", title_style))
    story.append(Paragraph(f"<b>Instituição Solicitante:</b> {tenant}", text_style))
    
    # CORREÇÃO: Adicionado colWidths para evitar erro de renderização
    story.append(Paragraph("1. Escopo de Avaliação Imobiliária", subtitle_style))
    t1 = Table([["Tipologia do Bem", tipologia, "Dimensão Principal", f"{area} m²"]], colWidths=[120, 100, 120, 100])
    t1.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F7FAFC")), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")), ('PADDING', (0,0), (-1,-1), 5)]))
    story.append(t1)
    
    story.append(Paragraph("2. Resultados do Motor de Machine Learning", subtitle_style))
    # CORREÇÃO: Adicionado colWidths
    t2 = Table([
        ["Métrica de Cobertura", "Valor"],
        ["Margem Segurança", f"R$ {valores['v_min']:,.2f}"],
        ["Valor Estimado", f"R$ {valores['v_medio']:,.2f}"]
    ], colWidths=[200, 200])
    t2.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.black)]))
    story.append(t2)
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# ... (O restante da sua interface permanece idêntica)
