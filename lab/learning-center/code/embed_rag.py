from transformers import AutoTokenizer, AutoModel, AutoModelForCausalLM
import torch
import torch.nn.functional as F
from typing import List, Dict, Tuple
import faiss
import numpy as np
from dataclasses import dataclass
import ast
from pathlib import Path


@dataclass
class CodeChunk:
    content: str
    file_path: str
    start_line: int
    end_line: int


@dataclass
class RetrievedContext:
    chunks: List[CodeChunk]
    similarities: List[float]


class CodeEmbeddingRAG:
    def __init__(self,
                 embedding_model="microsoft/codebert-base",
                 generation_model="Salesforce/codegen-350M-mono"):
        # Initialize models
        self.embed_tokenizer = AutoTokenizer.from_pretrained(embedding_model)
        self.embed_model = AutoModel.from_pretrained(embedding_model)

        self.gen_tokenizer = AutoTokenizer.from_pretrained(generation_model)
        self.gen_model = AutoModelForCausalLM.from_pretrained(generation_model)

        # Set device
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        else:
            self.device = torch.device("cpu")

        self.embed_model.to(self.device)
        self.gen_model.to(self.device)

        # Initialize FAISS index
        self.index = None
        self.chunks: List[CodeChunk] = []

    def get_code_embedding(self, code: str) -> np.ndarray:
        """Generate embeddings for code snippet"""
        # Tokenize code
        inputs = self.embed_tokenizer(
            code,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt"
        ).to(self.device)

        # Generate embeddings
        with torch.no_grad():
            outputs = self.embed_model(**inputs)
            # Use CLS token embedding
            embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()

        return embeddings

    def chunk_code(self, code: str, file_path: str) -> List[CodeChunk]:
        """Split code into meaningful chunks using AST"""
        chunks = []
        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    # Get the source lines for this node
                    start_line = node.lineno
                    end_line = node.end_lineno
                    chunk_content = "\n".join(
                        code.splitlines()[start_line - 1:end_line]
                    )

                    chunks.append(CodeChunk(
                        content=chunk_content,
                        file_path=file_path,
                        start_line=start_line,
                        end_line=end_line
                    ))

            if not chunks:  # If no functions/classes found, use whole file
                chunks.append(CodeChunk(
                    content=code,
                    file_path=file_path,
                    start_line=1,
                    end_line=len(code.splitlines())
                ))

        except SyntaxError:
            # Handle invalid code by using the whole content
            chunks.append(CodeChunk(
                content=code,
                file_path=file_path,
                start_line=1,
                end_line=len(code.splitlines())
            ))

        return chunks

    def index_codebase(self, root_dir: str):
        """Index all Python files in a directory"""
        code_chunks = []
        embeddings = []

        # Find all Python files
        for py_file in Path(root_dir).rglob("*.py"):
            with open(py_file, 'r', encoding='utf-8') as f:
                code = f.read()

            # Chunk the code
            chunks = self.chunk_code(code, str(py_file))
            code_chunks.extend(chunks)

            # Generate embeddings for chunks
            for chunk in chunks:
                embedding = self.get_code_embedding(chunk.content)
                embeddings.append(embedding)

        # Convert embeddings to numpy array
        embeddings_array = np.vstack(embeddings)

        # Create FAISS index
        dimension = embeddings_array.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings_array.astype('float32'))

        # Store chunks for later retrieval
        self.chunks = code_chunks

    def retrieve_similar(self,
                         query: str,
                         k: int = 3) -> RetrievedContext:
        """Retrieve similar code chunks for a query"""
        # Generate query embedding
        query_embedding = self.get_code_embedding(query)

        # Search in FAISS index
        distances, indices = self.index.search(
            query_embedding.astype('float32'),
            k
        )

        # Get corresponding chunks and similarities
        retrieved_chunks = [self.chunks[i] for i in indices[0]]
        similarities = [1 / (1 + d) for d in distances[0]]  # Convert distance to similarity

        return RetrievedContext(chunks=retrieved_chunks, similarities=similarities)

    def generate_with_context(self,
                              query: str,
                              retrieved_context: RetrievedContext,
                              max_length: int = 512) -> str:
        """Generate code based on query and retrieved context"""
        # Create prompt with context
        context_str = "\n\n".join(
            f"Reference code from {chunk.file_path}:\n{chunk.content}"
            for chunk in retrieved_context.chunks
        )

        prompt = f"""
        Retrieved similar code:
        {context_str}

        Based on the above code, complete this task:
        {query}

        Generated code:
        """

        # Generate completion
        inputs = self.gen_tokenizer(
            prompt,
            padding=True,
            truncation=True,
            max_length=max_length,
            return_tensors="pt"
        ).to(self.device)

        with torch.no_grad():
            outputs = self.gen_model.generate(
                inputs["input_ids"],
                max_length=max_length,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.gen_tokenizer.eos_token_id
            )

        generated_code = self.gen_tokenizer.decode(outputs[0], skip_special_tokens=True)

        return generated_code.strip()


# Example usage
def test_code_rag():
    # Initialize system
    rag = CodeEmbeddingRAG()

    # Example codebase to index
    example_code = {
        "math_utils.py": """
def calculate_average(numbers):
    return sum(numbers) / len(numbers)

def calculate_median(numbers):
    sorted_nums = sorted(numbers)
    mid = len(sorted_nums) // 2
    return sorted_nums[mid]
""",
        "string_utils.py": """
def reverse_string(text):
    return text[::-1]

def count_words(text):
    return len(text.split())
"""
    }

    # Create temporary directory and files
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmp_dir:
        for filename, content in example_code.items():
            with open(os.path.join(tmp_dir, filename), 'w') as f:
                f.write(content)

        # Index the codebase
        rag.index_codebase(tmp_dir)

        # Test retrieval and generation
        query = "Write a function to calculate the mode of a list of numbers"

        # Retrieve similar code
        retrieved = rag.retrieve_similar(query)

        print("Retrieved similar code chunks:")
        for chunk, similarity in zip(retrieved.chunks, retrieved.similarities):
            print(f"\nFile: {chunk.file_path}")
            print(f"Similarity: {similarity:.3f}")
            print("Content:")
            print(chunk.content)

        # Generate new code
        generated = rag.generate_with_context(query, retrieved)

        print("\nGenerated code:")
        print(generated)


if __name__ == "__main__":
    test_code_rag()