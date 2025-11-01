# ec2_parameter_generator.py
import json
from typing import Dict, Any

class EC2ParameterGenerator:
    @staticmethod
    def generate_ec2_parameters(
        instance_name: str,
        instance_type: str = "t2.micro",
        ami_id: str = "ami-0c55b159cbfafe1f0",  # Ubuntu 20.04 LTS
        key_pair_name: str = None,
        security_group_ids: list = None,
        subnet_id: str = None
    ) -> Dict[str, Any]:
        """
        Generates EC2 deployment parameters
        
        Args:
            instance_name: Name tag for the instance
            instance_type: EC2 instance type (default: t2.micro)
            ami_id: AMI ID (default: Ubuntu 20.04 LTS in us-east-1)
            key_pair_name: Existing key pair name for SSH access
            security_group_ids: List of security group IDs
            subnet_id: VPC subnet ID
            
        Returns:
            Dictionary with complete deployment parameters
        """
        return {
            "deployment_type": "ec2",
            "instance_name": instance_name,
            "instance_type": instance_type,
            "ami_id": ami_id,
            "key_pair_name": key_pair_name,
            "security_group_ids": security_group_ids or ["default"],
            "subnet_id": subnet_id,
            "tag_specifications": [
                {
                    "ResourceType": "instance",
                    "Tags": [
                        {"Key": "Name", "Value": instance_name}
                    ]
                }
            ]
        }

def get_ec2_user_input() -> Dict[str, str]:
    """Collects basic user input for EC2 deployment"""
    print("\nAWS EC2 Configuration")
    print("Please provide the following details:\n")
    
    return {
        "instance_name": input("Instance Name: "),
        "instance_type": input("Instance Type [t2.micro]: ") or "t2.micro",
        "ami_id": input("AMI ID [ami-0150ccaf51ab55a51]: ") or "ami-0150ccaf51ab55a51"
    }

if __name__ == "__main__":
    # Example standalone usage
    user_input = get_ec2_user_input()
    params = EC2ParameterGenerator.generate_ec2_parameters(**user_input)
    
    print("\nGenerated Deployment Parameters:")
    print(json.dumps(params, indent=2))