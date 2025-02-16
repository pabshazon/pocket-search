import os
import sqlite3

class AppDB:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppDB, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # Get the current macOS user's home directory
        home_directory = os.path.expanduser("~")

        # Construct the app data directory path
        app_data_dir = os.path.join(home_directory, "Library/Application Support/ai.on-metal.pocket-search.desktop-app")
        if not os.path.exists(app_data_dir):
            os.makedirs(app_data_dir)

        # Construct the database path and URL
        self.db_path = os.path.join(app_data_dir, "pocket-search.db")
        self.db_url = f"sqlite:///{self.db_path}"

    def get_connection(self):
        return sqlite3.connect(self.db_path)
