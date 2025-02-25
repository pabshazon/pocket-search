from typing import List, Dict, Any
import fitz
import cv2
import numpy as np
from PIL import Image
import io
from src.domain.on_metal.nlp.model.vlm import VisualLanguageModel

class PdfImageExtractor:
    def __init__(self):
        self.vlm = VisualLanguageModel()
    
    def extract(self, doc: fitz.Document) -> List[Dict[str, Any]]:
        images = []
        
        for page_num, page in enumerate(doc):
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                
                if base_image:
                    image_data = {
                        "page_num": page_num,
                        "index": img_index,
                        "bbox": self._get_image_bbox(page, xref),
                        "analysis": self._analyze_image(base_image["image"])
                    }
                    images.append(image_data)
        
        return images
    
    def _analyze_image(self, image_bytes: bytes) -> Dict[str, Any]:
        # Convert bytes to numpy array for OpenCV
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Use VLM for image analysis
        analysis = self.vlm.analyze_image(img)
        return analysis
    
    def _get_image_bbox(self, page, xref):
        # Get image location on page
        for img_info in page.get_images():
            if img_info[0] == xref:
                return img_info[1]  # bbox
        return None
