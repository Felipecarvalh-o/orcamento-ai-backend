import os
import hmac
import hashlib
from datetime import datetime, timedelta

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from supabase import create_client, Client

# ==========================
# CONFIGURAÇÕES
# ==========================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY or not WEBHOOK_SECRET:
    raise RuntimeError("Variáveis de ambiente não configuradas corretamente")

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY
)

app = FastAPI(title="Orçamento AI Backend")

# ==========================
# HEALTH CHECK
# ==========================

@app.get("/health")
def health():
    return {"status": "ok"}

# ==========================
# PLANOS
# ==========================

PLAN_LIMITS = {
    "basic": 30,
    "pro": 100,
    "premium": 300
}

# ==========================
# UTILIDADES
# ==========================

def validar_assinatura(payload: bytes, assinatura_recebida: str):
    assinatura_calculada = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(assinatura_calculada, assinatura_recebida):
        raise HTTPException(status_code=401, detail="Assinatura do webhook inválida")


def verificar_plano_e_limite(user_id: str):
    res = supabase.table("subscriptions") \
        .select("*") \
        .eq("user_id", user_id) \
        .single() \
        .execute()

    if not res.data:
        raise HTTPException(status_code=403, detail="Usuário sem assinatura")

    sub = res.data

    if sub["status"] != "active":
        raise HTTPException(status_code=403, detail="Assinatura inativa")

    # Reset automático
    if sub["renews_at"]:
        renews_at = datetime.fromisoformat(sub["renews_at"])
        if datetime.utcnow() > renews_at:
            supabase.table("subscriptions").update({
                "current_usage": 0,
                "renews_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }).eq("user_id", user_id).execute()

            sub["current_usage"] = 0

    if sub["current_usage"] >= sub["monthly_limit"]:
        raise HTTPException(
            status_code=429,
            detail="Limite mensal de orçamentos atingido"
        )


def incrementar_uso(user_id: str):
    """
    Incrementa +1 no uso mensal
    """
    res = supabase.table("subscriptions") \
        .select("current_usage") \
        .eq("user_id", user_id) \
        .single() \
        .execute()

    atual = res.data["current_usage"]

    supabase.table("subscriptions").update({
        "current_usage": atual + 1,
        "updated_at": datetime.utcnow().isoformat()
    }).eq("user_id", user_id).execute()

# ==========================
# ENDPOINT TESTE ORÇAMENTO
# ==========================

@app.post("/generate-budget")
def generate_budget(user_id: str):
    verificar_plano_e_limite(user_id)

    budget = {
        "descricao": "Serviço de construção",
        "valor_total": 1500
    }

    incrementar_uso(user_id)

    return {
        "success": True,
        "budget": budget
    }

# ==========================
# WEBHOOK CAKTO
# ==========================

@app.post("/webhook/cakto")
async def webhook_cakto(request: Request):
    payload_bytes = await request.body()
    payload = await request.json()

    assinatura = request.headers.get("X-Cakto-Signature")
    if not assinatura:
        raise HTTPException(status_code=400, detail="Assinatura ausente")

    validar_assinatura(payload_bytes, assinatura)

    event = payload.get("event")
    data = payload.get("data", {})

    user_id = data.get("external_id")
    plano = data.get("plan", "basic")

    if not user_id:
        raise HTTPException(status_code=400, detail="external_id ausente")

    supabase.table("payment_logs").insert({
        "provider": "cakto",
        "event": event,
        "payload": payload
    }).execute()

    if event == "payment.approved":
        limite = PLAN_LIMITS.get(plano, 30)

        supabase.table("subscriptions").upsert({
            "user_id": user_id,
            "plan": plano,
            "status": "active",
            "monthly_limit": limite,
            "current_usage": 0,
            "renews_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }).execute()

    elif event in ["payment.canceled", "subscription.canceled"]:
        supabase.table("subscriptions").update({
            "status": "canceled",
            "updated_at": datetime.utcnow().isoformat()
        }).eq("user_id", user_id).execute()

    elif event in ["payment.failed", "payment.past_due"]:
        supabase.table("subscriptions").update({
            "status": "past_due",
            "updated_at": datetime.utcnow().isoformat()
        }).eq("user_id", user_id).execute()

    return JSONResponse(content={"received": True})
