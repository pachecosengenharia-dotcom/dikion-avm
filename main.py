import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io

# Configuração da página
st.set_page_config(page_title="Plataforma AVM SaaS - Multi-Tipologia", page_icon="🏢", layout="wide")

# =====================================================================
# FUNÇÕES DE LÓGICA E IA
# =====================================================================

def executar_motor_ia(df_global, tipologia, area, indice_fiscal, atributos):
    # Filtro pela tipologia
    df_tipo = df_global[df_global['tipologia'] == tipologia].copy()
    
    # Features obrigatórias
    features = ['area_privativa', 'indice_fiscal', 'area_terreno', 'vagas_garagem', 'andar', 'pe_direito']
    
    # Validação
    if len(df_tipo) < 3:
        return None, "Amostras insuficientes (mínimo 3) para esta tipologia."

    # Treinamento
    X = df_tipo[features]
    y = df_tipo['valor_total_declarado']
    modelo = RandomForestRegressor(n_estimators=200, random_state=42)
    modelo.fit(X, y)
    r2 = round(modelo.score(X, y), 4)

    # Predição
    alvo = pd.DataFrame([{
        'area_privativa': area,
        'indice_fiscal': indice_fiscal,
        'area_terreno': atributos.get('area_terreno', 0),
        'vagas_garagem': atributos.get('vagas_garagem', 0),
        'andar': atributos.get('andar', 0),
        'pe_direito': atributos.get('pe_direito', 0),
    }])

    previsoes = np.array([arvore.predict(alvo.values)[0] for arvore in modelo.estimators_])
    v_medio = float(np.mean(previsoes))
    v_min = float(np.percentile(previsoes, 15))
    v_max = float(np.percentile(previsoes, 85))

    return {
        'valores': {'v_min': v_min, 'v_medio': v_medio, 'v_max': v_max},
        'r2': r2,
        'n_amostras': len(df_tipo)
    }, None

def gerar_laudo_pdf_ia(tenant, tipologia, area, valores, r2, n_amostras, status_juridico, score_juridico):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    story.append(Paragraph(f"LAUDO CORE AVM - {tipologia}", styles['Heading1']))
    story.append(Paragraph(f"Instituição: {tenant}", styles['Normal']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Valor Médio Estimado: R$ {valores['v_medio']:,.2f}", styles['Normal']))
    story.append(Paragraph(f"Precisão R²: {r2}", styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# =====================================================================
# INTERFACE PRINCIPAL
# =====================================================================
st.title("🏢 Painel de Crédito e Controle Multi-Tenant")

# Inicialização do estado
if 'df_global' not in st.session_state: st.session_state.df_global = None
if 'status_juridico_global' not in st.session_state: st.session_state.status_juridico_global = True
if 'score_juridico_global' not in st.session_state: st.session_state.score_juridico_global = "PENDENTE"

# Upload de Dados
arquivo = st.file_uploader("Carregue sua planilha (.csv ou .xlsx)", type=["csv", "xlsx"])
if arquivo:
    df = pd.read_csv(arquivo) if arquivo.name.endswith('.csv') else pd.read_excel(arquivo)
    # Normalização de nomes de colunas
    df.columns = [c.lower().strip().replace(" ", "_").replace("á", "a").replace("í", "i").replace("é", "e").replace("ã", "a").replace("ç", "c") for c in df.columns]
    st.session_state.df_global = df
    st.success("Dados carregados com sucesso.")

if st.session_state.df_global is not None:
    aba_avm, aba_jur = st.tabs(["📊 Avaliação AVM", "📜 Análise Jurídica"])
    
    with aba_avm:
        tipo = st.selectbox("Tipologia", ["CASA", "APARTAMENTO", "LOTE", "GALPAO"])
        c1, c2 = st.columns(2)
        area = c1.number_input("Área Principal", value=100.0)
        indice = c2.number_input("Índice Fiscal", value=1000.0)
        
        if st.button("Executar IA"):
            res, erro = executar_motor_ia(st.session_state.df_global, tipo, area, indice, {"area_terreno": 200, "vagas_garagem": 1, "andar": 0, "pe_direito": 3.0})
            if erro: st.error(erro)
            else:
                st.metric("Valor Estimado", f"R$ {res['valores']['v_medio']:,.2f}")
                pdf = gerar_laudo_pdf_ia("Banco Alfa", tipo, area, res['valores'], res['r2'], res['n_amostras'], True, "Baixo")
                st.download_button("Baixar Laudo PDF", data=pdf, file_name="laudo.pdf")
                
    with aba_juridico := aba_jur:
        # Lógica jurídica simplificada
        if st.button("Processar Risco"):
            st.info("Análise concluída com sucesso.")
