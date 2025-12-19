from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.supabase import supabase

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login")
def login(data: LoginRequest):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": data.email,
            "password": data.password
        })
        return {
            "access_token": response.session.access_token,
            "user": response.user
        }
    except Exception:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

