from fastapi import FastAPI, Body, Header
# from src.controllers.embeddings_controllers import EmbeddingsController
from typing import Optional
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

app = FastAPI()

@app.get("/hello")
async def root():
    return {"message": "Status Online"}
    
# @app.post("/api/embeddings")
# async def embeddings( payload: dict = Body(...), user_agent: Optional[str] = Header(None)):
#     text  = payload.get("text")
#     model = payload.get("model")
#     task  = payload.get("task")
#
#     return await EmbeddingsController.embeddings(text, model, task)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
