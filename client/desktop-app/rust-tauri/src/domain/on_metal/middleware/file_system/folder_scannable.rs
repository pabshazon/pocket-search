use crate::domain::on_metal::middleware::file_system::file_system_entry::FileSystemEntry;
use anyhow::Result;

pub trait FolderScannable {
    fn scan(&self) -> Result<(Vec<FileSystemEntry>, Vec<FileSystemEntry>), String>;
}
