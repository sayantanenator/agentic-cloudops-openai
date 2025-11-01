import os
import sys
import subprocess
import logging
from pathlib import Path
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_venv_python_path(venv_path):
    """Get the correct path to virtual environment Python"""
    if sys.platform == "win32":
        return os.path.join(venv_path, "Scripts", "python.exe")
    else:
        return os.path.join(venv_path, "bin", "python")

def get_pulumi_path():
    """Find Pulumi executable path"""
    if pulumi_path := shutil.which("pulumi"):
        return pulumi_path
    
    paths = [
        Path.home() / ".pulumi/bin/pulumi",
        Path("/usr/local/bin/pulumi"),
        Path("C:/Program Files/Pulumi/bin/pulumi.exe"),
        Path("C:/Users/sayan/.pulumi/bin/pulumi.exe")
    ]
    
    for path in paths:
        if path.exists():
            return str(path)
    
    raise FileNotFoundError("Pulumi CLI not found")

def verify_package_installation(venv_path, package_name):
    """Verify a package is properly installed in the virtual environment"""
    python_path = get_venv_python_path(venv_path)
    check_cmd = [python_path, "-c", f"import {package_name}; print('{package_name} version:', {package_name}.__version__)"]
    
    try:
        result = subprocess.run(
            check_cmd,
            capture_output=True,
            text=True
        )
        logger.info(result.stdout.strip())
        return True
    except subprocess.CalledProcessError:
        return False


def deploy_infrastructure(pulumi_dir, config, azure_creds=None):
    """Ultimate deployment solution with complete verification"""
    try:
        pulumi_path = get_pulumi_path()
        logger.info(f"Using Pulumi at: {pulumi_path}")
        
        root_dir = os.path.dirname(os.path.abspath(pulumi_dir))
        scripts_dir = os.path.abspath(pulumi_dir)
        venv_path = os.path.join(root_dir, "venv")
        stack_name = f"{config['environment']}-{config['application_name']}"

        logger.info("Creating fresh virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)

        python_path = get_venv_python_path(venv_path)
        pip_path = os.path.join(venv_path, "Scripts", "pip.exe")

        packages = [
            "pulumi>=3.0.0",
            "pulumi-azure-native>=2.0.0",
            "pulumi-random>=4.18.0"
        ]

        logger.info("Installing required packages...")
        for package in packages:
            subprocess.run([python_path, "-m", "pip", "install", package], check=True)
            package_import_name = package.split(">")[0].replace("-", "_")
            if not verify_package_installation(venv_path, package_import_name):
                raise RuntimeError(f"Failed to verify installation of {package}")

        env = os.environ.copy()
        env.update({
            "PULUMI_SKIP_UPDATE_CHECK": "true",
            "PULUMI_CONFIG_PASSPHRASE": "dev-passphrase",
            "PATH": f"{os.path.join(venv_path, 'Scripts')};{os.environ.get('PATH', '')}",
            "VIRTUAL_ENV": venv_path
        })

        if azure_creds:
            env.update({
                "AZURE_SUBSCRIPTION_ID": azure_creds.get("subscription_id", ""),
                "AZURE_TENANT_ID": azure_creds.get("tenant_id", ""),
                "AZURE_CLIENT_ID": azure_creds.get("client_id", ""),
                "AZURE_CLIENT_SECRET": azure_creds.get("client_secret", "")
            })

        stack_exists = subprocess.run(
            [pulumi_path, "stack", "ls"],
            cwd=scripts_dir,
            env=env,
            capture_output=True,
            text=True
        ).stdout.find(stack_name) != -1

        if stack_exists:
            logger.info(f"Selecting existing stack: {stack_name}")
            subprocess.run(
                [pulumi_path, "stack", "select", stack_name],
                cwd=scripts_dir,
                env=env,
                check=True
            )
        else:
            logger.info(f"Creating new stack: {stack_name}")
            subprocess.run(
                [pulumi_path, "stack", "init", stack_name],
                cwd=scripts_dir,
                env=env,
                check=True
            )

        # 🛠️ New line added to fix config variable error
        # 🔧 Set required Pulumi stack config variables
        subprocess.run(
            [pulumi_path, "config", "set", "infra-architecture:environment", config["environment"]],
            cwd=scripts_dir,
            env=env,
            check=True
        )
        subprocess.run(
            [pulumi_path, "config", "set", "infra-architecture:application_name", config["application_name"]],
            cwd=scripts_dir,
            env=env,
            check=True
        )
        subprocess.run(
            [pulumi_path, "config", "set", "azure-native:location", config["location"]],
            cwd=scripts_dir,
            env=env,
            check=True
        )

        plugins = [
            ("azure-native", "v2.0.0"),
            ("random", "4.18.0")
        ]
        
        for plugin, version in plugins:
            logger.info(f"Installing {plugin} plugin...")
            subprocess.run(
                [pulumi_path, "plugin", "install", "resource", plugin, version, "--non-interactive"],
                cwd=scripts_dir,
                env=env,
                check=True
            )

        pulumi_cmd = [
            pulumi_path,
            "up", "--yes", "--skip-preview",
            "--stack", stack_name,
            "--exec-agent", python_path
        ]
        
        logger.info("Running Pulumi deployment...")
        result = subprocess.run(
            pulumi_cmd,
            cwd=scripts_dir,
            env=env,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode, pulumi_cmd,
                result.stdout, result.stderr
            )

        logger.info(result.stdout)
        return {"status": "success"}
    
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr or e.stdout
        logger.error(f"Command failed:\n{error_msg}")
        
        error_log = os.path.join(root_dir, "deployment_error.log")
        with open(error_log, "w") as f:
            f.write(f"Failed command: {e.cmd}\n")
            f.write(f"Error output:\n{error_msg}\n")
        
        return {
            "status": "error",
            "message": f"Deployment failed at step: {e.cmd[1]}",
            "details": error_msg,
            "log_file": error_log
        }
    
    except Exception as e:
        logger.error(f"Deployment failed: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": "Unexpected deployment error",
            "details": str(e)
        }