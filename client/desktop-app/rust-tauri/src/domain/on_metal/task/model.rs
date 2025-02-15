use async_trait::async_trait;
use anyhow::Result;
use std::fmt::Debug;
use chrono::{DateTime, Utc};
use serde::{Serialize, Deserialize};
use serde_json::Value;

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum TaskStatus {
    Pending,
    InProgress,
    Completed,
    Failed,
}

#[derive(Debug, Clone, PartialEq)]
pub struct TaskMetadata {
    pub id: Option<i64>,
    pub ref_hyper_node_id: Option<String>,
    pub name: String,
    pub description: Option<String>,
    pub data: Option<Value>,          // JSON data
    pub status: TaskStatus,
    pub priority: i32,
    pub created_at: Option<DateTime<Utc>>,
    pub performed_at: Option<DateTime<Utc>>,
}

impl TaskMetadata {
    pub fn new(name: String, priority: i32) -> Self {
        Self {
            id: None,
            ref_hyper_node_id: None,
            name,
            description: None,
            data: None,
            status: TaskStatus::Pending,
            priority,
            created_at: None,
            performed_at: None,
        }
    }
}

#[async_trait]
pub trait Task: Send + Sync + Debug {
    fn metadata(&self) -> &TaskMetadata;
    fn metadata_mut(&mut self) -> &mut TaskMetadata;
    async fn execute(&self) -> Result<()>;
} 
