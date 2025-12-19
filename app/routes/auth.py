from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.supabase import supabase

router = APIRouter(prefix="/auth", tags=["Auth"])

class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
def login(data: LoginRequest):
    try:
        res = supabase.auth.sign_in_with_password({
            "email": data.email,
            "password": data.password
        })

        if not res.session:
            raise HTTPException(status_code=401, detail="Credenciais inválidas")

        return {
            "access_token": res.session.access_token,
            "user": {
                "id": res.user.id,
                "email": res.user.email
            }
        }

    except Exception:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
