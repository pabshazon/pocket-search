from fastapi import FastAPI, Body, Header

from typing import Optional
import os
import sys

from src.controllers.tasks_controller import TasksController


sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


app = FastAPI()

@app.get("/hello")
async def root():
    return {"message": "Status Online"}
    
@app.get("/consume_tasks")
async def consume_tasks():
    tasks_controller = TasksController()
    result = tasks_controller.consume_tasks_table()
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
