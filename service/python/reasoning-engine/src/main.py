from fastapi import FastAPI

import os
import sys

from src.domain.on_metal.logger       import init_logging, get_logger
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
    # Initialize with custom settings
    init_logging(
        show_filepath=True,
        level=logging.DEBUG,
        log_file="logs/app.log"
    )
    
    logger = get_logger(__name__)
    logger.info("> Application started")

    logger.info("> Starting FastAPI server...")
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

