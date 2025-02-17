from pydantic import BaseModel, validator
from typing import Optional, Dict, Any
from datetime import datetime
import sqlite3
from fastapi import HTTPException
from src.service.database.app_db import AppDB
import json
import logging

class Task(BaseModel):
    id: int
    hyper_node_id: Optional[str]
    name: str
    description: Optional[str]
    data: Optional[Dict[str, Any]] = None
    status: str
    priority: int
    created_at: Optional[datetime]
    performed_at: Optional[datetime]
    # Add other fields as necessary 

    @validator('data', pre=True, always=True)
    def set_data(cls, v):
        return v or {}

    @staticmethod
    def _deserialize_task(columns, row):
        """Helper method to deserialize a database row into a Task instance using column names."""
        task_attributes = dict(zip(columns, row))
        task_attributes['data'] = json.loads(task_attributes['data']) if task_attributes['data'] and task_attributes['data'] != 'null' else {}
        return Task(**task_attributes)

    @staticmethod
    def fetch_all_tasks():
        connection = AppDB().get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT * FROM task")
            columns = [column[0] for column in cursor.description]
            tasks = cursor.fetchall()
            
            task_list = [Task._deserialize_task(columns, row) for row in tasks]
            return task_list
        except sqlite3.Error as e:
            raise HTTPException(status_code=500, detail=f"Database error: {e}")
        finally:
            connection.close()
