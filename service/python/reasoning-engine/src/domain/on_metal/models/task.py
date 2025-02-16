from pydantic import BaseModel, validator
from typing import Optional, Dict, Any
from datetime import datetime
import sqlite3
from fastapi import HTTPException
from src.service.database.app_db import AppDB

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
    def fetch_all_tasks():
        connection = AppDB().get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT * FROM task")
            tasks = cursor.fetchall()
            
            # Debug: Print fetched rows
            print("Fetched rows:", tasks)
            
            # Convert fetched data to Task instances
            task_list = []
            for row in tasks:
                # Debug: Print each row's data field
                print("Row data field before conversion:", row[4])
                
                # Convert 'null' string to an empty dictionary
                data_field = row[4] if row[4] != 'null' else {}
                
                task = Task(
                    id=row[0], 
                    hyper_node_id=row[1], 
                    name=row[2], 
                    description=row[3], 
                    data=data_field,  # Use the converted data field
                    status=row[5], 
                    priority=row[6], 
                    created_at=row[7], 
                    performed_at=row[8]
                )
                
                # Debug: Print the task instance
                print("Created Task instance:", task)
                
                task_list.append(task)
            
            return task_list
        except sqlite3.Error as e:
            raise HTTPException(status_code=500, detail=f"Database error: {e}")
        finally:
            connection.close()
