
class Qdrant:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Qdrant, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        pass