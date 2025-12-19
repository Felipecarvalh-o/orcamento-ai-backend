from datetime import datetime
from fastapi import HTTPException
from app.supabase import supabase

# Limites por plano
PLAN_LIMITS = {
    "basic": 10,
    "pro": 50,
    "premium": None  # ilimitado
}

def get_active_subscription(user_id: str):
    """
    Busca a assinatura ativa do usuário
    """
    response = (
        supabase
        .table("subscriptions")
        .select("*")
        .eq("user_id", user_id)
        .eq("status", "active")
        .single()
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=403,
            detail="Você não possui uma assinatura ativa."
        )

    return response.data


def check_and_update_usage(user_id: str):
    """
    Verifica limite mensal e incrementa uso
    """
    subscription = get_active_subscription(user_id)

    plan = subscription["plan"]
    limit = PLAN_LIMITS.get(plan)

    # Reset automático se passou da renovação
    renews_at = subscription.get("renews_at")
    now = datetime.utcnow()

    if renews_at and now >= datetime.fromisoformat(renews_at):
        supabase.table("subscriptions").update({
            "current_usage": 0,
            "renews_at": now.replace(month=now.month + 1).isoformat()
        }).eq("id", subscription["id"]).execute()

        subscription["current_usage"] = 0

    # Plano ilimitado
    if limit is None:
        return True

    if subscription["current_usage"] >= limit:
        raise HTTPException(
            status_code=403,
            detail="Você atingiu o limite mensal do seu plano."
        )

    # Incrementa uso
    supabase.table("subscriptions").update({
        "current_usage": subscription["current_usage"] + 1,
        "updated_at": now.isoformat()
    }).eq("id", subscription["id"]).execute()

    return True
