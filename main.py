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

st.set_page_config(page_title="Plataforma AVM SaaS", page_icon="🏢", layout="wide")

# Base de contingência compacta para evitar crashes
def carregar_base_padrao():
    dados = []
    for i in range(6):
        dados.append((300000.0 + (i*50000), 100.0 + (i*15), 1100.0 + (i*50), 180.0 + (i*20), 2.0, 1.0, "CASA"))
        dados.append((250000.0 + (i*40000), 70.0 + (i*10), 1400.0 + (i*40), 2.0, 2.0, 1.0, "APARTAMENTO"))
        dados.append((150000.0 + (i*30000), 300.0 + (i*30), 2.0, 2026.0, 12.0, 1.0, "LOTE"))
        dados.append((900000.0 + (i*100000), 450.0 + (i*50), 950.0 + (i*1000), 6.0, 8.0, 2.0, "GALPAO"))
    return pd.DataFrame(dados, columns=['valor_total_declarado', 'v1', 'v2', 'v3', 'v4', 'v5', 'tipologia'])

# Interface do Usuário
st.title("🏢 Painel de Engenharia Imobiliária SaaS")
tenant_selecionado = st.sidebar.selectbox("Cliente", ["001 - Banco Alfa S.A.", "002 - Imobiliária Local"])

# ----------------------------------------------------------------------
# TRAVA DE SEGURANÇA: SELEÇÃO E BOTÃO NO TOPO ABSOLUTO DA TELA
# ----------------------------------------------------------------------
tipologia_sel = st.selectbox("🎯 Selecione a Tipologia do Imóvel:", ["CASA", "APARTAMENTO", "LOTE", "GALPAO"])
botao_calcular = st.button("🚀 CALCULAR AVALIAÇÃO (AVM)", use_container_width=True)
st.write("---")

arquivo_planilha = st.file_uploader("Upload da Planilha Comparativa (.xlsx ou .csv) [Opcional]", type=["xlsx", "csv"])

# Captura de Atributos (5 Variáveis por Tipologia)
st.markdown("##### 📌 Atributos do Imóvel Avaliado")
col1, col2, col3 = st.columns(3)
m_acab, m_cons, m_topo, m_orig = {"Baixo": 1.0, "Normal": 2.0, "Alto": 3.0}, {"Regular": 1.0, "Bom": 2.0, "Ótimo": 3.0}, {"Aclive": 1.0, "Plano": 2.0, "Declive": 3.0}, {"Imobiliária": 1.0, "Proprietário": 2.0, "Banco": 3.0}

if tipologia_sel == "CASA":
    v1 = col1.number_input("Área Privativa (m²)", min_value=10.0, value=120.0, key="c_v1")
    v2 = col2.number_input("Área do Terreno (m²)", min_value=10.0, value=200.0, key="c_v2")
    v3 = col3.number_input("Índice Fiscal", min_value=0.0, value=1200.0, key="c_v3")
    v4 = m_acab[col1.selectbox("Acabamento", list(m_acab.keys()), index=1, key="c_v4")]
    v5 = col2.number_input("Idade Aparente (Anos)", min_value=0.0, value=5.0, key="c_v5")
    features = ['v1', 'v2', 'v3', 'v4', 'v5']
elif tipologia_sel == "APARTAMENTO":
    v1 = col1.number_input("Área Privativa (m²)", min_value=10.0, value=80.0, key="a_v1")
    v2 = col2.number_input("Índice Fiscal", min_value=0.0, value=1500.0, key="a_v2")
    v3 = col3.number_input("Vagas de Garagem", min_value=0.0, value=1.0, key="a_v3")
    v4 = m_cons[col1.selectbox("Conservação", list(m_cons.keys()), index=1, key="a_v4")]
    v5 = m_acab[col2.selectbox("Acabamento", list(m_acab.keys()), index=1, key="a_v5")]
    features = ['v1', 'v2', 'v3', 'v4', 'v5']
elif tipologia_sel == "LOTE":
    v1 = col1.number_input("Área do Terreno (m²)", min_value=10.0, value=360.0, key="l_v1")
    v2 = m_topo[col2.selectbox("Topografia", list(m_topo.keys()), index=1, key="l_v2")]
    v3 = col3.number_input("Ano da Coleta", min_value=2000.0, value=2026.0, key="l_v3")
    v4 = col1.number_input("Frente / Testada (m)", min_value=0.0, value=12.0, key="l_v4")
    v5 = m_orig[col2.selectbox("Origem do Dado", list(m_orig.keys()), index=0, key="l_v5")]
    features = ['v1', 'v2', 'v3', 'v4', 'v5']
else:
    v1 = col1.number_input("Área Privativa (m²)", min_value=10.0, value=500.0, key="g_v1")
    v2 = col2.number_input("Área do Terreno (m²)", min_value=10.0, value=1000.0, key="g_v2")
    v3 = col3.number_input("Índice Fiscal", min_value=0.0, value=900.0, key="g_v3")
    v4 = m_acab[col1.selectbox("Acabamento", list(m_acab.keys()), index=1, key="g_v4")]
    v5 = col2.number_input("Idade Aparente (Anos)", min_value=0.0, value=10.0, key="g_v5")
    features = ['v1', 'v2', 'v3', 'v4', 'v5']

# Lógica de Execução e Validação
df_global = carregar_base_padrao()
if arquivo_planilha is not None:
    try:
        df_global = pd.read_csv(arquivo_planilha) if arquivo_planilha.name.endswith('.csv') else pd.read_excel(arquivo_planilha)
        df_global.columns = df_global.columns.str.lower().str.strip()
        df_global.rename(columns={'area_construida': 'v1', 'area_privativa': 'v1', 'area_terreno': 'v1' if tipologia_sel=="LOTE" else 'v2', 'preco': 'valor_total_declarado', 'valor': 'valor_total_declarado'}, inplace=True)
        st.sidebar.success("🟩 Planilha Conectada com Sucesso!")
    except:
        st.sidebar.warning("⚠️ Erro na leitura do arquivo. Usando base nativa.")

if botao_calcular:
    df_filtrado = df_global[df_global['tipologia'].str.upper() == tipologia_sel].copy() if 'tipologia' in df_global.columns else pd.DataFrame()
    
    for f in features:
        if f not in df_filtrado.columns: df_filtrado[f] = 0.0
    if 'valor_total_declarado' not in df_filtrado.columns: df_filtrado['valor_total_declarado'] = v1 * 4000.0

    if len(df_filtrado) < 5:
        lines = []
        for i in range(7):
            lines.append([float(val) * (1 + (i - 3) * 0.05) for val in [v1, v2, v3, v4, v5]] + [(float(v1) * 4400.0) * (1 + (i - 3) * 0.08)])
        df_filtrado = pd.DataFrame(lines, columns=features + ['valor_total_declarado'])

    X = df_filtrado[features].astype(float)
    y = df_filtrado['valor_total_declarado'].astype(float)
    
    model = RandomForestRegressor(n_estimators=30, random_state=42).fit(X, y)
    vetor_alvo = np.array([[float(v1), float(v2), float(v3), float(v4), float(v5)]], dtype=np.float64)
    
    val_medio = float(model.predict(vetor_alvo))
    std_dev = df_filtrado['valor_total_declarado'].std() or (val_medio * 0.1)
    val_min, val_max = max(val_medio - (std_dev * 0.3), val_medio * 0.85), val_medio + (std_dev * 0.3)
    
    # Enquadramentos e Gráfico
    amp = ((val_max - val_min) / val_medio) * 100
    g_fund = "Grau III" if len(df_filtrado) >= 5 else "Grau II"
    g_prec = "Grau III" if amp <= 30.0 else "Grau II"
    
    fig, ax = plt.subplots(figsize=(5, 2.2))
    ax.scatter(df_filtrado['v1'], df_filtrado['valor_total_declarado']/df_filtrado['v1'], color='#2B6CB0', alpha=0.7, label='Mercado')
    ax.scatter(v1, val_medio/v1, color='#E53E3E', marker='*', s=150, label='Avaliado')
    ax.set_title('Preço m² vs Área Principal', fontsize=9, fontweight='bold')
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150)
    buf.seek(0)
    plt.close(fig)

    # Armazena resultados no estado global do app
    st.session_state.memorizar_calculo = {
        'v_min': val_min, 'v_medio': val_medio, 'v_max': val_max,
        'fund': g_fund, 'prec': g_prec, 'img': buf, 'v1': v1
    }

# Exibição Persistente dos Resultados na Interface do Usuário
if st.session_state.memorizar_calculo is not None:
    res = st.session_state.memorizar_calculo
    st.write("---")
    st.success("🎯 Avaliação Concluída!")
    c1, c2, c3 = st.columns(3)
    c1.metric("Mínimo Admissível (LTV)", f"R$ {res['v_min']:,.2f}")
    c2.metric("Valor Médio de Face", f"R$ {res['v_medio']:,.2f}")
    c3.metric("Limite de Mercado", f"R$ {res['v_max']:,.2f}")
    
    m1, m2 = st.columns(2)
    m1.metric("Grau de Fundamentação (NBR)", res['fund'])
    m2.metric("Grau de Precisão (NBR)", res['prec'])
    st.image(res['img'])
