from datetime import datetime, timedelta
from fastapi import HTTPException
from supabase import create_client
import os

# ==========================
# CONEXÃO SUPABASE
# ==========================

supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_SERVICE_ROLE_KEY"]
)

# ==========================
# VERIFICA PLANO E LIMITE
# ==========================

def check_user_quota(user_id: str):
    """
    - Verifica assinatura ativa
    - Verifica limite mensal
    - Reseta contador se passou da renovação
    """

    res = supabase.table("subscriptions") \
        .select("*") \
        .eq("user_id", user_id) \
        .single() \
        .execute()

    if not res.data:
        raise HTTPException(
            status_code=403,
            detail="Usuário sem assinatura."
        )

    sub = res.data

    if sub["status"] != "active":
        raise HTTPException(
            status_code=403,
            detail="Assinatura inativa."
        )

    # 🔁 Reset automático na renovação
    if sub["renews_at"]:
        renews_at = datetime.fromisoformat(sub["renews_at"])
        if datetime.utcnow() > renews_at:
            supabase.table("subscriptions").update({
                "current_usage": 0,
                "renews_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", sub["id"]).execute()

            sub["current_usage"] = 0

    # 🚫 Limite atingido
    if sub["current_usage"] >= sub["monthly_limit"]:
        raise HTTPException(
            status_code=429,
            detail="Limite mensal de orçamentos atingido."
        )

# ==========================
# INCREMENTA USO
# ==========================

def increment_usage(user_id: str):
    """
    Incrementa o contador de uso em +1
    """

    # Busca uso atual
    res = supabase.table("subscriptions") \
        .select("current_usage") \
        .eq("user_id", user_id) \
        .single() \
        .execute()

    if not res.data:
        return

    novo_valor = res.data["current_usage"] + 1

    supabase.table("subscriptions").update({
        "current_usage": novo_valor,
        "updated_at": datetime.utcnow().isoformat()
    }).eq("user_id", user_id).execute()
