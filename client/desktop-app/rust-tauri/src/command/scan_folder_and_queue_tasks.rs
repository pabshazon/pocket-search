use tauri::command;
use anyhow::Result;
use crate::domain::on_metal::middleware::file_system::folder_scanner::FolderScanner;
use crate::domain::on_metal::middleware::file_system::folder_scannable::FolderScannable;
use regex::Regex;
use std::collections::HashSet;

const ENFORCED_FILTER_PATTERNS: &[&str] = &[
    r"^\.DS_Store$", 
    r"^\.git$",
    r"^\.idea$",
    r"^\.nvm$",
    r"^\.config$",
    r"^\.CFUserTextEncoding$",
    r"^\.npmrc$",
    r"^\.zoom.*$",
    r"^\.continue$",
    r"^\.void-editor$",
    r"^\.cargo$",
    r"^\.rustup$",
    r"^\.ssh$",
    r"^\.vscode$",
    r"^\.ollama$",    
    r"^\.cache$",
    r"^\.Trash$",
];

#[command]
pub async fn scan_folder_and_queue_tasks(
    folder_path: String, 
    app_handle: tauri::AppHandle,
    filter_pattern: Option<String>
) -> Result<(), String> {
    println!("Scanning folder '{}' and queueing tasks", folder_path);
    
    let scanner = FolderScanner::new(folder_path.clone());
    let (file_entries, directory_entries) = scanner.scan()?;
    
    let all_entries: Vec<_> = file_entries.into_iter()
        .chain(directory_entries.into_iter())
        .filter(|entry| {
            let mut patterns = HashSet::new();
            patterns.extend(ENFORCED_FILTER_PATTERNS.iter().cloned());
            if let Some(ref pattern) = filter_pattern {
                patterns.insert(pattern.as_str());
            }
            
            !patterns.iter().any(|pattern| {
                let regex = Regex::new(pattern).unwrap();
                if let Some(file_name) = std::path::Path::new(&entry.path).file_name() {
                    if let Some(file_name_str) = file_name.to_str() {
                        return regex.is_match(file_name_str);
                    }
                }
                false
            })
        })
        .collect();

    if let Err(err) = crate::service::database::app_db::store_file_system_entries(&app_handle, &all_entries).await {
         eprintln!("Error storing FS entries in bulk: {}", err);
    } else {
         println!("Successfully stored {} file system entries.", all_entries.len());
    }
    
    Ok(())
} 
