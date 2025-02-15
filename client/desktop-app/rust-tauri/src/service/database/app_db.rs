use sqlx::SqlitePool;
use anyhow::Result;
use crate::domain::on_metal::middleware::file_system::file_system_entry::FileSystemEntry;
use serde_json;
use tauri::{AppHandle, Manager};
use once_cell::sync::OnceCell;

static POOL: OnceCell<SqlitePool> = OnceCell::new();

/// Helper function to build the database URL from the application's data directory.
fn build_db_url(app_handle: &AppHandle) -> Result<String, String> {
    let app_data_dir = app_handle.path().app_data_dir()
        .map_err(|e| format!("Failed to get app data directory: {}", e))?;
    
    if cfg!(debug_assertions) {
        println!(">> app_data_dir: {:?}", app_data_dir);
    }
    let db_path = app_data_dir.join("pocket-search.db");
    Ok(format!("sqlite:{}", db_path.to_string_lossy()))
}

/// In production, consider reusing a connection pool instead of creating one on each call.
pub async fn store_file_system_entry(app_handle: &AppHandle, entry: &FileSystemEntry) -> Result<(), String> {
    let db_url = build_db_url(app_handle)?;

    let pool = SqlitePool::connect(&db_url)
        .await
        .map_err(|e| format!("Failed to connect to database: {}", e))?;

    // Serialize the optional metadata fields as JSON.
    let os_metadata_json = entry.os_metadata.as_ref()
        .and_then(|md| serde_json::to_string(md).ok());
    let semantic_metadata_json = entry.semantic_metadata.as_ref()
        .and_then(|sm| serde_json::to_string(sm).ok());
    
    sqlx::query(
        "INSERT INTO file_system_entries (path, file_size, is_read_only, inode, os_metadata, semantic_metadata)
         VALUES (?, ?, ?, ?, ?, ?)"
    )
    .bind(&entry.path)
    .bind(entry.file_size as i64)
    .bind(entry.is_read_only as i32)
    .bind(entry.inode.map(|i| i as i64))
    .bind(os_metadata_json)
    .bind(semantic_metadata_json)
    .execute(&pool)
    .await
    .map_err(|e| format!("Failed to insert entry: {}", e))?;
    Ok(())
}

/// In production, consider reusing a connection pool.
pub async fn store_file_system_entries(app_handle: &AppHandle, entries: &[FileSystemEntry]) -> Result<(), String> {
    let db_url = build_db_url(app_handle)?;

    let pool = SqlitePool::connect(&db_url)
        .await
        .map_err(|e| format!("Failed to connect to database: {}", e))?;
    
    // Build the bulk insertion query using QueryBuilder's push_values helper.
    let mut query_builder = sqlx::QueryBuilder::<sqlx::Sqlite>::new(
        "INSERT INTO file_system_entries (path, file_size, is_read_only, inode, os_metadata, semantic_metadata) "
    );
    query_builder.push_values(entries, |mut b, entry| {
        let os_metadata_json = entry.os_metadata.as_ref()
            .and_then(|md| serde_json::to_string(md).ok());
        let semantic_metadata_json = entry.semantic_metadata.as_ref()
            .and_then(|sm| serde_json::to_string(sm).ok());
        b.push_bind(&entry.path)
         .push_bind(entry.file_size as i64)
         .push_bind(entry.is_read_only as i32)
         .push_bind(entry.inode.map(|i| i as i64))
         .push_bind(os_metadata_json)
         .push_bind(semantic_metadata_json);
    });
    let query = query_builder.build();
    
    query.execute(&pool)
         .await
         .map_err(|e| format!("Failed to insert entries in bulk: {}", e))?;
    Ok(())
}

pub async fn get_pool(app_handle: &AppHandle) -> Result<SqlitePool, String> {
    if let Some(pool) = POOL.get() {
        return Ok(pool.clone());
    }

    let db_url = build_db_url(app_handle)?;
    let pool = SqlitePool::connect(&db_url)
        .await
        .map_err(|e| format!("Failed to connect to database: {}", e))?;

    POOL.set(pool.clone())
        .map_err(|_| "Failed to set database pool".to_string())?;

    Ok(pool)
}
