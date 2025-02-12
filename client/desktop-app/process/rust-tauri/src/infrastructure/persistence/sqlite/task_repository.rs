use async_trait::async_trait;
use anyhow::{Result, Context};
use tauri::AppHandle;
use chrono::Utc;
use serde_json::Value;

use crate::domain::on_metal::task::{
    model::{Task, TaskMetadata, TaskStatus},
    repository::TaskRepository,
};
use crate::service::database::app_db;

pub struct SqliteTaskRepository {
    app_handle: AppHandle,
}

impl SqliteTaskRepository {
    pub fn new(app_handle: AppHandle) -> Self {
        Self { app_handle }
    }
}

#[async_trait]
impl TaskRepository for SqliteTaskRepository {
    async fn load_active_tasks(&self, task_type: Option<TaskType>) -> Result<Vec<Box<dyn Task>>> {
        let pool = app_db::get_pool(&self.app_handle).await?;

        let query = match task_type {
            Some(_) => {
                sqlx::query!(
                    r#"
                    SELECT id, ref_hyper_node_id, name, description, data, status, priority, 
                           created_at, performed_at 
                    FROM task 
                    WHERE status != 'Completed' AND status != 'Failed'
                    "#
                )
            },
            None => {
                sqlx::query!(
                    r#"
                    SELECT id, ref_hyper_node_id, name, description, data, status, priority, 
                           created_at, performed_at 
                    FROM task 
                    WHERE status != 'Completed' AND status != 'Failed'
                    "#
                )
            }
        };

        let rows = query.fetch_all(&pool)
            .await
            .context("Failed to fetch tasks")?;

        let tasks: Vec<Box<dyn Task>> = rows
            .into_iter()
            .map(|row| {
                let metadata = TaskMetadata {
                    id: Some(row.id),
                    ref_hyper_node_id: row.ref_hyper_node_id,
                    name: row.name,
                    description: row.description,
                    data: row.data.and_then(|d| serde_json::from_str(&d).ok()),
                    status: serde_json::from_str(&row.status).unwrap_or(TaskStatus::Pending),
                    priority: row.priority,
                    created_at: row.created_at,
                    performed_at: row.performed_at,
                };
                
                // Create appropriate task type based on data
                if let Some(Value::Object(data)) = metadata.data.as_ref() {
                    if data.get("type").and_then(|v| v.as_str()) == Some("file_sync") {
                        if let Some(path) = data.get("path").and_then(|v| v.as_str()) {
                            return Box::new(FileSyncTask {
                                metadata,
                                path: PathBuf::from(path),
                            }) as Box<dyn Task>;
                        }
                    }
                }
                
                // Default to base task if type cannot be determined
                Box::new(BaseTask { metadata }) as Box<dyn Task>
            })
            .collect();

        Ok(tasks)
    }

    async fn save_task(&self, task: Box<dyn Task>) -> Result<()> {
        let pool = app_db::get_pool(&self.app_handle).await?;
        let metadata = task.metadata();

        sqlx::query!(
            r#"
            INSERT INTO task 
                (ref_hyper_node_id, name, description, data, status, priority, created_at, performed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            "#,
            metadata.ref_hyper_node_id,
            metadata.name,
            metadata.description,
            metadata.data.as_ref().map(|v| v.to_string()),
            serde_json::to_string(&metadata.status)?,
            metadata.priority,
            metadata.created_at.unwrap_or_else(|| Utc::now()),
            metadata.performed_at,
        )
        .execute(&pool)
        .await
        .context("Failed to save task")?;

        Ok(())
    }

    // Implement other repository methods...
} 