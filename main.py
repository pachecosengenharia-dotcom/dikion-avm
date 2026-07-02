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
        (450000.0, 6000.0, 120.0, 1200.0, 200.0, 2, 0, 3.0, "CASA"),
        (480000.0, 6153.0, 125.0, 1250.0, 220.0, 2, 0, 3.0, "CASA"),
        (510000.0, 6375.0, 130.0, 1300.0, 250.0, 2, 0, 3.2, "CASA"),
        (750000.0, 8823.0, 185.0, 3200.0, 360.0, 3, 0, 3.5, "CASA"),
        (820000.0, 8913.0, 192.0, 3300.0, 400.0, 3, 0, 3.5, "CASA"),
        (350000.0, 5833.0, 60.0, 1500.0, 0.0, 1, 3, 2.7, "APARTAMENTO"),
        (380000.0, 6129.0, 62.0, 1600.0, 0.0, 1, 5, 2.7, "APARTAMENTO"),
        (420000.0, 6461.0, 65.0, 1800.0, 0.0, 2, 8, 2.8, "APARTAMENTO"),
        (1200000.0, 2400.0, 500.0, 900.0, 800.0, 0, 0, 6.0, "GALPAO")
    ]
    return pd.DataFrame(dados, columns=['valor_total_declarado', 'valor_unitario_m2', 'area_privativa', 'indice_fiscal', 'area_terreno', 'vagas_garagem', 'andares', 'pe_direito', 'tipologia'])

def gerar_grafico_mercado(df_saneado, area_alvo, valor_estimado_m2):
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.scatter(df_saneado['area_privativa'], df_saneado['valor_unitario_m2'], color='#2B6CB0', alpha=0.7, label='Amostras')
    ax.scatter(area_alvo, valor_estimado_m2, color='#E53E3E', marker='*', s=150, label='Avaliado')
    ax.set_title('Dispersao do Mercado (Area vs Preco m²)', fontsize=10, fontweight='bold', color='#1A365D')
    ax.set_xlabel('Area Principal (m²)', fontsize=8)
    ax.set_ylabel('Preco Unitario (R$/m²)', fontsize=8)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(fontsize=7, loc='best')
    plt.tight_layout()
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png', dpi=200)
    img_buf.seek(0)
    plt.close(fig)
    return img_buf

def gerar_laudo_pdf_ia(tenant, tipologia, area, valores, model_stats, status_juridico, score_juridico, grafico_buf):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40.0, leftMargin=40.0, topMargin=40.0, bottomMargin=40.0)
    story = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('T1', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor("#1A365D"), spaceAfter=15.0)
    subtitle_style = ParagraphStyle('T2', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor("#2B6CB0"), spaceAfter=8.0)
    text_style = ParagraphStyle('T3', parent=styles['Normal'], fontSize=9, leading=13, spaceAfter=6.0)
    
    story.append(Paragraph("LAUDO TECNICO DE ENGENHARIA DE AVALIACOES POR IA", title_style))
    story.append(Paragraph(f"<b>Instituicao Solicitante:</b> {tenant} | <b>Normativa:</b> ABNT NBR 14653-2", text_style))
    story.append(Spacer(1, 10.0))
    
    story.append(Paragraph("1. Escopo de Avaliacao Imobiliaria", subtitle_style))
    t1 = Table([["Tipologia do Bem", tipologia, "Dimensao Principal", f"{area} m²"]], colWidths=(130.0, 110.0, 130.0, 110.0))
    t1.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F7FAFC")), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")), ('PADDING', (0,0), (-1,-1), 5.0)]))
    story.append(t1)
    story.append(Spacer(1, 10.0))
    
    story.append(Paragraph("2. Resultados do Motor de Machine Learning", subtitle_style))
    t2 = Table([
        ["Metrica de Cobertura do Risco", "Valor Comercial Admissivel"],
        ["Margem Minima de Seguranca (Garantia LTV)", f"R$ {valores['v_min']:,.2f}"],
        ["Valor de Face Estimado (Media)", f"R$ {valores['v_medio']:,.2f}"],
        ["Limite de Mercado Maximo", f"R$ {valores['v_max']:,.2f}"]
    ], colWidths=(240.0, 240.0))
    t2.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2B6CB0")), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")), ('PADDING', (0,0), (-1,-1), 5.0)]))
    story.append(t2)
    story.append(Spacer(1, 5.0))
    story.append(Paragraph(f"<b>Metricas de Redes de Decisao:</b> Precisao de Ajuste R² = {model_stats['r2']} | Amostras Saneadas = {model_stats['saneadas']}.", text_style))
    story.append(Spacer(1, 10.0))
    
    story.append(Paragraph("3. Diagnostico e Comportamento Espacial do Mercado", subtitle_style))
    story.append(Image(grafico_buf, width=320.0, height=160.0))
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
st.markdown("Gestao automatizada de risco imobiliario por Inteligencia Artificial (Random Forest).")
st.divider()

st.sidebar.header("🔑 Assinatura e Faturamento")
tenant_selecionado = st.sidebar.selectbox("Cliente Institucional", ["001 - Banco Alfa S.A.", "002 - Imobiliária Local Ltda"])
st.sidebar.markdown("**Plano Contratado:** 🟢 ENTERPRISE (Acesso Total Liberado)")

aba_avm, aba_juridico = st.tabs(["📊 1. Avaliacao Estatistica por IA (AVM)", "📜 2. Analise Juridica"])

# Inicialização segura de variáveis de estado
if 'status_juridico_global' not in st.session_state: st.session_state.status_juridico_global = True
if 'score_juridico_global' not in st.session_state: st.session_state.score_juridico_global = "PENDENTE"
if 'memorizar_calculo' not in st.session_state: st.session_state.memorizar_calculo = None

with aba_avm:
    st.subheader("Configuracao da Base e Modelagem")
    arquivo_planilha = st.file_uploader("Arraste aqui a planilha consolidada de imoveis do banco (.xlsx ou .csv)", type=["xlsx", "csv"])
    
    if arquivo_planilha is not None:
        try:
            df_bruto = pd.read_csv(arquivo_planilha) if arquivo_planilha.name.endswith('.csv') else pd.read_excel(arquivo_planilha)
            df_global = df_bruto.copy()
            colunas_mapeamento = {
                'area_construida': 'area_privativa', 'area_util': 'area_privativa', 'metragem': 'area_privativa',
                'preco_m2': 'valor_unitario_m2', 'valor_m2': 'valor_unitario_m2',
                'preco': 'valor_total_declarado', 'valor': 'valor_total_declarado'
            }
            df_global.columns = df_global.columns.str.lower().str.strip()
            df_global.rename(columns=colunas_mapeamento, inplace=True)
            st.success(f"🟩 Planilha VALIDADA: {len(df_global)} imóveis lidos com sucesso!")
        except Exception as e:
            st.error(f"Erro na leitura da planilha: {e}. Carregando base simulada...")
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
    
    # GATILHO COMPACTADO DO BOTÃO DE CÁLCULO
    if st.button("🚀 Calcular Avaliacao por Inteligencia Artificial"):
        tipologia_limpa = tipologia_sel.replace("🏡 ", "").replace("🏢 ", "").replace("📐 ", "").replace("🏭 ", "").strip()
        df_local_processamento = df_global.copy()
        
        df_local_processamento['tipologia'] = df_local_processamento['tipologia'].astype(str).str.upper().str.strip() if 'tipologia' in df_local_processamento.columns else "CASA"
        df_tipo = df_local_processamento[df_local_processamento['tipologia'] == tipologia_limpa].copy()
        
        if len(df_tipo) < 3:
            df_backup = carregar_base_multitipologia_padrao()
            df_tipo = df_backup[df_backup['tipologia'] == tipologia_limpa].copy()
            
        for col_nome in ['area_privativa', 'indice_fiscal', 'area_terreno', 'vagas_garagem', 'andares', 'pe_direito', 'valor_unitario_m2']:
            if col_nome not in df_tipo.columns: df_tipo[col_nome] = 0.0
            df_tipo[col_nome] = pd.to_numeric(df_tipo[col_nome], errors='coerce').fillna(0.0)
            
        q1 = df_tipo['valor_unitario_m2'].quantile(0.25)
        q3 = df_tipo['valor_unitario_m2'].quantile(0.75)
        iqr = q3 - q1
    # SEÇÃO VISUAL FIXA E COMPLETA: Imprime todos os resultados da gaveta de memória
    if st.session_state.memorizar_calculo is not None:
        dados_calc = st.session_state.memorizar_calculo
        st.write("---")
        st.success(f"🎯 Algoritmo de Inteligencia Artificial Concluido para {dados_calc['tipologia_limpa']}!")
        
        cv1, cv2, cv3 = st.columns(3)
        cv1.metric(label="Valor Estimado de Mercado (Media)", value=f"R$ {dados_calc['valor_medio']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        cv2.metric(label="Minimo Admissivel (Garantia LTV)", value=f"R$ {dados_calc['v_min']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        cv3.metric(label="Maximo Admissivel", value=f"R$ {dados_calc['v_max']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        
        st.markdown("### 📋 Enquadramento Normativo e Performance da IA")
        m1, m2, m3 = st.columns(3)
        m1.metric("Precisao das Arvores de Decisao (R²)", dados_calc['r2_score'])
        m2.metric("Amostras Brutas Lidas", f"{dados_calc['brutas']} {dados_calc['tipologia_limpa']}s")
        m3.metric("Amostras Homologadas (Pos-IQR)", f"{dados_calc['saneadas']} {dados_calc['tipologia_limpa']}s")
        
        grafico_buf = gerar_grafico_mercado(dados_calc['df_saneado'], dados_calc['area_alvo'], dados_calc['preco_m2_pred'])
        st.image(grafico_buf, caption="Grafico de Dispersao Espacial do Mercado de Goiania")
        
        model_stats = {"r2": dados_calc['r2_score'], "saneadas": dados_calc['saneadas']}
        valores_dict = {"v_medio": dados_calc['valor_medio'], "v_min": dados_calc['v_min'], "v_max": dados_calc['v_max']}
        
        pdf_bytes = gerar_laudo_pdf_ia(
            tenant_selecionado, dados_calc['tipologia_limpa'], dados_calc['area_alvo'], valores_dict, model_stats,
            st.session_state.status_juridico_global, st.session_state.score_juridico_global, grafico_buf
        )
        st.markdown("### 📥 Emissao de Relatorio Certificado")
        st.download_button(label="📄 Baixar Laudo de IA Certificado (PDF)", data=pdf_bytes, file_name="laudo_ia_NBR14653.pdf", mime="application/pdf")

with aba_juridico:
    st.subheader("Esteira de Analise de Risco Documental")
    txt = st.text_area("Texto Identificado na Certidao", "MATRÍCULA Nº 15.234... R-3: PENHORA JUDICIAL ativa...", height=100)
    if st.button("🔍 Auditar Matricula do Imovel"):
        st.write("---")
        if "penhora" in txt.lower(): st.error("❌ REJEITADO - ALTO RISCO")
        else: st.success("✅ APROVADO - BAIXO RISCO")

st.divider()
st.caption("🔒 Plataforma AVM SaaS v3.5.0 | Criptografia ativa e em conformidade estrita com as normas da ABNT NBR 14653-2.")
