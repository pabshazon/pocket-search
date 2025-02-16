CREATE TABLE task (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hyper_node_id TEXT,
    name TEXT NOT NULL,
    description TEXT,
    data JSON,
    status TEXT NOT NULL,
    priority INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    performed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraint
    FOREIGN KEY (hyper_node_id) REFERENCES hyper_node(id)
);

-- Create indexes for task table
CREATE INDEX idx_task_status ON task(status);
CREATE INDEX idx_task_hyper_node ON task(hyper_node_id);
CREATE INDEX idx_task_priority ON task(priority);
CREATE INDEX idx_task_created_at ON task(created_at);

-- iNode inspired table for file system metadata. hyper_node is the main interface referring to a multi-modal-multi-dimensional node: a hyper_node. Could be simplified to multi_modal_node or m_node or mi_node, but they are bad in other tradeoffs, so we are coining a term. HyperNode.
CREATE TABLE hyper_node (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    name TEXT NOT NULL UNIQUE,
    parent_hyper_node_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_folder INTEGER NOT NULL,
    is_file INTEGER NOT NULL,
    is_inside_fs_file INTEGER NOT NULL,
    
    -- FS Layer    
    fs_full_path TEXT NOT NULL,
    fs_file_name TEXT,
    fs_inode INTEGER,
    fs_file_extension TEXT,
    fs_file_size INTEGER,
    fs_device_id INTEGER,
    fs_user_id INTEGER,
    fs_group_id INTEGER,
    
    -- Cognitive/Semantic Layer
    -- cs_index TEXT,
    cs_parent_node INTEGER,
    cs_what_is_fs_folder_about TEXT,
    cs_what_is_fs_file_about TEXT,
    cs_hnode_title TEXT,
    cs_hnode_summary TEXT,
    cs_explain_contains TEXT,
    cs_what_info_can_be_found TEXT,
    cs_tags_obvious TEXT,
    cs_tags_extended TEXT,
    node_vision_type TEXT CHECK (node_vision_type IN ('chapter', 'section', 'table', 'bullet_item')),
    node_text_data TEXT,
    node_vision_data BLOB,
    open_with_application_type TEXT,
    cs_ns_full_path TEXT,
    last_updated_semantics_changes DATETIME,
    -- Stochastic/Cognitive/Text Space
    -- Stochastic/Cognitive/Image Space
    -- Stochastic/Cognitive/Audio Space
    -- Stochastic/Cognitive/Video Space
    -- Stochastic/Cognitive/Graph Space
    -- Stochastic/Kowledge/OrganizedChunks Space
    -- Deterministic/Variables/ManuallyDefined Values
    -- Deterministic/Variables/StochasticallyInferred Values
    -- Deterministic/Kowledge/Graph ER Values
    -- Deterministic/Kowledge/SQL ER Values
    
    -- Foreign Key Constraint
    FOREIGN KEY (parent_hyper_node_id) REFERENCES hyper_node(id)
);

-- Create indexes for hyper_node table
CREATE INDEX idx_hyper_node_parent ON hyper_node(parent_hyper_node_id);
CREATE INDEX idx_hyper_node_name ON hyper_node(name);
CREATE INDEX idx_hyper_node_path ON hyper_node(fs_full_path);
CREATE INDEX idx_hyper_node_cs_parent ON hyper_node(cs_parent_node);
CREATE INDEX idx_hyper_node_updated_at ON hyper_node(updated_at);
CREATE INDEX idx_hyper_node_cs_tags ON hyper_node(cs_tags_obvious, cs_tags_extended);
CREATE INDEX idx_hyper_node_vision_type ON hyper_node(node_vision_type);
