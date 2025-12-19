from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
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


class OrcamentoRequest(BaseModel):
    user_id: str
    tipo_servico: str   # pedreiro | eletricista | encanador
    margem_percentual: int


@router.post("/gerar")
def gerar_orcamento(req: OrcamentoRequest):

    # 1️⃣ validar plano
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

    # 3️⃣ chamar OpenAI (SDK NOVO)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4
    )

    resultado = json.loads(response.choices[0].message.content)

    # 4️⃣ salvar no banco
    supabase.table("orcamentos").insert({
        "user_id": req.user_id,
        "tipo_servico": req.tipo_servico,
        "descricao": resultado["descricao"],
        "valor_total": resultado["valor_sugerido"],
        "materiais": resultado["materiais"],
        "tempo_estimado": resultado["tempo_estimado"]
    }).execute()

    # 5️⃣ incrementar uso
    increment_usage(req.user_id)

    return {
        "success": True,
        "orcamento": resultado
    }
