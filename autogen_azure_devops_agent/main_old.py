import os
import asyncio
from dotenv import load_dotenv

from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import MaxMessageTermination
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

from autogen_azure_devops_agent.tools_old import (
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

# 🌍 Cargar entorno
load_dotenv()

# 🔐 Cliente de Azure OpenAI
az_model_client = AzureOpenAIChatCompletionClient(
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY")
)

# ✅ Verificar acceso al repositorio
print("\nChecking Azure DevOps configuration:")
print(f"Organization: {os.getenv('AZDO_ORG')}")
print(f"Project: {os.getenv('AZDO_PROJECT')}")
print(f"Repository: {os.getenv('AZDO_REPO')}")

if not verify_repo_access():
    raise ValueError("No se pudo acceder al repositorio de Azure DevOps")

# 🛠 Herramientas (funciones reales)
tools = [
    list_files,
    read_file,
    write_file,
    create_pull_request,
    clone_repo,
    create_branch,
    commit_and_push,
    search_code
]

# 🤖 Agentes
planner = AssistantAgent(
    name="planner",
    model_client=az_model_client,
    system_message="You are a technical project manager focused on analyzing and coordinating solutions for software bugs in C# and Blazor applications."
)

coder = AssistantAgent(
    name="coder",
    model_client=az_model_client,
    system_message="You are a C# and Blazor expert. Investigate and fix bugs in the codebase. Use tools as needed to search files and read content.",
    tools=tools
)

# 💬 Equipo de trabajo
team = RoundRobinGroupChat(
    [planner, coder],
    max_turns=10,
    termination_condition=MaxMessageTermination(10)
)

# 🚀 Conversación automatizada
async def main():
    task = f"""
Repositorio: {os.getenv('AZDO_REPO')}

Necesito investigar el Bug #123: Cuando un usuario sin rol hace login, la app se queda en blanco.
Sospechamos que el error ocurre en la navegación de Blazor, tras el refactor de roles.

Por favor:
- Busca archivos relacionados con autenticación o navegación.
- Analiza su contenido en busca de fallos relacionados con usuarios sin rol.
- Propón una causa raíz y una posible solución.
"""
    await Console(team.run_stream(task=task), output_stats=True)

if __name__ == "__main__":
    asyncio.run(main())
