import streamlit as st
from PIL import Image
import json
import time
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from controller import DeploymentController

# Initialize session state
if "params" not in st.session_state:
    st.session_state.params = {}
if "plan" not in st.session_state:
    st.session_state.plan = {}
if "params_collected" not in st.session_state:
    st.session_state.params_collected = False
if "deployment_result" not in st.session_state:
    st.session_state.deployment_result = None

# Configure page
st.set_page_config(
    page_title="CloudDeploy AI Agent",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stTextInput input {
        border-radius: 10px !important;
        padding: 10px !important;
    }
    .stButton button {
        background-color: #4CAF50;
        color: white;
        border-radius: 10px;
        padding: 10px 24px;
        font-weight: bold;
    }
    .stButton button:hover {
        background-color: #45a049;
    }
    .deployment-card {
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
    }
    .success-card {
        background-color: #e8f5e9;
        border-left: 5px solid #4CAF50;
    }
    .error-card {
        background-color: #ffebee;
        border-left: 5px solid #f44336;
    }
</style>
""", unsafe_allow_html=True)

# App Header
col1, col2 = st.columns([1, 4])
with col1:
    st.image(Image.open("asset/kpmg.png"), width=80)
with col2:
    st.title("CloudDeploy AI Agent")
    st.caption("Autonomous multi-cloud infrastructure deployment powered by AI")

# Sidebar
with st.sidebar:
    st.header("Configuration")
    cloud_provider = st.radio("Preferred Cloud", ["Auto-Select", "AWS", "Azure"], index=0)
    enable_cost_estimate = st.checkbox("Show Cost Estimates", True)
    st.divider()
    st.markdown("**Agent Settings**")
    agent_verbosity = st.slider("Agent Verbosity", 1, 3, 2)
    st.divider()
    st.markdown("Built with ❤️ by Sayantan")

# Main Interface
tab1, tab2, tab3 = st.tabs(["Deploy", "History", "Analytics"])

# ... (previous imports and setup code)

with tab1:
    st.subheader("New Deployment Request")
    
    # Request input
    user_request = st.text_area(
        "Describe your deployment needs:",
        placeholder="e.g. 'I need a secure VM with 4 CPUs and 16GB RAM running Ubuntu'",
        height=100,
        key="user_request"
    )

    if st.button("Generate Deployment Plan", use_container_width=True):
        if not user_request:
            st.warning("Please enter a deployment request")
        else:
            with st.spinner("Analyzing request with AI..."):
                controller = DeploymentController()
                plan = controller.determine_deployment_plan(user_request)
                st.session_state.plan = plan
                # Clear previous deployment state
                keys_to_clear = ['params', 'params_collected', 'deployment_result', 'deployment_logs']
                for key in keys_to_clear:
                    if key in st.session_state:
                        del st.session_state[key]
                
                # Display the AI thought process
                with st.expander("🧠 AI Thought Process", expanded=True):
                    st.write("**Determining optimal deployment strategy...**")
                    st.json(plan)
                    
                    # Visualization
                    if plan["cloud_platform"] == "Azure":
                        st.image("asset/azure_arch.png", caption="Recommended Azure Architecture")
                    else:
                        st.image("asset/aws_arch.png", caption="Recommended AWS Architecture")
                
                st.rerun()

# Parameter Collection
if st.session_state.get('plan') and not st.session_state.get('params_collected'):
    st.subheader("🧩 Deployment Parameters")
    deployment_type = st.session_state.plan["deployment_type"].lower()
    
    if deployment_type == "ec2":
        with st.form("ec2_params"):
            cols = st.columns(2)
            instance_name = cols[0].text_input("Instance Name", "my-ec2-instance")
            instance_type = cols[1].selectbox("Instance Type", ["t2.micro", "t3.medium", "m5.large"], index=0)
            
            cols = st.columns(2)
            ami_id = cols[0].text_input("AMI ID", "ami-0c55b159cbfafe1f0")
            key_pair_name = cols[1].text_input("Key Pair (optional)", "")
            
            submitted = st.form_submit_button("Confirm Parameters")
            if submitted:
                st.session_state.params = {
                    "instance_name": instance_name,
                    "instance_type": instance_type,
                    "ami_id": ami_id,
                    "key_pair_name": key_pair_name or None
                }
                st.session_state.params_collected = True
                st.rerun()
    
    elif deployment_type == "vm":
        with st.form("azure_vm_params"):
            cols = st.columns(2)
            resource_group = cols[0].text_input("Resource Group", "my-resource-group")
            location = cols[1].text_input("Location", "eastus")
            
            cols = st.columns(2)
            vm_name = cols[0].text_input("VM Name", "my-vm")
            admin_username = cols[1].text_input("Admin Username", "adminuser")
            
            admin_password = st.text_input("Admin Password", type="password", value="")
            
            submitted = st.form_submit_button("Confirm Parameters")
            if submitted:
                if not admin_password:
                    st.error("Admin password is required for Azure VM deployment")
                else:
                    st.session_state.params = {
                        "resource_group_name": resource_group,
                        "location": location,
                        "vm_name": vm_name,
                        "admin_username": admin_username,
                        "admin_password": admin_password
                    }
                    st.session_state.params_collected = True
                    st.rerun()
    
    elif deployment_type == "webapp":
        with st.form("azure_webapp_params"):
            cols = st.columns(2)
            resource_group = cols[0].text_input("Resource Group", "my-resource-group")
            app_name = cols[1].text_input("WebApp Name", "my-webapp")
            
            cols = st.columns(2)
            location = cols[0].text_input("Location", "eastus")
            runtime = cols[1].text_input("Runtime Stack", "python:3.9")
            
            sku = st.selectbox("Pricing Tier", ["F1 (Free)", "B1", "S1"], index=0)
            
            submitted = st.form_submit_button("Confirm Parameters")
            if submitted:
                st.session_state.params = {
                    "resource_group_name": resource_group,
                    "app_name": app_name,
                    "location": location,
                    "runtime": runtime,
                    "sku": sku.split(" ")[0]  # Extract SKU code
                }
                st.session_state.params_collected = True
                st.rerun()

# Deployment Execution
if st.session_state.get('params_collected') and not st.session_state.get('deployment_result'):
    st.subheader("🚀 Deployment Status")
    
    # Initialize logs in session state
    if 'deployment_logs' not in st.session_state:
        st.session_state.deployment_logs = []
    
    # Create a placeholder for live logs
    log_placeholder = st.empty()
    
    # Function to update logs in UI
    def update_logs(message, status="info"):
        st.session_state.deployment_logs.append({
            "message": message,
            "status": status,
            "timestamp": time.strftime("%H:%M:%S")
        })
        
        # Build log display
        log_content = ""
        for log in st.session_state.deployment_logs:
            icon = "✅" if log["status"] == "success" else "ℹ️" if log["status"] == "info" else "⏳"
            if log["status"] == "error":
                icon = "❌"
            log_content += f"{icon} **{log['timestamp']}** - {log['message']}  \n"
        
        log_placeholder.markdown(log_content)
    
    try:
        # Simulate deployment steps
        update_logs("Initializing deployment workflow...")
        time.sleep(1)
        
        deployment_type = st.session_state.plan["deployment_type"].lower()
        if deployment_type == "vm":
            update_logs("Starting Azure VM deployment workflow...")
        elif deployment_type == "ec2":
            update_logs("Starting AWS EC2 deployment workflow...")
        elif deployment_type == "webapp":
            update_logs("Starting Azure WebApp deployment workflow...")
        
        time.sleep(1)
        
        # Execute actual deployment
        controller = DeploymentController()
        deployment_request = {
            "cloud_platform": st.session_state.plan["cloud_platform"],
            "deployment_type": st.session_state.plan["deployment_type"],
            "parameters": st.session_state.params
        }
        
        # Execute deployment
        result = controller.execute_deployment(deployment_request)
        st.session_state.deployment_result = result
        
        # Process results
        if result.get("status") == "success":
            # Add success logs
            if "resources" in result:
                if "resource_group" in result["resources"]:
                    update_logs(f"Created resource group: {result['resources']['resource_group']}", "success")
                if "vm_name" in result["resources"]:
                    update_logs(f"Created virtual machine: {result['resources']['vm_name']}", "success")
                if "public_ip" in result["resources"]:
                    update_logs(f"Public IP: {result['resources']['public_ip']}", "success")
                if "app_name" in result["resources"]:
                    update_logs(f"Created web application: {result['resources']['app_name']}", "success")
            
            update_logs("Deployment completed successfully!", "success")
            st.balloons()
        else:
            update_logs(f"Deployment failed: {result.get('message', 'Unknown error')}", "error")
        
        # Rerun to show final state
        st.rerun()
                
    except Exception as e:
        update_logs(f"Deployment error: {str(e)}", "error")
        st.session_state.deployment_result = {
            "status": "error",
            "message": str(e)
        }
        st.rerun()

# Display final deployment result
if st.session_state.get('deployment_result'):
    result = st.session_state.deployment_result
    
    if result.get("status") == "success":
        st.success("✅ Deployment Completed Successfully!")
        
        # Show connection details
        if "resources" in result:
            if "public_ip" in result["resources"]:
                st.subheader("Connection Details")
                st.code(f"ssh {st.session_state.params.get('admin_username', 'admin')}@{result['resources']['public_ip']}")
                
            if "app_url" in result["resources"]:
                st.markdown(f"**Application URL:** [{result['resources']['app_url']}]({result['resources']['app_url']})")
    else:
        st.error(f"❌ Deployment Failed: {result.get('message', 'Unknown error')}")

# Reset functionality
if st.session_state.get('deployment_result'):
    if st.button("Start New Deployment", use_container_width=True, key="new_deployment"):
        # Clear all deployment-related state
        keys_to_clear = ['plan', 'params', 'params_collected', 'deployment_result', 'deployment_logs']
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()


with tab2:
    st.subheader("Deployment History")
    deployments = [
        {"id": 1, "name": "prod-web-server", "status": "success", "cloud": "AWS", "type": "EC2", "date": "2023-11-15"},
        {"id": 2, "name": "dev-test-vm", "status": "failed", "cloud": "Azure", "type": "VM", "date": "2023-11-14"}
    ]

    for dep in deployments:
        status_color = "green" if dep["status"] == "success" else "red"
        with st.container():
            cols = st.columns([1, 3, 2, 2, 1])
            cols[0].write(f"`{dep['id']}`")
            cols[1].write(f"**{dep['name']}**")
            cols[2].write(f"{dep['type']} ({dep['cloud']})")
            cols[3].write(f":{status_color}[{dep['status'].upper()}]")
            with cols[4]:
                if st.button("🔍", key=f"view_{dep['id']}"):
                    st.session_state.view_deployment = dep["id"]

with tab3:
    st.subheader("Deployment Analytics")
    
    # Sample metrics
    fig = go.Figure(go.Pie(
        labels=['AWS', 'Azure'],
        values=[65, 35],
        hole=.4,
        marker_colors=['#FF9900', '#0089D6']
    ))
    fig.update_layout(title_text="Cloud Distribution")
    st.plotly_chart(fig, use_container_width=True)
    
    # Cost comparison
    st.bar_chart({
        'AWS EC2': 120,
        'Azure VM': 145,
        'AWS Lambda': 85
    })