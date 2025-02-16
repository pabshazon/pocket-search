from fastapi import APIRouter, HTTPException
from src.domain.on_metal.models.task import Task

class TasksController:
    def consume_tasks_table(self):
        try:
            tasks = Task.fetch_all_tasks()
            for task in tasks:
                print("task")
                print(task)
        except HTTPException as e:
            raise e
        
        response = {
            "result": f"All tasks Done. Number of tasks performed: {len(tasks)}"
        }
        
        return response