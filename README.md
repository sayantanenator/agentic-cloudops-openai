
# Cloud Deployment AI Agent 🚀

![App Screenshot](asset/screenshot.png)

A multi-cloud infrastructure deployment orchestrator powered by AI agents with intelligent routing capabilities.

## Features ✨

- **Intelligent Routing Agent** 🤖
  - Analyzes natural language requests to determine optimal cloud platform (AWS/Azure)
  - Selects appropriate deployment type (VM/WebApp/EC2) based on requirements
  - Uses Azure OpenAI for decision-making with JSON response formatting

- **Multi-Cloud Deployment** ☁️
  - Azure Virtual Machine provisioning
  - Azure WebApp deployments
  - AWS EC2 instance creation
  - Infrastructure provisioning from architecture diagrams

- **Visual Analytics** 📊
  - Cloud resource distribution visualization
  - Cost comparison charts
  - Deployment history tracking

## Prerequisites 📋

- Python 3.8+
- Azure account with OpenAI access
- AWS account (for EC2 deployments)
- Required environment variables (see `.env.example`)

## Installation & Local Development 🛠️

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-repo/cloud-deploy-ai-agent.git
   cd cloud-deploy-ai-agent
Set up virtual environment

bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
Install dependencies

bash
pip install -r requirements.txt
Configure environment variables
Create a .env file based on the example:

ini
AZURE_OPENAI_ENDPOINT=your-azure-openai-endpoint
AZURE_OPENAI_KEY=your-azure-openai-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_SUBSCRIPTION_ID=your-azure-subscription-id
AZURE_CLIENT_ID=your-azure-client-id
AZURE_TENANT_ID=your-azure-tenant-id
AZURE_CLIENT_SECRET=your-azure-client-secret
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
Running the Application 🚀
Start Streamlit app

bash
streamlit run streamlit.py
Access the application
Open your browser to: http://localhost:8501

Deployment Instructions ☁️
Option 1: Azure App Service
bash
az webapp up --runtime PYTHON:3.9 --sku B1 --name your-app-name
Option 2: AWS Elastic Beanstalk
Initialize EB CLI:

bash
eb init -p python-3.8 your-app-name --region your-region
Create environment:

bash
eb create your-env-name
Agent Capabilities Overview 🤖
Intelligent Routing Agent
python
def determine_deployment_plan(user_request):
    """
    Analyzes user request and returns deployment plan
    Sample JSON response:
    {
        "cloud_platform": "Azure|AWS",
        "deployment_type": "vm|webapp|ec2"
    }
    """
    system_prompt = """You are a cloud deployment routing assistant..."""
    # Calls Azure OpenAI to analyze request
Deployment Agents
Agent	Capabilities	Example Usage
Azure VM Agent	Creates virtual machines with custom configs	deploy_from_parameters(vm_params)
Azure WebApp Agent	Deploys web applications with runtime stacks	deploy_webapp(webapp_params)
AWS EC2 Agent	Provisions EC2 instances with AMI selection	deploy_ec2_instance(ec2_params)
Diagram Analyzer	Extracts infrastructure from architecture diagrams	analyze_diagram(image_file)
