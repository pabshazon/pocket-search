from typing import Dict, Any
import torch
from transformers import ViltProcessor, ViltForImageAndTextRetrieval
import numpy as np
from PIL import Image
from src.config.device_config import DeviceConfig
from src.config.models_config import ModelsConfig
from src.domain.on_metal.logger import get_logger
logger = get_logger(__name__)

class VisualLanguageModel:
    def __init__(self):
        self.config     = ModelsConfig.VISION
        self.device     = DeviceConfig.get_device(self.config.device_priority)
        self.processor  = ViltProcessor.from_pretrained(self.config.name)
        self.model      = ViltForImageAndTextRetrieval.from_pretrained(
            self.config.name
        ).to(self.device)
        
        # Predefined questions for comprehensive image analysis
        self.analysis_questions = [
            "What type of image is this?",
            "What is the main subject of this image?",
            "Are there any text elements in this image?",
            "Is this a chart or diagram?",
            "What colors are predominantly used in this image?",
            "Does this image contain any tables or structured data?",
            "Are there any identifiable symbols or icons?",
            "What is the overall layout of this image?"
        ]
    
    def analyze_image(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Analyzes an image using the ViLT model by asking predefined questions.
        
        Args:
            image (np.ndarray): The image to analyze in numpy array format
            
        Returns:
            Dict[str, Any]: Analysis results including responses to predefined questions
                           and confidence scores
        """
        try:
            # Convert numpy array to PIL Image
            if image.shape[2] == 4:  # If RGBA, convert to RGB
                image = image[:, :, :3]
            pil_image = Image.fromarray(image)
            
            results = {}
            confidences = []
            
            for question in self.analysis_questions:
                try:
                    # Prepare inputs for the model
                    inputs = self.processor(
                        images=pil_image,
                        text=question,
                        return_tensors="pt",
                        padding=True
                    )
                    
                    # Move inputs to the same device as the model
                    inputs = {k: v.to(self.device) for k, v in inputs.items()}
                    
                    # Get model outputs
                    with torch.no_grad():
                        outputs = self.model(**inputs)
                    
                    # Process outputs
                    logits = outputs.logits
                    probs = torch.nn.functional.softmax(logits, dim=1)
                    confidence = float(torch.max(probs).cpu().numpy())
                    
                    results[question] = {
                        "confidence": confidence,
                        "score": float(torch.max(logits).cpu().numpy())
                    }
                    confidences.append(confidence)
                    
                except Exception as e:
                    logger.error(f"Error processing question '{question}': {str(e)}")
                    results[question] = {
                        "confidence": 0.0,
                        "score": 0.0,
                        "error": str(e)
                    }
            
            # Add overall analysis metrics
            analysis_summary = {
                "analysis_results": results,
                "overall_confidence": np.mean(confidences) if confidences else 0.0,
                "num_successful_analyses": len([c for c in confidences if c > 0.0])
            }
            
            return analysis_summary
            
        except Exception as e:
            logger.error(f"Error in image analysis: {str(e)}")
            return {
                "error": str(e),
                "analysis_results": {},
                "overall_confidence": 0.0,
                "num_successful_analyses": 0
            }
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocesses the input image for the model.
        
        Args:
            image (np.ndarray): Input image
            
        Returns:
            np.ndarray: Preprocessed image
        """
        # Handle different color channels
        if len(image.shape) == 2:  # Grayscale
            image = np.stack([image] * 3, axis=-1)
        elif image.shape[2] == 4:  # RGBA
            image = image[:, :, :3]
        
        return image
