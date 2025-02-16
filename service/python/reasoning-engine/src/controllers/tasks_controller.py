from fastapi import APIRouter, HTTPException
from src.domain.on_metal.models.task import Task
import logging

class TasksController:
    def consume_tasks_table(self):
        try:
            tasks = Task.fetch_all_tasks()
            for task in tasks:
                print("task")
                print(task)
        except HTTPException as e:
            logging.error(f"HTTPException occurred: {e.detail}")
            raise e
        except Exception as e:
            logging.error(f"An unexpected error occurred: {str(e)}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred while processing tasks.")
        
        response = {
            "result": f"All tasks Done. Number of tasks performed: {len(tasks)}"
        }
        
        return response