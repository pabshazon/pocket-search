use std::path::{Path, PathBuf};
use std::sync::mpsc::{channel, Receiver};
use std::time::Duration;
use std::thread;

use notify::{Watcher, RecommendedWatcher, RecursiveMode, Event, EventKind, Config};
use log::{info, error};
use anyhow::Result;

use crate::domain::on_metal::middleware::file_system::fs_events_listener::{FsChangeEvent, map_event};

/// Trait defining the repository interface for loading tasks.
/// The repository abstracts the SQLite-specific code.
/// In a real-world DDD approach, this lives in the domain layer.
pub trait TaskRepository: Send + Sync {
    fn load_sync_tasks(&self) -> Result<Vec<PathBuf>>;
}

/// Dummy implementation of TaskRepository using SQLite.
/// In a production application, this would perform a query on the
/// "tasks" table (e.g. filtering tasks of type "start_fs_sync") and
/// return the selected directories/files to be watched.
pub struct SQLiteTaskRepository {
    // In a real implementation, you would store the connection details here.
}

impl SQLiteTaskRepository {
    pub fn new() -> Self {
        Self { }
    }
}

impl TaskRepository for SQLiteTaskRepository {
    fn load_sync_tasks(&self) -> Result<Vec<PathBuf>> {
        // For demonstration purposes, we return two dummy paths.
        Ok(vec![
            PathBuf::from("/path/to/watch1"),
            PathBuf::from("/path/to/watch2"),
        ])
    }
}

/// Daemon responsible for syncing file system changes.
/// It loads task paths from a repository and creates a watcher
/// to listen to FSEvents (or native events) with the notify crate.
pub struct FsSyncDaemon {
    task_repo: Box<dyn TaskRepository>,
    // We keep our watchers alive as part of the daemon state.
    watchers: Vec<RecommendedWatcher>,
}

impl FsSyncDaemon {
    /// Creates a new daemon instance with an injected task repository.
    pub fn new(task_repo: Box<dyn TaskRepository>) -> Self {
        Self {
            task_repo,
            watchers: Vec::new(),
        }
    }

    /// Runs the daemon. This method loads the directories/files to watch,
    /// sets up the watcher with proper callbacks, and enters a loop to continuously
    /// listen for events.
    pub fn run(&mut self) -> Result<()> {
        // Load the tasks (directories/files to watch) via the repository.
        let tasks = self.task_repo.load_sync_tasks()?;

        // Create a channel for receiving filesystem events (if needed).
        let (tx, rx): (_, Receiver<Event>) = channel();

        // Create a watcher. We use a callback-based approach. The callback converts the raw
        // notify event into a domain event and logs it. In a more complex system, you could dispatch
        // the event via an event bus to various subscribers.
        let mut watcher: RecommendedWatcher = RecommendedWatcher::new(
            move |res: Result<Event, notify::Error>| {
                match res {
                    Ok(event) => {
                        // Iterate over all the paths in the event.
                        for path in event.paths.iter() {
                            if let Some(domain_event) = map_event(&event.kind, path) {
                                info!("Filesystem event: {:?}", domain_event);
                                // TODO: Dispatch domain_event to other parts of the app if needed.
                            }
                        }
                    },
                    Err(e) => {
                        error!("Filesystem watch error: {:?}", e);
                    }
                }
            },
            Config::default(),
        )?;

        // Register each task path with the watcher.
        // We watch them recursively.
        for path in tasks {
            if path.exists() {
                info!("Adding watch for path: {:?}", path);
                watcher.watch(&path, RecursiveMode::Recursive)?;
            } else {
                info!("Path does not exist, skipping watch: {:?}", path);
            }
        }

        // Keep the watcher alive by storing it in the daemon state.
        self.watchers.push(watcher);

        // The daemon loop. You can also process events from the rx channel if you modify the above callback.
        self.event_loop(rx);

        Ok(())
    }

    /// A simple event loop that keeps the daemon alive.
    /// You can extend this loop to also process queued domain events.
    fn event_loop(&self, rx: Receiver<Event>) {
        loop {
            // Here we wait for any event from the rx channel (with timeout).
            match rx.recv_timeout(Duration::from_secs(5)) {
                Ok(event) => {
                    info!("Received event from channel: {:?}", event);
                    // Optionally, you could add further domain processing here.
                },
                Err(_) => {
                    // Timeout reached; can perform background maintenance here.
                    // For now, we simply continue.
                }
            }
            // Sleep shortly to avoid tight looping.
            thread::sleep(Duration::from_millis(100));
        }
    }
}
