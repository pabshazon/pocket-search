from fastapi import APIRouter, HTTPException
from src.service.database.models.task import Task
from src.service.database.models.hnode import HNode
from src.domain.on_metal.tasks.Analyzer import Analyzer
import logging

class TasksController:
    def consume_tasks_table(self):
        try:
            logging.debug("> TASK: Consuming tasks SQLite table...")
            tasks = Task.fetch_all_tasks()
            for task in tasks:
                if task.name == "Analyze-new":
                    hnode = HNode.fetch_by_hyper_node_id(task.hyper_node_id)
                    if hnode.is_file == 1:
                        Analyzer.analyze_file(hnode)
                    elif hnode.is_folder == 1:
                        Analyzer.analyze_folder(hnode)
                    else:
                        print("Unknown")
                        raise HTTPException(status_code=400, detail="Unknown task type")

        except HTTPException as e:
            logging.error(f"HTTPException occurred: {e.detail}")
            raise e
        except Exception as e:
            logging.error(f"An unexpected error occurred: {str(e)}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred while processing tasks.")
        
        print("All tasks done.")

        response = {
            "result": f"All tasks Done. Number of tasks performed: {len(tasks)}"
        }
        
        return response
