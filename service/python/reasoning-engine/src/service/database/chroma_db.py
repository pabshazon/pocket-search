import os
from chromadb import PersistentClient

class Chroma:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PersistentClient, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        home_directory = os.path.expanduser("~")
        app_data_dir = os.path.join(home_directory, "Library/Application Support/ai.on-metal.pocket-search.desktop-app/chromadb")
        if not os.path.exists(app_data_dir):
            os.makedirs(app_data_dir)

        self.db_path = app_data_dir
        self.chroma_client = PersistentClient(path=self.db_path)

    def get_client(self):
        return self.chroma_client

    def store_fs_entry_cs_summary(self, fs_entry, cs_summary):
        pass

