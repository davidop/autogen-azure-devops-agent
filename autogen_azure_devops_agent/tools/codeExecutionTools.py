import re
import os
import tempfile
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass

# Intentar importar las dependencias Docker
try:
    from autogen_core.code_executor import CodeBlock, CodeExecutor
    from autogen_ext.code_executors.docker import DockerCommandLineCodeExecutor
    HAS_DOCKER_SUPPORT = True
except ImportError:
    HAS_DOCKER_SUPPORT = False
    print("Aviso: Las dependencias Docker no están instaladas. Algunas funciones de ejecución de código podrían no funcionar.")

@dataclass
class CodeExecutionResult:
    """Clase para representar el resultado de la ejecución de código."""
    success: bool
    output: str
    error_message: Optional[str] = None

def extract_markdown_code_blocks(markdown_text: str) -> List[Dict[str, str]]:
    """
    Extrae bloques de código de un texto en formato markdown.
    
    Args:
        markdown_text: Texto en formato markdown que contiene bloques de código
        
    Returns:
        Lista de diccionarios con las claves 'code' y 'language'
    """
    pattern = re.compile(r"```(?:\s*([a-zA-Z0-9\+\-]+))?[\s\n]*([\s\S]*?)```")
    matches = pattern.findall(markdown_text)
    code_blocks = []
    
    for match in matches:
        language = match[0].strip() if match[0] else "python"  # default to python
        code_content = match[1].strip()
        code_blocks.append({
            "code": code_content,
            "language": language
        })
    
    return code_blocks

async def execute_code_safely(code: str, language: str = "python") -> CodeExecutionResult:
    """
    Ejecuta código de forma segura usando un contenedor Docker.
    
    Args:
        code: El código a ejecutar
        language: El lenguaje de programación del código (por defecto: 'python')
        
    Returns:
        Un objeto CodeExecutionResult con el resultado de la ejecución
    """
    if not HAS_DOCKER_SUPPORT:
        return CodeExecutionResult(
            success=False,
            output="",
            error_message="Las dependencias Docker no están instaladas. No se puede ejecutar el código de forma segura."
        )
    
    # Crear directorio temporal para la ejecución
    work_dir = tempfile.mkdtemp()
    print(f"Ejecutando código en directorio temporal: {work_dir}")
    
    try:
        # Crear un CodeBlock para la ejecución
        blocks = [CodeBlock(code=code, language=language)]
        
        # Ejecutar el código en un contenedor Docker
        async with DockerCommandLineCodeExecutor(work_dir=work_dir) as executor:
            result = await executor.execute_code_blocks(blocks)
            
            if result.error:
                return CodeExecutionResult(
                    success=False,
                    output=result.output,
                    error_message=result.error
                )
            else:
                return CodeExecutionResult(
                    success=True,
                    output=result.output,
                    error_message=None
                )
                
    except Exception as e:
        return CodeExecutionResult(
            success=False,
            output="",
            error_message=f"Error al ejecutar el código: {str(e)}"
        )

def execute_markdown_code(markdown_text: str) -> Dict[str, Any]:
    """
    Extrae y ejecuta todos los bloques de código en un texto markdown.
    
    Args:
        markdown_text: Texto markdown que contiene bloques de código
        
    Returns:
        Diccionario con resultados de ejecución para cada bloque de código
    """
    import asyncio
    
    code_blocks = extract_markdown_code_blocks(markdown_text)
    if not code_blocks:
        return {"success": False, "message": "No se encontraron bloques de código en el texto"}
    
    results = {}
    
    for i, block in enumerate(code_blocks):
        code = block["code"]
        language = block["language"]
        
        print(f"\n--- Ejecutando bloque de código #{i+1} ({language}) ---")
        try:
            result = asyncio.run(execute_code_safely(code, language))
            
            results[f"block_{i+1}"] = {
                "language": language,
                "code": code,
                "success": result.success,
                "output": result.output,
                "error": result.error_message
            }
            
            print(f"--- Resultado de ejecución: {'Éxito' if result.success else 'Error'} ---")
            if result.success:
                print(f"Salida:\n{result.output}")
            else:
                print(f"Error:\n{result.error_message}")
                
        except Exception as e:
            results[f"block_{i+1}"] = {
                "language": language,
                "code": code,
                "success": False,
                "output": "",
                "error": str(e)
            }
            print(f"Error inesperado: {str(e)}")
    
    # Resumen de resultados
    success_count = sum(1 for r in results.values() if r["success"])
    results["summary"] = {
        "total_blocks": len(code_blocks),
        "successful_executions": success_count,
        "failed_executions": len(code_blocks) - success_count,
        "all_succeeded": success_count == len(code_blocks)
    }
    
    return results

if __name__ == "__main__":
    # Ejemplo de uso
    test_code = """
```python
import numpy as np
import matplotlib.pyplot as plt

# Crear datos para la gráfica
x = np.linspace(0, 10, 100)
y = np.sin(x)

# Crear una gráfica
plt.figure(figsize=(8, 4))
plt.plot(x, y, label='sin(x)')
plt.title('Función seno')
plt.xlabel('x')
plt.ylabel('y')
plt.grid(True)
plt.legend()
plt.savefig('test_plot.png')
print("Gráfica guardada como 'test_plot.png'")
```
"""
    
    results = execute_markdown_code(test_code)
    print("\nResumen de ejecución:", results["summary"])