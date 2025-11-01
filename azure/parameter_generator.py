# parameter_generator.py
import json
from typing import Dict, Any

class AzureParameterGenerator:
    @staticmethod
    def generate_vm_parameters(
        resource_group_name: str,
        location: str,
        vm_name: str,
        admin_username: str,
        admin_password: str,
        vm_size: str = "Standard_D2s_v3",
        image_reference: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Generates complete Azure VM deployment parameters
        
        Args:
            resource_group_name: Name of the Azure resource group
            location: Azure region (e.g., 'eastus')
            vm_name: Name for the virtual machine
            admin_username: Admin username for the VM
            admin_password: Admin password for the VM
            vm_size: (Optional) Azure VM size, defaults to Standard_D2s_v3
            image_reference: (Optional) Custom image reference
            
        Returns:
            Dictionary with complete deployment parameters
        """
        # Default to Ubuntu 22.04 LTS if no image specified
        if not image_reference:
            image_reference = {
                "publisher": "Canonical",
                "offer": "0001-com-ubuntu-server-jammy",
                "sku": "22_04-lts-gen2",
                "version": "latest"
            }
        
        return {
            "deployment_type": "virtual_machine",
            "resource_group_name": resource_group_name,
            "location": location,
            "vm_size": vm_size,
            "admin_username": admin_username,
            "admin_password": admin_password,
            "vm_name": vm_name,
            "image_reference": image_reference
        }

def get_user_input() -> Dict[str, str]:
    """Collects basic user input for VM deployment"""
    print("Azure VM Deployment Parameters")
    print("Please provide the following details:\n")
    
    return {
        "resource_group_name": input("Resource Group Name: "),
        "location": input("Location (e.g., eastus, westus): "),
        "vm_name": input("VM Name: "),
        "admin_username": input("Admin Username: "),
        "admin_password": input("Admin Password: ")
    }

if __name__ == "__main__":
    # Example standalone usage
    user_input = get_user_input()
    params = AzureParameterGenerator.generate_vm_parameters(**user_input)
    
    print("\nGenerated Deployment Parameters:")
    print(json.dumps(params, indent=2))