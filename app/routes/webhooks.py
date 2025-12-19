from fastapi import APIRouter, Request, Header, HTTPException
from supabase import create_client
import os
import json

router = APIRouter()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")


@router.post("/webhooks/payment")
async def payment_webhook(
    request: Request,
    x_webhook_secret: str = Header(None)
):
    """
    Webhook para Cakto / Kiwify
    """

    # 1️⃣ Segurança básica
    if x_webhook_secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")

    payload = await request.json()

    event = payload.get("event")
    user_id = payload.get("customer", {}).get("external_id")
    plan = payload.get("plan", "basic")

    # 2️⃣ Log bruto do webhook
    supabase.table("payment_logs").insert({
        "provider": "cakto_ou_kiwify",
        "event": event,
        "payload": payload
    }).execute()

    # 3️⃣ Definição de planos
    PLAN_LIMITS = {
        "basic": 30,
        "pro": 200,
        "premium": 9999
    }

    # 4️⃣ Eventos tratados
    if event == "payment_approved":
        supabase.table("subscriptions").upsert({
            "user_id": user_id,
            "plan": plan,
            "status": "active",
            "monthly_limit": PLAN_LIMITS.get(plan, 30)
        }).execute()

    elif event in ["payment_canceled", "payment_overdue"]:
        supabase.table("subscriptions").update({
            "status": "inactive"
        }).eq("user_id", user_id).execute()

    return {"ok": True}
