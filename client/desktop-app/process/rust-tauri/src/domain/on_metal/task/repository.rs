use async_trait::async_trait;
use anyhow::Result;
use super::model::{Task, TaskStatus};

#[async_trait]
pub trait TaskRepository: Send + Sync {
    async fn load_tasks(&self, 
        status: Option<TaskStatus>, 
        hyper_node_id: Option<String>
    ) -> Result<Vec<Box<dyn Task>>>;
    
    async fn save_task(&self, task: Box<dyn Task>) -> Result<()>;
    
    async fn update_task_status(
        &self, 
        task_id: i64, 
        status: TaskStatus,
        performed_at: Option<chrono::DateTime<chrono::Utc>>
    ) -> Result<()>;
    
    async fn get_tasks_by_priority(
        &self,
        min_priority: i32,
        status: Option<TaskStatus>
    ) -> Result<Vec<Box<dyn Task>>>;
}
