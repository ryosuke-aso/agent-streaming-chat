import os
import logging
from typing import List
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import boto3
from strands import Agent
from strands.models import BedrockModel
from strands.session.s3_session_manager import S3SessionManager


# --- Configuration ---
BUCKET_NAME="your-s3-bucket-name"
PREFIX="strands-session-data"
REGION="ap-northeast-1"
MODEL="global.amazon.nova-2-lite-v1:0"

# --- Logging Config ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- LLM Definition ---
model = BedrockModel(
    model_id=MODEL,
    region_name=REGION,
    boto_session=boto3.Session(
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=REGION
    )
)

# --- Pydantic models ---
class Msg(BaseModel):
    role: str
    content: list

class MsgResponse(BaseModel):
    message: Msg
    message_id: str
    created_at: str
    updated_at: str

class ChatRequest(BaseModel):
    user_id: str
    message: str

# --- FastAPI app setup ---
app = FastAPI(
    title="Agent API",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/chats", response_model=List[MsgResponse])
async def get_chat(user_id: str):
    session_manager = S3SessionManager(
        session_id=user_id,
        bucket=BUCKET_NAME,
        prefix=PREFIX,
        region_name=REGION
    )
    messages = session_manager.list_messages(session_id=user_id, agent_id="default")
    logging.info(f"messages: {messages}")

    return [
        MsgResponse(
            message=Msg(
                role=msg.message.get("role", "assistant"),
                content=msg.message.get("content", [])
            ),
            message_id=str(msg.message_id),
            created_at=msg.created_at,
            updated_at=msg.updated_at
        )
        for msg in messages
    ]

@app.post("/chats")
async def post_chat(data: ChatRequest):
    session_manager = S3SessionManager(
        session_id=data.user_id,
        bucket=BUCKET_NAME,
        prefix=PREFIX,
        region_name=REGION
    )
    async def generate():
        agent = Agent(
            model=model,
            session_manager=session_manager,
            system_prompt=(
                "You are a helpful agent."
                "You must answer shortly and clearly."
            )
        )
        try:
            async for event in agent.stream_async(data.message):
                if "data" in event:
                    # Only stream text chunks to the client
                        yield event["data"]
                else:
                    logger.info(f"event: {event}")
        except Exception as e:
            yield f"Error: {str(e)}"

    return StreamingResponse(
        generate(),
        media_type="text/plain"
    )



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
