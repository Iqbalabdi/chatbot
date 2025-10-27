from pydantic import BaseModel, Field
from typing import List

class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role,'user' or 'assistant'")
    content: str = Field(..., description="The message text")

class ChatSession(BaseModel):
    user_id: str
    history: List[ChatMessage] = Field(default_factory=list)

class ChatRequest(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    user_id: str
    reply: str

class StreamChunk(BaseModel):
    token: str
    is_final: bool = False