from pydantic import BaseModel, validator
from typing import Optional, Dict, Any
from datetime import datetime
import sqlite3
from fastapi import HTTPException
from src.service.database.app_db import AppDB
import json
from src.domain.on_metal.logger import get_logger
logger = get_logger(__name__)


class Task(BaseModel):
    id: int
    hyper_node_id: Optional[str]
    name: str
    description: Optional[str]
    status: str
    priority: int
    created_at: Optional[datetime]
    performed_at: Optional[datetime]
    # Add other fields as necessary 

    @staticmethod
    def fetch_all_tasks():
        connection = AppDB().get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT * FROM task")
            columns = [column[0] for column in cursor.description]
            tasks = cursor.fetchall()
            
            task_list = [Task(**dict(zip(columns, row))) for row in tasks]
            return task_list
        except sqlite3.Error as e:
            raise HTTPException(status_code=500, detail=f"Database error: {e}")
        finally:
            connection.close()
