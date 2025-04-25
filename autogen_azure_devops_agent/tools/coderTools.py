import os
import glob
import subprocess
import re

def explore_repository() -> str:
    """
    Explora la estructura del repositorio y devuelve una lista de directorios y archivos.
    
    Returns:
        str: Un informe con la estructura del repositorio.
    """
    repo_path = os.getenv("REPO_PATH", "./repo_clonado")
    
    if not os.path.exists(repo_path):
        return f"Error: El directorio del repositorio '{repo_path}' no existe. Clona primero el repositorio."
    
    try:
        # Obtener la lista de archivos y directorios usando el comando find con profundidad limitada
        cmd = f"find {repo_path} -type d -not -path '*/\\.*' | sort"
        result = subprocess.check_output(cmd, shell=True, text=True)
        
        directories = [d.replace(repo_path + "/", "") for d in result.strip().split('\n') if d != repo_path]
        
        # Encontrar soluciones y proyectos
        solutions = glob.glob(f"{repo_path}/**/*.sln", recursive=True)
        csproj_files = glob.glob(f"{repo_path}/**/*.csproj", recursive=True)
        
        # Formato de salida
        output = "Estructura del Repositorio\n"
        output += "=======================\n\n"
        
        output += "Soluciones encontradas:\n"
        for sol in solutions:
            output += f"- {os.path.basename(sol)}\n"
        
        output += "\nProyectos encontrados:\n"
        for proj in csproj_files:
            output += f"- {os.path.basename(proj)}\n"
        
        output += "\nDirectorios principales:\n"
        for directory in directories[:20]:  # Limitar a los primeros 20 directorios
            if directory:  # Evitar directorios vacíos
                output += f"- {directory}\n"
        
        if len(directories) > 20:
            output += f"... y {len(directories) - 20} directorios más\n"
        
        return output
    
    except subprocess.CalledProcessError as e:
        return f"Error al explorar el repositorio: {str(e)}"


def find_files(pattern: str) -> str:
    """
    Busca archivos en el repositorio que coincidan con un patrón.
    
    Args:
        pattern (str): Patrón de búsqueda (por ejemplo, "*.cs" o "Controller*.cs")
        
    Returns:
        str: Lista de archivos encontrados.
    """
    repo_path = os.getenv("REPO_PATH", "./repo_clonado")
    
    if not os.path.exists(repo_path):
        return f"Error: El directorio del repositorio '{repo_path}' no existe. Clona primero el repositorio."
    
    try:
        files = glob.glob(f"{repo_path}/**/{pattern}", recursive=True)
        
        if not files:
            return f"No se encontraron archivos que coincidan con el patrón '{pattern}'."
        
        # Formatear los resultados de manera legible
        result = f"Archivos encontrados para el patrón '{pattern}':\n\n"
        for file in files:
            relative_path = os.path.relpath(file, repo_path)
            result += f"- {relative_path}\n"
        
        return result
    
    except Exception as e:
        return f"Error al buscar archivos: {str(e)}"


def read_file(file_path: str) -> str:
    """
    Lee el contenido de un archivo en el repositorio.
    
    Args:
        file_path (str): Ruta relativa al archivo dentro del repositorio.
        
    Returns:
        str: Contenido del archivo.
    """
    repo_path = os.getenv("REPO_PATH", "./repo_clonado")
    
    full_path = os.path.join(repo_path, file_path)
    
    if not os.path.exists(full_path):
        return f"Error: El archivo '{file_path}' no existe en el repositorio."
    
    try:
        with open(full_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        return f"Contenido de {file_path}:\n\n```{os.path.splitext(file_path)[1]}\n{content}\n```"
    
    except Exception as e:
        return f"Error al leer el archivo: {str(e)}"


def write_file(file_path: str, content: str) -> str:
    """
    Escribe contenido en un archivo del repositorio, creándolo si no existe.
    
    Args:
        file_path (str): Ruta relativa al archivo dentro del repositorio.
        content (str): Contenido a escribir en el archivo.
        
    Returns:
        str: Mensaje de resultado.
    """
    repo_path = os.getenv("REPO_PATH", "./repo_clonado")
    
    full_path = os.path.join(repo_path, file_path)
    
    # Crear el directorio si no existe
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    try:
        with open(full_path, 'w', encoding='utf-8') as file:
            file.write(content)
        
        return f"Archivo '{file_path}' escrito correctamente."
    
    except Exception as e:
        return f"Error al escribir el archivo: {str(e)}"


def update_file(file_path: str, search_pattern: str, replacement: str) -> str:
    """
    Actualiza un archivo buscando un patrón y reemplazándolo con nuevo contenido.
    
    Args:
        file_path (str): Ruta relativa al archivo dentro del repositorio.
        search_pattern (str): Expresión regular para buscar en el archivo.
        replacement (str): Texto de reemplazo.
        
    Returns:
        str: Mensaje de resultado.
    """
    repo_path = os.getenv("REPO_PATH", "./repo_clonado")
    
    full_path = os.path.join(repo_path, file_path)
    
    if not os.path.exists(full_path):
        return f"Error: El archivo '{file_path}' no existe en el repositorio."
    
    try:
        # Leer el archivo original
        with open(full_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Realizar el reemplazo
        new_content = re.sub(search_pattern, replacement, content)
        
        # Si no hubo cambios, informar
        if new_content == content:
            return f"No se encontró el patrón en el archivo '{file_path}'. No se realizaron cambios."
        
        # Escribir el archivo actualizado
        with open(full_path, 'w', encoding='utf-8') as file:
            file.write(new_content)
        
        return f"Archivo '{file_path}' actualizado correctamente."
    
    except Exception as e:
        return f"Error al actualizar el archivo: {str(e)}"


def insert_code_in_file(file_path: str, marker: str, code_to_insert: str, insert_after: bool = True) -> str:
    """
    Inserta código en un archivo en una posición específica marcada por una cadena.
    
    Args:
        file_path (str): Ruta relativa al archivo dentro del repositorio.
        marker (str): Cadena de texto que marca dónde insertar el código.
        code_to_insert (str): Código a insertar.
        insert_after (bool): Si es True, inserta después del marcador; si es False, inserta antes.
        
    Returns:
        str: Mensaje de resultado.
    """
    repo_path = os.getenv("REPO_PATH", "./repo_clonado")
    
    full_path = os.path.join(repo_path, file_path)
    
    if not os.path.exists(full_path):
        return f"Error: El archivo '{file_path}' no existe en el repositorio."
    
    try:
        # Leer el archivo original
        with open(full_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Buscar el marcador y realizar la inserción
        if marker not in content:
            return f"Error: No se encontró el marcador '{marker}' en el archivo '{file_path}'."
        
        if insert_after:
            new_content = content.replace(marker, f"{marker}{code_to_insert}")
        else:
            new_content = content.replace(marker, f"{code_to_insert}{marker}")
        
        # Escribir el archivo actualizado
        with open(full_path, 'w', encoding='utf-8') as file:
            file.write(new_content)
        
        return f"Código insertado correctamente en el archivo '{file_path}'."
    
    except Exception as e:
        return f"Error al insertar código: {str(e)}"


def create_csharp_class(file_path: str, namespace: str, class_name: str, properties: list = None, base_class: str = None) -> str:
    """
    Crea una nueva clase C# con propiedades opcionales.
    
    Args:
        file_path (str): Ruta relativa al archivo dentro del repositorio.
        namespace (str): Espacio de nombres para la clase.
        class_name (str): Nombre de la clase.
        properties (list): Lista de diccionarios con propiedades. Cada diccionario debe tener 'type' y 'name'.
        base_class (str): Clase base opcional.
        
    Returns:
        str: Mensaje de resultado.
    """
    if properties is None:
        properties = []
    
    # Construir la clase
    class_declaration = f"public class {class_name}"
    if base_class:
        class_declaration += f" : {base_class}"
    
    class_content = f"""namespace {namespace}
{{
    {class_declaration}
    {{"""
    
    # Agregar propiedades
    for prop in properties:
        prop_type = prop.get("type", "string")
        prop_name = prop.get("name", "Property")
        class_content += f"""
        public {prop_type} {prop_name} {{ get; set; }}"""
    
    if properties:
        class_content += "\n"
    
    class_content += f"""    }}
}}
"""
    
    # Escribir el archivo
    result = write_file(file_path, class_content)
    return result


def implement_controller_endpoint(file_path: str, endpoint_name: str, http_method: str, route: str, 
                                 return_type: str, repository_method_name: str = None) -> str:
    """
    Implementa un nuevo endpoint en un controlador existente.
    
    Args:
        file_path (str): Ruta relativa al archivo del controlador.
        endpoint_name (str): Nombre del método del endpoint.
        http_method (str): Método HTTP (Get, Post, Put, Delete).
        route (str): Ruta del endpoint.
        return_type (str): Tipo de retorno del endpoint.
        repository_method_name (str): Nombre del método del repositorio a llamar.
        
    Returns:
        str: Mensaje de resultado.
    """
    repo_path = os.getenv("REPO_PATH", "./repo_clonado")
    
    full_path = os.path.join(repo_path, file_path)
    
    if not os.path.exists(full_path):
        return f"Error: El archivo del controlador '{file_path}' no existe."
    
    try:
        with open(full_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Buscar la clase del controlador
        class_match = re.search(r'public\s+class\s+(\w+Controller)\s*(?::\s*\w+Controller)?\s*', content)
        if not class_match:
            return f"Error: No se pudo encontrar la clase del controlador en '{file_path}'."
        
        controller_name = class_match.group(1)
        
        # Buscar la inyección de dependencias para el repositorio
        repo_field_match = re.search(r'private\s+readonly\s+I(\w+)Repository\s+_(\w+)Repository', content)
        if not repo_field_match:
            return f"Error: No se pudo encontrar el campo del repositorio en el controlador '{controller_name}'."
        
        repo_interface = f"I{repo_field_match.group(1)}Repository"
        repo_field = f"_{repo_field_match.group(1).lower()}Repository"
        
        # Preparar el código del nuevo endpoint
        if not repository_method_name:
            repository_method_name = endpoint_name
        
        new_endpoint = f"""
        [Http{http_method}("{route}")]
        public async Task<ActionResult<{return_type}>> {endpoint_name}()
        {{
            try
            {{
                var result = await {repo_field}.{repository_method_name}();
                return Ok(result);
            }}
            catch (Exception ex)
            {{
                return StatusCode(500, $"Error interno: {{ex.Message}}");
            }}
        }}
"""
        
        # Encontrar dónde insertar el nuevo endpoint (justo antes de la última llave de cierre)
        last_brace_match = re.search(r'\n\s*}\s*$', content)
        if not last_brace_match:
            return f"Error: No se pudo encontrar el lugar adecuado para insertar el endpoint en '{file_path}'."
        
        # Insertar el nuevo endpoint
        insert_position = last_brace_match.start()
        new_content = content[:insert_position] + new_endpoint + content[insert_position:]
        
        # Escribir el archivo actualizado
        with open(full_path, 'w', encoding='utf-8') as file:
            file.write(new_content)
        
        return f"Endpoint '{endpoint_name}' implementado correctamente en '{controller_name}'."
    
    except Exception as e:
        return f"Error al implementar el endpoint: {str(e)}"


def implement_repository_method(file_path: str, interface_file_path: str, method_name: str, 
                               return_type: str, implementation: str = None) -> str:
    """
    Implementa un nuevo método en un repositorio y su interfaz.
    
    Args:
        file_path (str): Ruta relativa al archivo del repositorio.
        interface_file_path (str): Ruta relativa al archivo de la interfaz.
        method_name (str): Nombre del método a implementar.
        return_type (str): Tipo de retorno del método.
        implementation (str): Código de implementación del método.
        
    Returns:
        str: Mensaje de resultado.
    """
    repo_path = os.getenv("REPO_PATH", "./repo_clonado")
    
    full_repo_path = os.path.join(repo_path, file_path)
    full_interface_path = os.path.join(repo_path, interface_file_path)
    
    if not os.path.exists(full_repo_path) or not os.path.exists(full_interface_path):
        return f"Error: El repositorio o su interfaz no existen."
    
    # Si no se proporciona implementación, crear una implementación básica
    if not implementation:
        implementation = f"""
        public async Task<{return_type}> {method_name}()
        {{
            // Implementación por defecto
            return new {return_type}();
        }}"""
    
    try:
        # Primero añadir el método a la interfaz
        with open(full_interface_path, 'r', encoding='utf-8') as file:
            interface_content = file.read()
        
        interface_method = f"Task<{return_type}> {method_name}();"
        
        # Buscar dónde insertar el método (antes de la última llave de cierre)
        interface_last_brace = re.search(r'\n\s*}\s*$', interface_content)
        if not interface_last_brace:
            return f"Error: No se pudo encontrar el lugar adecuado para insertar el método en la interfaz."
        
        interface_insert_position = interface_last_brace.start()
        new_interface_content = (
            interface_content[:interface_insert_position] + 
            f"\n        {interface_method}\n" + 
            interface_content[interface_insert_position:]
        )
        
        # Guardar la interfaz actualizada
        with open(full_interface_path, 'w', encoding='utf-8') as file:
            file.write(new_interface_content)
        
        # Ahora implementar el método en el repositorio
        with open(full_repo_path, 'r', encoding='utf-8') as file:
            repo_content = file.read()
        
        repo_last_brace = re.search(r'\n\s*}\s*$', repo_content)
        if not repo_last_brace:
            return f"Error: No se pudo encontrar el lugar adecuado para insertar el método en el repositorio."
        
        repo_insert_position = repo_last_brace.start()
        new_repo_content = (
            repo_content[:repo_insert_position] + 
            f"\n        {implementation}\n" + 
            repo_content[repo_insert_position:]
        )
        
        # Guardar el repositorio actualizado
        with open(full_repo_path, 'w', encoding='utf-8') as file:
            file.write(new_repo_content)
        
        return f"Método '{method_name}' implementado correctamente en el repositorio y su interfaz."
    
    except Exception as e:
        return f"Error al implementar el método: {str(e)}"