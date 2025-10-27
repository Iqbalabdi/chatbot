from fastapi import APIRouter
from pydantic import BaseModel
from app.auth.service.jwt_service import jwt_service

router = APIRouter()

class LoginRequest(BaseModel):
    user_id: str

@router.post("/login")
async def login(request: LoginRequest):
    token = jwt_service.create_token(request.user_id)
    return {"access_token": token, "token_type": "bearer"}