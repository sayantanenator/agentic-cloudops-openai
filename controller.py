# controller.py
import os
import json
from dotenv import load_dotenv
from openai import AzureOpenAI
from azure.azure_deployment_agent import VMDeploymentAgent
from azure.parameter_generator import AzureParameterGenerator
from azure.webapp_parameter_generator import WebAppParameterGenerator
from azure.webapp_deployment_agent import WebAppDeploymentAgent
from aws.ec2_deployment_agent import EC2DeploymentAgent
from aws.ec2_parameter_generator import EC2ParameterGenerator

# Load environment variables
load_dotenv()

class DeploymentController:
    def __init__(self):
        # Initialize Azure OpenAI client
        self.llm_client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version="2023-05-15",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
        
        # Initialize deployment agents
        self.azure_vm_agent = VMDeploymentAgent()
        self.azure_webapp_agent = WebAppDeploymentAgent()
        self.aws_ec2_agent = EC2DeploymentAgent()
    
    def get_user_request(self):
        """Get deployment request from user"""
        print("\nWelcome to Cloud Deployment Orchestrator")
        print("Please describe your deployment needs (e.g., 'I need a VM with 4 cores and 16GB RAM')")
        return input("Your request: ")
    
    def determine_deployment_plan(self, user_request):
        """Use LLM to determine target cloud and deployment type"""
        system_prompt = """You are a cloud deployment routing assistant. Analyze the user request and determine:
                            1. Target cloud platform (Azure|AWS|GCP)
                            2. Deployment type (vm|webapp|ec2)

                            Rules:
                            - Choose 'AWS' if request mentions AWS, EC2, or specific AWS services
                            - Choose 'Azure' for Azure-specific requests or when unspecified
                            - For AWS compute requests, choose 'ec2'
                            - For Azure compute requests, choose 'vm'
                            - For web applications, choose 'webapp' (Azure) or the appropriate AWS service
                            - Provide estimate resource cost per month for this deployment.

                            Return JSON with this structure:
                            {
                                "cloud_platform": "Azure|AWS|GCP",
                                "deployment_type": "vm|webapp|ec2"
                                "estimated_cost":  "per-month"
                            }                          
                            
                            """
        
        response = self.llm_client.chat.completions.create(
            model=self.deployment_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_request}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError as e:
            print(f"Error parsing LLM response: {e}")
            return None
    
    def collect_azure_vm_parameters(self):
        """Collect Azure VM parameters from user"""
        print("\nAzure VM Configuration")
        print("Please provide the following details:")
        
        return {
            "resource_group_name": input("Resource Group Name: "),
            "location": input("Location (e.g., eastus): "),
            "vm_name": input("VM Name: "),
            "admin_username": input("Admin Username: "),
            "admin_password": input("Admin Password: ")
        }
    
    def collect_azure_webapp_parameters(self):
        """Collect Azure WebApp parameters from user"""
        print("\nAzure WebApp Configuration")
        print("Please provide the following details:")
        
        return {
            "resource_group_name": input("Resource Group Name: "),
            "app_name": input("WebApp Name: "),
            "location": input("Location (e.g., eastus): "),
            "runtime": input("Runtime stack [python:3.9, node:16-lts, etc.]: ") or "python:3.9",
            "sku": input("Pricing tier [F1 (free), B1, etc.]: ") or "F1"
        }
    
    def collect_ec2_parameters(self):
        """Collect EC2 parameters from user"""
        print("\nAWS EC2 Configuration")
        print("Please provide the following details:")
        
        return {
            "instance_name": input("Instance Name: "),
            "instance_type": input("Instance Type [t2.micro]: ") or "t2.micro",
            "ami_id": input("AMI ID [ami-0b11fdf21b051501b]: ") or "ami-0b11fdf21b051501b",
            "key_pair_name": input("Key Pair Name (optional): ") or None
        }
    
    
    def execute_deployment(self, deployment_plan):
        """Route to the appropriate deployment workflow"""
        if not deployment_plan:
            return {"status": "error", "message": "Invalid deployment plan"}
            
        cloud_platform = deployment_plan["cloud_platform"].lower()
        deployment_type = deployment_plan["deployment_type"].lower()
        
        if cloud_platform == "azure":
            if deployment_type == "vm":
                # Capture print output for Azure VM deployment
                import io
                import sys
                
                # Redirect stdout to capture print statements
                old_stdout = sys.stdout
                sys.stdout = buffer = io.StringIO()
                
                try:
                    print("\nStarting Azure VM deployment workflow...")
                    user_params = deployment_plan["parameters"]
                    deployment_params = AzureParameterGenerator.generate_vm_parameters(**user_params)
                    result = self.azure_vm_agent.deploy_from_parameters(deployment_params)
                    
                    # Get captured output
                    output = buffer.getvalue()
                    result["logs"] = output.split('\n')
                    
                    return result
                finally:
                    # Restore stdout
                    sys.stdout = old_stdout
                    
            elif deployment_type == "webapp":
                print("\nStarting Azure WebApp deployment workflow...")
                user_params = deployment_plan["parameters"]
                deployment_params = WebAppParameterGenerator.generate_webapp_parameters(**user_params)
                return self.azure_webapp_agent.deploy_webapp(deployment_params)
            else:
                return {"status": "error", "message": "Unsupported Azure deployment type"}
        
        # elif cloud_platform == "aws":
        #     if deployment_type == "ec2":
        #         print("\nStarting AWS EC2 deployment workflow...")
        #         user_params = deployment_plan["parameters"]
        #         deployment_params = EC2ParameterGenerator.generate_ec2_parameters(**user_params)
        #         return self.aws_ec2_agent.deploy_ec2_instance(deployment_params)
        #     else:
        #         return {"status": "error", "message": "Unsupported AWS deployment type"}
        
        elif cloud_platform == "aws":
             if deployment_type == "ec2":
                 print("\nStarting AWS EC2 deployment workflow...")
                 user_params = self.collect_ec2_parameters()
                 deployment_params = EC2ParameterGenerator.generate_ec2_parameters(**user_params)
                 return self.aws_ec2_agent.deploy_ec2_instance(deployment_params)
             else:
                 return {"status": "error", "message": "Unsupported AWS deployment type"}
        
    #     else:
    #         return {"status": "error", "message": "Unknown cloud platform"}
        
        else:
            return {"status": "error", "message": "Unknown cloud platform"}
        
    def run(self):
        """Main orchestration workflow"""
        try:
            # Step 1: Get user request
            user_request = self.get_user_request()
            
            # Step 2: Determine deployment plan
            print("\nAnalyzing request with Azure OpenAI...")
            deployment_plan = self.determine_deployment_plan(user_request)
            
            if not deployment_plan:
                return {"status": "error", "message": "Failed to analyze request"}
            
            print(f"\nDeployment plan:\n{json.dumps(deployment_plan, indent=2)}")
            
            # Step 3: Execute deployment
            result = self.execute_deployment(deployment_plan)
            
            # Step 4: Return results
            print("\nDeployment completed!")
            return {
                "status": "success",
                "deployment_plan": deployment_plan,
                "execution_result": result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

if __name__ == "__main__":
    # Required environment variables:
    # AZURE_OPENAI_ENDPOINT
    # AZURE_OPENAI_KEY
    # AZURE_OPENAI_DEPLOYMENT_NAME
    # AWS_ACCESS_KEY_ID (for EC2)
    # AWS_SECRET_ACCESS_KEY (for EC2)
    
    controller = DeploymentController()
    result = controller.run()
    print("\nFinal result:", json.dumps(result, indent=2))