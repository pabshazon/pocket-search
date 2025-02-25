import torch
import torch.nn as nn
from torch import Tensor


class SimpleEmbeddingModel(nn.Module):
    """A simple embedding model that transforms input vectors into a lower-dimensional space."""
    
    def __init__(self, input_size: int, embedding_size: int) -> None:
        """
        Initialize the embedding model.
        
        Args:
            input_size: Dimension of the input vectors
            embedding_size: Dimension of the output embedding space
        """
        super(SimpleEmbeddingModel, self).__init__()
        self.embedding = nn.Linear(input_size, embedding_size)
    
    def forward(self, x: Tensor) -> Tensor:
        """
        Transform input vectors into embedding space.
        
        Args:
            x: Input tensor of shape (batch_size, input_size)
            
        Returns:
            Embedded tensor of shape (batch_size, embedding_size)
        """
        return self.embedding(x)


model = SimpleEmbeddingModel(input_size=10, embedding_size=5)

class DocumentEmbedder:
    """Handles document embedding operations using a pre-configured embedding model."""

    def __init__(self, model: SimpleEmbeddingModel):
        """
        Initialize the document embedder.
        
        Args:
            model: A configured SimpleEmbeddingModel instance for embedding generation
        """
        self._model = model
        self._model.eval()  # Set model to evaluation mode

    def embed_document(self, document_tensor: Tensor) -> Tensor:
        """
        Generates embeddings for a document.
        
        Args:
            document_tensor: Tensor representation of the document
                           Expected shape: (batch_size, input_size)
        
        Returns:
            Tensor containing document embeddings
            Shape: (batch_size, embedding_size)
        """
        with torch.no_grad():
            return self._model(document_tensor)

    @classmethod
    def create_default(cls, input_size: int = 768, embedding_size: int = 256) -> 'DocumentEmbedder':
        """
        Factory method to create a DocumentEmbedder with default parameters.
        
        Args:
            input_size: Dimension of input vectors (default: 768 for BERT-like models)
            embedding_size: Desired embedding dimension (default: 256)
            
        Returns:
            Configured DocumentEmbedder instance
        """
        model = SimpleEmbeddingModel(input_size=input_size, embedding_size=embedding_size)
        return cls(model)
