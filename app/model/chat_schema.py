from pydantic import BaseModel

class ChatRequest(BaseModel):
    prompt: str
    session_id: str = "default"  # default session  


class ChatResponse(BaseModel):
    session_id: str
    response: str