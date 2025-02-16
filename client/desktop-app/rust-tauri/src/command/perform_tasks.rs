use tauri::command;
use anyhow::Result;
use reqwest::Client;

#[command]
pub async fn perform_tasks() -> Result<(), String> {
    println!("Performing tasks");

    // Make HTTP request to FastAPI endpoint
    let client = Client::new();
    match client.get("http://127.0.0.1:8000/hello").send().await {
        Ok(response) => {
            if response.status().is_success() {
                println!("Successfully connected to FastAPI service");
            } else {
                println!("Failed to connect to FastAPI service: {}", response.status());
            }
        },
        Err(e) => {
            println!("Error connecting to FastAPI service: {}", e);
        }
    }

    Ok(())
}
