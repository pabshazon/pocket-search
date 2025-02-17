from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import sqlite3
from fastapi import HTTPException
from src.service.database.app_db import AppDB
import json
import logging

def log_error(error_message: str):
    """Helper function to log errors."""
    logger = logging.getLogger(__name__)
    logger.error(error_message)

class HNode(BaseModel):
    id: str
    name: str
    parent_hyper_node_id: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    is_folder: int
    is_file: int
    is_inside_fs_file: int
    fs_full_path: str
    fs_file_name: Optional[str]
    fs_inode: Optional[int]
    fs_file_extension: Optional[str]
    fs_file_size: Optional[int]
    fs_device_id: Optional[int]
    fs_user_id: Optional[int]
    fs_group_id: Optional[int]
    cs_parent_node: Optional[int]
    cs_what_is_fs_folder_about: Optional[str]
    cs_what_is_fs_file_about: Optional[str]
    cs_hnode_title: Optional[str]
    cs_hnode_summary: Optional[str]
    cs_explain_contains: Optional[str]
    cs_what_info_can_be_found: Optional[str]
    cs_tags_obvious: Optional[str]
    cs_tags_extended: Optional[str]
    node_vision_type: Optional[str]
    node_text_data: Optional[str]
    node_vision_data: Optional[bytes]
    open_with_application_type: Optional[str]
    cs_ns_full_path: Optional[str]
    last_updated_semantics_changes: Optional[datetime]

    @staticmethod
    def fetch_by_hyper_node_id(hyper_node_id: str):
        connection = AppDB().get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT * FROM hyper_node WHERE id = ?", (hyper_node_id,))
            columns = [column[0] for column in cursor.description]
            row = cursor.fetchone()
            if row:
                return HNode(**dict(zip(columns, row)))
            else:
                raise HTTPException(status_code=404, detail="HNode not found")
        except sqlite3.Error as e:
            # Log the database error before raising the exception
            log_error(f"Database error: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {e}")
        except Exception as e:
            # Log the general error before raising the exception
            log_error(f"Unexpected error: {e}")
            raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
        finally:
            connection.close()
