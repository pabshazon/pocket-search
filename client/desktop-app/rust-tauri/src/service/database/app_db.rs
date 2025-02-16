use sqlx::SqlitePool;
use anyhow::Result;
use crate::domain::on_metal::middleware::file_system::file_system_entry::FileSystemEntry;
use serde_json;
use tauri::{AppHandle, Manager};
use crate::domain::on_metal::middleware::file_system::entry_type::EntryType;
use sqlx::{QueryBuilder, Row};

fn build_db_url(app_handle: &AppHandle) -> Result<String, String> {
    let app_data_dir = app_handle.path().app_data_dir()
        .map_err(|e| format!("Failed to get app data directory: {}", e))?;
    
    if cfg!(debug_assertions) {
        println!(">> app_data_dir: {:?}", app_data_dir);
    }
    let db_path = app_data_dir.join("pocket-search.db");
    Ok(format!("sqlite:{}", db_path.to_string_lossy()))
}

async fn get_db_pool(app_handle: &AppHandle) -> Result<SqlitePool, String> {
    let db_url = build_db_url(app_handle)?;
    SqlitePool::connect(&db_url)
        .await
        .map_err(|e| format!("Failed to connect to database: {}", e))
}

/// @todo In production, consider reusing a connection pool.
pub async fn store_file_system_entries(
    app_handle: &AppHandle,
    entries: &[FileSystemEntry],
    task_trigger_extensions: &[&str]
) -> Result<(), String> {
    // Establish database connection.
    let pool = get_db_pool(app_handle).await?;

    // Process only those entries that have a valid inode (i.e. representing a file/folder).
    let file_and_folder_entries: Vec<&FileSystemEntry> = entries
        .iter()
        .filter(|entry| entry.inode.unwrap_or(0) != 0)
        .collect();

    if file_and_folder_entries.is_empty() {
        return Ok(());
    }

    // Clone the vector before using it in push_values
    let file_and_folder_entries_clone = file_and_folder_entries.clone();

    let mut query_builder = QueryBuilder::<sqlx::Sqlite>::new(
        "INSERT INTO hyper_node (
            name,
            parent_hyper_node_id,
            is_folder,
            is_file,
            is_inside_fs_file,
            fs_full_path,
            fs_file_name,
            fs_inode,
            fs_file_extension,
            fs_file_size,
            fs_device_id,
            fs_user_id,
            fs_group_id,
            cs_what_is_fs_folder_about,
            cs_what_is_fs_file_about,
            cs_hnode_title,
            cs_hnode_summary
        ) "
    );

    query_builder.push_values(file_and_folder_entries_clone, |mut b, entry| {
        use std::path::Path;

        let path = entry.path.as_str();
        let path_obj = Path::new(path);

        // Derive a name from the file system path.
        let fs_file_name = path_obj
            .file_name()
            .and_then(|s| s.to_str())
            .unwrap_or(path);

        // Extract file extension if available.
        let fs_file_extension = path_obj
            .extension()
            .and_then(|s| s.to_str())
            .unwrap_or("");

        // Determine file vs folder based on EntryType.
        let (is_folder, is_file) = match entry.entry_type {
            EntryType::Directory => (1, 0),
            EntryType::File      => (0, 1),
        };
        let is_inside_fs_file = 0; // Default value
        let parent_hyper_node_id: Option<&str> = None;
        let fs_inode = entry.inode.unwrap_or(0);

        // Map OS metadata to FS fields. We cast user and group IDs to i32.
        let (fs_device_id, fs_user_id, fs_group_id) = if let Some(ref meta) = entry.os_metadata {
            (meta.device_id, meta.user_id as i32, meta.group_id as i32)
        } else {
            (0, 0, 0)
        };

        // Serialize OS metadata to JSON.
        let (cs_what_is_fs_folder_about, cs_what_is_fs_file_about) = match entry.entry_type {
            EntryType::Directory => (
                entry.os_metadata
                    .as_ref()
                    .and_then(|m| serde_json::to_string(m).ok()),
                None,
            ),
            EntryType::File => (
                None,
                entry.os_metadata
                    .as_ref()
                    .and_then(|m| serde_json::to_string(m).ok()),
            ),
        };

        // Serialize semantic metadata, if any.
        let cs_hnode_summary = entry.semantic_metadata
            .as_ref()
            .and_then(|m| serde_json::to_string(m).ok());

        let cs_hnode_title: Option<String> = None; // Placeholder for a future title.

        let hnode_name = if is_inside_fs_file == 0 {
            match parent_hyper_node_id {
                Some(parent_id) => format!("{}::{}", path, parent_id),
                None => format!("{}", path),
            }
        } else {
            format!("{}::{}", path, fs_file_name)
        };

        b.push_bind(hnode_name)                      // name
         .push_bind(parent_hyper_node_id)            // parent_hyper_node_id
         .push_bind(is_folder)                       // is_folder
         .push_bind(is_file)                         // is_file
         .push_bind(is_inside_fs_file)               // is_inside_fs_file
         .push_bind(path)                            // fs_full_path
         .push_bind(fs_file_name)                    // fs_file_name
         .push_bind(fs_inode as i64)                 // fs_inode
         .push_bind(fs_file_extension)               // fs_file_extension
         .push_bind(entry.file_size as i64)          // fs_file_size
         .push_bind(fs_device_id as i64)                    // fs_device_id
         .push_bind(fs_user_id as i64)                      // fs_user_id
         .push_bind(fs_group_id as i64)                     // fs_group_id
         .push_bind(cs_what_is_fs_folder_about)      // cs_what_is_fs_folder_about
         .push_bind(cs_what_is_fs_file_about)        // cs_what_is_fs_file_about
         .push_bind(cs_hnode_title)                  // cs_hnode_title
         .push_bind(cs_hnode_summary);               // cs_hnode_summary
    });

    // Add RETURNING clause to capture hyper_node_id
    query_builder.push(
        " ON CONFLICT(name) DO UPDATE SET
            name = excluded.name,
            is_folder = excluded.is_folder,
            is_file = excluded.is_file,
            is_inside_fs_file = excluded.is_inside_fs_file,
            fs_file_name = excluded.fs_file_name,
            fs_inode = excluded.fs_inode,
            fs_file_extension = excluded.fs_file_extension,
            fs_file_size = excluded.fs_file_size,
            fs_device_id = excluded.fs_device_id,
            fs_user_id = excluded.fs_user_id,
            fs_group_id = excluded.fs_group_id,
            cs_what_is_fs_folder_about = excluded.cs_what_is_fs_folder_about,
            cs_what_is_fs_file_about = excluded.cs_what_is_fs_file_about,
            cs_hnode_title = excluded.cs_hnode_title,
            cs_hnode_summary = excluded.cs_hnode_summary
        RETURNING id"
    );

    let query = query_builder.build();

    // Execute the query and collect the returned hyper_node_ids
    let hyper_node_ids: Vec<String> = query
        .fetch_all(&pool)
        .await
        .map_err(|e| format!("Failed to upsert file system entries: {}", e))?
        .iter()
        .map(|row| {
            let id: String = row.try_get("id").unwrap_or_default();
            println!("Fetched hyper_node_id: {}", id); // Debugging output
            id
        })
        .collect();

    // Use the original file_and_folder_entries for further processing
    let task_entries: Vec<&FileSystemEntry> = file_and_folder_entries.into_iter()
        .filter(|entry| {
            if entry.entry_type == EntryType::Directory {
                return true;
            }
            if let Some(extension) = std::path::Path::new(&entry.path).extension() {
                return task_trigger_extensions.contains(&extension.to_str().unwrap_or(""));
            }
            false
        })
        .collect();

    // Create tasks for each entry
    for (entry, hyper_node_id) in task_entries.iter().zip(hyper_node_ids.iter()) {
        let task_name = format!("Task for {}", entry.path);
        let task_description = format!("Generated task for entry at path: {}", entry.path);

        // Use QueryBuilder to check if the task already exists
        let mut existing_task_query_builder = QueryBuilder::<sqlx::Sqlite>::new(
            "SELECT COUNT(*) as count FROM task WHERE name = "
        );

        existing_task_query_builder
            .push_bind(task_name.clone())
            .push(" AND data = ")
            .push_bind(serde_json::Value::Null.to_string())
            .push(" AND description = ")
            .push_bind(task_description.clone())
            .push(" AND hyper_node_id = ")
            .push_bind(hyper_node_id.as_str())
            .push(" AND priority = ")
            .push_bind(0) // priority
            .push(" AND status = ")
            .push_bind("pending"); // status

        let existing_task_query = existing_task_query_builder.build();

        let existing_task_count: i64 = existing_task_query
            .fetch_one(&pool)
            .await
            .map_err(|e| format!("Failed to check existing task: {}", e))?
            .try_get("count")
            .unwrap_or(0);


        if existing_task_count > 0 {
            println!("Repeated the demand for a pending task");
            continue;
        }

        let mut task_query_builder = QueryBuilder::<sqlx::Sqlite>::new(
            "INSERT INTO task (
                name,
                data,
                description,
                hyper_node_id,
                priority,
                status
            ) "
        );

        task_query_builder.push_values(std::iter::once(entry), |mut b, _| {
            b.push_bind(task_name.clone())
             .push_bind(serde_json::Value::Null.to_string()) // Convert JSON value to string
             .push_bind(task_description.clone())
             .push_bind(hyper_node_id.as_str()) // Use a reference to the hyper_node_id
             .push_bind(0) // priority
             .push_bind("pending"); // status
        });

        let task_query = task_query_builder.build();

        task_query.execute(&pool)
            .await
            .map_err(|e| format!("Failed to insert task for entry: {}", e))?;
    }

    Ok(())
}
