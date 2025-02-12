#@todo fix this mess below

class SimpleEmbeddingModel(nn.Module):
    def __init__(self, input_size, embedding_size):
        super(SimpleEmbeddingModel, self).__init__()
        self.embedding = nn.Linear(input_size, embedding_size)
    
    def forward(self, x):
        return self.embedding(x)


model = SimpleEmbeddingModel(input_size=10, embedding_size=5)
