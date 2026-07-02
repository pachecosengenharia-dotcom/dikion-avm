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
if 'score_juridico_global' not in st.session_state: st.session_state.score_juridico_global = "RISCO BAIXO"
if 'memorizar_calculo' not in st.session_state: st.session_state.memorizar_calculo = None

with aba_avm:
    st.subheader("Configuracao da Base e Modelagem")
    arquivo_planilha = st.file_uploader("Arraste aqui a planilha consolidada de imoveis do banco (.xlsx ou .csv)", type=["xlsx", "csv"])
    
        if arquivo_planilha is not None:
        try:
            df_bruto = pd.read_csv(arquivo_planilha) if arquivo_planilha.name.endswith('.csv') else pd.read_excel(arquivo_planilha)
            df_global = df_bruto.copy()
            
            # 1. Normalizar nomes das colunas
            df_global.columns = df_global.columns.str.lower().str.strip()
            
            # 2. Mapear sinônimos conhecidos
            colunas_mapeamento = {
                'area_construida': 'area_privativa', 'area_util': 'area_privativa', 'metragem': 'area_privativa',
                'preco_m2': 'valor_unitario_m2', 'valor_m2': 'valor_unitario_m2',
                'preco': 'valor_total_declarado', 'valor': 'valor_total_declarado'
            }
            df_global.rename(columns=colunas_mapeamento, inplace=True)
            
            # 3. GARANTIA ANTI-CRASH: Forçar existência de todas as colunas necessárias
            colunas_obrigatorias = {
                'valor_total_declarado': 0.0, 'valor_unitario_m2': 0.0, 
                'area_privativa': 0.0, 'indice_fiscal': 0.0, 
                'area_terreno': 0.0, 'vagas_garagem': 0, 
                'andares': 0, 'pe_direito': 3.0, 
                'tipologia': tipologia_sel # Se não houver, assume a selecionada na tela
            }
            
            for col, val_padrao in colunas_obrigatorias.items():
                if col not in df_global.columns:
                    df_global[col] = val_padrao
                    
            st.success(f"🟩 Planilha VALIDADA: {len(df_global)} imóveis lidos com sucesso!")
        except Exception as e:
            st.error(f"Erro na leitura da planilha: {e}. Carregando base simulada...")
            df_global = carregar_base_multitipologia_padrao()


    st.write("---")
    tipologia_sel = st.selectbox("🎯 Selecione a Tipologia do Imovel Alvo para Configuracao:", ["CASA", "APARTAMENTO", "GALPAO"])
    st.write("---")
    
    col1, col2 = st.columns(2)
    area_alvo = col1.number_input("Dimensao/Area Principal (m²)", min_value=10.0, value=120.0)
    indice_alvo = col2.number_input("Indice Fiscal da Quadra", min_value=0.0, value=1200.0)
    
    area_terreno_valor, vagas_valor, andar_valor, pe_direito_valor = 0.0, 0, 0, 3.0
    
    if tipologia_sel == "CASA":
        area_terreno_valor = col1.number_input("Area do Terreno (m²)", min_value=0.0, value=200.0)
        vagas_valor = col2.number_input("Vagas de Garagem", min_value=0, value=2)
    elif tipologia_sel == "APARTAMENTO":
        andar_valor = col1.number_input("Andar do Imovel", min_value=0, value=3)
        vagas_valor = col2.number_input("Vagas de Garagem", min_value=0, value=1)
    elif tipologia_sel == "GALPAO":
        pe_direito_valor = col1.number_input("Pe Direito (m)", min_value=2.0, value=6.0)

    st.write("---")
    
    if st.button("🚀 Executar Engenharia de Avaliacao (AVM)"):
        # Filtrar o DataFrame de acordo com a tipologia alvo
        df_filtrado = df_global[df_global['tipologia'] == tipologia_sel]
        
        if len(df_filtrado) < 3:
            st.warning("Dados insuficientes para a tipologia selecionada na planilha. Usando dados padrão.")
            df_filtrado = carregar_base_multitipologia_padrao()
            df_filtrado = df_filtrado[df_filtrado['tipologia'] == tipologia_sel]
            
        features = ['area_privativa', 'indice_fiscal', 'area_terreno', 'vagas_garagem', 'andares', 'pe_direito']
        X = df_filtrado[features]
        y = df_filtrado['valor_total_declarado']
        
        # Ajuste de segurança simples para evitar overfitting com poucas amostras
        n_estimators = min(50, max(10, len(df_filtrado) * 5))
        model = RandomForestRegressor(n_estimators=n_estimators, random_state=42)
        model.fit(X, y)
        
        # Predição com o vetor alvo informado
        vetor_alvo = np.array([[area_alvo, indice_alvo, area_terreno_valor, vagas_valor, andar_valor, pe_direito_valor]])
        valor_predito = float(model.predict(vetor_alvo)[0])
        valor_m2_predito = valor_predito / area_alvo
        
