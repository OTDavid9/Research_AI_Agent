from fastapi import FastAPI, WebSocket, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from app.chat_app.openai_client import LLMClient
from app.model.chat_schema import ChatRequest, ChatResponse  

app = FastAPI()
llm = LLMClient()


# ------------------------
# HTTP Endpoint
# ------------------------

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=BASE_DIR.parent / "app/templates")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )

@app.post("/chat")
async def chat(chat_request: ChatRequest):
    response = llm.chat(session_id=chat_request.session_id, prompt=chat_request.prompt) # type: ignore
    return ChatResponse(session_id=chat_request.session_id, response=response) # type: ignore

# ------------------------
# WebSocket Endpoint
# ------------------------
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str = "default"):
    await websocket.accept()

    while True:
        try:
            prompt = await websocket.receive_text()

            response = llm.chat(session_id=session_id, prompt=prompt)

            # send full response (simple version)
            await websocket.send_text(response)


        except Exception as e:
            await websocket.send_text(f"Error: {str(e)}")


@app.websocket("/ws/stream/{session_id}")
async def websocket_endpoint_stream(websocket: WebSocket, session_id: str):
    await websocket.accept()

    while True:
        try:
            prompt = await websocket.receive_text()

            for token in llm.chat_stream(session_id, prompt):
                await websocket.send_text(token)

            # # optional: signal end of message
            # await websocket.send_text("[DONE]")

        except Exception as e:
            await websocket.send_text(f"Error: {str(e)}") 