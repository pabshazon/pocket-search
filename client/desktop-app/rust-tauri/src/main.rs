#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod command;
mod domain;
mod service;

use command::initialize_app::{init_db, run_db_migrations};
use command::perform_tasks::perform_tasks;
use command::scan_folder_and_queue_tasks::scan_folder_and_queue_tasks;
use std::process::{Child, Command};
use std::sync::{Arc, Mutex};
use tauri::Manager;
use tokio;

struct FastAPIServer {
    child: Option<Child>,
}

impl FastAPIServer {
    fn new() -> Self {
        let child = Command::new("python3")
            .arg("start_fastapi.py")
            .spawn()
            .expect("Failed to start FastAPI server");
        Self { child: Some(child) }
    }
}

impl Drop for FastAPIServer {
    fn drop(&mut self) {
        if let Some(mut child) = self.child.take() {
            println!("Terminating FastAPI server...");
            if let Err(e) = child.kill() {
                eprintln!("Failed to kill FastAPI server: {}", e);
            } else {
                println!("FastAPI server terminated.");
            }
            // Optionally, wait for the process to exit
            let _ = child.wait();
        }
    }
}

fn main() {
    // @todo tbc if we need line underneath or we can init this differently
    let _fastapi_server = Arc::new(Mutex::new(FastAPIServer::new()));

    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .setup(move |app| {
            // DB Init and migrations
            let path = app.path().data_dir();
            println!("----{:?}-----", path);
            init_db(app.handle())?;
            run_db_migrations(app.handle())?;

            // HACK @todo remove for prod.
            tauri::async_runtime::spawn(async {
                tokio::time::sleep(tokio::time::Duration::from_secs(3)).await;
                if let Err(e) = perform_tasks().await {
                    eprintln!("Error performing tasks: {}", e);
                }
            });

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            scan_folder_and_queue_tasks,
            perform_tasks
        ])
        .plugin(tauri_plugin_dialog::init())
        .run(tauri::generate_context!())
        .expect("error while running pocket-search application");

    // FastAPIServer will be dropped here, ensuring the server is stopped
}
