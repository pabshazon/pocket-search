use crate::domain::on_metal::middleware::file_system::entry_type::EntryType;
use crate::domain::on_metal::middleware::file_system::os_metadata::OsMetadata;
use crate::domain::on_metal::middleware::file_system::semantic_metadata::SemanticMetadata;

#[derive(Debug)]
pub struct FileSystemEntry {
    pub entry_type: EntryType,
    pub path: String,
    pub file_size: u64,
    #[allow(dead_code)]
    pub is_read_only: bool,
    pub inode: Option<u64>,
    pub os_metadata: Option<OsMetadata>,
    /// Enriched semantic metadata derived from the file content.
    pub semantic_metadata: Option<SemanticMetadata>,
}
