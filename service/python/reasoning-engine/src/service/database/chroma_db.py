import os
from chromadb import PersistentClient, Settings

class Chroma:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Chroma, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        home_directory = os.path.expanduser("~")
        app_data_dir = os.path.join(home_directory, "Library/Application Support/ai.on-metal.pocket-search.desktop-app/chromadb")
        if not os.path.exists(app_data_dir):
            os.makedirs(app_data_dir)

        self.db_path = app_data_dir
        self.chroma_client = PersistentClient(path=self.db_path, settings=Settings(anonymized_telemetry=False))

    def get_client(self):
        return self.chroma_client

    @staticmethod
    def ensure_metadata_types(metadatas):
        return {k: (v if isinstance(v, (str, int, float, bool)) else str(v))
                  for k, v in metadatas.items()}
