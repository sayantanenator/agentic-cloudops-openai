# webapp_parameter_generator.py
from typing import Dict, Any
import json

class WebAppParameterGenerator:
    @staticmethod
    def generate_webapp_parameters(
        resource_group_name: str,
        app_name: str,
        location: str,
        runtime: str = "python:3.9",
        sku: str = "F1"
    ) -> Dict[str, Any]:
        """
        Generates Azure WebApp deployment parameters
        
        Args:
            resource_group_name: Name of the Azure resource group
            app_name: Name for the web application
            location: Azure region (e.g., 'eastus')
            runtime: Runtime stack (default: python:3.9)
            sku: Pricing tier (default: F1 - free tier)
            
        Returns:
            Dictionary with complete deployment parameters
        """
        return {
            "deployment_type": "webapp",
            "resource_group_name": resource_group_name,
            "app_name": app_name,
            "location": location,
            "runtime": runtime,
            "sku": sku
        }

def get_webapp_user_input() -> Dict[str, str]:
    """Collects user input for WebApp deployment"""
    print("\nAzure WebApp Configuration")
    print("Please provide the following details:\n")
    
    return {
        "resource_group_name": input("Resource Group Name: "),
        "app_name": input("WebApp Name: "),
        "location": input("Location (e.g., eastus): "),
        "runtime": input("Runtime stack [python:3.9, node:16-lts, etc.]: ") or "python:3.9",
        "sku": input("Pricing tier [F1 (free), B1, etc.]: ") or "F1"
    }

if __name__ == "__main__":
    # Example standalone usage
    user_input = get_webapp_user_input()
    params = WebAppParameterGenerator.generate_webapp_parameters(**user_input)
    
    print("\nGenerated Deployment Parameters:")
    print(json.dumps(params, indent=2))