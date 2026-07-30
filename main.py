import io
import math
import logging
from typing import List, Optional
from datetime import datetime
import pandas as pd
import statsmodels.api as sm
from statsmodels.sandbox.regression.predstd import wls_prediction_std
from fastapi import FastAPI, HTTPException, Depends, Security, status
from fastapi.security.api_key import APIKeyHeader
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Configuração de Logs para monitoramento na Nuvem (CloudWatch/Azure Monitor)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AVM_PRODUCAO")

app = FastAPI(
    title="Plataforma Core AVM & Compliance Imobiliário SaaS",
    description="API de produção em conformidade com as Resoluções CMN 4.676/2018 e 4.925/2021 do Banco Central.",
    version="2.0.0"
)

# =====================================================================
# 1. CAMADA DE SEGURANÇA E MULTI-TENANCY (Exigência Bacen)
# =====================================================================
API_KEY_HEADER = APIKeyHeader(name="X-API-KEY", auto_error=True)

# Banco de dados de Tenants simulado na memória do servidor para validação de chaves
TENANTS_AUTENTICADOS = {
    "token_secreto_banco_alfa_2026": {"id": 101, "nome": "Banco Alfa S.A.", "plano": "ENTERPRISE"},
    "token_secreto_imobiliaria_beta": {"id": 102, "nome": "Imobiliária Beta Ltda", "plano": "STANDARD"}
}

def validar_inquilino_saas(api_key: str = Security(API_KEY_HEADER)):
    """Injeta a proteção Multi-Tenant e valida as permissões do plano (Bacen 4.893)."""
    if api_key not in TENANTS_AUTENTICADOS:
        logger.warning(f"Tentativa de acesso não autorizada com a chave: {api_key[:5]}...")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token inválido ou revogado.")
    return TENANTS_AUTENTICADOS[api_key]

# =====================================================================
# 2. ESQUEMAS DE DADOS (Pydantic para Validação de Payload)
# =====================================================================
class RegistroAmostra(BaseModel):
    valor_total_declarado: float
    valor_unitario_m2: float
    area_privativa: float
    distancia_polo_m2: float

class RequisicaoAvaliacao(BaseModel):
    area_privativa: float = Field(..., example=75.0)
    qtd_quartos: int = Field(..., example=2)
    padrao_construtivo_id: int = Field(..., example=2)
    texto_matricula_ocr: Optional[str] = Field(None, example="Consta R-3: PENHORA JUDICIAL ativa...")
    base_amostras: List[RegistroAmostra] = Field(..., description="Lista de imóveis semelhantes fornecida pelo banco ou coletada na região.")

# =====================================================================
# 3. MÓDULO MATEMÁTICO: FILTRO IQR + REGRESSÃO LINEAR (AVM)
# =====================================================================
def executar_saneamento_mercado_iqr(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica o critério rigoroso do Intervalo Interquartil para expurgar ruídos de preços."""
    q1 = df['valor_unitario_m2'].quantile(0.25)
    q3 = df['valor_unitario_m2'].quantile(0.75)
    iqr = q3 - q1
    limite_inferior = q1 - (1.5 * iqr)
    limite_superior = q3 + (1.5 * iqr)
    return df[(df['valor_unitario_m2'] >= limite_inferior) & (df['valor_unitario_m2'] <= limite_superior)]

def processar_calculo_estatistico(df_saneado: pd.DataFrame, area_alvo: float):
    """Roda a regressão linear múltipla via MQO e extrai os intervalos de confiança (95%)."""
    Y = df_saneado['valor_unitario_m2']
    X = df_saneado[['area_privativa', 'distancia_polo_m2']]
    X = sm.add_constant(X)
    
    modelo = sm.OLS(Y, X).fit()
    
    # Imóvel alvo posicionado a 400 metros do polo de valorização local para a predição
    vetor_alvo = [1, area_alvo, 400]
    
    _, iv_l, iv_u = wls_prediction_std(modelo, exog=[vetor_alvo], alpha=0.05)
    
    preco_m2_predito = float(modelo.predict([vetor_alvo]))
    
    return {
        "valor_estimado": round(preco_m2_predito * area_alvo, 2),
        "v_min": round(float(iv_l) * area_alvo, 2),
        "v_max": round(float(iv_u) * area_alvo, 2),
        "r2": round(modelo.rsquared, 4)
    }

# =====================================================================
# 4. MÓDULO JURÍDICO: POLÍTICA DE RISCO DE GARANTIAS (Bacen 4.925)
# =====================================================================
def executar_auditoria_juridica(texto_ocr: Optional[str]):
    """Varre o documento e aplica os Hard Blocks corporativos de risco de crédito."""
    if not texto_ocr:
        return True, "RISCO_NAO_AVALIADO"
        
    texto_min = texto_ocr.lower()
    has_penhora = "penhora" in texto_min and "cancelamento" not in texto_min
    has_indisponibilidade = "indisponibilidade" in texto_min
    has_alienacao = "alienação fiduciária" in texto_min and "quitação" not in texto_min
    
    if has_penhora or has_indisponibilidade:
        return False, "ALTO_RISCO_BLOQUEADO"
    elif has_alienacao:
        return True, "MEDIO_RISCO_REQUER_INTERVENIENTE"
    
    return True, "BAIXO_RISCO_APROVADO"

# =====================================================================
# 5. GERADOR DO RELATÓRIO PDF (Armazenamento na Memória RAM / Buffer)
# =====================================================================
def construir_pdf_laudo(tenant_nome, dados_req, res_mat, aprovado_jur, score_jur, n_amostras) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('T1', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor("#1A365D"), spaceAfter=15)
    subtitle_style = ParagraphStyle('T2', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor("#2B6CB0"), spaceAfter=8)
    text_style = ParagraphStyle('T3', parent=styles['Normal'], fontSize=9, leading=13, spaceAfter=6)
    
    story.append(Paragraph("LAUDO TÉCNICO E LEGAL DE GARANTIA IMOBILIÁRIA (AVM)", title_style))
    story.append(Paragraph(f"<b>Emissor Técnico:</b> {tenant_nome} | <b>Data de Emissão:</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", text_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("1. Dados do Imóvel Solicitado", subtitle_style))
    t1 = Table(
    [["Área Privativa", f"{dados_req.area_privativa} m²", "Quantidade de Quartos", f"{dados_req.qtd_quartos}"]], 
    colWidths=[100, 100, 100, 100]
)
    t1.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F7FAFC")), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")), ('PADDING', (0,0), (-1,-1), 5)]))
    story.append(t1)
    
    story.append(Paragraph("2. Avaliação Estatística e Intervalos de Confiança (95%)", subtitle_style))
    t2 = Table([
        ["Métrica", "Valor Total Admissível"],
        ["Limite Mínimo Admissível (Garantia Máxima LTV)", f"R$ {res_mat['v_min']:,.2f}"],
        ["Valor Médio Estimado de Mercado", f"R$ {res_mat['valor_estimado']:,.2f}"],
        ["Limite Máximo Admissível", f"R$ {res_mat['v_max']:,.2f}"]
    ], colWidths=)
    t2.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2B6CB0")), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")), ('PADDING', (0,0), (-1,-1), 5)]))
    story.append(t2)
    
    story.append(Paragraph("3. Status da Esteira de Risco Jurídico", subtitle_style))
    t3 = Table([
        ["Validação Cadastral", "APROVADO" if aprovado_jur else "REPROVADO / BLOQUEADO"],
        ["Classificação de Risco Legal", score_jur]
    ], colWidths=)
    t3.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")), ('PADDING', (0,0), (-1,-1), 5), ('TEXTCOLOR', (1,0), (1,0), colors.HexColor("#38A169") if aprovado_jur else colors.HexColor("#E53E3E"))]))
    story.append(t3)
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# =====================================================================
# 6. ENDPOINT FINAL DE PRODUÇÃO (A MÁGICA INDUSTRIAL)
# =====================================================================
@app.post("/api/v2/credito/avaliar-garntia")
def pipeline_principal_producao(requisicao: RequisicaoAvaliacao, tenant: dict = Depends(validar_inquilino_saas)):
    """Pipeline unificado: Valida inquilino, limpa amostras, calcula preço, analisa matrícula e cospe as respostas."""
    logger.info(f"Requisição iniciada pelo Tenant ID: {tenant['id']} ({tenant['nome']})")
    
    # TRAVA COMERCIAL SAAS: Bloqueia a execução jurídica se o plano for básico
    if "STANDARD" in tenant["plano"] and requisicao.texto_matricula_ocr is not None:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="O módulo de análise documental jurídica via OCR/IA não está ativo no seu plano Standard.")
    
    if len(requisicao.base_amostras) < 5:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amostras de mercado insuficientes para garantir a fundamentação estatística (mínimo de 5).")
        
    # Converter a lista enviada pelo banco em um DataFrame Pandas
    dados_brutos = [{ "valor_total_declarado": am.valor_total_declarado, "valor_unitario_m2": am.valor_unitario_m2, "area_privativa": am.area_privativa, "distancia_polo_m2": am.distancia_polo_m2 } for am in requisicao.base_amostras]
    df_bruto = pd.DataFrame(dados_brutos)
    
    # Fluxo Executivo do Motor
    df_saneado = executar_saneamento_mercado_iqr(df_bruto)
    resultado_matematico = processar_calculo_estatistico(df_saneado, requisicao.area_privativa)
    aprovado_jur, score_jur = executar_auditoria_juridica(requisicao.texto_matricula_ocr)
    
    # Log de Auditoria na Nuvem
