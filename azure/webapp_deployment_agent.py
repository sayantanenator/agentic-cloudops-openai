# webapp_deployment_agent.py
import os
import json
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.mgmt.web import WebSiteManagementClient
from azure.mgmt.resource import ResourceManagementClient

load_dotenv()

class WebAppDeploymentAgent:
    def __init__(self):
        self.credential = DefaultAzureCredential()
        self.subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
        self.runtime_mappings = {
            "python:3.9": "PYTHON|3.9",
            "python:3.8": "PYTHON|3.8",
            "node:16-lts": "NODE|16-lts",
            "node:18-lts": "NODE|18-lts",
            "dotnet:6": "DOTNETCORE|6.0",
            "php:8": "PHP|8.0"
        }
        
    def _validate_runtime(self, runtime):
        """Validate and format the runtime string"""
        # Check if it's already in correct format
        if "|" in runtime:
            return runtime
            
        # Try to map from shorthand format
        if runtime in self.runtime_mappings:
            return self.runtime_mappings[runtime]
            
        # Default to Python 3.9 if invalid
        print(f"Warning: Unknown runtime '{runtime}'. Defaulting to Python 3.9")
        return "PYTHON|3.9"
    
    def deploy_webapp(self, params):
        """Deploys an Azure WebApp"""
        try:
            web_client = WebSiteManagementClient(self.credential, self.subscription_id)
            resource_client = ResourceManagementClient(self.credential, self.subscription_id)
            
            # Create resource group if not exists
            print(f"\nCreating/verifying resource group: {params['resource_group_name']}")
            resource_client.resource_groups.create_or_update(
                params["resource_group_name"],
                {"location": params["location"]}
            )
            
            # Create App Service plan
            print(f"\nCreating App Service plan for {params['app_name']}")
            plan_result = web_client.app_service_plans.begin_create_or_update(
                params["resource_group_name"],
                f"{params['app_name']}-plan",
                {
                    "location": params["location"],
                    "kind": "linux",  # Required for Linux apps
                    "reserved": True,  # Required for Linux apps
                    "sku": {
                        "name": params["sku"],
                        "tier": params["sku"].rstrip('0123456789'),
                        "size": params["sku"],
                        "family": params["sku"][0],
                        "capacity": 1
                    }
                }
            ).result()
            
            # Validate and format runtime
            formatted_runtime = self._validate_runtime(params["runtime"])
            
            # Create WebApp
            print(f"\nCreating WebApp: {params['app_name']}")
            webapp_result = web_client.web_apps.begin_create_or_update(
                params["resource_group_name"],
                params["app_name"],
                {
                    "location": params["location"],
                    "server_farm_id": plan_result.id,
                    "kind": "app,linux",  # Required for Linux apps
                    "site_config": {
                        "linux_fx_version": formatted_runtime,
                        "app_settings": [
                            {
                                "name": "WEBSITES_ENABLE_APP_SERVICE_STORAGE",
                                "value": "false"
                            }
                        ]
                    }
                }
            ).result()
            
            return {
                "status": "success",
                "resources": {
                    "resource_group": params["resource_group_name"],
                    "webapp_name": webapp_result.name,
                    "default_hostname": webapp_result.default_host_name,
                    "app_service_plan": plan_result.name,
                    "runtime": formatted_runtime,
                    "sku": params["sku"],
                    "url": f"https://{webapp_result.default_host_name}"
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "details": f"Failed to deploy WebApp. Check runtime format. Valid examples: python:3.9, node:16-lts"
            }

# Test function
def test_deployment():
    """Test the deployment agent with sample parameters"""
    test_params = {
        "deployment_type": "webapp",
        "resource_group_name": "test-webapp-rg",
        "app_name": "aicoe-webapp-56",
        "location": "eastus",
        "runtime": "python:3.9",
        "sku": "F1"
    }
    
    print("Starting test deployment...")
    agent = WebAppDeploymentAgent()
    result = agent.deploy_webapp(test_params)
    print("\nDeployment result:", json.dumps(result, indent=2))

if __name__ == "__main__":
    test_deployment()