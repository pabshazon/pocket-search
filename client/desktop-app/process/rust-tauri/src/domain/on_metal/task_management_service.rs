pub struct TaskManagementService {
    task_queue: TaskQueue,
}

impl TaskManagementService {
    pub fn new(database_service: &DatabaseService) -> Self {
        let task_queue = TaskQueue::new(database_service.get_sqlite_handler());
        Self { task_queue }
    }

    pub fn scan_folder_and_queue(&self, folder_path: String) -> Result<(), String> {
        let path_obj = PathBuf::from(folder_path);
        self.task_queue.scan_and_enqueue_files(&path_obj)
    }
}

