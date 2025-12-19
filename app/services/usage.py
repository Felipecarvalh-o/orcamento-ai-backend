from fastapi import HTTPException
from app.services.supabase import supabase

def check_usage(user_id: str):
    res = supabase.table("subscriptions") \
        .select("*") \
        .eq("user_id", user_id) \
        .eq("status", "active") \
        .single() \
        .execute()

    sub = res.data

    if not sub:
        raise HTTPException(
            status_code=403,
            detail="Você não possui assinatura ativa"
        )

    if sub["current_usage"] >= sub["monthly_limit"]:
        raise HTTPException(
            status_code=403,
            detail="Limite mensal de orçamentos atingido"
        )

    return sub
