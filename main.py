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

# Base de dados sintética robusta de backup (Caso o upload falhe)
@st.cache_data
def carregar_base_multitipologia_padrao():
    dados = [
        (450000.0, 120.0, 200.0, 1200.0, 2.0, 5.0, "CASA"),
        (480000.0, 125.0, 220.0, 1250.0, 2.0, 6.0, "CASA"),
        (510000.0, 130.0, 250.0, 1300.0, 3.0, 4.0, "CASA"),
        (350000.0, 60.0, 1500.0, 1.0, 2.0, 2.0, "APARTAMENTO"),
        (380000.0, 62.0, 1600.0, 1.0, 2.0, 2.0, "APARTAMENTO"),
        (420000.0, 65.0, 1800.0, 2.0, 3.0, 3.0, "APARTAMENTO"),
        (250000.0, 360.0, 2.0, 2026.0, 12.0, 1.0, "LOTE"),
        (1200000.0, 500.0, 1000.0, 900.0, 2.0, 10.0, "GALPAO")
    ]
    return pd.DataFrame(dados, columns=['valor_total_declarado', 'v1', 'v2', 'v3', 'v4', 'v5', 'tipologia'])

def gerar_grafico_mercado(df_saneado, area_alvo, valor_estimado_m2):
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.scatter(df_saneado['v1'], df_saneado['valor_total_declarado'] / df_saneado['v1'], color='#2B6CB0', alpha=0.7, label='Amostras')
    ax.scatter(area_alvo, valor_estimado_m2, color='#E53E3E', marker='*', s=150, label='Avaliado')
    ax.set_title('Dispersao do Mercado (Area vs Preco m²)', fontsize=10, fontweight='bold', color='#1A365D')
    ax.set_xlabel('Dimensao Principal', fontsize=8)
    ax.set_ylabel('Preco Unitario (R$/m²)', fontsize=8)
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
    title_style = ParagraphStyle('T1', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor("#1A365D"), spaceAfter=15.0)
    subtitle_style = ParagraphStyle('T2', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor("#2B6CB0"), spaceAfter=8.0)
    text_style = ParagraphStyle('T3', parent=styles['Normal'], fontSize=9, leading=13, spaceAfter=6.0)
    
    story.append(Paragraph("LAUDO TECNICO DE ENGENHARIA DE AVALIACOES POR IA", title_style))
    story.append(Paragraph(f"<b>Instituicao Solicitante:</b> {tenant} | <b>Normativa:</b> ABNT NBR 14653", text_style))
    story.append(Spacer(1, 10.0))
    
    story.append(Paragraph("1. Escopo de Avaliacao Imobiliaria", subtitle_style))
    t1 = Table([["Tipologia do Bem", tipologia, "Dimensao Principal", f"{area} m²"]], colWidths=(130.0, 110.0, 130.0, 110.0))
    t1.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F7FAFC")), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")), ('PADDING', (0,0), (-1,-1), 5.0)]))
    story.append(t1)
    story.append(Spacer(1, 10.0))
    
    story.append(Paragraph("2. Resultados do Motor de Machine Learning & NBR 14653", subtitle_style))
    t2 = Table([
        ["Metrica de Cobertura do Risco", "Valor Comercial Admissivel"],
        ["Margem Minima de Seguranca (Garantia LTV)", f"R$ {valores['v_min']:,.2f}"],
        ["Valor de Face Estimado (Media)", f"R$ {valores['v_medio']:,.2f}"],
        ["Limite de Mercado Maximo", f"R$ {valores['v_max']:,.2f}"],
        ["Grau de Fundamentacao", model_stats['fundamentacao']],
        ["Grau de Precisao", model_stats['precisao']]
    ], colWidths=(240.0, 240.0))
    t2.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2B6CB0")), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")), ('PADDING', (0,0), (-1,-1), 5.0)]))
    story.append(t2)
    story.append(Spacer(1, 5.0))
    story.append(Paragraph(f"<b>Equacao Estimada do Mercado:</b> {equacao}", text_style))
    story.append(Spacer(1, 10.0))
    
    story.append(Paragraph("3. Diagnostico e Comportamento Espacial do Mercado", subtitle_style))
    story.append(Image(grafico_buf, width=340.0, height=170.0))
    story.append(Spacer(1, 10.0))
    
    story.append(Paragraph("4. Status da Esteira de Risco Juridico", subtitle_style))
    t3 = Table([["Status Documental", "APROVADO PARA GARANTIA" if status_juridico else "REPROVADO"], ["Grau de Risco Legal", score_juridico]], colWidths=(240.0, 240.0))
    t3.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")), ('PADDING', (0,0), (-1,-1), 5.0), ('TEXTCOLOR', (1,0), (1,0), colors.HexColor("#38A169") if status_juridico else colors.HexColor("#E53E3E"))]))
    story.append(t3)
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# Interface Streamlit
st.title("🏢 Painel Avancado de Engenharia Imobiliaria SaaS")
st.markdown("Gestao automatizada de risco imobiliario por Inteligencia Artificial conforme NBR 14653.")
st.divider()

st.sidebar.header("🔑 Assinatura e Faturamento")
tenant_selecionado = st.sidebar.selectbox("Cliente Institucional", ["001 - Banco Alfa S.A.", "002 - Imobiliária Local Ltda"])
st.sidebar.markdown("**Plano Contratado:** 🟢 ENTERPRISE (Acesso Total Liberado)")

aba_avm, aba_juridico = st.tabs(["📊 1. Avaliacao Estatistica por IA (AVM)", "📜 2. Analise Juridica"])

if 'status_juridico_global' not in st.session_state: st.session_state.status_juridico_global = True
if 'score_juridico_global' not in st.session_state: st.session_state.score_juridico_global = "RISCO BAIXO"
if 'memorizar_calculo' not in st.session_state: st.session_state.memorizar_calculo = None

with aba_avm:
    st.subheader("Configuracao da Base e Modelagem")
    arquivo_planilha = st.file_uploader("Arraste aqui a planilha consolidada de imoveis do banco (.xlsx ou .csv)", type=["xlsx", "csv"])
    
    if arquivo_planilha is not None:
        try:
            df_global = pd.read_csv(arquivo_planilha) if arquivo_planilha.name.endswith('.csv') else pd.read_excel(arquivo_planilha)
            st.success(f"🟩 Planilha VALIDADA: {len(df_global)} imóveis lidos com sucesso!")
        except Exception as e:
            st.error(f"Erro na leitura da planilha: {e}. Carregando base simulada...")
            df_global = carregar_base_multitipologia_padrao()
    else:
        st.info("💡 Modo de Demonstracao: Utilizando a base de dados sintetica.")
        df_global = carregar_base_multitipologia_padrao()

    st.write("---")
    tipologia_sel = st.selectbox("🎯 Selecione a Tipologia do Imovel Alvo para Configuracao:", ["CASA", "APARTAMENTO", "LOTE", "GALPAO"])
    st.write("---")
    
    col1, col2, col3 = st.columns(3)
    
    map_acabamento = {"Baixo": 1.0, "Normal": 2.0, "Alto": 3.0}
    map_conservacao = {"Regular": 1.0, "Bom": 2.0, "Ótimo": 3.0}
    map_topografia = {"Aclive": 1.0, "Plano": 2.0, "Declive": 3.0}
    map_origem = {"Imobiliária": 1.0, "Proprietário": 2.0, "Banco": 3.0}

    # Bloco condicional corrigido e alinhado (Sempre 5 variáveis por tipologia)
    if tipologia_sel == "CASA":
        v1 = col1.number_input("Área Privativa (m²)", min_value=10.0, value=120.0)
        v2 = col2.number_input("Área do Terreno (m²)", min_value=10.0, value=200.0)
        v3 = col3.number_input("Índice Fiscal da Quadra", min_value=0.0, value=1200.0)
        v4_texto = col1.selectbox("Padrão de Acabamento", list(map_acabamento.keys()), index=1)
        v5 = col2.number_input("Idade Aparente (Anos)", min_value=0.0, value=5.0)
        v4 = map_acabamento[v4_texto]
        features_lista = ['area_privativa', 'area_terreno', 'indice_fiscal', 'padrao_acabamento', 'idade_aparente']

    elif tipologia_sel == "APARTAMENTO":
        v1 = col1.number_input("Área Privativa (m²)", min_value=10.0, value=80.0)
        v2 = col2.number_input("Índice Fiscal da Quadra", min_value=0.0, value=1500.0)
        v3 = col3.number_input("Vagas de Garagem", min_value=0.0, value=1.0)
        v4_texto = col1.selectbox("Estado de Conservação", list(map_conservacao.keys()), index=1)
        v5_texto = col2.selectbox("Padrão de Acabamento", list(map_acabamento.keys()), index=1)
        v4 = map_conservacao[v4_texto]
        v5 = map_acabamento[v5_texto]
        features_lista = ['area_privativa', 'indice_fiscal', 'vagas_garagem', 'estado_conservacao', 'padrao_acabamento']

    elif tipologia_sel == "LOTE":
        v1 = col1.number_input("Área do Terreno (m²)", min_value=10.0, value=360.0)
        v2_texto = col2.selectbox("Topografia", list(map_topografia.keys()), index=1)
        v3 = col3.number_input("Data do Evento (Ano Corrente)", min_value=2000.0, value=2026.0)
        v4 = col1.number_input("Testada / Frente (m)", min_value=0.0, value=12.0)
        v5_texto = col2.selectbox("Origem da Informação", list(map_origem.keys()), index=0)
        v2 = map_topografia[v2_texto]
        v5 = map_origem[v5_texto]
        features_lista = ['area_terreno', 'topografia', 'data_evento', 'frente', 'origem_informacao']

    elif tipologia_sel == "GALPAO":
        v1 = col1.number_input("Área Privativa (m²)", min_value=10.0, value=500.0)
        v2 = col2.number_input("Área do Terreno (m²)", min_value=10.0, value=1000.0)
        v3 = col3.number_input("Índice Fiscal da Quadra", min_value=0.0, value=900.0)
        v4_texto = col1.selectbox("Padrão de Acabamento", list(map_acabamento.keys()), index=1)
        v5 = col2.number_input("Idade Aparente (Anos)", min_value=0.0, value=10.0)
        v4 = map_acabamento[v4_texto]
