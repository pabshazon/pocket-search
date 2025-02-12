use std::fs;
use std::path::Path;
use std::ffi::CString;
use std::os::unix::fs::MetadataExt;
#[cfg(target_os = "windows")]
use std::os::windows::fs::MetadataExt;
use libc::{stat, lstat};
use anyhow::Result;

use crate::domain::on_metal::middleware::file_system::entry_type::EntryType;
use crate::domain::on_metal::middleware::file_system::os_metadata::OsMetadata;
use crate::domain::on_metal::middleware::file_system::file_system_entry::FileSystemEntry;
use crate::domain::on_metal::middleware::file_system::folder_scannable::FolderScannable;

pub struct FolderScanner {
    pub folder_path: String,
    pub os: String,
}

impl FolderScanner {
    pub fn new(folder_path: String) -> Self {
        let os = if cfg!(target_os = "windows") {
            "Windows".to_string()
        } else if cfg!(target_os = "macos") {
            "macOS".to_string()
        } else if cfg!(target_os = "linux") {
            "Linux".to_string()
        } else {
            "Unknown".to_string()
        };
        Self { folder_path, os }
    }

    fn get_os_metadata(path: &Path) -> Option<OsMetadata> {
        let c_path    = CString::new(path.to_str()?).ok()?;
        let mut stat_buf: stat = unsafe { std::mem::zeroed() };
        if unsafe { lstat(c_path.as_ptr(), &mut stat_buf) } == 0 {
            #[cfg(target_os = "macos")]
            {
                Some(OsMetadata {
                    device_id:          stat_buf.st_dev as u64,
                    hard_links:         stat_buf.st_nlink as u64,
                    user_id:            stat_buf.st_uid as u32,
                    group_id:           stat_buf.st_gid as u32,
                    total_size:         stat_buf.st_size,
                    block_size:         stat_buf.st_blksize as i64,
                    blocks_allocated:   stat_buf.st_blocks as i64,
                    atime:              libc::timespec {
                        tv_sec:  stat_buf.st_atime as i64,
                        tv_nsec: stat_buf.st_atime_nsec as i64,
                    },
                    mtime:              libc::timespec {
                        tv_sec:  stat_buf.st_mtime as i64,
                        tv_nsec: stat_buf.st_mtime_nsec as i64,
                    },
                    ctime:              libc::timespec {
                        tv_sec:  stat_buf.st_ctime as i64,
                        tv_nsec: stat_buf.st_ctime_nsec as i64,
                    },
                    birthtime:          libc::timespec {
                        tv_sec:  stat_buf.st_birthtime as i64,
                        tv_nsec: stat_buf.st_birthtime_nsec as i64,
                    },
                })
            }
            #[cfg(not(target_os = "macos"))]
            {
                Some(OsMetadata {
                    device_id: stat_buf.st_dev as u64,
                    hard_links: stat_buf.st_nlink as u64,
                    user_id: stat_buf.st_uid as u32,
                    group_id: stat_buf.st_gid as u32,
                    total_size: stat_buf.st_size,
                    block_size: stat_buf.st_blksize as i64,
                    blocks_allocated: stat_buf.st_blocks as i64,
                })
            }
        } else {
            println!("Failed to retrieve detailed inode information for path: {:?}", path);
            None
        }
    }
}

impl FolderScannable for FolderScanner {
    fn scan(&self) -> Result<(Vec<FileSystemEntry>, Vec<FileSystemEntry>), String> {
        let mut file_entries      = Vec::new();
        let mut directory_entries = Vec::new();
        let path                                 = Path::new(&self.folder_path);

        if !path.is_dir() {
            return Err("Provided path is not a directory".to_string());
        }

        let read_dir = fs::read_dir(path)
            .map_err(|e| format!("Failed to read directory: {}", e))?;
        for entry in read_dir {
            let entry = entry.map_err(|e| e.to_string())?;
            let path_buf = entry.path();
            let metadata = fs::metadata(&path_buf)
                .map_err(|e| e.to_string())?;
            
            let entry_type = if path_buf.is_file() {
                EntryType::File
            } else if path_buf.is_dir() {
                EntryType::Directory
            } else {
                continue;
            };

            let mut os_metadata = None;
            let mut inode        = None;

            if self.os == "Linux" || self.os == "macOS" {
                inode       = Some(metadata.ino());
                os_metadata = FolderScanner::get_os_metadata(&path_buf);
            } else if self.os == "Windows" {
                // @todo Windows-specific logic if needed.
            }

            let fs_entry = FileSystemEntry {
                entry_type:        entry_type,
                path:              path_buf.display().to_string(),
                file_size:         metadata.len(),
                is_read_only:      metadata.permissions().readonly(),
                inode:             inode,
                os_metadata:       os_metadata,
                semantic_metadata: None,
            };

            match fs_entry.entry_type {
                EntryType::File => {
                    file_entries.push(fs_entry);
                }
                EntryType::Directory => {
                    directory_entries.push(fs_entry);
                }
            }
        }

        Ok((file_entries, directory_entries))
    }
}

// Removed inline store_fs_entry. 