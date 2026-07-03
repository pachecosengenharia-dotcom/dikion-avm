import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io
import matplotlib.pyplot as plt

st.set_page_config(page_title="Plataforma AVM SaaS - Engenharia", page_icon="🏢", layout="wide")

# ==========================================
# 1. FUNÇÕES SUPORTE E SEGURANÇA DE DADOS
# ==========================================

@st.cache_data
def carregar_base_multitipologia_padrao():
    """Garante amostras base para treinamento caso o usuário não envie uma planilha."""
    dados = []
    for i in range(8):
        dados.append((300000.0 + (i*50000), 5000.0, 100.0 + (i*15), 1100.0 + (i*50), 180.0 + (i*20), 2.0, 1.0, "CASA"))
        dados.append((250000.0 + (i*40000), 5500.0, 70.0 + (i*10), 1400.0 + (i*40), 2.0, 2.0, 1.0, "APARTAMENTO"))
        dados.append((150000.0 + (i*30000), 1000.0, 300.0 + (i*30), 2.0, 2026.0, 12.0, 1.0, "LOTE"))
        dados.append((900000.0 + (i*100000), 2200.0, 450.0 + (i*50), 950.0 + (i*1000), 6.0, 8.0, 2.0, "GALPAO"))
        
    colunas = ['valor_total_declarado', 'valor_unitario_m2', 'v1', 'v2', 'v3', 'v4', 'v5', 'tipologia']
    return pd.DataFrame(dados, columns=colunas)

def gerar_grafico_mercado(df_saneado, area_alvo, valor_estimado_m2):
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.scatter(df_saneado['v1'], df_saneado['valor_unitario_m2'], color='#2B6CB0', alpha=0.7, label='Amostras')
    ax.scatter(area_alvo, valor_estimado_m2, color='#E53E3E', marker='*', s=200, label='Avaliado')
    ax.set_title('Dispersão do Mercado (Área Principal vs Preço m²)', fontsize=10, fontweight='bold', color='#1A365D')
    ax.set_xlabel('Dimensão / Área Principal', fontsize=8)
    ax.set_ylabel('Preço Unitário (R$/m²)', fontsize=8)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(fontsize=7, loc='best')
    plt.tight_layout()
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png', dpi=200)
    img_buf.seek(0)
    plt.close(fig)
    return img_buf

def gerar_laudo_pdf_ia(tenant, tipologia, area, valores, model_stats, status_juridico, score_juridico, grafico_buf, equacao):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40.0, leftMargin=40.0, topMargin=40.0, bottomMargin=40.0)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('T1', parent=styles['Heading1'], fontSize=15, textColor=colors.HexColor("#1A365D"), spaceAfter=12.0)
    subtitle_style = ParagraphStyle('T2', parent=styles['Heading2'], fontSize=11, textColor=colors.HexColor("#2B6CB0"), spaceAfter=6.0)
    text_style = ParagraphStyle('T3', parent=styles['Normal'], fontSize=8.5, leading=12, spaceAfter=5.0)
    code_style = ParagraphStyle('T4', parent=styles['Normal'], fontSize=7.5, leading=10, textColor=colors.HexColor("#2D3748"), spaceAfter=5.0)
    
    story.append(Paragraph("LAUDO TÉCNICO DE ENGENHARIA DE AVALIAÇÕES POR INTELIGÊNCIA ARTIFICIAL", title_style))
    story.append(Paragraph(f"<b>Instituição Solicitante:</b> {tenant} | <b>Normativa Regulamentar:</b> ABNT NBR 14653", text_style))
    story.append(Spacer(1, 8.0))
    
    story.append(Paragraph("1. Escopo do Bem Avaliado", subtitle_style))
    t1 = Table([["Tipologia do Bem", tipologia, "Área / Dimensão Principal", f"{area:,.2f} m²"]], colWidths=(120.0, 120.0, 120.0, 120.0))
    t1.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F7FAFC")), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")), ('PADDING', (0,0), (-1,-1), 4.0)]))
    story.append(t1)
    story.append(Spacer(1, 8.0))
    
    story.append(Paragraph("2. Resultados do Motor Estatístico (AVM)", subtitle_style))
    t2 = Table([
        ["Métrica de Cobertura do Risco", "Valor Comercial Admissível"],
        ["Margem Mínima de Segurança (LTV Líquido)", f"R$ {valores['v_min']:,.2f}"],
        ["Valor de Face Estimado (Mediana do Mercado)", f"R$ {valores['v_medio']:,.2f}"],
        ["Limite Superior de Mercado", f"R$ {valores['v_max']:,.2f}"]
    ], colWidths=(240.0, 240.0))
    t2.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2B6CB0")), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")), ('PADDING', (0,0), (-1,-1), 4.0)]))
    story.append(t2)
    story.append(Spacer(1, 4.0))
    
    story.append(Paragraph(f"<b>Enquadramento Legal:</b> Grau de Fundamentação: <b>{model_stats['fundamentacao']}</b> | Grau de Precisão: <b>{model_stats['precisao']}</b> | Coeficiente R² = {model_stats['r2']}.", text_style))
    story.append(Spacer(1, 6.0))
    
    story.append(Paragraph("3. Comportamento Espacial e Fórmula Simbólica do Mercado", subtitle_style))
    story.append(Paragraph(f"<code>{equacao}</code>", code_style))
    story.append(Spacer(1, 4.0))
    story.append(Image(grafico_buf, width=340.0, height=170.0))
    story.append(Spacer(1, 8.0))
    
    story.append(Paragraph("4. Parecer da Esteira de Risco Jurídico", subtitle_style))
    status_texto = "APROVADO PARA COLATERAL" if status_juridico else "REPROVADO / RESTRITO"
    t3 = Table([["Status de Conformidade", status_texto], ["Grau de Vulnerabilidade Legal", score_juridico]], colWidths=(240.0, 240.0))
    t3.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")), ('PADDING', (0,0), (-1,-1), 4.0), ('TEXTCOLOR', (1,0), (1,0), colors.HexColor("#38A169") if status_juridico else colors.HexColor("#E53E3E"))]))
    story.append(t3)
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# ==========================================
# 2. INTERFACE GRÁFICA PRINCIPAL (STREAMLIT)
# ==========================================

st.title("🏢 Painel Avançado de Engenharia Imobiliária SaaS")
st.markdown("Gestão automatizada e homologação de risco de garantias por Machine Learning (Random Forest).")
st.divider()

st.sidebar.header("🔑 Assinatura e Faturamento")
tenant_selecionado = st.sidebar.selectbox("Cliente Institucional", ["001 - Banco Alfa S.A.", "002 - Imobiliária Local Ltda"])
st.sidebar.markdown("**Plano Ativo:** 🟢 ENTERPRISE")

aba_avm, aba_juridico = st.tabs(["📊 1. Avaliação Estatística por IA (AVM)", "📜 2. Análise Jurídica de Risco"])

# Inicialização de estados
if 'status_juridico_global' not in st.session_state: st.session_state.status_juridico_global = True
if 'score_juridico_global' not in st.session_state: st.session_state.score_juridico_global = "RISCO BAIXO"
if 'memorizar_calculo' not in st.session_state: st.session_state.memorizar_calculo = None

with aba_avm:
    # ----------------------------------------------------
    # POSICIONAMENTO CRÍTICO E FIXO NO TOPO DA TELA
    # ----------------------------------------------------
    tipologia_sel = st.selectbox("🎯 Selecione a Tipologia do Imóvel Alvo:", ["CASA", "APARTAMENTO", "LOTE", "GALPAO"])
    
    # BOTÃO TOTALMENTE DESTACADO E SEM ANINHAMENTO CONDICIONAL
    botao_calcular = st.button("🚀 CALCULAR AVALIAÇÃO IMOBILIÁRIA", use_container_width=True)
    
    st.write("---")
    arquivo_planilha = st.file_uploader("Arraste aqui a planilha de imóveis comparáveis (.xlsx ou .csv) [Opcional]", type=["xlsx", "csv"])
    st.write("---")
    
    st.markdown("##### 📌 Atributos Específicos do Imóvel (Exatamente 5 Variáveis)")
    col1, col2, col3 = st.columns(3)
    
    map_acabamento = {"Baixo": 1.0, "Normal": 2.0, "Alto": 3.0}
    map_conservacao = {"Regular": 1.0, "Bom": 2.0, "Ótimo": 3.0}
    map_topografia = {"Aclive": 1.0, "Plano": 2.0, "Declive": 3.0}
    map_origem = {"Imobiliária": 1.0, "Proprietário": 2.0, "Banco": 3.0}
    
    if tipologia_sel == "CASA":
        v1 = col1.number_input("Área Privativa (m²)", min_value=10.0, value=120.0, key="casa_v1")
        v2 = col2.number_input("Área do Terreno (m²)", min_value=10.0, value=200.0, key="casa_v2")
        v3 = col3.number_input("Índice Fiscal da Quadra", min_value=0.0, value=1200.0, key="casa_v3")
        v4_txt = col1.selectbox("Padrão de Acabamento", list(map_acabamento.keys()), index=1, key="casa_v4")
        v5 = col2.number_input("Idade Aparente (Anos)", min_value=0.0, value=5.0, key="casa_v5")
        v4 = map_acabamento[v4_txt]
        features_lista = ['area_privativa', 'area_terreno', 'indice_fiscal', 'padrao_acabamento', 'idade_aparente']

    elif tipologia_sel == "APARTAMENTO":
        v1 = col1.number_input("Área Privativa (m²)", min_value=10.0, value=80.0, key="ap_v1")
        v2 = col2.number_input("Índice Fiscal da Quadra", min_value=0.0, value=1500.0, key="ap_v2")
        v3 = col3.number_input("Vagas de Garagem (Unidades)", min_value=0.0, value=1.0, key="ap_v3")
        v4_txt = col1.selectbox("Estado de Conservação", list(map_conservacao.keys()), index=1, key="ap_v4")
        v5_txt = col2.selectbox("Padrão de Acabamento", list(map_acabamento.keys()), index=1, key="ap_v5")
        v4 = map_conservacao[v4_txt]
        v5 = map_acabamento[v5_txt]
        features_lista = ['area_privativa', 'indice_fiscal', 'vagas_garagem', 'estado_conservacao', 'padrao_acabamento']

    elif tipologia_sel == "LOTE":
        v1 = col1.number_input("Área do Terreno (m²)", min_value=10.0, value=360.0, key="lote_v1")
        v2_txt = col2.selectbox("Topografia", list(map_topografia.keys()), index=1, key="lote_v2")
        v3 = col3.number_input("Data do Evento (Ano Coleta)", min_value=2000.0, value=2026.0, key="lote_v3")
        v4 = col1.number_input("Testada / Frente (m)", min_value=0.0, value=12.0, key="lote_v4")
        v5_txt = col2.selectbox("Origem da Informação", list(map_origem.keys()), index=0, key="lote_v5")
        v2 = map_topografia[v2_txt]
        v5 = map_origem[v5_txt]
        features_lista = ['area_terreno', 'topografia', 'data_evento', 'frente', 'origem_informacao']

