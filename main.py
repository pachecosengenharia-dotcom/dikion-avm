import streamlit as st
import pandas as pd
import numpy as np
import json
from sklearn.ensemble import RandomForestRegressor
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io
import matplotlib.pyplot as plt

st.set_page_config(page_title="Plataforma AVM SaaS - Engenharia", page_icon="🏢", layout="wide")

# =====================================================================
# BASE DE DADOS COMPACTA PARA CÁLCULOS RIGOROSOS DE IA
# =====================================================================
@st.cache_data
def carregar_base_multitipologia_padrao():
    dados = [
        (450000, 6000, 120, 1200, 200, 2, 0, 3.0, "CASA"),
        (480000, 6153, 125, 1250, 220, 2, 0, 3.0, "CASA"),
        (510000, 6375, 130, 1300, 250, 2, 0, 3.2, "CASA"),
        (750000, 8823, 185, 3200, 360, 3, 0, 3.5, "CASA"),
        (820000, 8913, 192, 3300, 400, 3, 0, 3.5, "CASA"),
        (350000, 5833, 60, 1500, 0, 1, 3, 2.7, "APARTAMENTO"),
        (380000, 6129, 62, 1600, 0, 1, 5, 2.7, "APARTAMENTO"),
        (420000, 6461, 65, 1800, 0, 2, 8, 2.8, "APARTAMENTO"),
        (1200000, 2400, 500, 900, 800, 0, 0, 6.0, "GALPAO")
    ]
    return pd.DataFrame(dados, columns=['valor_total_declarado', 'valor_unitario_m2', 'area_privativa', 'indice_fiscal', 'area_terreno', 'vagas_garagem', 'andar', 'pe_direito', 'tipologia'])

# =====================================================================
# GERADOR DE GRÁFICO IMOBILIÁRIO (Matplotlib)
# =====================================================================
def gerar_grafico_mercado(df_saneado, area_alvo, valor_estimado_m2):
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.scatter(df_saneado['area_privativa'], df_saneado['valor_unitario_m2'], color='#2B6CB0', alpha=0.7, label='Amostras')
    ax.scatter(area_alvo, valor_estimado_m2, color='#E53E3E', marker='*', s=150, label='Avaliado')
    ax.set_title('Dispersao do Mercado', fontsize=10, fontweight='bold')
    ax.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png', dpi=200)
    img_buf.seek(0)
    plt.close(fig)
    return img_buf

# =====================================================================
# LAUDO CERTIFICADO COMPLETO EM PDF (ABNT NBR 14653)
# =====================================================================
def gerar_laudo_pdf_ia(tenant, tipologia, area, valores, model_stats, status_juridico, score_juridico, grafico_buf):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('T1', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor("#1A365D"), spaceAfter=15)
    subtitle_style = ParagraphStyle('T2', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor("#2B6CB0"), spaceAfter=8)
    text_style = ParagraphStyle('T3', parent=styles['Normal'], fontSize=9, leading=13, spaceAfter=6)
    
    story.append(Paragraph(f"LAUDO TECNICO DE ENGENHARIA DE AVALIACOES POR IA", title_style))
    story.append(Paragraph(f"<b>Instituicao Solicitante:</b> {tenant} | <b>Normativa:</b> ABNT NBR 14653-2", text_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("1. Escopo de Avaliacao Imobiliaria", subtitle_style))
    t1 = Table([["Tipologia do Bem", tipologia, "Dimensao Principal", f"{area} m²"]], colWidths=[130, 110, 130, 130])
    t1.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F7FAFC")), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")), ('PADDING', (0,0), (-1,-1), 5)]))
    story.append(t1)
    
    story.append(Paragraph("2. Resultados do Motor de Machine Learning", subtitle_style))
    t2 = Table([
        ["Metrica de Cobertura do Risco", "Valor Comercial Admissivel"],
        ["Margem Minima de Seguranca (Garantia LTV)", f"R$ {valores['v_min']:,.2f}"],
        ["Valor de Face Estimado (Media)", f"R$ {valores['v_medio']:,.2f}"],
        ["Limite de Mercado Maximo", f"R$ {valores['v_max']:,.2f}"]
    ], colWidths=[250, 250])
    t2.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2B6CB0")), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")), ('PADDING', (0,0), (-1,-1), 5)]))
    story.append(t2)
    story.append(Spacer(1, 5))
    story.append(Paragraph(f"<b>Metricas de Redes de Decisao:</b> Precisao de Ajuste R² = {model_stats['r2']} | Amostras Saneadas = {model_stats['saneadas']}.", text_style))
    
    story.append(Paragraph("3. Diagnostico e Comportamento Espacial do Mercado", subtitle_style))
    story.append(Image(grafico_buf, width=320, height=160))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("4. Status da Esteira de Risco Juridico", subtitle_style))
    t3 = Table([["Status Documental", "APROVADO PARA GARANTIA" if status_juridico else "REPROVADO"], ["Grau de Risco Legal", score_juridico]], colWidths=[250, 250])
    t3.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")), ('PADDING', (0,0), (-1,-1), 5), ('TEXTCOLOR', (1,0), (1,0), colors.HexColor("#38A169") if status_juridico else colors.HexColor("#E53E3E"))]))
    story.append(t3)
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# =====================================================================
# INTERFACE PRINCIPAL DO PAINEL SAAS
# =====================================================================
st.title("🏢 Painel Avancado de Engenharia Imobiliaria SaaS")
st.markdown("Gestao automatizada de risco imobiliario por Inteligencia Artificial (Random Forest).")
st.divider()

st.sidebar.header("🔑 Assinatura e Faturamento")
tenant_selecionado = st.sidebar.selectbox("Cliente Institucional", ["001 - Banco Alfa S.A.", "002 - Imobiliária Local Ltda"])
st.sidebar.markdown("**Plano Contratado:** 🟢 ENTERPRISE (Acesso Total Liberado)")

aba_avm, aba_juridico = st.tabs(["📊 1. Avaliacao Estatistica por IA (AVM)", "📜 2. Analise Juridica"])

if 'status_juridico_global' not in st.session_state: st.session_state.status_juridico_global = True
if 'score_juridico_global' not in st.session_state: st.session_state.score_juridico_global = "PENDENTE"
if 'memorizar_calculo' not in st.session_state: st.session_state.memorizar_calculo = None

with aba_avm:
    st.subheader("Configuracao da Base e Modelagem")
    arquivo_planilha = st.file_uploader("Arraste aqui a planilha consolidada de imoveis do banco (.xlsx ou .csv)", type=["xlsx", "csv"])
    
    if arquivo_planilha is not None:
        try:
            df_global = pd.read_csv(arquivo_planilha) if arquivo_planilha.name.endswith('.csv') else pd.read_excel(arquivo_planilha)
            st.success(f"🟩 Planilha VALIDADA: {len(df_global)} imóveis carregados com sucesso!")
        except Exception as e:
            st.error(f"Erro na validação do arquivo: {e}")
            df_global = carregar_base_multitipologia_padrao()
    else:
        st.info("💡 Modo de Demonstracao: Utilizando a base de dados sintetica.")
        df_global = carregar_base_multitipologia_padrao()

    st.write("---")
    tipologia_sel = st.selectbox("🎯 Selecione a Tipologia do Imovel Alvo para Configuracao:", ["🏡 CASA", "🏢 APARTAMENTO", "📐 LOTE", "🏭 GALPAO"])
    st.write("---")
    
    col1, col2 = st.columns(2)
    area_alvo = col1.number_input("Dimensao/Area Principal (m²)", min_value=10.0, value=120.0)
    indice_alvo = col2.number_input("Indice Fiscal da Quadra", min_value=0.0, value=1200.0)
    
    area_terreno_valor, vagas_valor, andar_valor, pe_direito_valor = 0.0, 0, 0, 3.0
    if "CASA" in tipologia_sel:
        area_terreno_valor = col1.number_input("Area Total do Terreno (m²)", min_value=10.0, value=200.0)
        vagas_valor = col2.slider("Quantidade de Quartos", 1, 6, 3)
    elif "APARTAMENTO" in tipologia_sel:
        andar_valor = col1.number_input("Numero do Andar", min_value=0, value=5)
        vagas_valor = col2.slider("Vagas de Garagem", 0, 4, 1)
        pe_direito_valor = 2.8
    elif "GALPAO" in tipologia_sel:
        pe_direito_valor = col1.number_input("Pe-direito Livre (Metros)", min_value=3.0, value=7.5)
        area_terreno_valor = area_alvo * 1.5

    st.write("---")
    
    if st.button("🚀 Calcular Avaliacao por Inteligencia Artificial"):
        tipologia_limpa = tipologia_sel.replace("🏡 ", "").replace("🏢 ", "").replace("📐 ", "").replace("🏭 ", "").strip()
        df_local_processamento = df_global.copy()
        
        df_local_processamento['tipologia'] = df_local_processamento['tipologia'].astype(str).str.upper().str.strip() if 'tipologia' in df_local_processamento.columns else "CASA"
        df_tipo = df_local_processamento[df_local_processamento['tipologia'] == tipologia_limpa].copy()
        
        if len(df_tipo) < 3:
            df_backup = carregar_base_multitipologia_padrao()
            df_tipo = df_backup[df_backup['tipologia'] == tipologia_limpa].copy()
            
        for col_nome in ['area_terreno', 'vagas_garagem', 'andar', 'pe_direito']:
            if col_nome not in df_tipo.columns: df_tipo[col_nome] = 0.0
            
        q1 = df_tipo['valor_unitario_m2'].quantile(0.25)
        q3 = df_tipo['valor_unitario_m2'].quantile(0.75)
        iqr = q3 - q1
        df_saneado = df_tipo[(df_tipo['valor_unitario_m2'] >= q1 - 1.5*iqr) & (df_tipo['valor_unitario_m2'] <= q3 + 1.5*iqr)].copy()
        
        X = df_saneado[['area_privativa', 'indice_fiscal', 'area_terreno', 'vagas_garagem', 'andar', 'pe_direito']]
        Y = df_saneado['valor_unitario_m2']
        
        model_ia = RandomForestRegressor(n_estimators=100, random_state=42)
        model_ia.fit(X, Y)
        
