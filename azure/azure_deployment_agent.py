# vm_deployment_agent.py
import json
import os
from dotenv import load_dotenv
from azure.identity import ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.core.exceptions import ResourceNotFoundError
import time

class VMDeploymentAgent:
    def __init__(self):
        load_dotenv()
        self.credential, self.subscription_id = self._get_azure_credentials()
        
    def _get_azure_credentials(self):
        """Retrieve Azure credentials from environment variables"""
        subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
        client_id = os.getenv('AZURE_CLIENT_ID')
        tenant_id = os.getenv('AZURE_TENANT_ID')
        client_secret = os.getenv('AZURE_CLIENT_SECRET')
        
        if not all([subscription_id, client_id, tenant_id, client_secret]):
            raise ValueError("Missing required Azure credentials in environment variables")
        
        credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        return credential, subscription_id
    
    def _check_resource_group_exists(self, resource_client, rg_name):
        """Check if resource group exists"""
        try:
            resource_client.resource_groups.get(rg_name)
            return True
        except ResourceNotFoundError:
            return False
    
    def _check_vnet_exists(self, network_client, rg_name, vnet_name):
        """Check if virtual network exists"""
        try:
            network_client.virtual_networks.get(rg_name, vnet_name)
            return True
        except ResourceNotFoundError:
            return False
    
    def _check_public_ip_exists(self, network_client, rg_name, ip_name):
        """Check if public IP exists"""
        try:
            network_client.public_ip_addresses.get(rg_name, ip_name)
            return True
        except ResourceNotFoundError:
            return False
    
    def _check_nic_exists(self, network_client, rg_name, nic_name):
        """Check if network interface exists"""
        try:
            network_client.network_interfaces.get(rg_name, nic_name)
            return True
        except ResourceNotFoundError:
            return False
    
    def _check_vm_exists(self, compute_client, rg_name, vm_name):
        """Check if virtual machine exists"""
        try:
            compute_client.virtual_machines.get(rg_name, vm_name)
            return True
        except ResourceNotFoundError:
            return False
    
    def deploy_from_parameters(self, params):
        """
        Main deployment method that can be called externally
        Args:
            params: Either a JSON string or dictionary containing deployment parameters
        Returns:
            Dictionary with deployment status and results
        """
        try:
            if isinstance(params, str):
                params = json.loads(params)
                
            # Validate required parameters
            self._validate_parameters(params)
            
            # Execute deployment
            return self._execute_deployment(params)
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "details": "Failed to deploy Azure resources"
            }
    
    def _validate_parameters(self, params):
        """Validate all required parameters exist"""
        required_params = [
            "deployment_type", 
            "resource_group_name",
            "location"
        ]
        
        if params["deployment_type"] == "virtual_machine":
            required_params.extend([
                "vm_size",
                "admin_username",
                "admin_password"
            ])
        
        for param in required_params:
            if param not in params:
                raise ValueError(f"Missing required parameter: {param}")
    
    def _execute_deployment(self, params):
        """Handles the actual deployment logic"""
        # Initialize clients
        resource_client = ResourceManagementClient(self.credential, self.subscription_id)
        network_client = NetworkManagementClient(self.credential, self.subscription_id)
        compute_client = ComputeManagementClient(self.credential, self.subscription_id)
        
        # Set default values
        rg_name = params["resource_group_name"]
        location = params["location"]
        
        # Create or get resource group
        if not self._check_resource_group_exists(resource_client, rg_name):
            print(f"\nCreating resource group: {rg_name}")
            resource_client.resource_groups.create_or_update(
                rg_name,
                {"location": location}
            )
        else:
            print(f"\nResource group {rg_name} already exists")
        
        # VNet configuration
        vnet_name = params.get("vnet_name", f"{rg_name}-vnet")
        subnet_name = params.get("subnet_name", "default-subnet")
        address_space = params.get("address_space", "10.0.0.0/16")
        
        # Create Virtual Network if it doesn't exist
        if not self._check_vnet_exists(network_client, rg_name, vnet_name):
            print(f"\nCreating virtual network: {vnet_name}")
            vnet_params = {
                "location": location,
                "address_space": {
                    "address_prefixes": [address_space]
                },
                "subnets": [{
                    "name": subnet_name,
                    "address_prefix": "10.0.0.0/24"
                }]
            }
            vnet_poller = network_client.virtual_networks.begin_create_or_update(
                rg_name,
                vnet_name,
                vnet_params
            )
            vnet_result = vnet_poller.result()
            print(f"Successfully created virtual network: {vnet_result.name}")
        else:
            print(f"\nVirtual network {vnet_name} already exists")
            vnet_result = network_client.virtual_networks.get(rg_name, vnet_name)
        
        # Get subnet information
        subnet_info = network_client.subnets.get(
            rg_name,
            vnet_name,
            subnet_name
        )
        
        # If deployment includes VM
        if params["deployment_type"] == "virtual_machine":
            return self._deploy_virtual_machine(
                params,
                rg_name,
                location,
                subnet_info,
                vnet_name,
                network_client,
                compute_client
            )
        else:
            return {
                "status": "success",
                "resources": {
                    "resource_group": rg_name,
                    "vnet": vnet_result.name,
                    "subnet": subnet_name,
                    "message": "VNet only deployment completed"
                }
            }
    
    def _deploy_virtual_machine(self, params, rg_name, location, subnet_info, vnet_name, network_client, compute_client):
        """Handles VM-specific deployment"""
        vm_name = params.get("vm_name", f"{rg_name}-vm")
        
        # Check if VM already exists
        if self._check_vm_exists(compute_client, rg_name, vm_name):
            vm_result = compute_client.virtual_machines.get(rg_name, vm_name)
            return {
                "status": "success",
                "resources": {
                    "resource_group": rg_name,
                    "vnet": vnet_name,
                    "subnet": subnet_info.name,
                    "vm": vm_result.name,
                    "message": "VM already exists",
                    "existing": True
                }
            }
        
        # Create public IP address if it doesn't exist
        public_ip_name = f"{vm_name}-ip"
        if not self._check_public_ip_exists(network_client, rg_name, public_ip_name):
            print(f"\nCreating public IP address: {public_ip_name}")
            public_ip_params = {
                "location": location,
                "public_ip_allocation_method": "Dynamic",
                "sku": {"name": "Basic"}
            }
            public_ip_poller = network_client.public_ip_addresses.begin_create_or_update(
                rg_name,
                public_ip_name,
                public_ip_params
            )
            public_ip_result = public_ip_poller.result()
        else:
            print(f"\nPublic IP {public_ip_name} already exists")
            public_ip_result = network_client.public_ip_addresses.get(rg_name, public_ip_name)
        
        # Create network interface if it doesn't exist
        nic_name = f"{vm_name}-nic"
        if not self._check_nic_exists(network_client, rg_name, nic_name):
            print(f"\nCreating network interface: {nic_name}")
            nic_params = {
                "location": location,
                "ip_configurations": [{
                    "name": f"{vm_name}-ipconfig",
                    "subnet": {"id": subnet_info.id},
                    "public_ip_address": {"id": public_ip_result.id}
                }]
            }
            nic_poller = network_client.network_interfaces.begin_create_or_update(
                rg_name,
                nic_name,
                nic_params
            )
            nic_result = nic_poller.result()
        else:
            print(f"\nNetwork interface {nic_name} already exists")
            nic_result = network_client.network_interfaces.get(rg_name, nic_name)
        
        # Create virtual machine
        print(f"\nCreating virtual machine: {vm_name}")
        vm_params = {
            "location": location,
            "hardware_profile": {
                "vm_size": params["vm_size"]
            },
            "storage_profile": {
                "image_reference": params.get("image_reference", {
                    "publisher": "Canonical",
                    "offer": "0001-com-ubuntu-server-jammy",
                    "sku": "22_04-lts-gen2",
                    "version": "latest"
                }),
                "os_disk": {
                    "create_option": "FromImage",
                    "delete_option": "Delete",
                    "disk_size_gb": params.get("disk_size_gb", 30),
                    "name": f"{vm_name}-osdisk",
                    "caching": "ReadWrite"
                }
            },
            "os_profile": {
                "computer_name": vm_name,
                "admin_username": params["admin_username"],
                "admin_password": params["admin_password"],
                "linux_configuration": {
                    "disable_password_authentication": False
                }
            },
            "network_profile": {
                "network_interfaces": [{
                    "id": nic_result.id,
                    "primary": True
                }]
            }
        }
        
        vm_poller = compute_client.virtual_machines.begin_create_or_update(
            rg_name,
            vm_name,
            vm_params
        )
        vm_result = vm_poller.result()
        print(f"Successfully created virtual machine: {vm_result.name}")
        
        # Get public IP address
        print("\nWaiting for public IP address allocation...")
        time.sleep(30)
        public_ip = network_client.public_ip_addresses.get(
            rg_name,
            public_ip_name
        )
        
        return {
            "status": "success",
            "resources": {
                "resource_group": rg_name,
                "vnet": vnet_name,
                "subnet": subnet_info.name,
                "vm": vm_result.name,
                "public_ip": public_ip.ip_address,
                "admin_username": params["admin_username"],
                "message": "New VM deployment completed"
            }
        }

def test_deployment():
    """Test the deployment agent with sample parameters"""
    # Sample parameters (would normally come from OpenAI)
    test_params = {
        "deployment_type": "virtual_machine",
        "resource_group_name": "test-rg-01",
        "location": "eastus",
        "vm_size": "Standard_D2s_v3",
        "admin_username": "testadmin",
        "admin_password": "SecurePass123!",
        "vm_name": "test-vm-01",
        "image_reference": {
            "publisher": "Canonical",
            "offer": "0001-com-ubuntu-server-jammy",
            "sku": "22_04-lts-gen2",
            "version": "latest"
        }
    }
    
    print("Starting test deployment...")
    agent = VMDeploymentAgent()
    result = agent.deploy_from_parameters(test_params)
    print("\nDeployment result:", json.dumps(result, indent=2))

if __name__ == "__main__":
    test_deployment()