from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import sqlite3
from fastapi import HTTPException
from src.service.database.app_db import AppDB

class Task(BaseModel):
    id: int
    hyper_node_id: Optional[str]
    name: str
    description: Optional[str]
    data: Optional[dict]
    status: str
    priority: int
    created_at: Optional[datetime]
    performed_at: Optional[datetime]
    # Add other fields as necessary 

    @staticmethod
    def fetch_all_tasks():
        app_db = AppDB()
        connection = app_db.get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT * FROM task")
            tasks = cursor.fetchall()
            # Convert fetched data to Task instances
            return [Task(
                id=row[0], 
                hyper_node_id=row[1], 
                name=row[2], 
                description=row[3], 
                data=row[4], 
                status=row[5], 
                priority=row[6], 
                created_at=row[7], 
                performed_at=row[8]) for row in tasks]
        except sqlite3.Error as e:
            raise HTTPException(status_code=500, detail=f"Database error: {e}")
        finally:
            connection.close()
