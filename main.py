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

# =====================================================================
# SIMULADOR DE GERADOR DE BANCO DE DADOS INTEGRADO (Casas, Aptos, Lotes e Galpões)
# =====================================================================
@st.cache_data
def carregar_base_multitipologia_padrao():
    # Amostras simuladas estruturadas para alimentar as árvores de decisão
    dados = [
        # CASAS (total, unitario, area_principal, indice_fiscal, area_terreno, vagas, andar, pe_direito, tipologia)
        (450000, 6000, 75, 1200, 200, 2, 0, 3.0, "CASA"),
        (480000, 6153, 78, 1250, 220, 2, 0, 3.0, "CASA"),
        (510000, 6375, 80, 1300, 250, 2, 0, 3.2, "CASA"),
        (750000, 8823, 85, 3200, 360, 3, 0, 3.5, "CASA"),
        (820000, 8913, 92, 3300, 400, 3, 0, 3.5, "CASA"),
        # APARTAMENTOS
        (350000, 5833, 60, 1500, 0, 1, 3, 2.7, "APARTAMENTO"),
        (380000, 6129, 62, 1600, 0, 1, 5, 2.7, "APARTAMENTO"),
        (420000, 6461, 65, 1800, 0, 2, 8, 2.8, "APARTAMENTO"),
        (650000, 8666, 75, 3400, 0, 2, 12, 2.9, "APARTAMENTO"),
        (720000, 9000, 80, 3600, 0, 2, 15, 3.0, "APARTAMENTO"),
        # LOTES / TERRENOS
        (150000, 428, 350, 800, 350, 0, 0, 0, "LOTE"),
        (165000, 458, 360, 850, 360, 0, 0, 0, "LOTE"),
        (210000, 525, 400, 1100, 400, 0, 0, 0, "LOTE"),
        (450000, 900, 500, 2800, 500, 0, 0, 0, "LOTE"),
        # GALPÕES COMERCIAIS
        (1200000, 2400, 500, 900, 800, 0, 0, 6.0, "GALPAO"),
        (1500000, 2500, 600, 950, 900, 0, 0, 7.0, "GALPAO"),
        (2100000, 2625, 800, 1100, 1200, 0, 0, 8.0, "GALPAO")
    ]
    return pd.DataFrame(dados, columns=[
        'valor_total_declarado', 'valor_unitario_m2', 'area_privativa', 
        'indice_fiscal', 'area_terreno', 'vagas_garagem', 'andar', 'pe_direito', 'tipologia'
    ])

# =====================================================================
# GERADOR DE PDF CUSTOMIZADO PARA MULTI-TIPOLOGIA
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
    story.append(Paragraph("<b>Metodologia Core:</b> Algoritmo de Árvores de Decisão (Random Forest Regressor) | NBR 14653", text_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("1. Escopo de Avaliação Imobiliária", subtitle_style))
    t1 = Table([["Tipologia do Bem", tipologia, "Dimensão Principal", f"{area} m²"]], colWidths=)
    t1.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F7FAFC")), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")), ('PADDING', (0,0), (-1,-1), 5)]))
    story.append(t1)
    
    story.append(Paragraph("2. Resultados do Motor de Machine Learning", subtitle_style))
    t2 = Table([
        ["Métrica de Cobertura do Risco", "Valor Comercial Admissível"],
        ["Margem Mínima de Segurança (Garantia)", f"R$ {valores['v_min']:,.2f}"],
        ["Valor de Face Estimado (Média)", f"R$ {valores['v_medio']:,.2f}"],
        ["Limite de Mercado Máximo", f"R$ {valores['v_max']:,.2f}"]
    ], colWidths=)
    t2.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2B6CB0")), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")), ('PADDING', (0,0), (-1,-1), 5)]))
    story.append(t2)
    story.append(Spacer(1, 5))
    story.append(Paragraph(f"<b>Métricas de Redes de Decisão:</b> Precisão de Treino R² = {r2} | Amostras Saneadas = {n_amostras}.", text_style))
    
    story.append(Paragraph("3. Status da Esteira de Risco Jurídico", subtitle_style))
    t3 = Table([["Status Documental", "APROVADO" if status_juridico else "REPROVADO"], ["Grau de Risco Legal", score_juridico]], colWidths=)
    t3.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")), ('PADDING', (0,0), (-1,-1), 5), ('TEXTCOLOR', (1,0), (1,0), colors.HexColor("#38A169") if status_juridico else colors.HexColor("#E53E3E"))]))
    story.append(t3)
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# =====================================================================
# INTERFACE PRINCIPAL DO PAINEL SAAS
# =====================================================================
st.title("🏢 Painel de Crédito e Controle Multi-Tenant - Inteligência Artificial")
st.markdown("Gestão automatizada de risco imobiliário horizontal, vertical e industrial.")
st.hr()

st.sidebar.header("🔑 Assinatura e Faturamento")
tenant_selecionado = st.sidebar.selectbox("Cliente Institucional", ["001 - Banco Alfa S.A.", "002 - Imobiliária Local Ltda"])
plano_assinatura = "ENTERPRISE" if "Alfa" in tenant_selecionado else "STANDARD"

st.sidebar.markdown(f"**Plano Contratado:** {'🟢 ENTERPRISE' if plano_assinatura == 'ENTERPRISE' else '🟡 STANDARD'}")

# ABA DE ATRIBUTOS PRINCIPAIS
aba_avm, aba_juridico = st.tabs(["📊 1. Avaliação Estatística por IA (AVM)", "📜 2. Análise Jurídica da Matrícula"])

if 'status_juridico_global' not in st.session_state:
    st.session_state.status_juridico_global = True
if 'score_juridico_global' not in st.session_state:
    st.session_state.score_juridico_global = "PENDENTE"

with aba_avm:
    st.subheader("Configuração da Base e Modelagem")
    arquivo_planilha = st.file_uploader("Arraste aqui a planilha consolidada de imóveis do banco (.xlsx ou .csv)", type=["xlsx", "csv"])
    
    if arquivo_planilha is not None:
        try:
            if arquivo_planilha.name.endswith('.csv'):
                df_global = pd.read_csv(arquivo_planilha)
            else:
                df_global = pd.read_excel(arquivo_planilha)
            st.success(f"🟩 Base do banco '{arquivo_planilha.name}' carregada com sucesso!")
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {e}")
            df_global = carregar_base_multitipologia_padrao()
    else:
        st.info("💡 Modo de Demonstração: Utilizando a base de dados sintética de múltiplas tipologias.")
        df_global = carregar_base_multitipologia_padrao()

    st.write("---")
    st.markdown("#### 🎯 Selecione a Tipologia do Imóvel Alvo")
    
    # CRIAÇÃO DAS SUB-ABAS DE TIPOLOGIAS (Múltiplos formulários dinâmicos)
    sub_casa, sub_apto, sub_lote, sub_galpao = st.tabs(["🏡 Casas", "🏢 Apartamentos", "📐 Lotes / Terrenos", "🏭 Galpões Comerciais"])
    
    # Inicialização de variáveis de controle para o motor de IA
    tipologia_selecionada = "CASA"
    area_alvo = 75.0
    indice_fiscal_alvo = 100.0
    atributos_adicionais = {}
    
    with sub_casa:
        st.markdown("##### Parâmetros para Imóveis Horizontais")
        c1, c2, c3 = st.columns(3)
        area_casa = c1.number_input("Área Construída Privativa (m²)", min_value=10.0, value=120.0, key="c_a")
        terreno_casa = c1.number_input("Área Total do Terreno (m²)", min_value=10.0, value=360.0, key="c_t")
        quartos_casa = c2.slider("Quantidade de Quartos", 1, 6, 3, key="c_q")
        indice_casa = c2.number_input("Índice Fiscal da Quadra (Prefeitura)", min_value=0.0, value=1450.0, key="c_i")
        padrao_casa = c3.selectbox("Padrão Construtivo da Casa", ["Baixo", "Normal", "Alto"], index=1, key="c_p")
        if st.button("🚀 Calcular AVM de Casa"):
            tipologia_selecionada = "CASA"
            area_alvo = area_casa
            indice_fiscal_alvo = indice_casa
            atributos_adicionais = {"area_terreno": terreno_casa, "vagas_garagem": quartos_casa - 1, "andar": 0, "pe_direito": 3.0}
            st.session_state.executar_ia = True

    with sub_apto:
        st.markdown("##### Parâmetros para Edificações Verticais")
        a1, a2, a3 = st.columns(3)
        area_apto = a1.number_input("Área Privativa do Apartamento (m²)", min_value=10.0, value=75.0, key="ap_a")
        andar_apto = a1.number_input("Número do Andar / Pavimento", min_value=0, value=5, key="ap_an")
        vagas_apto = a2.slider("Vagas de Garagem no Subsolo", 0, 4, 1, key="ap_v")
        indice_apto = a2.number_input("Índice Fiscal da Quadra (Prefeitura)", min_value=0.0, value=2800.0, key="ap_i")
        padrao_apto = a3.selectbox("Padrão Construtivo do Prédio", ["Baixo", "Normal", "Alto"], index=1, key="ap_p")
        if st.button("🚀 Calcular AVM de Apartamento"):
            tipologia_selecionada = "APARTAMENTO"
            area_alvo = area_apto
            indice_fiscal_alvo = indice_apto
            atributos_adicionais = {"area_terreno": 0, "vagas_garagem": vagas_apto, "andar": andar_apto, "pe_direito": 2.8}
            st.session_state.executar_ia = True

    with sub_lote:
        st.markdown("##### Parâmetros para Solos Nus / Lotes")
        l1, l2 = st.columns(2)
        area_lote = l1.number_input("Área Total do Lote (m²)", min_value=10.0, value=450.0, key="lo_a")
