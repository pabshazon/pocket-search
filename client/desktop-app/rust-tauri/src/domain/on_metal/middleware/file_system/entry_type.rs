use serde::Serialize;

#[derive(Debug, PartialEq, Serialize)]
pub enum EntryType {
    File,
    Directory,
}
