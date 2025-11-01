# ec2_deployment_agent.py
import os
import json
import boto3
from botocore.exceptions import ClientError, ParamValidationError
from dotenv import load_dotenv

load_dotenv()

class EC2DeploymentAgent:
    def __init__(self):
        self.client = boto3.client('ec2',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        )
    
    def _get_tag_specifications(self, instance_name):
        """Generate tag specifications for EC2 instance"""
        return [{
            'ResourceType': 'instance',
            'Tags': [{
                'Key': 'Name',
                'Value': instance_name
            }]
        }]
    
    def deploy_ec2_instance(self, params):
        """Deploys an EC2 instance"""
        try:
            print(f"\nDeploying EC2 instance: {params['instance_name']}")
            
            # Validate required parameters
            if 'instance_name' not in params:
                raise ValueError("instance_name is required")
                
            # Set default values
            params.setdefault('instance_type', 't2.micro')
            params.setdefault('ami_id', 'ami-0c55b159cbfafe1f0')  # Ubuntu 20.04 LTS
            params.setdefault('security_group_ids', ['default'])
            
            # Prepare the run_instances parameters
            run_params = {
                'ImageId': params['ami_id'],
                'InstanceType': params['instance_type'],
                'MinCount': 1,
                'MaxCount': 1,
                'SecurityGroupIds': params['security_group_ids'],
                'TagSpecifications': self._get_tag_specifications(params['instance_name'])
            }
            
            # Only add KeyName if provided and not empty
            if params.get('key_pair_name'):
                run_params['KeyName'] = params['key_pair_name']
            
            response = self.client.run_instances(**run_params)
            
            instance_id = response['Instances'][0]['InstanceId']
            
            # Wait for instance to be running
            print(f"Waiting for instance {instance_id} to start...")
            waiter = self.client.get_waiter('instance_running')
            waiter.wait(InstanceIds=[instance_id])
            
            # Get instance details
            instance = self.client.describe_instances(
                InstanceIds=[instance_id]
            )['Reservations'][0]['Instances'][0]
            
            return {
                "status": "success",
                "resources": {
                    "instance_id": instance_id,
                    "instance_name": params['instance_name'],
                    "public_ip": instance.get('PublicIpAddress', 'N/A'),
                    "public_dns": instance.get('PublicDnsName', 'N/A'),
                    "state": instance['State']['Name'],
                    "message": "EC2 instance deployed successfully"
                }
            }
            
        except ParamValidationError as e:
            return {
                "status": "error",
                "message": "Invalid parameters provided",
                "details": str(e),
                "suggestion": "Check your input parameters and try again"
            }
        except ClientError as e:
            return {
                "status": "error",
                "message": "AWS API error",
                "details": e.response['Error']['Message'],
                "aws_error_code": e.response['Error']['Code']
            }
        except Exception as e:
            return {
                "status": "error",
                "message": "Unexpected error",
                "details": str(e)
            }

def test_deployment():
    """Test the deployment agent with sample parameters"""
    test_params = {
        "instance_name": "test-instance",
        "instance_type": "t2.micro",
        "ami_id": "ami-0150ccaf51ab55a51",
        "security_group_ids": ["default"]
    }
    
    print("Starting EC2 test deployment...")
    agent = EC2DeploymentAgent()
    result = agent.deploy_ec2_instance(test_params)
    print("\nDeployment result:", json.dumps(result, indent=2))

if __name__ == "__main__":
    test_deployment()

