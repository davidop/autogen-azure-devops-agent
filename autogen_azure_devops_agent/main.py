import asyncio
import os
from dotenv import load_dotenv
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

# Corregir importaciones para usar rutas relativas y actualizar nombre de función
from autogen_azure_devops_agent.agents.plannerAgent import create_task_planner_agent
from autogen_azure_devops_agent.agents.devopsAgent import create_devops_agent
from autogen_azure_devops_agent.agents.coderAgent import create_coder_agent
from autogen_azure_devops_agent.agents.coordinatorAgent import create_coordinator_agent
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

# Cargar variables de entorno - asegurarse de que esto funcione primero
load_dotenv(override=True)  # Agregar override=True para forzar la recarga

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

# Crear agentes especializados
planner = create_task_planner_agent(az_model_client)
devops = create_devops_agent(az_model_client)
coder = create_coder_agent(az_model_client)
coordinator = create_coordinator_agent(az_model_client)

# Crear el flujo de conversación
async def main():
    
    # Definir condiciones de terminación - Cambiado para pasar directamente el objeto sin envolverlo en una lista
    termination_condition = TextMentionTermination("Pull Request completed!")

    # Diseño de un selector que controla el flujo de trabajo
    selector_prompt = """
    Basado en la descripción de los agentes y el contexto actual, selecciona el agente más apropiado para manejar la tarea.
    
    AGENTES:
    - DevTaskPlannerAgent: Analiza tareas de desarrollo y genera resúmenes estructurados para la planificación del trabajo.
    - DevOpsAgent: Gestiona operaciones Git en Azure DevOps, incluyendo clonación de repositorios, creación de ramas, commits y pull requests.
    - CoderAgent: Implementa soluciones técnicas en el código base usando diversas herramientas.
    - Coordinator: Supervisa el proceso y dirige el flujo de trabajo.
    
    REGLAS DE SECUENCIA:
    1. La conversación siempre empieza con el DevTaskPlannerAgent para analizar la tarea.
    2. Después del plan, el DevOpsAgent debe clonar el repositorio y crear la rama.
    3. Solo cuando el repositorio está listo, el CoderAgent puede implementar la solución.
    4. El CoderAgent debe implementar COMPLETAMENTE todas las partes de la solución antes de finalizar:
       - Crear la clase FancyDashboard
       - Implementar el método en IDashboardRepository
       - Implementar el método en DashboardRepository
       - Implementar el endpoint en DashboardController
       - Una vez completado, debe indicar "Task completed successfully!"
    5. Solo después de que el CoderAgent indique "Task completed successfully!", el DevOpsAgent debe hacer commit y push.
    6. Después del commit y push, el DevOpsAgent debe crear un pull request hacia la rama main.
    7. El DevOpsAgent debe indicar "Pull Request completed!" cuando termine el proceso completo.
    8. El Coordinator interviene cuando es necesario dirigir o corregir el flujo.
    9. La conversación solo finaliza cuando el DevOpsAgent indica "Pull Request completed!"
    
    ESTADO ACTUAL:
    {history}
    
    ÚLTIMAS ACCIONES:
    {roles}
    
    ACTORES DISPONIBLES:
    {participants}
    
    Basado en el estado actual y las reglas de secuencia, selecciona UN SOLO agente para el siguiente paso.
    """

    # Crear el grupo de chat con selector inteligente
    group_chat = SelectorGroupChat(
        participants=[coordinator, planner, devops, coder],
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

Seguiremos un flujo de trabajo estructurado donde:
1. El planificador analizará la tarea y creará un plan técnico
2. El equipo de DevOps clonará el repositorio y preparará el entorno
3. El equipo de desarrollo implementará el endpoint solicitado, que debe incluir:
   - Crear la clase FancyDashboard
   - Añadir el método necesario a IDashboardRepository
   - Implementar el método en DashboardRepository
   - Añadir el endpoint GetFancyDashboard al DashboardController
4. DevOps finalizará con commit, push de los cambios y creación de un pull request
5. El proceso completo termina cuando el pull request esté creado con éxito

DevTaskPlannerAgent, por favor comienza analizando la tarea y generando un plan estructurado.
"""
    
    # Ejecutar el chat y mostrar resultados
    await Console(
        group_chat.run_stream(
            task=initial_message
        )
    )

if __name__ == "__main__":
    asyncio.run(main())
