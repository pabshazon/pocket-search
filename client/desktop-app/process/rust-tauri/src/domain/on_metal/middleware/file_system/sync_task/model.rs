use std::path::PathBuf;
use async_trait::async_trait;
use anyhow::Result;
use serde_json::json;

use crate::domain::on_metal::task::model::{Task, TaskMetadata};

#[derive(Debug)]
pub struct FileSyncTask {
    metadata: TaskMetadata,
    path: PathBuf,
}

impl FileSyncTask {
    pub fn new(path: PathBuf, priority: i32) -> Self {
        let mut metadata = TaskMetadata::new(
            format!("File Sync: {}", path.display()),
            priority
        );
        
        metadata.data = Some(json!({
            "path": path.to_string_lossy(),
            "type": "file_sync"
        }));

        Self {
            metadata,
            path,
        }
    }
}

#[async_trait]
impl Task for FileSyncTask {
    fn metadata(&self) -> &TaskMetadata {
        &self.metadata
    }

    fn metadata_mut(&mut self) -> &mut TaskMetadata {
        &mut self.metadata
    }

    async fn execute(&self) -> Result<()> {
        // Implementation for file sync task execution
        Ok(())
    }
} 