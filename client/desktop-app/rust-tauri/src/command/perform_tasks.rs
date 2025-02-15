use tauri::command;
use anyhow::Result;
use reqwest::Client;
use tokio::runtime::Runtime;

#[command]
pub fn perform_tasks() -> Result<(), String> {
    println!("Performing tasks");

    // Create a new Tokio runtime
    let runtime = Runtime::new().map_err(|e| format!("Failed to create Tokio runtime: {}", e))?;

    // Run the async block
    runtime.block_on(async {
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
    });

    Ok(())
}
