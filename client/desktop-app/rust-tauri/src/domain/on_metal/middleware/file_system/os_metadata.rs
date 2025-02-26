#[cfg(target_os = "macos")]
mod serde_helpers {
    use libc::timespec;
    use serde::ser::{SerializeStruct, Serializer};

    pub fn serialize_timespec<S>(ts: &timespec, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut state = serializer.serialize_struct("timespec", 2)?;
        state.serialize_field("tv_sec", &ts.tv_sec)?;
        state.serialize_field("tv_nsec", &ts.tv_nsec)?;
        state.end()
    }
}

use serde::Serialize;

#[derive(Debug, Serialize)]
pub struct OsMetadata {
    pub device_id: u64,
    pub hard_links: u64,
    pub user_id: u32,
    pub group_id: u32,
    pub total_size: i64,
    pub block_size: i64,
    pub blocks_allocated: i64,
    #[cfg(target_os = "macos")]
    #[serde(serialize_with = "serde_helpers::serialize_timespec")]
    pub atime: libc::timespec,
    #[cfg(target_os = "macos")]
    #[serde(serialize_with = "serde_helpers::serialize_timespec")]
    pub mtime: libc::timespec,
    #[cfg(target_os = "macos")]
    #[serde(serialize_with = "serde_helpers::serialize_timespec")]
    pub ctime: libc::timespec,
    #[cfg(target_os = "macos")]
    #[serde(serialize_with = "serde_helpers::serialize_timespec")]
    pub birthtime: libc::timespec,
}
