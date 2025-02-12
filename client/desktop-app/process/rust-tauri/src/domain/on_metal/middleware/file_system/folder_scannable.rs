use anyhow::Result;
use crate::domain::on_metal::middleware::file_system::file_system_entry::FileSystemEntry;

pub trait FolderScannable {
    fn scan(&self) -> Result<(Vec<FileSystemEntry>, Vec<FileSystemEntry>), String>;
} 