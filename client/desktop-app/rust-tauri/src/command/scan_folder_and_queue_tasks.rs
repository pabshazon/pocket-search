use tauri::command;
use anyhow::Result;
use crate::domain::on_metal::middleware::file_system::folder_scanner::FolderScanner;
use crate::domain::on_metal::middleware::file_system::folder_scannable::FolderScannable;

#[command]
pub async fn scan_folder_and_queue_tasks(folder_path: String, app_handle: tauri::AppHandle) -> Result<(), String> {
    println!("Scanning folder '{}' and queueing tasks", folder_path);
    
    let scanner = FolderScanner::new(folder_path.clone());
    let (file_entries, directory_entries) = scanner.scan()?;
    
    let all_entries: Vec<_> = file_entries.into_iter()
        .chain(directory_entries.into_iter())
        .collect();

    if let Err(err) = crate::service::database::app_db::store_file_system_entries(&app_handle, &all_entries).await {
         eprintln!("Error storing FS entries in bulk: {}", err);
    } else {
         println!("Successfully stored {} file system entries.", all_entries.len());
    }
    
    Ok(())
} 
