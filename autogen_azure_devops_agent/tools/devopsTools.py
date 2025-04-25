import os
import subprocess
import shutil

# Las variables se obtendrán dinámicamente en cada función, no al importar el módulo
def clone_repo(branch: str = "master") -> str:
    """Clone the Azure DevOps repository into local path."""
    # Obtener las variables de entorno en el momento de la ejecución
    AZDO_PAT = os.getenv("AZDO_PAT")
    AZDO_ORG = os.getenv("AZDO_ORG")
    AZDO_PROJECT = os.getenv("AZDO_PROJECT")
    AZDO_REPO = os.getenv("AZDO_REPO")
    REPO_PATH = os.getenv("REPO_PATH", "./repo_clonado")
    
    # Verificar que todas las variables necesarias estén configuradas
    if not all([AZDO_PAT, AZDO_ORG, AZDO_PROJECT, AZDO_REPO]):
        missing_vars = []
        if not AZDO_PAT: missing_vars.append("AZDO_PAT")
        if not AZDO_ORG: missing_vars.append("AZDO_ORG")
        if not AZDO_PROJECT: missing_vars.append("AZDO_PROJECT")
        if not AZDO_REPO: missing_vars.append("AZDO_REPO")
        return f"Error: Variables de entorno faltantes: {', '.join(missing_vars)}"
    
    # Extraer el nombre de la organización del URL
    org_name = AZDO_ORG
    if AZDO_ORG and "://" in AZDO_ORG:
        org_name = AZDO_ORG.replace("https://", "").split(".")[0]
    
    repo_url = f"https://{AZDO_PAT}@dev.azure.com/{org_name}/{AZDO_PROJECT}/_git/{AZDO_REPO}"
    
    print("******************************************")
    print(f"Using clone_repo on branch: {branch}")
    print(f"Cloning from: {repo_url}")
    
    # Crear el directorio si no existe
    os.makedirs(os.path.dirname(REPO_PATH), exist_ok=True)
    
    # Si el directorio ya existe, eliminarlo
    if os.path.exists(REPO_PATH):
        shutil.rmtree(REPO_PATH)
    
    try:
        subprocess.run(["git", "clone", "-b", branch, repo_url, REPO_PATH], check=True)
        return f"Repositorio clonado en '{REPO_PATH}'."
    except subprocess.CalledProcessError as e:
        return f"Error al clonar el repositorio: {str(e)}"

def create_branch(branch_name: str, base_branch: str = "master") -> str:
    """
    Crea una nueva rama a partir de la rama base especificada y la publica en el remoto.
    """
    # Obtener las variables de entorno en el momento de la ejecución
    REPO_PATH = os.getenv("REPO_PATH", "./repo_clonado")
    
    if not os.path.exists(REPO_PATH):
        return f"Error: El directorio del repositorio '{REPO_PATH}' no existe. Clona primero el repositorio."
    
    original_cwd = os.getcwd()
    os.chdir(REPO_PATH)
    try:
        # Asegurarse de estar en la rama base
        subprocess.run(["git", "checkout", base_branch], check=True)
        # Crear y cambiar a la nueva rama
        subprocess.run(["git", "checkout", "-b", branch_name], check=True)
        # Publicar la rama en el remoto
        subprocess.run(["git", "push", "-u", "origin", branch_name], check=True)
        return f"Rama '{branch_name}' creada a partir de '{base_branch}' y publicada en el remoto."
    except subprocess.CalledProcessError as e:
        return f"Error al crear o publicar la rama: {str(e)}"
    finally:
        os.chdir(original_cwd)

def commit_and_push(branch_name: str, commit_message: str) -> str:
    """
    Realiza commit y push de los cambios en la rama especificada.
    """
    # Obtener las variables de entorno en el momento de la ejecución
    REPO_PATH = os.getenv("REPO_PATH", "./repo_clonado")
    
    if not os.path.exists(REPO_PATH):
        return f"Error: El directorio del repositorio '{REPO_PATH}' no existe. Clona primero el repositorio."
        
    original_cwd = os.getcwd()
    os.chdir(REPO_PATH)
    try:
        # Asegurarse de estar en la rama correcta
        subprocess.run(["git", "checkout", branch_name], check=True)
        # Añadir todos los cambios
        subprocess.run(["git", "add", "."], check=True)
        # Realizar el commit
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        # Hacer push de la rama
        subprocess.run(["git", "push", "-u", "origin", branch_name], check=True)
        return f"Commit y push realizados en la rama '{branch_name}'."
    except subprocess.CalledProcessError as e:
        return f"Error en el commit/push: {str(e)}"
    finally:
        os.chdir(original_cwd)