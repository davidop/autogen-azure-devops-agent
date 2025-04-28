import asyncio
import os
from dotenv import load_dotenv
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

# Importar todos los agentes especializados
from autogen_azure_devops_agent.agents.devopsAgent import create_devops_agent
from autogen_azure_devops_agent.agents.coderAgent import create_coder_agent
from autogen_azure_devops_agent.agents.coordinatorAgent import create_coordinator_agent
from autogen_azure_devops_agent.agents.architectAgent import create_architect_agent
from autogen_azure_devops_agent.agents.qaAgent import create_qa_agent
from autogen_azure_devops_agent.agents.securityAgent import create_security_agent
from autogen_azure_devops_agent.agents.databaseAgent import create_database_agent
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

# Crear todos los agentes especializados
devops = create_devops_agent(az_model_client)
coder = create_coder_agent(az_model_client)
coordinator = create_coordinator_agent(az_model_client)
architect = create_architect_agent(az_model_client)
qa = create_qa_agent(az_model_client)
security = create_security_agent(az_model_client)
database = create_database_agent(az_model_client)

# Crear el flujo de conversación
async def main():
    
    # Definir condiciones de terminación
    termination_condition = TextMentionTermination("Pull Request completed!")

    # Diseño de un selector que controla el flujo de trabajo con todos los agentes especializados
    selector_prompt = """
    Basado en la descripción de los agentes y el contexto actual, selecciona el agente más apropiado para manejar la tarea.
    
    AGENTES:
    - Coordinator: Supervisa el proceso y dirige el flujo de trabajo, analiza tareas y genera planes técnicos.
    - ArchitectAgent: Especialista en diseño de arquitectura, patrones de diseño y principios SOLID.
    - CoderAgent: Implementa soluciones técnicas en el código base usando diversas herramientas.
    - QAAgent: Se enfoca en calidad, pruebas y validación del código desarrollado.
    - SecurityAgent: Evalúa y mitiga riesgos de seguridad en el código y la arquitectura.
    - DatabaseAgent: Especialista en modelado de datos, optimización de consultas y estructuras de persistencia.
    - DevOpsAgent: Gestiona operaciones Git en Azure DevOps, incluyendo clonación, ramas, commits y pull requests.
    
    REGLAS DE SECUENCIA:
    1. La conversación siempre empieza con el Coordinator para analizar la tarea y crear un plan.
    2. Para tareas que requieran decisiones arquitectónicas, involucra al ArchitectAgent después del plan inicial.
    3. Si hay consideraciones de datos o persistencia, el DatabaseAgent debe evaluar el enfoque.
    4. En caso de nuevas funcionalidades que puedan tener impacto en seguridad, consulta al SecurityAgent.
    5. Para cambios en repositorios, el DevOpsAgent debe preparar el entorno de trabajo.
    6. El CoderAgent implementa soluciones basadas en directrices del Architect y otros especialistas.
    7. Cuando el CoderAgent indique que ha completado la implementación, el ArchitectAgent DEBE realizar una revisión formal del código para verificar que cumple con los patrones de diseño y principios arquitectónicos establecidos.
    8. Después de la aprobación del ArchitectAgent, el QAAgent debe verificar que el código cumpla requisitos y buenas prácticas de calidad.
    9. Si el ArchitectAgent o QAAgent encuentran problemas, el CoderAgent debe realizar las correcciones necesarias y volver a solicitar revisión.
    10. El CoderAgent debe implementar COMPLETAMENTE todas las partes de la solución antes de finalizar e indicar "Task completed successfully!"
    11. Solo después de la aprobación del ArchitectAgent y QAAgent, el DevOpsAgent hace commit y push.
    12. Finalmente, el DevOpsAgent debe crear un pull request e indicar "Pull Request completed!"
    13. El Coordinator interviene cuando es necesario dirigir o corregir el flujo.
    14. La conversación solo finaliza cuando el DevOpsAgent indica "Pull Request completed!"
    
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
        participants=[coordinator, architect, coder, qa, security, database, devops],
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

Seguiremos un flujo de trabajo estructurado donde participarán varios especialistas:

1. El Coordinator analizará la tarea y creará un plan técnico
2. El Arquitecto evaluará y propondrá el diseño apropiado para el nuevo endpoint
3. El especialista en Bases de Datos analizará el modelo de datos necesario
4. El especialista en Seguridad evaluará consideraciones de seguridad relevantes
5. El equipo de DevOps clonará el repositorio y preparará el entorno
6. El equipo de desarrollo implementará el endpoint solicitado, incluyendo:
   - Crear la clase FancyDashboard
   - Añadir el método necesario a IDashboardRepository
   - Implementar el método en DashboardRepository
   - Añadir el endpoint GetFancyDashboard al DashboardController
7. El Arquitecto revisará el código para asegurar que sigue los patrones y principios arquitectónicos
8. El equipo de QA verificará la calidad y cobertura de pruebas
9. DevOps finalizará con commit, push de los cambios y creación de un pull request

Coordinator, por favor comienza analizando la tarea y generando un plan estructurado.
"""
    
    # Ejecutar el chat y mostrar resultados
    await Console(
        group_chat.run_stream(
            task=initial_message
        )
    )

if __name__ == "__main__":
    asyncio.run(main())
