import asyncio
import os
import sys
import datetime
from dotenv import load_dotenv
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

# Importar solo los agentes necesarios
from autogen_azure_devops_agent.agents.devopsAgent import create_devops_agent
from autogen_azure_devops_agent.agents.coderAgent import create_coder_agent
from autogen_azure_devops_agent.agents.architectAgent import create_architect_agent
from autogen_azure_devops_agent.agents.qaAgent import create_qa_agent
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.ui import Console

# Importar herramientas
from autogen_azure_devops_agent.tools.devopsTools import clone_repo, create_branch, commit_and_push
from autogen_azure_devops_agent.tools.coderTools import (
    explore_repository,
    find_files,
    read_file,
    write_file,
    update_file,
    insert_code_in_file,
    create_csharp_class,
    implement_controller_endpoint,
    implement_repository_method
)

# Configurar registro de salida a archivo
def setup_logging():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = "./logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = f"{log_dir}/agentchat_{timestamp}.log"
    
    # Crear un archivo de registro
    log_file_handle = open(log_file, "w", encoding="utf-8")
    
    # Clase que captura la salida y la envía tanto a stdout como al archivo
    class TeeOutput:
        def __init__(self, file_handle, original_stream):
            self.file_handle = file_handle
            self.original_stream = original_stream
        
        def write(self, message):
            self.original_stream.write(message)
            self.file_handle.write(message)
            self.file_handle.flush()  # Asegurar que se escriba inmediatamente
        
        def flush(self):
            self.original_stream.flush()
            self.file_handle.flush()
    
    # Redirigir stdout y stderr
    sys.stdout = TeeOutput(log_file_handle, sys.stdout)
    sys.stderr = TeeOutput(log_file_handle, sys.stderr)
    
    print(f"===== REGISTRO DE EJECUCIÓN INICIADO {timestamp} =====")
    print(f"La salida se está guardando en: {log_file}")
    
    return log_file

# Cargar variables de entorno - asegurarse de que esto funcione primero
load_dotenv(override=True)  # Agregar override=True para forzar la recarga

# Configurar registro
log_file = setup_logging()

# Depuración: Imprimir las variables cargadas para verificar
print("Variables de entorno cargadas:")
print(f"AZDO_PAT: {'Configurado' if os.getenv('AZDO_PAT') else 'No configurado'}")
print(f"AZDO_ORG: {os.getenv('AZDO_ORG')}")
print(f"AZDO_PROJECT: {os.getenv('AZDO_PROJECT')}")
print(f"AZDO_REPO: {os.getenv('AZDO_REPO')}")

# Establecer las variables necesarias para las herramientas de DevOps
# Forzamos la asignación con valores concretos para evitar problemas
os.environ["AZDO_PAT"] = os.getenv("AZDO_PAT", "")
os.environ["AZDO_ORG"] = os.getenv("AZDO_ORG", "")
os.environ["AZDO_PROJECT"] = os.getenv("AZDO_PROJECT", "")
os.environ["AZDO_REPO"] = os.getenv("AZDO_REPO", "")
os.environ["REPO_PATH"] = "./repo_clonado"  # Directorio local donde se clonará el repo

az_model_client = AzureOpenAIChatCompletionClient(
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY")
)

# Crear solo los agentes especializados requeridos
devops = create_devops_agent(az_model_client)
coder = create_coder_agent(az_model_client)
architect = create_architect_agent(az_model_client)
qa = create_qa_agent(az_model_client)

# Crear el flujo de conversación
async def main():
    
    # Definir condiciones de terminación
    termination_condition = TextMentionTermination("Pull Request completed!")

    # Diseño de un selector que controla el flujo de trabajo con los agentes especializados reducidos
    selector_prompt = """
    Basado en la descripción de los agentes y el contexto actual, selecciona el agente más apropiado para manejar la tarea.
    
    AGENTES:
    - ArchitectAgent: Especialista en diseño de arquitectura, patrones de diseño y principios SOLID.
    - CoderAgent: Implementa soluciones técnicas en el código base usando diversas herramientas.
    - QAAgent: Se enfoca en calidad, pruebas y validación del código desarrollado.
    - DevOpsAgent: Gestiona operaciones Git en Azure DevOps, incluyendo clonación, ramas, commits y pull requests.
    
    REGLAS DE SECUENCIA:
    1. La conversación siempre empieza con el ArchitectAgent para analizar la tarea y crear un plan inicial.
    2. El ArchitectAgent DEBE identificar EXACTAMENTE qué archivos deben ser creados o modificados en un formato JSON estructurado.
    3. Para cambios en repositorios, el DevOpsAgent debe preparar el entorno de trabajo después del plan del Arquitecto.
    4. El CoderAgent implementa soluciones basadas en directrices del Architect, enfocándose SOLO en los archivos identificados en el plan JSON.
    5. Cuando el CoderAgent indique que ha completado la implementación, el ArchitectAgent DEBE realizar una revisión formal del código para verificar que cumple con los patrones de diseño y principios arquitectónicos establecidos.
    6. Después de la aprobación del ArchitectAgent, el QAAgent debe verificar que el código cumpla requisitos y buenas prácticas de calidad.
    7. Si el ArchitectAgent o QAAgent encuentran problemas, el CoderAgent debe realizar las correcciones necesarias y volver a solicitar revisión.
    8. El CoderAgent debe implementar COMPLETAMENTE todas las partes de la solución antes de finalizar e indicar "Task completed successfully!"
    9. Solo después de la aprobación del ArchitectAgent y QAAgent, el DevOpsAgent hace commit y push.
    10. Finalmente, el DevOpsAgent debe crear un pull request e indicar "Pull Request completed!"
    11. La conversación solo finaliza cuando el DevOpsAgent indica "Pull Request completed!"
    
    ESTADO ACTUAL:
    {history}
    
    ÚLTIMAS ACCIONES:
    {roles}
    
    ACTORES DISPONIBLES:
    {participants}
    
    Basado en el estado actual y las reglas de secuencia, selecciona UN SOLO agente para el siguiente paso.
    """

    # Crear el grupo de chat con selector inteligente y solo los agentes requeridos
    group_chat = SelectorGroupChat(
        participants=[architect, coder, qa, devops],
        model_client=az_model_client,
        termination_condition=termination_condition,
        selector_prompt=selector_prompt
    )
    
    # Definir la tarea
    task = """
Quiero introducir un nuevo endpoint con su controlador en la API de ProdwareAzureCopilot.
El endpoint se va a llamar GetFancyDashboard y debe incluirse dentro del DashboardController existente.
El Repository se encuentra dentro de Repositories/General/DashboardRepository junto con su interfaz IDashboardRepository.
Debemos crear una clase FancyDashboard para hacer pruebas.
Clona el repositorio, crea una rama feature/fancy-dashboard y publícala.
"""

    # Iniciar el chat con un mensaje que establece el contexto y la secuencia
    initial_message = f"""
Tenemos la siguiente tarea de desarrollo:

{task}

Seguiremos un flujo de trabajo estructurado donde participarán los especialistas:

1. El Arquitecto evaluará la tarea y propondrá el diseño apropiado para el nuevo endpoint
2. El equipo de DevOps clonará el repositorio y preparará el entorno
3. El equipo de desarrollo implementará el endpoint solicitado, incluyendo:
   - Crear la clase FancyDashboard
   - Añadir el método necesario a IDashboardRepository
   - Implementar el método en DashboardRepository
   - Añadir el endpoint GetFancyDashboard al DashboardController
4. El Arquitecto revisará el código para asegurar que sigue los patrones y principios arquitectónicos
5. El equipo de QA verificará la calidad y cobertura de pruebas
6. DevOps finalizará con commit, push de los cambios y creación de un pull request

ArchitectAgent, por favor comienza analizando la tarea y generando un plan estructurado.
"""
    
    try:
        # Ejecutar el chat y mostrar resultados
        await Console(
            group_chat.run_stream(
                task=initial_message
            )
        )
    except Exception as e:
        print(f"\n\n===== ERROR DE EJECUCIÓN: {str(e)} =====")
    finally:
        print(f"\n\n===== REGISTRO DE EJECUCIÓN FINALIZADO =====")
        print(f"La salida completa ha sido guardada en: {log_file}")

if __name__ == "__main__":
    asyncio.run(main())
