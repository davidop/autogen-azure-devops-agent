import asyncio
import os
from dotenv import load_dotenv
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

from autogen_agentchat.agents import UserProxyAgent
from autogen_azure_devops_agent.agents.devopsAgent import create_devops_agent
from autogen_azure_devops_agent.agents.coderAgent import create_coder_agent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.ui import Console

# Tools
from autogen_azure_devops_agent.tools.devopsTools import clone_repo, create_branch, commit_and_push

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

# Crear agentes
devops = create_devops_agent(az_model_client)
coder = create_coder_agent(az_model_client)

# Crear el flujo de conversación
async def main():
    # Crear el UserProxyAgent siguiendo el ejemplo que funciona
    user_proxy = UserProxyAgent(name="user")
    
    # Definir condiciones de terminación
    text_mention_termination = TextMentionTermination("TERMINATE")
    max_messages_termination = MaxMessageTermination(max_messages=30)  # Aumentado para permitir más interacciones
    termination = text_mention_termination | max_messages_termination
    
    # Crear el RoundRobinGroupChat con el formato del ejemplo que funciona
    group_chat = RoundRobinGroupChat(
        [user_proxy, devops, coder],  # Orden: usuario → devops → coder → usuario → ...
        max_turns=15,  # Aumentado para permitir más interacciones
        termination_condition=termination,
    )
    
    # Usar Console para mostrar la conversación como en el ejemplo que funciona
    await Console(
        group_chat.run_stream(
            task="""
Tenemos un bug en el repositorio Next.Frontend.apps. 
Cuando un usuario sin rol hace login, la app se queda en blanco.
Sospechamos que es por la navegación. 
Clona el repositorio, crea una rama y analiza el código para corregir el bug.

Flujo de trabajo:
1. El agente DevOps clonará el repositorio y creará una rama para la corrección
2. El agente Coder analizará el código, encontrará la causa del error y lo corregirá
3. El agente DevOps realizará commit y push de los cambios
"""
        )
    )  # Stream the messages to the console.

if __name__ == "__main__":
    asyncio.run(main())
