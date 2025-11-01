import os
import json
from openai import AzureOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def extract_azure_resources(input_json_path, output_txt_path):
    # Read OCR output
    with open(input_json_path) as f:
        ocr_data = json.load(f)

    # Prepare prompt for LLM
    prompt = (
        "You are an Azure cloud architect. "
        "Given this OCR output from an architecture diagram, extract a clean, structured list of valid Azure resources. "
        "For each resource, output its type and name in the format: <ResourceType>: <ResourceName>. "
        "Ignore any irrelevant or ambiguous entries. Only include resources that are valid in Azure (e.g., VirtualNetwork, Subnet, API Management, AKS, Application Gateway, SQL, etc.). "
        "Output one resource per line, no explanations, no markdown."
        "\n\nOCR JSON:\n"
        f"{json.dumps(ocr_data, indent=2)}"
    )

    # Initialize Azure OpenAI client
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        api_version="2024-02-01",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        max_retries=3
    )

    # Call LLM
    messages = [
        {"role": "system", "content": "You are an Azure cloud architect."},
        {"role": "user", "content": prompt}
    ]
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        messages=messages,
        temperature=0.2,
        max_tokens=1500
    )
    extracted_resources = response.choices[0].message.content.strip()

    # Save to text file
    with open(output_txt_path, "w") as f:
        f.write(extracted_resources)

    print(f"Extracted Azure resources saved to {output_txt_path}")

if __name__ == "__main__":
    extract_azure_resources(
        input_json_path="azure_resources.json",
        output_txt_path="extracted_resources.txt"
    )