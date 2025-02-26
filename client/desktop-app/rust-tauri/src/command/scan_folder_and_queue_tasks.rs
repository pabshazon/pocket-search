use anyhow::Result;
use regex::Regex;
use std::collections::HashSet;
use tauri::command;

use crate::domain::on_metal::middleware::file_system::entry_type::EntryType;
use crate::domain::on_metal::middleware::file_system::file_system_entry::FileSystemEntry;
use crate::domain::on_metal::middleware::file_system::folder_scannable::FolderScannable;
use crate::domain::on_metal::middleware::file_system::folder_scanner::FolderScanner;

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

const TASK_TRIGGER_EXTENSIONS: &[&str] = &[
    ".pdf", ".key", ".docx", ".xlsx", ".txt", ".md", ".csv", ".json", ".xml", ".html", ".css",
    ".js", ".ts", ".py", ".java", ".c", ".cpp", ".h", ".hpp", ".cs", ".vb", ".php", ".rb",
    ".swift", ".kt", ".go", ".rs", ".scala", ".sql", ".yaml", ".yml", ".toml", ".ini", ".cfg",
    ".conf", ".log",
];

#[command]
pub async fn scan_folder_and_queue_tasks(
    folder_path: String,
    app_handle: tauri::AppHandle,
    filter_pattern: Option<String>,
) -> Result<(), String> {
    println!("Scanning folder '{}' and queueing tasks", folder_path);

    let scanner = FolderScanner::new(folder_path.clone());
    let (file_entries, directory_entries) = scanner.scan()?;

    let all_entries: Vec<_> = file_entries
        .into_iter()
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

    if let Err(err) = crate::service::database::app_db::store_file_system_entries(
        &app_handle,
        &all_entries,
        TASK_TRIGGER_EXTENSIONS,
    )
    .await
    {
        eprintln!("Error storing FS entries in bulk: {}", err);
    } else {
        println!(
            "Successfully stored {} file system entries.",
            all_entries.len()
        );
    }

    // Call the perform_tasks function
    use crate::command::perform_tasks::perform_tasks;
    if let Err(err) = perform_tasks().await {
        eprintln!("Error performing tasks: {}", err);
    } else {
        println!("Tasks performed successfully.");
    }

    Ok(())
}
