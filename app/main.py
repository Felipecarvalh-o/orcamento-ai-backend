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

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Variáveis do Supabase não configuradas")

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY
)

app = FastAPI(title="Orçamento AI Backend")

# ==========================
# HEALTH CHECK (Render)
# ==========================

@app.get("/health")
def health():
    return {"status": "ok"}

# ==========================
# UTIL: validar assinatura
# ==========================

def validar_assinatura(payload: bytes, assinatura_recebida: str):
    assinatura_calculada = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(assinatura_calculada, assinatura_recebida):
        raise HTTPException(status_code=401, detail="Assinatura inválida")

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

    user_id = data.get("external_id")  # ID do usuário no seu sistema
    plano = data.get("plan", "basic")

    # ==========================
    # LOG DO WEBHOOK
    # ==========================
    supabase.table("payment_logs").insert({
        "provider": "cakto",
        "event": event,
        "payload": payload
    }).execute()

    # ==========================
    # EVENTOS
    # ==========================

    if event == "payment.approved":
        limite = 30 if plano == "basic" else 100

        supabase.table("subscriptions").upsert({
            "user_id": user_id,
            "plan": plano,
            "status": "active",
            "monthly_limit": limite,
            "current_usage": 0,
            "renews_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }).execute()

    elif event == "payment.canceled":
        supabase.table("subscriptions").update({
            "status": "canceled",
            "updated_at": datetime.utcnow().isoformat()
        }).eq("user_id", user_id).execute()

    elif event == "payment.failed":
        supabase.table("subscriptions").update({
            "status": "past_due",
            "updated_at": datetime.utcnow().isoformat()
        }).eq("user_id", user_id).execute()

    return JSONResponse(content={"received": True})
