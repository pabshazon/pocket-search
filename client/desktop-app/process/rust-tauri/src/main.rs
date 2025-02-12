#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod command;
mod domain;
mod service;

use command::initialize_app::{init_db, run_db_migrations};
use command::scan_folder_and_queue_tasks::scan_folder_and_queue_tasks;
use command::perform_tasks::perform_tasks;
use tauri::Manager;
use std::process::Command;

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            // DB Init and migrations
            let path = app.path().data_dir();
            println!("----{:?}-----", path);
            init_db(app.handle())?;
            run_db_migrations(app.handle())?;
            // Start as an embedded process the python FastAPI server
            Command::new("python3")
            .arg("start_fastapi.py")
            .spawn()
            .expect("Failed to start FastAPI server");
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            scan_folder_and_queue_tasks,
            perform_tasks
        ])
        .run(tauri::generate_context!())
        .expect("error while running pocket-search application");
}
