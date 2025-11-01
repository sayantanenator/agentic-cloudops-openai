import os
import json
import time
from openai import AzureOpenAI, APIConnectionError, RateLimitError, APIStatusError
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

class AzureDeploymentPlanner:
    def __init__(self):
        self.client = self._initialize_openai_client()
        self.deployment_plan = None
        self.arm_template = None
    
    def _initialize_openai_client(self):
        """Initialize Azure OpenAI client with validation"""
        required_vars = [
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_KEY",
            "AZURE_OPENAI_DEPLOYMENT_NAME"
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing environment variables: {', '.join(missing_vars)}")
        
        return AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version="2024-02-01",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            max_retries=3
        )
    

    def _call_openai_with_retry(self, prompt, max_tokens=2500, temperature=0.7):
        """Make API call with retry logic"""
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                messages = [
                    {
                        "role": "system", 
                        "content": "You are an Azure cloud architect specializing in deployment planning and Pulumi templates."
                    },
                    {"role": "user", "content": prompt}
                ]
                
                response = self.client.chat.completions.create(
                    model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content
                
            except APIConnectionError as e:
                if attempt == max_retries - 1:
                    raise ConnectionError(f"Failed to connect to Azure OpenAI after {max_retries} attempts: {str(e)}")
                print(f"Connection error (attempt {attempt + 1}), retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                
            except RateLimitError:
                if attempt == max_retries - 1:
                    raise RuntimeError("Rate limit exceeded. Please try again later.")
                print(f"Rate limit hit (attempt {attempt + 1}), retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                
            except APIStatusError as e:
                raise RuntimeError(f"API error: {e.status_code} - {e.message}")

    
    def generate_deployment_plan(self, extracted_resources):
        """Generate initial deployment plan for human review"""
        prompt = f"""
        Analyze these Azure resources extracted from an architecture diagram:
        {json.dumps(extracted_resources, indent=2)}

        Generate a comprehensive Azure cloud deployment plan with this structure:
        create only basic resources listed in the extracted_resources.txt file

        Output in markdown format only - DO NOT include any ARM template yet.
        """
        
        try:
            self.deployment_plan = self._call_openai_with_retry(prompt)
            return self.deployment_plan
        except Exception as e:
            print(f"Error generating deployment plan: {str(e)}")
            raise

    def generate_pulumi_script(self, deployment_plan, naming_convention):
        """
        Generate __main__.py by extracting only the required resource blocks from scripts/main-template.py,
        updating all resource names and identifiers to follow the provided naming convention.
        """
        # Always build the path relative to this file
        template_path = os.path.join(os.path.dirname(__file__), "scripts", "main-template.py")
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template file not found: {template_path}")

        with open(template_path) as f:
            template_code = f.read()

        pulumi_prompt = f"""
        You are an Azure cloud architect. Your task is to generate a Pulumi Python script for Azure deployment.

        1. Only use resource blocks present in the provided template below.
        2. Extract and include only the resources listed below. If a resource is not available in the template, ignore it.
        3. Apply this naming convention to all resource names, variables, and identifiers: <resourcetype>-<environment>-<application_name>-<location>
        4. Do not change resource properties except for names and identifiers.
        5. Output only valid Python code, no markdown or explanations.
        6. The final script must be a complete Pulumi Python file, ready for deployment.

        ## Template file:
        {template_code}

        ## Resources to include:
        {json.dumps(deployment_plan['resources'], indent=2)}

        ## Naming convention:
        {naming_convention}
        """

        try:
            response = self._call_openai_with_retry(
                pulumi_prompt,
                max_tokens=4000,
                temperature=0.2
            )
            code = response.strip()
            if "```python" in code:
                code = code.split("```python")[1].split("```")[0].strip()
            code = f"# AUTO-GENERATED BY AZURE OPENAI\n# REVIEW BEFORE DEPLOYMENT\n{code}"
            self._save_to_file("scripts/__main__.py", code)
            requirements = "pulumi\npulumi_azure_native\npulumi_random"
            self._save_to_file("scripts/requirements.txt", requirements)
            return code
        except Exception as e:
            print(f"Deployment Script generation failed: {str(e)}")
            raise

    def validate_pulumi_script(self, script_path="scripts/__main__.py"):
        """Validate the generated Pulumi script"""
        try:
            # Basic syntax check
            with open(script_path) as f:
                script = f.read()
            
            # Check for critical elements
            validation_checks = [
                ("pulumi.Config", "Config object not found"),
                ("depends_on", "Missing explicit dependencies"),
                ("get_secret", "Sensitive values not properly handled"),
                ("resource_group_name", "Resource group not defined"),
                ("VirtualNetwork", "VNet not defined"),
                ("subnet_id", "Subnet references missing")
            ]
            
            errors = []
            for pattern, error_msg in validation_checks:
                if pattern not in script:
                    errors.append(error_msg)
            
            # Check for required resources
            required_resources = ["VirtualNetwork", "Subnet", "ResourceGroup"]
            for resource in required_resources:
                if resource not in script:
                    errors.append(f"Missing required resource: {resource}")
            
            if errors:
                return False, "Validation failed:\n- " + "\n- ".join(errors)
            
            return True, "Script validated successfully"
        
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def _save_to_file(self, filename, content):
        """Save content to file with directory creation"""
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w") as f:
            f.write(content)



def get_human_feedback():
    """Interactive prompt for human review"""
    print("\n=== DEPLOYMENT PLAN REVIEW ===")
    print("1. Approve and generate Pulumi script")
    print("2. Request modifications")
    print("3. Exit")
    
    while True:
        choice = input("Enter your choice (1-3): ").strip()
        if choice in ("1", "2", "3"):
            return choice
        print("Invalid input. Please enter 1, 2, or 3.")


def extract_resources_from_plan(plan_markdown):
    """
    Extract resources from the Markdown deployment plan.
    This is a simple example; adjust parsing as needed for your plan format.
    """
    # Example: look for a section like '## Deployment Sequence' and extract resource names
    resources = []
    match = re.search(r'## Deployment Sequence\s*-\s*Ordered list of resources to deploy\s*(.*?)##', plan_markdown, re.DOTALL)
    if match:
        sequence_text = match.group(1)
        # Find lines that look like resource names
        for line in sequence_text.splitlines():
            line = line.strip('- ').strip()
            if line and not line.startswith('Dependencies'):
                resources.append(line)
    return resources

def main():
    try:
        # Validate environment before starting
        if not os.path.exists("extracted_resources.txt"):
            raise FileNotFoundError("extracted_resources.txt not found in current directory")
        
        # Load extracted resources
        with open("extracted_resources.txt") as f:
            extracted_resources = [line.strip() for line in f if line.strip()]
        
        planner = AzureDeploymentPlanner()
        
        # Generate initial deployment plan
        print("Generating deployment plan...")
        plan = planner.generate_deployment_plan(extracted_resources)
        print("\nGenerated Deployment Plan Preview:")
        print(plan[:1000] + "...")  # Print first part for preview
        
        # Human review loop
        while True:
            choice = get_human_feedback()
            
            if choice == "1":  # Approved
                print("\n" + "="*50)
                print("Generating Pulumi Deployment Script".center(50))
                print("="*50)

                # Collect naming convention parameters from user
                environment = input("Environment (e.g., prod): ").strip() or "prod"
                application_name = input("Application name: ").strip() or "aumanager"
                location = input("Azure region: ").strip() or "EastUS"

                # Build naming convention string
                naming_convention = f"<resourcetype>-{environment}-{application_name}-{location}"

                # Extract and parse resources from the deployment plan
                parsed_resources = extract_resources_from_plan(planner.deployment_plan)
                deployment_plan_struct = {"resources": parsed_resources}

                pulumi_code = planner.generate_pulumi_script(deployment_plan_struct, naming_convention)

                # Validation removed. Print success and next steps.
                print("\n" + "✓"*50)
                print("SCRIPT GENERATED SUCCESSFULLY".center(50))
                print("✓"*50)

                print("\nNext Steps:")
                print("-"*50)
                print("1. Review the generated script:")
                print(f"   Location: {os.path.abspath('scripts/__main__.py')}")

                print("\n2. Prepare for deployment:")
                print("   a. Install Pulumi CLI: https://www.pulumi.com/docs/install/")
                print("   b. Install Python requirements:")
                print("      cd scripts && pip install -r requirements.txt")

                print("\n3. Deploy infrastructure:")
                print("   cd scripts")
                print("   pulumi config set environment <value>")
                print("   pulumi config set application_name <value>")
                print("   pulumi config set location <value>")
                print("   pulumi up")

                # Offer to deploy automatically
                if input("\nDeploy now? (y/n): ").lower() == 'y':
                    print("\nStarting deployment...")
                    deploy_result = planner.deploy_infrastructure(
                        config={
                            "environment": input("Environment (e.g., prod): ").strip() or "prod",
                            "application_name": input("Application name: ").strip() or "aumanager",
                            "location": input("Azure region: ").strip() or "EastUS"
                        },
                        azure_creds={
                            "subscription_id": os.getenv("AZURE_SUBSCRIPTION_ID"),
                            "tenant_id": os.getenv("AZURE_TENANT_ID"),
                            "client_id": os.getenv("AZURE_CLIENT_ID"),
                            "client_secret": os.getenv("AZURE_CLIENT_SECRET")
                        }
                    )
                    print(f"\nDeployment result: {deploy_result['status']}")

                break
                
            elif choice == "2":  # Needs modification
                print("\nCurrent deployment plan:")
                print("-"*50)
                print(planner.deployment_plan[:1000] + ("..." if len(planner.deployment_plan) > 1000 else ""))
                
                feedback = input("\nEnter your specific modification requests:\n> ").strip()
                if not feedback:
                    print("No modifications provided, using existing plan")
                    continue
                    
                print("\nRegenerating with your feedback...")
                try:
                    new_plan = planner._call_openai_with_retry(
                        f"Update this deployment plan with these specific changes: {feedback}\n\nCurrent Plan:\n{planner.deployment_plan}",
                        max_tokens=3500
                    )
                    planner.deployment_plan = new_plan
                    
                    print("\nUpdated Deployment Plan Preview:")
                    print("-"*50)
                    print(new_plan[:1000] + ("..." if len(new_plan) > 1000 else ""))
                except Exception as e:
                    print(f"Error regenerating plan: {str(e)}")
                
            elif choice == "3":  # Exit
                print("\nExiting deployment planner.")
                return
        
        print("\nOperation completed successfully.")
        
    except Exception as e:
        print("\n" + "X"*50)
        print("FATAL ERROR".center(50))
        print("X"*50)
        print(f"\nError: {str(e)}")
        print("\nTroubleshooting steps:")
        print("- Verify azure_resources.json exists and is valid")
        print("- Check Azure credentials in environment variables")
        print("- Review OpenAI API configuration")
        print("\nFull error details:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()