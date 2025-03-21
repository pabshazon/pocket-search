use anyhow::Result;
use std::env;
use tauri::{command, AppHandle, Manager};
use tokio::runtime::Runtime;
use sqlx::sqlite::{SqliteConnectOptions, SqlitePoolOptions};
use std::str::FromStr;

#[command]
pub fn init_db(app_handle: &AppHandle) -> Result<(), String> {
    println!("Initializing database...");

    let app_data_dir = app_handle
        .path()
        .app_data_dir()
        .map_err(|e| format!("Failed to get app data directory: {}", e))?;

    if cfg!(debug_assertions) {
        println!("App data directory: {:?}", app_data_dir);
    }

    std::fs::create_dir_all(&app_data_dir)
        .map_err(|e| format!("Failed to create app data directory: {}", e))?;

    let db_path = app_data_dir.join("pocket-search.db");

    if !db_path.exists() {
        println!("Database file does not exist, it will be created.");
        std::fs::File::create(&db_path)
            .map_err(|e| format!("Failed to create database file: {}", e))?;
    }

    Ok(())
}

#[command]
pub fn run_db_migrations(app_handle: &AppHandle) -> Result<(), String> {
    println!("Initializing db migrations...");

    // Get and handle POCKET_GITHUB_PATH environment variable
    let pocket_github_path = env::var("POCKET_GITHUB_PATH")
        .map_err(|e| format!("Failed to get POCKET_GITHUB_PATH: {}", e))?;

    let migrations_path = format!("{}client/desktop-app/db_migrations", pocket_github_path);
    let sqlite_vector_extension = format!("{}client/desktop-app/sqlite/vec0.dylib", pocket_github_path);

    println!("migrations_path: {}", migrations_path);
    println!("SQLite extension: {}", sqlite_vector_extension);

    let app_data_dir = app_handle
        .path()
        .app_data_dir()
        .map_err(|e| format!("Failed to get app data directory: {}", e))?;

    let db_path = app_data_dir.join("pocket-search.db");
    let db_url = format!("sqlite:{}", db_path.to_string_lossy());

    if !std::path::Path::new(&sqlite_vector_extension).exists() {
        return Err(format!("SQLite vector extension not found at: {}", sqlite_vector_extension));
    }

    let escaped_extension_path = sqlite_vector_extension.replace("'", "''");
    println!("escaped_extension_path: {}", escaped_extension_path);

    let tokio_runtime =
        Runtime::new().map_err(|e| format!("Failed to create Tokio runtime: {}", e))?;

    println!("Installing SQLite-vector extension...");

    tokio_runtime.block_on(async {
        let connect_options = SqliteConnectOptions::from_str(&db_url)
            .map_err(|e| format!("Invalid connection URL: {}", e))?
            .filename(&db_path)
            .create_if_missing(true)
            .journal_mode(sqlx::sqlite::SqliteJournalMode::Wal)
            .pragma("foreign_keys", "ON")
            .pragma("trusted_schema", "OFF")
            .pragma("enable_load_extension", "ON")
            .extension(escaped_extension_path);

        println!("connect_options done.");
        let pool = SqlitePoolOptions::new()
            .connect_with(connect_options)
            .await
            .map_err(|e| format!("Failed to connect to database: {}", e))?;

        println!("pool done.");

        let test_query = "SELECT vec_version();";
        let row: (String,) = sqlx::query_as(test_query)
            .fetch_one(&pool)
            .await
            .map_err(|e| format!("Extension test query failed: {}", e))?;

        println!("sqlite-vec extension loaded. Version: {}", row.0);

        // Confirm migrations directory exists before migrating
        if !std::path::Path::new(&migrations_path).exists() {
            return Err(format!("Migrations path does not exist: {}", migrations_path));
        }

        // Run migrations
        sqlx::migrate!("../../../client/desktop-app/db_migrations")
            .run(&pool)
            .await
            .map_err(|e| format!("Failed to run migrations: {}", e))?;

        println!("Database migrations completed successfully!");
        Ok(())
    })
}
