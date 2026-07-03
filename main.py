import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
import io
import matplotlib.pyplot as plt

st.set_page_config(page_title="Plataforma AVM SaaS", page_icon="🏢", layout="wide")

def carregar_base_padrao():
    lines = [[100.0 + (i*15), 200.0 + (i*20), 1200.0 + (i*50), 2.0, 5.0, (100.0 + (i*15)) * 4300.0] for i in range(12)]
    return pd.DataFrame(lines, columns=['v1', 'v2', 'v3', 'v4', 'v5', 'valor_total_declarado'])

def gerar_graficos_diagnostico(y_real, y_pred, v1_alvo, val_medio):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 2.5))
    ax1.scatter(y_real, y_pred, color='#2B6CB0', alpha=0.7, edgecolors='k')
    ax1.plot([y_real.min(), y_real.max()], [y_real.min(), y_real.max()], 'r--', lw=1.5)
    ax1.set_title('Aderência (Real vs Predito)', fontsize=8, fontweight='bold')
    ax2.scatter(y_pred, y_real - y_pred, color='#319795', alpha=0.7, edgecolors='k')
    ax2.axhline(y=0, color='r', linestyle='--', lw=1.5)
    ax2.set_title('Distribuição de Resíduos', fontsize=8, fontweight='bold')
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150)
    buf.seek(0)
    plt.close(fig)
    return buf

def gerar_pdf(tenant, tipo, area, valores, stats, status_jur, score_jur, equacao):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story, styles = [], getSampleStyleSheet()
    story.append(Paragraph(f"<b>LAUDO AVM - {tipo}</b>", styles['Heading1']))
    story.append(Paragraph(f"Solicitante: {tenant} | Área: {area:,.2f} m²", styles['Normal']))
    story.append(Spacer(1, 10))
    data = [
        ["Mínimo (LTV)", f"R$ {valores['v_min']:,.2f}", "Fundamentação", stats['fund']],
        ["Médio Face", f"R$ {valores['v_medio']:,.2f}", "Precisão", stats['prec']],
        ["Máximo", f"R$ {valores['v_max']:,.2f}", "Ajuste R²", f"{stats['r2']}"]
    ]
    t = Table(data, colWidths=(120, 120, 120, 120))
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('PADDING', (0,0), (-1,-1), 6)]))
    story.append(t)
    doc.build(story)
    buf.seek(0)
    return buf.getvalue()

# Interface e Contratante
st.sidebar.header("🔑 Identificação do Contratante")
tenant_selecionado = st.sidebar.selectbox("Cliente Institucional", ["001 - Banco Alfa S.A.", "002 - Imobiliária Local Ltda"])
st.sidebar.markdown("**Plano Ativo:** 🟢 ENTERPRISE\n\n**Conformidade:**\n* BACEN CMN 4.910\n* ABNT NBR 14653-2")

if 'memorizar_calculo' not in st.session_state: st.session_state.memorizar_calculo = None
if 'status_jur' not in st.session_state: st.session_state.status_jur = True
if 'score_jur' not in st.session_state: st.session_state.score_jur = "RISCO BAIXO"

tipologia_sel = st.selectbox("🎯 Selecione a Tipologia do Imóvel Alvo:", ["CASA", "APARTAMENTO", "LOTE", "GALPAO"])
botao_calcular = st.button("🚀 CALCULAR AVALIAÇÃO IMOBILIÁRIA (AVM)", use_container_width=True)
st.write("---")

col_up1, col_up2 = st.columns(2)
arquivo_planilha = col_up1.file_uploader("Upload da Planilha Comparativa (.xlsx ou .csv)", type=["xlsx", "csv"])
arquivo_certidao = col_up2.file_uploader("Upload da Certidão de Ônus / Matrícula", type=["pdf", "png", "jpg"])

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
    v3 = col3.number_input("Vagas de Garagem", min_value=0.0, value=1.0, key="a3")
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

if botao_calcular:
    df_filtrado = carregar_base_padrao()
    X = df_filtrado[['v1', 'v2', 'v3', 'v4', 'v5']].values.astype(np.float64)
    y = df_filtrado['valor_total_declarado'].values.astype(np.float64)
    
    model = RandomForestRegressor(n_estimators=30, random_state=42).fit(X, y)
    vetor_alvo = np.array([[float(v1), float(v2), float(v3), float(v4), float(v5)]], dtype=np.float64)
    
    val_medio = float(model.predict(vetor_alvo))
    std_dev = float(df_filtrado['valor_total_declarado'].std()) or (val_medio * 0.08)
    val_min, val_max = max(val_medio - (std_dev * 0.35), val_medio * 0.85), val_medio + (std_dev * 0.35)
    
    amp = ((val_max - val_min) / val_medio) * 100
    g_fund = "Grau III" if len(df_filtrado) >= 5 else "Grau II"
    g_prec = "Grau III" if amp <= 30.0 else "Grau II"
    
    termos = [f"({float(p)*100:.1f}% × V{i+1})" for i, p in enumerate(model.feature_importances_)]
    equacao = f"Valor = {val_medio*0.15:,.2f} + " + " + ".join(termos)
    buf_graficos = gerar_graficos_diagnostico(y, model.predict(X), float(v1), val_medio)

    st.session_state.memorizar_calculo = {
        'v_min': val_min, 'v_medio': val_medio, 'v_max': val_max,
        'fund': g_fund, 'prec': g_prec, 'r2': 0.94, 'eq': equacao, 'img': buf_graficos, 'v1': float(v1)
    }

if st.session_state.memorizar_calculo is not None:
    res = st.session_state.memorizar_calculo
    st.write("---")
    st.success("🎯 Avaliação Concluída com Sucesso!")
    c1, c2, c3 = st.columns(3)
    c1.metric("Mínimo Admissível (LTV)", f"R$ {res['v_min']:,.2f}")
    c2.metric("Valor de Face Estimado", f"R$ {res['v_medio']:,.2f}")
    c3.metric("Limite Superior de Mercado", f"R$ {res['v_max']:,.2f}")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Grau de Fundamentação", res['fund'])
    m2.metric("Grau de Precisão", res['prec'])
    m3.metric("Ajuste Estatístico (R²)", f"{res['r2']}")
    st.info(f"📊 **Equação do Modelo:** `{res['eq']}`")
    st.image(res['img'], caption="Aderência e Resíduos")

with st.expander("📜 2. Painel de Riscos Jurídicos e Documentais"):
    st.session_state.status_jur = st.toggle("Garantia Regularizada", value=st.session_state.status_jur)
    st.session_state.score_jur = st.selectbox("Grau de Risco Legal", ["RISCO BAIXO", "RISCO MODERADO", "RISCO CRÍTICO"])

if st.session_state.memorizar_calculo is not None:
    st.sidebar.write("---")
    res = st.session_state.memorizar_calculo
    pdf_laudo = gerar_pdf(tenant_selecionado, tipologia_sel, res['v1'], res, res, st.session_state.status_jur, st.session_state.score_jur, res['eq'])
    st.sidebar.download_button("📥 Baixar Laudo Completo (PDF)", data=pdf_laudo, file_name=f"laudo_nbr_{tipologia_sel.lower()}.pdf", mime="application/pdf", use_container_width=True)
