from fastapi import APIRouter, Request, HTTPException
from app.config.plans import PLANS
from app.services.supabase import supabase
import os

router = APIRouter()

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

@router.post("/webhook/cakto")
async def cakto_webhook(request: Request):
    payload = await request.json()

    # 🔐 validação simples
    if payload.get("secret") != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Webhook inválido")

    event = payload.get("event")
    data = payload.get("data", {})

    # salva log bruto
    supabase.table("payment_logs").insert({
        "provider": "cakto",
        "event": event,
        "payload": payload
    }).execute()

    # eventos importantes
    if event == "payment.approved":
        user_id = data["customer"]["external_id"]  # seu user_id
        product_name = data["product"]["name"]

        if product_name not in PLANS:
            raise HTTPException(status_code=400, detail="Plano desconhecido")

        plan_info = PLANS[product_name]

        supabase.table("subscriptions").upsert({
            "user_id": user_id,
            "plan": plan_info["plan"],
            "status": "active",
            "monthly_limit": plan_info["monthly_limit"],
            "current_usage": 0
        }).execute()

    elif event in ["subscription.canceled", "payment.failed"]:
        user_id = data["customer"]["external_id"]

        supabase.table("subscriptions") \
            .update({"status": "inactive"}) \
            .eq("user_id", user_id) \
            .execute()

    return {"status": "ok"}
