from datetime import datetime
from fastapi import HTTPException
from supabase import create_client
import os

# Conexão com Supabase
supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_SERVICE_ROLE_KEY"]
)

# Limites por plano
PLAN_LIMITS = {
    "basic": 20,
    "pro": 100,
    "premium": 999999  # ilimitado
}

def check_user_quota(user_id: str):
    """
    Verifica se o usuário tem assinatura ativa
    e se ainda pode gerar orçamentos no mês
    """

    res = supabase.table("subscriptions") \
        .select("*") \
        .eq("user_id", user_id) \
        .eq("status", "active") \
        .single() \
        .execute()

    if not res.data:
        raise HTTPException(
            status_code=403,
            detail="Você não possui uma assinatura ativa."
        )

    sub = res.data
    limit = PLAN_LIMITS.get(sub["plan"], 0)

    if sub["current_usage"] >= limit:
        raise HTTPException(
            status_code=403,
            detail="Limite mensal de orçamentos atingido."
        )

    # Reset automático se passou da data de renovação
    if sub["renews_at"] and datetime.utcnow() > datetime.fromisoformat(sub["renews_at"]):
        supabase.table("subscriptions") \
            .update({
                "current_usage": 0,
                "renews_at": datetime.utcnow()
            }) \
            .eq("id", sub["id"]) \
            .execute()

def increment_usage(user_id: str):
    """
    Incrementa uso após gerar orçamento
    """
    supabase.table("subscriptions") \
        .update({
            "current_usage": supabase.rpc("increment", {})
        }) \
        .eq("user_id", user_id) \
        .execute()
