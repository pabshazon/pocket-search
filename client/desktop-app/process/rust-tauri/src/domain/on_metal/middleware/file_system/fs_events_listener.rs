use std::path::{Path, PathBuf};
use notify::EventKind; // Import notify's EventKind for mapping events.

/// Domain event for file system changes.
#[derive(Debug)]
pub enum FsChangeEvent {
    FileCreated(PathBuf),
    FileModified(PathBuf),
    FileDeleted(PathBuf),
    DirCreated(PathBuf),
    DirModified(PathBuf),
    DirDeleted(PathBuf),
}

/// Converts a notify EventKind and a path to our domain event.
/// This function checks if the path is a file or a directory and maps common events accordingly.
pub fn map_event(kind: &EventKind, path: &Path) -> Option<FsChangeEvent> {
    let is_dir = std::fs::metadata(path)
        .map(|m| m.is_dir())
        .unwrap_or(false);
    match kind {
        EventKind::Create(_) => {
            if is_dir {
                Some(FsChangeEvent::DirCreated(path.to_path_buf()))
            } else {
                Some(FsChangeEvent::FileCreated(path.to_path_buf()))
            }
        },
        EventKind::Modify(_) => {
            if is_dir {
                Some(FsChangeEvent::DirModified(path.to_path_buf()))
            } else {
                Some(FsChangeEvent::FileModified(path.to_path_buf()))
            }
        },
        EventKind::Remove(_) => {
            if is_dir {
                Some(FsChangeEvent::DirDeleted(path.to_path_buf()))
            } else {
                Some(FsChangeEvent::FileDeleted(path.to_path_buf()))
            }
        },
        _ => None,
    }
} 