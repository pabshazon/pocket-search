use serde::Serialize;
use std::collections::HashMap;

/// Represents an extracted entity from the file content.
#[derive(Debug, Clone, Serialize)]
pub struct ExtractedEntity {
    pub name: String,
    pub entity_type: String,
    pub confidence: f32,
}

/// Represents a semantic chunk of text that was split out during analysis.
#[derive(Debug, Clone, Serialize)]
pub struct SemanticChunk {
    pub text: String,
    pub embedding: Vec<f32>,
}

/// Represents a node from an extracted knowledge graph.
#[derive(Debug, Clone, Serialize)]
pub struct GraphNode {
    pub id: String,
    pub label: String,
    pub properties: Option<HashMap<String, String>>,
}

/// SemanticMetadata stores enriched content analysis data for a file system entry.
/// It includes a summary of the content, a vector embedding, extracted entities,
/// semantic chunks, and nodes extracted from a knowledge graph.
#[derive(Debug, Clone, Serialize)]
pub struct SemanticMetadata {
    pub summary: String,
    pub embedding: Vec<f32>,
    pub extracted_entities: Vec<ExtractedEntity>,
    pub semantic_chunks: Vec<SemanticChunk>,
    pub graph_nodes: Vec<GraphNode>,
}
