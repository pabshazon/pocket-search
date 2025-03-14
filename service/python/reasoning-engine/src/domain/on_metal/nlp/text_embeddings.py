import string
from sentence_transformers import SentenceTransformer

default_model_name  = "sentence-transformers/all-MiniLM-L6-v2"



class TextEmbeddings:
    @staticmethod
    def embed(text: string, model_name: string =None):
        if text is None: raise Exception("Text cannot be None")
        if model_name is not None:
            model = SentenceTransformer(model_name)
        else:
            model = SentenceTransformer(default_model_name)

        embeddings = model.encode(text)
        return embeddings



