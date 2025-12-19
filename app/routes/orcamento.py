from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import json

from openai import OpenAI

from app.usage import check_user_quota, increment_usage
from app.ai_prompts import (
    prompt_pedreiro,
    prompt_eletricista,
    prompt_encanador
)
from app.supabase import supabase
from app.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

router = APIRouter(prefix="/orcamento", tags=["Orçamento"])


# ==========================
# SCHEMA
# ==========================

class OrcamentoRequest(BaseModel):
    user_id: str
    tipo_servico: str  # pedreiro | eletricista | encanador
    margem_percentual: int = Field(ge=0, le=200)


# ==========================
# ENDPOINT
# ==========================

@router.post("/gerar")
def gerar_orcamento(req: OrcamentoRequest):

    # 1️⃣ validar plano e limite
    check_user_quota(req.user_id)

    # 2️⃣ escolher prompt
    if req.tipo_servico == "pedreiro":
        prompt = prompt_pedreiro(req.margem_percentual)
    elif req.tipo_servico == "eletricista":
        prompt = prompt_eletricista(req.margem_percentual)
    elif req.tipo_servico == "encanador":
        prompt = prompt_encanador(req.margem_percentual)
    else:
        raise HTTPException(status_code=400, detail="Tipo de serviço inválido")

    # 3️⃣ chamar OpenAI
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Erro ao gerar orçamento com IA")

    # 4️⃣ parse seguro do JSON
    try:
        resultado = json.loads(response.choices[0].message.content)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Resposta da IA inválida (JSON malformado)"
        )

    # valida campos mínimos
    campos_obrigatorios = [
        "descricao",
        "materiais",
        "tempo_estimado",
        "valor_sugerido",
        "texto_whatsapp"
    ]

    for campo in campos_obrigatorios:
        if campo not in resultado:
            raise HTTPException(
                status_code=500,
                detail=f"Resposta da IA incompleta: campo '{campo}' ausente"
            )

    # 5️⃣ salvar no banco
    supabase.table("orcamentos").insert({
        "user_id": req.user_id,
        "tipo_servico": req.tipo_servico,
        "descricao": resultado["descricao"],
        "valor_total": resultado["valor_sugerido"],
        "materiais": resultado["materiais"],
        "tempo_estimado": resultado["tempo_estimado"]
    }).execute()

    # 6️⃣ incrementar uso (SÓ depois de sucesso)
    increment_usage(req.user_id)

    return {
        "success": True,
        "orcamento": resultado
    }
