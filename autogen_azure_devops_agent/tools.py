import os
import subprocess
import requests
from base64 import b64encode
from typing import List, Optional
import git

REPO_PATH = "./autogen_azure_devops_agent/repositorio"

AZDO_ORG = os.environ.get("AZDO_ORG")
AZDO_PROJECT = os.environ.get("AZDO_PROJECT")
AZDO_REPO = os.environ.get("AZDO_REPO")
AZDO_PAT = os.environ.get("AZDO_PAT")

AZDO_URL = f"https://dev.azure.com/{AZDO_ORG}/{AZDO_PROJECT}/_apis"

def get_azdo_headers() -> dict:
    """Get headers for Azure DevOps API calls."""
    pat = os.getenv("AZDO_PAT")
    auth = b64encode(f":{pat}".encode()).decode()
    print("******************************************")
    print("Using get_azdo_headers")
    return {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json"
    }

def list_files(path: str = "") -> List[str]:
    """List files in a directory relative to the repository root."""
    full_path = os.path.join(REPO_PATH, path)
    print("******************************************")
    print("Using list_files")
    return os.listdir(full_path)

def read_file(filepath: str) -> str:
    """Read content from a file within the repository."""
    full_path = os.path.join(REPO_PATH, filepath)
    print("******************************************")
    print("Using read_file")
    with open(full_path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(filepath: str, content: str) -> str:
    """Write content to a file within the repository."""
    full_path = os.path.join(REPO_PATH, filepath)
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("******************************************")
    print("Using write_file")
    return f"Archivo escrito: {filepath}"

def clone_repo(branch: str = "main") -> str:
    """Clone the Azure DevOps repository into local path."""
    repo_url = f"https://{AZDO_ORG}@dev.azure.com/{AZDO_ORG}/{AZDO_PROJECT}/_git/{AZDO_REPO}"
    subprocess.run(["git", "clone", "-b", branch, repo_url, REPO_PATH], check=True)
    print("******************************************")
    print("Using clone_repo")
    return "Repo clonado."

def create_branch(branch: str = "fix/bug-123") -> str:
    """Create a new local git branch."""
    os.chdir(REPO_PATH)
    subprocess.run(["git", "checkout", "-b", branch], check=True)
    os.chdir("../..")
    print("******************************************")
    print("Using create_branch")
    return f"Rama {branch} creada."

def commit_and_push(branch: str = "fix/bug-123", message: str = "Fix for bug") -> str:
    """Commit and push changes to remote branch."""
    os.chdir(REPO_PATH)
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", message], check=True)
    subprocess.run(["git", "push", "--set-upstream", "origin", branch], check=True)
    os.chdir("../..")
    print("******************************************")
    print("Using commit_and_push")
    return "Cambios commiteados y enviados."

def create_pull_request(title: str = "Fix bug", description: str = "Automated fix", branch: str = "fix/bug-123", target_branch: str = "main") -> str:
    """Create a pull request in Azure DevOps."""
    url = f"{AZDO_URL}/git/repositories/{AZDO_REPO}/pullrequests?api-version=7.0"
    payload = {
        "sourceRefName": f"refs/heads/{branch}",
        "targetRefName": f"refs/heads/{target_branch}",
        "title": title,
        "description": description
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {b64encode(f':{AZDO_PAT}'.encode()).decode()}"
    }
    res = requests.post(url, headers=headers, json=payload)
    res.raise_for_status()
    print("******************************************")
    print("Using create_pull_request")
    return f"PR creada: {res.json()['url']}"

def verify_repo_access() -> bool:
    """Verify access to the Azure DevOps repository."""
    pat = os.getenv("AZDO_PAT")
    org = os.getenv("AZDO_ORG").rstrip('/')
    project = os.getenv("AZDO_PROJECT")
    repo = os.getenv("AZDO_REPO")

    authorization = b64encode(f":{pat}".encode()).decode()
    url = f"{org}/{project}/_apis/git/repositories/{repo}?api-version=7.0"

    headers = {
        "Authorization": f"Basic {authorization}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            print(f"\nAcceso verificado al repositorio: {repo}")
            return True
        else:
            print(f"\nError accediendo al repositorio: {response.status_code}")
            print(response.json())
            return False
    except Exception as e:
        print(f"\nError de conexión: {e}")
        return False

def search_code(query: str) -> List[dict]:
    """Search C# code files in Azure DevOps repository that contain the query."""
    org = os.getenv("AZDO_ORG").rstrip('/')
    project = os.getenv("AZDO_PROJECT")
    repo = os.getenv("AZDO_REPO")
    
    url = f"{org}/{project}/_apis/git/repositories/{repo}/items?api-version=6.0&searchCriteria.itemPath=/"
    matches = []

    try:
        response = requests.get(url, headers=get_azdo_headers())
        if response.status_code == 200:
            items = response.json().get("value", [])
            for item in items:
                if ".cs" in item["path"].lower():
                    file_url = f"{org}/{project}/_apis/git/repositories/{repo}/items?path={item['path']}&api-version=6.0"
                    content_response = requests.get(file_url, headers=get_azdo_headers())
                    if content_response.status_code == 200 and query.lower() in content_response.text.lower():
                        matches.append({
                            "path": item["path"],
                            "url": item["url"]
                        })
            return matches
        return [{"error": f"Error searching code: {response.status_code}"}]
    except Exception as e:
        return [{"error": str(e)}]
