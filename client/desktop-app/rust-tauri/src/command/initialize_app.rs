use tauri::{command, AppHandle, Manager};
use anyhow::Result;
use sqlx::sqlite::SqlitePool;
use std::env;
use tokio::runtime::Runtime;

#[command]
pub fn init_db(app_handle: &AppHandle) -> Result<(), String> {
    println!("Initializing database...");

    let app_data_dir = app_handle.path().app_data_dir()
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

    println!("Database OK.");
    Ok(())
}

#[command]
pub fn run_db_migrations(app_handle: &AppHandle) -> Result<(), String> {
    println!("Initializing db migrations...");

    // @todo This is a hack to get the migrations path. Move it to a config file that can work for dev and prod.
    let pocket_github_path: std::result::Result<String, std::env::VarError> = env::var("POCKET_GITHUB_PATH");
    let migrations_path: String = format!("{}client/desktop-app/db_migrations", pocket_github_path.unwrap());

    let app_data_dir = app_handle.path().app_data_dir()
        .map_err(|e| format!("Failed to get app data directory: {}", e))?;

    if cfg!(debug_assertions) {
        println!(">> app_data_dir: {:?}", app_data_dir);
    }

    let db_path = app_data_dir.join("pocket-search.db");
    let db_url = format!("sqlite:{}", db_path.to_string_lossy());

    if cfg!(debug_assertions) {
        println!(">> DB url: {:?}", db_url);
    }

    if cfg!(debug_assertions) {
        println!(">> DB migrations path: {:?}", migrations_path);
    }

    let tokio_runtime = Runtime::new()
        .map_err(|e| format!("Failed to create Tokio runtime: {}", e))?;

    tokio_runtime.block_on(async {
        let pool = SqlitePool::connect(&db_url)
            .await
            .map_err(|e| format!("Failed to connect to database: {}", e))?;

        // Check if the migrations directory exists
        if !std::path::Path::new(&migrations_path).exists() {
            return Err(format!("Migrations path does not exist: {}", migrations_path));
        }

        sqlx::migrate!("../../../client/desktop-app/db_migrations")
            .run(&pool)
            .await
            .map_err(|e| format!("Failed to run migrations: {}", e))?;

        println!("Database migrations completed successfully!");
        Ok(())
    })
}
