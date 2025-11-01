import easyocr
import cv2
import json

def image_extraction_agent(image_path, languages=['en'], confidence_threshold=0.4):
    """
    The Agent will Extracts text from Azure architecture diagrams.
    
    Args:
        image_path (str): Path to the image file
        languages (list): Languages for OCR (default: English)
        confidence_threshold (float): Minimum confidence score (0-1)
    
    Returns:
        List of dictionaries with text and metadata
    """
    # Initialize EasyOCR reader (CPU mode)
    reader = easyocr.Reader(languages, gpu=False)
    
    # Read image
    img = cv2.imread(image_path)
    
    # Extract text
    results = reader.readtext(img)
    
    # Process results
    extracted_text = []
    for (bbox, text, prob) in results:
        if prob >= confidence_threshold:
            extracted_text.append({
                "text": text.strip(),
                #"confidence": float(prob),
                #"bounding_box": [[int(x), int(y)] for [x, y] in bbox]  # Convert to integers
            })
    
    return extracted_text

def save_text_to_json(text_data, output_file="extracted_text.json"):
    """Saves extracted text to JSON file"""
    with open(output_file, 'w') as f:
        json.dump(text_data, f, indent=2)
    print(f"Text saved to {output_file}")


def extract_tier_information(self, analysis_result):
        """Extract tier information from the diagram"""
        tiers = {
            "web_tier": [],
            "business_tier": [],
            "data_tier": []
        }
        
        if 'description' in analysis_result and 'tags' in analysis_result['description']:
            tags = analysis_result['description']['tags']
            
            # Look for tier indicators
            if "web" in tags and "tier" in tags:
                tiers["web_tier"] = self.find_resources_in_area(analysis_result, "web tier")
            if "business" in tags and "tier" in tags:
                tiers["business_tier"] = self.find_resources_in_area(analysis_result, "business tier")
            if "data" in tags and "tier" in tags:
                tiers["data_tier"] = self.find_resources_in_area(analysis_result, "data tier")
        
        return tiers

# Example usage
if __name__ == "__main__":
    # Configure as needed
    image_path = "protect-apis.png"
    output_json = "azure_resources.json"
    
    # Extract text
    extracted_text = image_extraction_agent(image_path)
    
    # Save to JSON
    save_text_to_json(extracted_text, output_json)
    
    # Print results
    print("Extracted Azure Resources:")
    # for item in extracted_text:
    #     print(f"- {item['text']} (Confidence: {item['confidence']:.2f})")

