from fastapi import HTTPException

from src.domain.on_metal.logger         import get_logger
from src.domain.on_metal.tasks.Analyzer import Analyzer
from src.service.database.models.task   import Task
from src.service.database.models.hnode  import HNode

logger = get_logger(__name__)

class TasksController:
    @staticmethod
    async def consume_tasks_table():
        try:
            tasks = Task.fetch_all_tasks()
            logger.debug(f">> TASK: Consuming {len(tasks)} tasks from SQLite table...")
            for task in tasks:
                if task.name == "Analyze-new":
                    hnode = HNode.fetch_by_hyper_node_id(task.hyper_node_id)
                    if hnode.is_file == 1:
                        await Analyzer.analyze_file(hnode)
                    elif hnode.is_folder == 1:
                        Analyzer.analyze_folder(hnode)
                    else:
                        logger.debug("Unknown")
                        raise HTTPException(status_code=400, detail="Unknown task type")

        except HTTPException as e:
            logger.error(f"HTTPException occurred: {e.detail}")
            raise e
        except Exception as e:
            logger.error(f"An unexpected error occurred: {str(e)}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred while processing tasks.")
        
        logger.debug(f">> Processed {len(tasks)} tasks done.")

        response = {
            "result": f"All tasks Done. Number of tasks performed: {len(tasks)}"
        }
        
        return response
