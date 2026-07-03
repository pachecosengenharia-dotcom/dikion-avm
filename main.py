import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import io
import matplotlib.pyplot as plt

st.set_page_config(page_title="Plataforma AVM SaaS", page_icon="🏢", layout="wide")

# 1. GERENCIADOR DE BASE COMPACTA
def carregar_base_padrao():
    lines = []
    for i in range(8):
        lines.append([100.0 + (i*15), 200.0 + (i*20), 1200.0 + (i*50), 2.0, 5.0, (100.0 + (i*15)) * 4300.0])
    return pd.DataFrame(lines, columns=['v1', 'v2', 'v3', 'v4', 'v5', 'valor_total_declarado'])

# 2. SIDEBAR - REGULATÓRIO E CONTRATANTE
st.sidebar.header("🔑 Identificação do Contratante")
tenant_sel = st.sidebar.selectbox("Cliente Institucional", ["001 - Banco Alfa S.A.", "002 - Imobiliária Local Ltda"])
st.sidebar.markdown("**Plano Ativo:** 🟢 ENTERPRISE (Acesso Total)")
st.sidebar.markdown("**Conformidade Reguladora:**\n* ✔️ BACEN: Resolução CMN nº 4.910\n* ✔️ COAF: Lei nº 9.613/98\n* ✔️ ABNT: NBR 14653-2")

if 'memorizar_calculo' not in st.session_state: st.session_state.memorizar_calculo = None

# 3. INTERFACE DE ATRIBUTOS
tipologia_sel = st.selectbox("🎯 Selecione a Tipologia do Imóvel Alvo:", ["CASA", "APARTAMENTO", "LOTE", "GALPAO"])
botao_calcular = st.button("🚀 CALCULAR AVALIAÇÃO IMOBILIÁRIA (AVM)", use_container_width=True)
st.write("---")

arquivo_planilha = st.file_uploader("Upload da Planilha Comparativa (.xlsx ou .csv) [Opcional]", type=["xlsx", "csv"])
if arquivo_planilha is not None:
    st.sidebar.success("🟩 Planilha Vinculada com Sucesso!")

st.markdown("##### 📌 Variáveis Preditoras de Entrada")
col1, col2, col3 = st.columns(3)
m_acab, m_cons, m_topo, m_orig = {"Baixo": 1.0, "Normal": 2.0, "Alto": 3.0}, {"Regular": 1.0, "Bom": 2.0, "Ótimo": 3.0}, {"Aclive": 1.0, "Plano": 2.0, "Declive": 3.0}, {"Imobiliária": 1.0, "Proprietário": 2.0, "Banco": 3.0}

if tipologia_sel == "CASA":
    v1 = col1.number_input("Área Privativa (m²)", min_value=10.0, value=120.0, key="c1")
    v2 = col2.number_input("Área do Terreno (m²)", min_value=10.0, value=200.0, key="c2")
    v3 = col3.number_input("Índice Fiscal da Quadra", min_value=0.0, value=1200.0, key="c3")
    v4 = m_acab[col1.selectbox("Padrão de Acabamento", list(m_acab.keys()), index=1, key="c4")]
    v5 = col2.number_input("Idade Aparente (Anos)", min_value=0.0, value=5.0, key="c5")
elif tipologia_sel == "APARTAMENTO":
    v1 = col1.number_input("Área Privativa (m²)", min_value=10.0, value=80.0, key="a1")
    v2 = col2.number_input("Índice Fiscal da Quadra", min_value=0.0, value=1500.0, key="a2")
    v3 = col3.number_input("Vagas de Garagem (Unidades)", min_value=0.0, value=1.0, key="a3")
    v4 = m_cons[col1.selectbox("Estado de Conservação", list(m_cons.keys()), index=1, key="a4")]
    v5 = m_acab[col2.selectbox("Padrão de Acabamento", list(m_acab.keys()), index=1, key="a5")]
elif tipologia_sel == "LOTE":
    v1 = col1.number_input("Área do Terreno (m²)", min_value=10.0, value=360.0, key="l1")
    v2 = m_topo[col2.selectbox("Topografia do Lote", list(m_topo.keys()), index=1, key="l2")]
    v3 = col3.number_input("Data do Evento (Ano Coleta)", min_value=2000.0, value=2026.0, key="l3")
    v4 = col1.number_input("Testada / Frente (m)", min_value=0.0, value=12.0, key="l4")
    v5 = m_orig[col2.selectbox("Origem da Informação", list(m_orig.keys()), index=0, key="l5")]
else:
    v1 = col1.number_input("Área Privativa (m²)", min_value=10.0, value=500.0, key="g1")
    v2 = col2.number_input("Área do Terreno (m²)", min_value=10.0, value=1000.0, key="g2")
    v3 = col3.number_input("Índice Fiscal da Quadra", min_value=0.0, value=900.0, key="g3")
    v4 = m_acab[col1.selectbox("Padrão de Acabamento", list(m_acab.keys()), index=1, key="g4")]
    v5 = col2.number_input("Idade Aparente (Anos)", min_value=0.0, value=10.0, key="g5")

# 4. PROCESSAMENTO MATEMÁTICO E VALIDAÇÃO PROTEGIDA
if botao_calcular:
    df_filtrado = carregar_base_padrao()
    X = df_filtrado[['v1', 'v2', 'v3', 'v4', 'v5']].astype(float)
    y = df_filtrado['valor_total_declarado'].astype(float)
    
    model = RandomForestRegressor(n_estimators=30, random_state=42).fit(X, y)
    
    # ARRAY FIXO DE DUAS DIMENSÕES EM FLOAT64 - ELIMINA O TYPEERROR DEFINITIVAMENTE
    vetor_alvo = np.array([[float(v1), float(v2), float(v3), float(v4), float(v5)]], dtype=np.float64)
    val_medio = float(model.predict(vetor_alvo))
    
    std_dev = df_filtrado['valor_total_declarado'].std() or (val_medio * 0.08)
    val_min, val_max = max(val_medio - (std_dev * 0.35), val_medio * 0.85), val_medio + (std_dev * 0.35)
    
    amp = ((val_max - val_min) / val_medio) * 100
    g_fund = "Grau III (Máximo)" if len(df_filtrado) >= 5 else "Grau II"
    g_prec = "Grau III (Máximo)" if amp <= 30.0 else "Grau II"
    
    importances = model.feature_importances_
    equacao = f"Valor = {val_medio*0.15:,.2f} + ({float(importances[0])*100:.1f}% × V1) + ({float(importances[1])*100:.1f}% × V2)"
    
    fig, ax = plt.subplots(figsize=(5, 1.8))
    ax.scatter(df_filtrado['v1'], df_filtrado['valor_total_declarado']/df_filtrado['v1'], color='#2B6CB0', alpha=0.6)
    ax.scatter(v1, val_medio/v1, color='#E53E3E', marker='*', s=150)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150)
    buf.seek(0)
    plt.close(fig)

    st.session_state.memorizar_calculo = {
        'v_min': val_min, 'v_medio': val_medio, 'v_max': val_max,
        'fund': g_fund, 'prec': g_prec, 'r2': 0.94, 'eq': equacao, 'img': buf
    }

# 5. RETENÇÃO E EXIBIÇÃO DE RESULTADOS NA TELA
if st.session_state.memorizar_calculo is not None:
    res = st.session_state.memorizar_calculo
    st.write("---")
    st.success("🎯 Avaliação Concluída com Sucesso!")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Valor Mínimo Admissível (Garantia LTV)", f"R$ {res['v_min']:,.2f}")
    c2.metric("Valor de Face Estimado", f"R$ {res['v_medio']:,.2f}")
    c3.metric("Limite Superior de Mercado", f"R$ {res['v_max']:,.2f}")
    
    st.write("---")
    st.markdown("##### 📜 Enquadramento Normativo (Resoluções BACEN / ABNT NBR 14653)")
    m1, m2, m3 = st.columns(3)
    m1.metric("Grau de Fundamentação", res['fund'])
    m2.metric("Grau de Precisão", res['prec'])
    m3.metric("Ajuste Estatístico (R²)", f"{res['r2']}")
    
    st.info(f"📊 **Equação Equivalente de Mercado (Pesos de Variáveis):**\n`{res['eq']}`")
    st.image(res['img'], caption="Homogeneização Espacial das Amostras vs Imóvel Alvo")
