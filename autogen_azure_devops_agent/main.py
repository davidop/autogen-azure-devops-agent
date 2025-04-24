import os
from dotenv import load_dotenv
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

from azure.core.credentials import AzureKeyCredential
import asyncio
 
from dotenv import load_dotenv
from tools import (
    list_files, 
    read_file, 
    write_file, 
    create_pull_request, 
    clone_repo, 
    create_branch, 
    commit_and_push, 
    verify_repo_access,
    search_code
)

# Load environment variables
load_dotenv()

az_model_client = AzureOpenAIChatCompletionClient(
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY")
    )

AZDO_ORG = os.getenv("AZDO_ORG")
AZDO_PROJECT = os.getenv("AZDO_PROJECT")
AZDO_REPO = os.getenv("AZDO_REPO")
AZDO_URL = os.getenv("AZDO_URL")


# Add Azure DevOps configuration check
print("\nChecking Azure DevOps configuration:")
print(f"Organization: {os.getenv('AZDO_ORG')}")
print(f"Project: {os.getenv('AZDO_PROJECT')}")
print(f"Repository: {os.getenv('AZDO_REPO')}")

# Verificar acceso al repositorio antes de configurar las herramientas
if not verify_repo_access():
    raise ValueError("No se pudo acceder al repositorio de Azure DevOps")

# Herramientas del agente
tools = [
    {
        "name": "list_files",
        "func": list_files,
        "description": "Lista los archivos en un directorio"
    },
    {
        "name": "read_file",
        "func": read_file,
        "description": "Lee el contenido de un archivo"
    },
    {
        "name": "write_file",
        "func": write_file,
        "description": "Escribe contenido en un archivo"
    },
    {
        "name": "create_pull_request",
        "func": create_pull_request,
        "description": "Crea un pull request"
    },
    {
        "name": "clone_repo",
        "func": clone_repo,
        "description": "Clona un repositorio"
    },
    {
        "name": "create_branch",
        "func": create_branch,
        "description": "Crea una rama nueva"
    },
    {
        "name": "commit_and_push",
        "func": commit_and_push,
        "description": "Realiza commit y push de los cambios"
    }
]

# Add to existing tools list
tools.extend([
    {
        "name": "search_code",
        "func": search_code,
        "description": "Busca código en el repositorio de Azure DevOps"
    }
])

# Agentes
planner = AssistantAgent(
    name="planner", 
    client=az_model_client,
    system_message="You are a project manager and software architect. Help plan the development of a new feature in a C# and Blazor application. "
)

coder = AssistantAgent(
    name="coder",
    system_message="""You are a C# and Blazor expert. Help investigate and fix bugs in the codebase.
    First search for relevant files, then analyze them for potential issues.""",
    client=az_model_client
)

user_proxy = UserProxyAgent(name="user", human_input_mode="NEVER")

# Flujo de conversación
groupchat = GroupChat(agents=[user_proxy, planner, coder], messages=[], max_round=10)

# Update manager configuration to use Azure deployment
manager = GroupChatManager(
    groupchat=groupchat,
    client=az_model_client
)

# Bug como entrada
user_proxy.initiate_chat(manager, message="""
Bug #123: Cuando un usuario sin rol hace login, la app se queda en blanco.
Sospechamos que ocurre en la navegación Blazor tras el refactor de roles.
""")

async def main():
    question = input("Que historia quieres que te cuente hoy: ")
    await Console(team.run_stream(task=question))
 
 
# Run the asynchronous function
if __name__ == "__main__":
    asyncio.run(main())