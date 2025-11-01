import os
import json
from architecture.image_analysis_agent import image_extraction_agent, save_text_to_json
from architecture.plan_generation_agent import AzureDeploymentPlanner, extract_resources_from_plan
from architecture.resource_manager_agent import extract_azure_resources

def get_human_feedback():
    print("\n=== DEPLOYMENT PLAN REVIEW ===")
    print("1. Approve and generate Pulumi script")
    print("2. Request modifications")
    print("3. Exit")
    while True:
        choice = input("Enter your choice (1-3): ").strip()
        if choice in ("1", "2", "3"):
            return choice
        print("Invalid input. Please enter 1, 2, or 3.")

def main():
    try:
        # Step 1: OCR and resource extraction
        image_path = "protect-apis.png"
        print("Extracting text from architecture diagram...")
        extracted_text = image_extraction_agent(image_path)
        save_text_to_json(extracted_text, "azure_resources.json")

        print("\nExtracting Azure resources from OCR output...")
        extract_azure_resources("azure_resources.json", "extracted_resources.txt")

        # Validate environment before starting
        if not os.path.exists("extracted_resources.txt"):
            raise FileNotFoundError("extracted_resources.txt not found in current directory")

        # Load extracted resources
        with open("extracted_resources.txt") as f:
            extracted_resources = f.read().splitlines()

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
                parsed_resources = extract_resources_from_plan(plan)
                deployment_plan_struct = {"resources": parsed_resources}

                # Only call the agent to generate the script
                planner.generate_pulumi_script(deployment_plan_struct, naming_convention)

                print("\n" + "✓"*50)
                print("SCRIPT GENERATED SUCCESSFULLY".center(50))
                print("✓"*50)

                print("\nNext Steps:")
                print("-"*50)
                print("1. Review the generated script:")
                print(f"   Location: {os.path.abspath('/architecture/scripts/__main__.py')}")

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

                break

            elif choice == "2":  # Needs modification
                print("\nCurrent deployment plan:")
                print("-"*50)
                print(plan[:1000] + ("..." if len(plan) > 1000 else ""))

                feedback = input("\nEnter your specific modification requests:\n> ").strip()
                if not feedback:
                    print("No modifications provided, using existing plan")
                    continue

                print("\nRegenerating with your feedback...")
                try:
                    new_plan = planner._call_openai_with_retry(
                        f"Update this deployment plan with these specific changes: {feedback}\n\nCurrent Plan:\n{plan}",
                        max_tokens=3500
                    )
                    plan = new_plan

                    print("\nUpdated Deployment Plan Preview:")
                    print("-"*50)
                    print(new_plan[:1000] + ("..." if len(new_plan) > 1000 else ""))
                except Exception as e:
                    print(f"Error regenerating plan: {str(e)}")
                    continue

            elif choice == "3":  # Exit
                print("Exiting the process.")
                break

    except FileNotFoundError as e:
        print(f"File error: {str(e)}")
    except json.JSONDecodeError:
        print("Invalid JSON data format")
    except Exception as e:
        print(f"Processing error: {str(e)}")

# Use this to always get the correct path, regardless of where you run the script:
template_path = os.path.join(os.path.dirname(__file__), "architecture", "scripts", "main-template.py")
if not os.path.exists(template_path):
    raise FileNotFoundError(f"Template file not found: {template_path}")

with open(template_path) as f:
    template_code = f.read()

if __name__ == "__main__":
    main()