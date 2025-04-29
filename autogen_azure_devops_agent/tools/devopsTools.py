import os
import subprocess
import shutil

# Las variables se obtendrán dinámicamente en cada función, no al importar el módulo
def clone_repo(branch: str = "main", git_user_name: str = None, git_user_email: str = None) -> str:
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
    
    # Extraer el nombre de la organización del URL correctamente
    org_name = AZDO_ORG
    if AZDO_ORG and "dev.azure.com/" in AZDO_ORG:
        org_name = AZDO_ORG.split("dev.azure.com/")[1].rstrip('/')
    
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
        # Intentar clonar con la rama especificada
        try:
            subprocess.run(["git", "clone", "-b", branch, repo_url, REPO_PATH], check=True)
            
            # Configurar la identidad Git después de clonar si se proporcionaron valores
            if git_user_name and git_user_email:
                os.chdir(REPO_PATH)
                subprocess.run(["git", "config", "user.name", git_user_name], check=True)
                subprocess.run(["git", "config", "user.email", git_user_email], check=True)
                os.chdir("..")
                print(f"Configurada identidad Git local: {git_user_name} <{git_user_email}>")
            
            return f"Repositorio clonado en '{REPO_PATH}' usando la rama '{branch}'."
        except subprocess.CalledProcessError:
            # Si falló con la rama especificada, intentar clonar con otra rama común o sin especificar rama
            if branch == "main":
                print("La rama 'main' no está disponible. Intentando con 'master'...")
                try:
                    subprocess.run(["git", "clone", "-b", "master", repo_url, REPO_PATH], check=True)
                    
                    # Configurar la identidad Git después de clonar si se proporcionaron valores
                    if git_user_name and git_user_email:
                        os.chdir(REPO_PATH)
                        subprocess.run(["git", "config", "user.name", git_user_name], check=True)
                        subprocess.run(["git", "config", "user.email", git_user_email], check=True)
                        os.chdir("..")
                        print(f"Configurada identidad Git local: {git_user_name} <{git_user_email}>")
                        
                    return f"Repositorio clonado en '{REPO_PATH}' usando la rama 'master'."
                except subprocess.CalledProcessError:
                    print("La rama 'master' tampoco está disponible. Intentando clonar sin especificar rama...")
                    return _clone_default_branch(repo_url, REPO_PATH, git_user_name, git_user_email)
            else:
                print(f"La rama '{branch}' no está disponible. Intentando clonar sin especificar rama...")
                return _clone_default_branch(repo_url, REPO_PATH, git_user_name, git_user_email)
    except subprocess.CalledProcessError as e:
        return f"Error al clonar el repositorio: {str(e)}"

def _clone_default_branch(repo_url: str, repo_path: str, git_user_name: str = None, git_user_email: str = None) -> str:
    """Helper function to clone the default branch of a repository without specifying branch name."""
    try:
        subprocess.run(["git", "clone", repo_url, repo_path], check=True)
        # Determinar qué rama se clonó
        os.chdir(repo_path)
        current_branch = subprocess.check_output(["git", "branch", "--show-current"], text=True).strip()
        
        # Configurar la identidad Git después de clonar si se proporcionaron valores
        if git_user_name and git_user_email:
            subprocess.run(["git", "config", "user.name", git_user_name], check=True)
            subprocess.run(["git", "config", "user.email", git_user_email], check=True)
            print(f"Configurada identidad Git local: {git_user_name} <{git_user_email}>")
        
        os.chdir("..")
        return f"Repositorio clonado en '{repo_path}' usando la rama principal '{current_branch}'."
    except subprocess.CalledProcessError as e:
        return f"Error al clonar el repositorio sin especificar rama: {str(e)}"

def create_branch(branch_name: str, base_branch: str = "main") -> str:
    """
    Crea una nueva rama a partir de la rama base especificada y la publica en el remoto.
    Primero verifica si la rama ya existe localmente o en remoto.
    
    Args:
        branch_name (str): Nombre de la rama a crear
        base_branch (str, optional): Rama base desde la que crear la nueva rama. Por defecto "main".
        
    Returns:
        str: Mensaje con el resultado de la operación
    """
    # Obtener las variables de entorno en el momento de la ejecución
    REPO_PATH = os.getenv("REPO_PATH", "./repo_clonado")
    
    # Validar que el nombre de la rama no esté vacío
    if not branch_name or not branch_name.strip():
        return "Error: El nombre de la rama no puede estar vacío."
    
    # Validar que el nombre de la rama no contenga caracteres no permitidos
    import re
    if not re.match(r'^[a-zA-Z0-9_\-/.]+$', branch_name):
        return "Error: El nombre de la rama contiene caracteres no permitidos. Usa solo letras, números, guiones, barras y guiones bajos."
    
    if not os.path.exists(REPO_PATH):
        return f"Error: El directorio del repositorio '{REPO_PATH}' no existe. Clona primero el repositorio."
    
    original_cwd = os.getcwd()
    os.chdir(REPO_PATH)
    try:
        # Actualizar la lista de ramas remotas
        subprocess.run(["git", "fetch"], check=True)
        
        # Verificar si la rama base existe
        all_branches = subprocess.check_output(["git", "branch", "-a"], text=True).splitlines()
        base_exists = False
        for branch in all_branches:
            branch = branch.strip().replace("* ", "")
            if branch == base_branch or branch == f"remotes/origin/{base_branch}":
                base_exists = True
                break
        
        # Si la rama base especificada no existe, intentar con "master" como alternativa
        if not base_exists and base_branch == "main":
            print(f"La rama base '{base_branch}' no existe. Comprobando si existe 'master' como alternativa...")
            for branch in all_branches:
                branch = branch.strip().replace("* ", "")
                if branch == "master" or branch == "remotes/origin/master":
                    base_exists = True
                    base_branch = "master"
                    print(f"Usando 'master' como rama base alternativa.")
                    break
                    
        if not base_exists:
            # Intentar encontrar la rama predeterminada
            try:
                # Listar todas las ramas remotas y buscar HEAD
                remote_head = subprocess.check_output(["git", "symbolic-ref", "refs/remotes/origin/HEAD"], text=True).strip()
                if remote_head:
                    # Convertir algo como "refs/remotes/origin/HEAD -> refs/remotes/origin/main" a "main"
                    default_branch = remote_head.split("refs/remotes/origin/")[-1]
                    print(f"Usando la rama predeterminada del repositorio: {default_branch}")
                    base_branch = default_branch
                    base_exists = True
            except subprocess.CalledProcessError:
                # Si no se puede determinar la rama predeterminada
                pass
                
        if not base_exists:
            return f"Error: No se pudo encontrar una rama base válida. Ni '{base_branch}', ni 'master', ni la rama predeterminada existen."
        
        # Verificar si la rama ya existe localmente
        local_branches = subprocess.check_output(["git", "branch"], text=True).splitlines()
        local_branches = [b.strip().replace("* ", "") for b in local_branches]
        
        # Verificar si la rama ya existe en remoto
        remote_branches = subprocess.check_output(["git", "branch", "-r"], text=True).splitlines()
        remote_branches = [b.strip().replace("origin/", "") for b in remote_branches]
        
        # Buscar ramas similares
        similar_branches = []
        for branch in local_branches + remote_branches:
            if branch_name.lower() in branch.lower() or branch.lower() in branch_name.lower():
                if branch != branch_name:  # No incluir la misma rama como "similar"
                    similar_branches.append(branch)
        
        # Si la rama existe exactamente con el mismo nombre
        if branch_name in local_branches or branch_name in remote_branches:
            # Cambiar a la rama si ya existe
            subprocess.run(["git", "checkout", branch_name], check=True)
            
            # Verificar si la rama local está actualizada con la remota
            if branch_name in remote_branches:
                try:
                    status_output = subprocess.check_output(["git", "status", "-sb"], text=True)
                    if f"...origin/{branch_name}" in status_output and ("behind" in status_output or "ahead" in status_output):
                        if "behind" in status_output:
                            # Actualizar la rama local si está detrás de la remota
                            subprocess.run(["git", "pull", "origin", branch_name], check=True)
                            return f"La rama '{branch_name}' ya existía y ha sido actualizada con los cambios remotos."
                        else:
                            return f"La rama '{branch_name}' ya existe. Se ha cambiado a esta rama. Tiene commits locales que no están en remoto."
                except subprocess.CalledProcessError:
                    pass
            
            return f"La rama '{branch_name}' ya existe. Se ha cambiado a esta rama."
        
        # Si hay ramas similares, informar pero continuar
        similar_info = ""
        if similar_branches:
            unique_similar = list(set(similar_branches))
            similar_info = f"Nota: Se encontraron ramas similares: {', '.join(unique_similar)}. "
        
        # Asegurarse de estar en la rama base y actualizarla
        subprocess.run(["git", "checkout", base_branch], check=True)
        subprocess.run(["git", "pull", "origin", base_branch], check=True)
        
        # Crear y cambiar a la nueva rama
        subprocess.run(["git", "checkout", "-b", branch_name], check=True)
        # Publicar la rama en el remoto
        subprocess.run(["git", "push", "-u", "origin", branch_name], check=True)
        return f"{similar_info}Rama '{branch_name}' creada a partir de '{base_branch}' y publicada en el remoto."
    except subprocess.CalledProcessError as e:
        # Intentar proporcionar un mensaje de error más descriptivo
        error_msg = str(e)
        if "already exists" in error_msg:
            return f"Error: La rama '{branch_name}' ya existe en remoto pero no localmente. Ejecuta 'git fetch' y luego 'git checkout {branch_name}'."
        elif "Permission denied" in error_msg:
            return "Error: Permisos denegados. Verifica las credenciales de Git y los permisos en el repositorio."
        elif "not found" in error_msg:
            return f"Error: El repositorio remoto no se encontró. Verifica la configuración de Git."
        else:
            return f"Error al crear o publicar la rama: {error_msg}"
    finally:
        os.chdir(original_cwd)

def commit_and_push(branch_name: str, commit_message: str, git_user_name: str = None, git_user_email: str = None) -> str:
    """
    Realiza commit y push de los cambios en la rama especificada.
    
    Args:
        branch_name (str): Nombre de la rama donde se realizarán los commits
        commit_message (str): Mensaje del commit
        git_user_name (str, optional): Nombre del usuario de Git para firmar el commit
        git_user_email (str, optional): Email del usuario de Git para firmar el commit
        
    Returns:
        str: Mensaje con el resultado de la operación
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
        
        # Configurar la identidad Git si se proporcionaron valores
        identity_configured = False
        if git_user_name and git_user_email:
            subprocess.run(["git", "config", "user.name", git_user_name], check=True)
            subprocess.run(["git", "config", "user.email", git_user_email], check=True)
            print(f"Configurada identidad Git para commit: {git_user_name} <{git_user_email}>")
            identity_configured = True
        else:
            # Verificar si existe una configuración de usuario en el repositorio
            try:
                user_name = subprocess.check_output(["git", "config", "user.name"], text=True).strip()
                user_email = subprocess.check_output(["git", "config", "user.email"], text=True).strip()
                if user_name and user_email:
                    print(f"Usando identidad Git existente: {user_name} <{user_email}>")
                    identity_configured = True
            except subprocess.CalledProcessError:
                print("No se encontró configuración de identidad Git en el repositorio local")

        # Advertir si no hay identidad configurada
        if not identity_configured:
            print("ADVERTENCIA: No se ha configurado una identidad Git específica. Se usará la configuración global si existe.")
                
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

def create_pull_request(branch_name: str, target_branch: str = "main", title: str = None, description: str = None) -> str:
    """
    Crea un pull request desde la rama especificada hacia la rama destino.
    
    Args:
        branch_name (str): Nombre de la rama de origen (feature branch)
        target_branch (str): Rama destino (generalmente main o develop)
        title (str): Título del pull request
        description (str): Descripción del pull request
        
    Returns:
        str: Mensaje con el resultado de la operación
    """
    # Obtener las variables de entorno
    AZDO_PAT = os.getenv("AZDO_PAT")
    AZDO_ORG = os.getenv("AZDO_ORG")
    AZDO_PROJECT = os.getenv("AZDO_PROJECT")
    AZDO_REPO = os.getenv("AZDO_REPO")
    REPO_PATH = os.getenv("REPO_PATH", "./repo_clonado")
    
    # Verificar que las variables necesarias estén configuradas
    if not all([AZDO_PAT, AZDO_ORG, AZDO_PROJECT, AZDO_REPO]):
        missing_vars = []
        if not AZDO_PAT: missing_vars.append("AZDO_PAT")
        if not AZDO_ORG: missing_vars.append("AZDO_ORG")
        if not AZDO_PROJECT: missing_vars.append("AZDO_PROJECT")
        if not AZDO_REPO: missing_vars.append("AZDO_REPO")
        return f"Error: Variables de entorno faltantes: {', '.join(missing_vars)}"
    
    # Si no se proporciona un título, crear uno basado en el nombre de la rama
    if not title:
        title = f"Merge {branch_name} into {target_branch}"
    
    # Si no se proporciona una descripción, crear una predeterminada
    if not description:
        description = f"Pull request para fusionar la rama {branch_name} en {target_branch}."
    
    # Extraer el nombre de la organización del URL correctamente
    org_name = AZDO_ORG
    if AZDO_ORG and "dev.azure.com/" in AZDO_ORG:
        org_name = AZDO_ORG.split("dev.azure.com/")[1].rstrip('/')
    
    # Usando el API REST de Azure DevOps para crear el pull request
    # El comando curl con autenticación básica y datos JSON
    create_pr_command = [
        "curl", "-X", "POST",
        f"https://dev.azure.com/{org_name}/{AZDO_PROJECT}/_apis/git/repositories/{AZDO_REPO}/pullrequests?api-version=7.0",
        "-H", "Content-Type: application/json",
        "-u", f":{AZDO_PAT}",
        "-d", f'{{"sourceRefName":"refs/heads/{branch_name}","targetRefName":"refs/heads/{target_branch}","title":"{title}","description":"{description}"}}'
    ]
    
    try:
        result = subprocess.run(create_pr_command, check=True, capture_output=True, text=True)
        
        # Verificar si la creación del PR fue exitosa
        if result.returncode == 0:
            response = result.stdout
            
            # Intentar extraer la URL del pull request de la respuesta
            import json
            try:
                response_json = json.loads(response)
                pr_url = response_json.get('url') or response_json.get('webUrl')
                pr_id = response_json.get('pullRequestId')
                
                if pr_url:
                    return f"Pull request #{pr_id} creado exitosamente: {pr_url}"
                else:
                    return f"Pull request creado exitosamente, pero no se pudo obtener la URL."
                
            except json.JSONDecodeError:
                return f"Pull request posiblemente creado, pero no se pudo analizar la respuesta: {response[:100]}..."
        else:
            return f"Error al crear el pull request. Código de salida: {result.returncode}"
    
    except subprocess.CalledProcessError as e:
        error_output = e.stderr.strip() if e.stderr else str(e)
        return f"Error al crear el pull request: {error_output}"
    except Exception as e:
        return f"Error inesperado al crear el pull request: {str(e)}"