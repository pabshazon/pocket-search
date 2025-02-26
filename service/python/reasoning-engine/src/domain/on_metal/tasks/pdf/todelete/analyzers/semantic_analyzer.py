from typing import List, Dict, Any
from dataclasses import dataclass
from transformers import LayoutLMv3Processor, LayoutLMv3Model
import torch
from src.domain.on_metal.tasks.pdf.extractors.text_extractor import TextBlock
from src.config.device_config import DeviceConfig
from src.config.models_config import ModelsConfig

@dataclass
class SemanticChunk:
    content: str
    chunk_type: str
    confidence: float
    page_num: int
    bbox: tuple
    relationships: List[Dict[str, Any]]

class SemanticAnalyzer:
    def __init__(self):
        self.device     = DeviceConfig.get_device(ModelsConfig.LAYOUT.device_priority)
        self.processor  = LayoutLMv3Processor.from_pretrained(ModelsConfig.LAYOUT.name)
        self.model      = LayoutLMv3Model.from_pretrained(ModelsConfig.LAYOUT.name).to(self.device)
        print("Semantic analyzer initialized.")
        
    # def analyze(self, text_blocks: List[TextBlock], layout_info: Dict[str, Any]) -> List[SemanticChunk]:
    def analyze(self, text: List[TextBlock], layout_info: Dict[str, Any]) -> List[SemanticChunk]:
        chunks = []
        
        # Process blocks in batches for GPU efficiency
        batch_size = 8
        for i in range(0, len(text_blocks), batch_size):
            batch = text_blocks[i:i + batch_size]
            batch_chunks = self._process_batch(batch, layout_info)
            chunks.extend(batch_chunks)
            
        # Post-process to establish relationships between chunks
        self._establish_relationships(chunks)
        
        return chunks
    
    def _process_batch(self, batch: List[TextBlock], layout_info: Dict[str, Any]) -> List[SemanticChunk]:
        batch_chunks = []
        
        texts = [block.text for block in batch]
        boxes = [block.bbox for block in batch]
        
        # Prepare inputs for LayoutLM and ensure the tensors are on the target device
        encoding = self.processor(
            texts,
            boxes=boxes,
            return_tensors="pt",
            padding=True,
            truncation=True
        )
        encoding = {k: v.to(self.device) for k, v in encoding.items()}
        
        # Get model outputs
        with torch.no_grad():
            outputs = self.model(**encoding)
        
        # Process each block in the batch
        for idx, block in enumerate(batch):
            chunk_type = self._determine_chunk_type(
                block,
                outputs.last_hidden_state[idx],
                layout_info
            )
            
            chunk = SemanticChunk(
                content=block.text,
                chunk_type=chunk_type,
                confidence=self._calculate_confidence(outputs.last_hidden_state[idx]),
                page_num=block.page_num,
                bbox=block.bbox,
                relationships=[]
            )
            batch_chunks.append(chunk)
        
        return batch_chunks
    
    def _determine_chunk_type(self, block: TextBlock, hidden_state: torch.Tensor, layout_info: Dict[str, Any]) -> str:
        # Map the block_type from TextBlock to our semantic chunk_type
        base_type = block.block_type  # Using block_type from TextBlock
        # For now, maintain the simple mapping but we can expand this later
        return base_type
    
    def _calculate_confidence(self, hidden_state: torch.Tensor) -> float:
        # Calculate confidence score based on model outputs
        return float(torch.mean(hidden_state).cpu().numpy())
    
    def _establish_relationships(self, chunks: List[SemanticChunk]):
        # Establish hierarchical and reference relationships between chunks
        for i, chunk in enumerate(chunks):
            if i > 0:
                # Check for a hierarchical relationship with the previous chunk
                prev_chunk = chunks[i-1]
                if self._is_hierarchical_relationship(prev_chunk, chunk):
                    chunk.relationships.append({
                        "type": "parent",
                        "chunk_id": i-1
                    })
    
    def _is_hierarchical_relationship(self, chunk1: SemanticChunk, chunk2: SemanticChunk) -> bool:
        # Determine if there's a hierarchical relationship between chunks.
        return False
