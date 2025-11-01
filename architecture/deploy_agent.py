import os
import json
from deploy_infrastructure import deploy_infrastructure
from dotenv import load_dotenv

load_dotenv()

class DeploymentAgent:
    @staticmethod
    def get_azure_credentials():
        """Retrieve Azure credentials from environment or user input"""
        credentials = {
            "subscription_id": os.getenv("AZURE_SUBSCRIPTION_ID"),
            "tenant_id": os.getenv("AZURE_TENANT_ID"),
            "client_id": os.getenv("AZURE_CLIENT_ID"),
            "client_secret": os.getenv("AZURE_CLIENT_SECRET")
        }
        
        missing = [k for k, v in credentials.items() if not v]
        if missing:
            print("\n=== AZURE CREDENTIALS REQUIRED ===")
            for var in missing:
                credentials[var] = input(f"Enter {var.replace('_', ' ').title()}: ").strip()
        
        return credentials

    @staticmethod
    def get_deployment_config():
        """Get deployment configuration from user"""
        print("\n=== DEPLOYMENT CONFIGURATION ===")
        return {
            "environment": input("Environment (prod/stage): ").strip() or "prod",
            "application_name": input("Application name: ").strip() or "aumanager",
            "location": input("Azure region: ").strip() or "EastUS"
        }

def main():
    print("Azure Infrastructure Deployment Agent")
    print("------------------------------------")
    
    # Get deployment parameters
    pulumi_dir = "scripts"  # Directory with generated __main__.py
    azure_creds = DeploymentAgent.get_azure_credentials()
    config = DeploymentAgent.get_deployment_config()
    
    # Execute deployment
    print("\nStarting deployment...")
    result = deploy_infrastructure(pulumi_dir, config, azure_creds)
    
    # Handle results
    if result["status"] == "success":
        print("\nDEPLOYMENT SUCCESSFUL!")
        print(f"Resource Group: rg-{config['environment']}-{config['application_name']}-{config['location']}")
    elif result["status"] == "no_changes":
        print("\nNo changes to deploy")
    else:
        print(f"\nDEPLOYMENT FAILED: {result.get('message', 'Unknown error')}")

if __name__ == "__main__":
    main()