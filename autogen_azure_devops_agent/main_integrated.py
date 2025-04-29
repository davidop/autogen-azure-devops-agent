import os
import sys

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Use absolute imports for modules in the same package
from autogen_azure_devops_agent.agents.devopsAgent import create_devops_agent
from autogen_azure_devops_agent.agents.coderAgent import create_coder_agent
from autogen_azure_devops_agent.agents.architectAgent import create_architect_agent
from autogen_azure_devops_agent.agents.qaAgent import create_qa_agent
from autogen_azure_devops_agent.agents.securityAgent import create_security_agent
from autogen_azure_devops_agent.agents.databaseAgent import create_database_agent
from autogen_azure_devops_agent.agents.coordinatorAgent import create_coordinator_agent

from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.ui import Console

# Import basic tools
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

# Import new integrated pattern tools
from autogen_azure_devops_agent.tools.codeExecutionTools import execute_code_safely, execute_markdown_code
from autogen_azure_devops_agent.tools.reflectionTools import (
    create_code_implementation,
    create_code_review,
    create_architectural_review,
    create_quality_review,
    get_review_summary,
    reflection_cycle_needed
)
from autogen_azure_devops_agent.tools.handoffTools import (
    TaskStatus,
    AgentType,
    create_task_context,
    handoff_task,
    add_code_artifact,
    add_review_artifact,
    get_task_status_report
)

# Load environment variables
from dotenv import load_dotenv
load_dotenv(override=True)

# Debug: Print loaded variables to verify
print("Loaded environment variables:")
print(f"AZDO_PAT: {'Configured' if os.getenv('AZDO_PAT') else 'Not configured'}")
print(f"AZDO_ORG: {os.getenv('AZDO_ORG')}")
print(f"AZDO_PROJECT: {os.getenv('AZDO_PROJECT')}")
print(f"AZDO_REPO: {os.getenv('AZDO_REPO')}")

# Set required variables for DevOps tools
os.environ["AZDO_PAT"] = os.getenv("AZDO_PAT", "")
os.environ["AZDO_ORG"] = os.getenv("AZDO_ORG", "")
os.environ["AZDO_PROJECT"] = os.getenv("AZDO_PROJECT", "")
os.environ["AZDO_REPO"] = os.getenv("AZDO_REPO", "")
os.environ["REPO_PATH"] = "./repo_clonado"  # Local directory for repo cloning

# Set up model client
az_model_client = AzureOpenAIChatCompletionClient(
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY")
)

# Create enhanced tools for agents
def create_enhanced_agents(model_client):
    """
    Create agents with enhanced capabilities by integrating
    CodeExecution, Reflection, and Handoff patterns.
    """
    # Common tools for all agents
    common_tools = {
        # Handoff tools
        "create_task_context": create_task_context,
        "handoff_task": handoff_task,
        "get_task_status_report": get_task_status_report,
    }
    
    # Specific tools for each agent type
    coordinator_tools = {
        **common_tools,
    }
    
    architect_tools = {
        **common_tools,
        # Basic tools
        "explore_repository": explore_repository,
        "find_files": find_files,
        "read_file": read_file,
        # Reflection tools
        "create_architectural_review": create_architectural_review,
        # Code execution tools
        "execute_code_safely": execute_code_safely,
    }
    
    coder_tools = {
        **common_tools,
        # Basic tools
        "explore_repository": explore_repository,
        "find_files": find_files,
        "read_file": read_file,
        "write_file": write_file,
        "update_file": update_file,
        "insert_code_in_file": insert_code_in_file,
        "create_csharp_class": create_csharp_class,
        "implement_controller_endpoint": implement_controller_endpoint,
        "implement_repository_method": implement_repository_method,
        # Reflection tools
        "create_code_implementation": create_code_implementation,
        # Code execution tools
        "execute_code_safely": execute_code_safely,
        "execute_markdown_code": execute_markdown_code,
        # Artifact tools
        "add_code_artifact": add_code_artifact,
    }
    
    qa_tools = {
        **common_tools,
        # Basic tools
        "explore_repository": explore_repository,
        "find_files": find_files,
        "read_file": read_file,
        # Reflection tools
        "create_quality_review": create_quality_review,
        # Code execution tools
        "execute_code_safely": execute_code_safely,
        "execute_markdown_code": execute_markdown_code,
        # Artifact tools
        "add_review_artifact": add_review_artifact,
    }
    
    security_tools = {
        **common_tools,
        # Basic tools
        "explore_repository": explore_repository,
        "find_files": find_files,
        "read_file": read_file,
        # Artifact tools
        "add_review_artifact": add_review_artifact,
    }
    
    database_tools = {
        **common_tools,
        # Basic tools
        "explore_repository": explore_repository,
        "find_files": find_files,
        "read_file": read_file,
        # Artifact tools
        "add_review_artifact": add_review_artifact,
    }
    
    devops_tools = {
        **common_tools,
        # Basic DevOps tools
        "clone_repo": clone_repo, 
        "create_branch": create_branch, 
        "commit_and_push": commit_and_push,
        # Artifact tools
        "add_code_artifact": add_code_artifact,
    }
    
    # Create agents with enhanced tools
    coordinator = create_coordinator_agent(model_client)
    architect = create_architect_agent(model_client)
    coder = create_coder_agent(model_client)
    qa = create_qa_agent(model_client)
    security = create_security_agent(model_client)
    database = create_database_agent(model_client)
    devops = create_devops_agent(model_client)
    
    # Register functions with agents using llm_config approach
    # Set up a function registry for each agent
    coordinator._function_map = coordinator_tools
    architect._function_map = architect_tools
    coder._function_map = coder_tools
    qa._function_map = qa_tools
    security._function_map = security_tools
    database._function_map = database_tools
    devops._function_map = devops_tools
    
    return coordinator, architect, coder, qa, security, database, devops

# Create conversation flow
async def main():
    # Create enhanced agents
    coordinator, architect, coder, qa, security, database, devops = create_enhanced_agents(az_model_client)
    
    # Define termination conditions
    termination_condition = TextMentionTermination("Pull Request completed!")

    # Design a selector that controls workflow with integrated patterns
    selector_prompt = """
    Based on the description of the agents and the current context, select the most appropriate agent to handle the task.
    
    AGENTS:
    - Coordinator: Supervises the process and directs workflow, analyzes tasks and generates technical plans.
    - ArchitectAgent: Specialist in architecture design, design patterns and SOLID principles.
    - CoderAgent: Implements technical solutions in the codebase using various tools.
    - QAAgent: Focuses on quality, testing and validation of developed code.
    - SecurityAgent: Evaluates and mitigates security risks in code and architecture.
    - DatabaseAgent: Specialist in data modeling, query optimization and persistence structures.
    - DevOpsAgent: Manages Git operations in Azure DevOps, including cloning, branches, commits and pull requests.
    
    INTEGRATED PATTERNS:
    1. Handoff: Agents can transfer tasks between them using create_task_context and handoff_task
    2. Reflection: Agents can review code using create_code_implementation and create_architectural_review processes
    3. CodeExecution: Agents can execute code safely with execute_code_safely to test solutions
    
    SEQUENCE RULES:
    1. The conversation always starts with the Coordinator to analyze the task and create a plan.
    2. The Coordinator must create an initial task context with create_task_context.
    3. For tasks requiring architectural decisions, involve the ArchitectAgent after the initial plan.
    4. If there are data or persistence considerations, the DatabaseAgent should evaluate the approach.
    5. In case of tasks that may have security impact, consult the SecurityAgent.
    6. For repository changes, the DevOpsAgent must prepare the work environment.
    7. The CoderAgent implements solutions based on guidelines from the Architect and other specialists, using add_code_artifact.
    8. When the CoderAgent finishes, it must transfer the task to the ArchitectAgent for review with handoff_task.
    9. The ArchitectAgent MUST perform a formal review with create_architectural_review.
    10. After architectural review, transfer the task to the QAAgent for quality verification.
    11. The QAAgent must use create_quality_review to evaluate the implementation.
    12. If any review finds issues, it should be transferred to the CoderAgent for corrections.
    13. Only after complete approval, the DevOpsAgent makes commit and push.
    14. Finally, the DevOpsAgent must create a pull request and indicate "Pull Request completed!"
    15. The conversation only ends when the DevOpsAgent indicates "Pull Request completed!"
    
    CURRENT STATE:
    {history}
    
    LATEST ACTIONS:
    {roles}
    
    AVAILABLE ACTORS:
    {participants}
    
    Based on the current state and sequence rules, select ONE SINGLE agent for the next step.
    """

    # Create chat group with intelligent selector
    group_chat = SelectorGroupChat(
        participants=[coordinator, architect, coder, qa, security, database, devops],
        model_client=az_model_client,
        termination_condition=termination_condition,
        selector_prompt=selector_prompt
    )
    
    # Define the specific task for this example
    # This is just an example task, the system can process any type of request
    task = """
I want to introduce a new endpoint with its controller in the ProdwareAzureCopilot API.
The endpoint will be called GetFancyDashboard and should be included in the existing DashboardController.
The Repository is located in Repositories/General/DashboardRepository along with its interface IDashboardRepository.
We should create a FancyDashboard class for testing.
Clone the repository, create a feature/fancy-dashboard branch and publish it.
"""

    # Start the chat with a message that establishes context and sequence
    initial_message = f"""
We have the following development task:

{task}

This system of specialized agents can address various types of development tasks, including:
- Implementation of new features and components
- Bug fixing and problem resolution
- Optimization of existing code
- Refactoring and architecture improvement
- Integration of new technologies or libraries

For any task, we will follow a structured workflow using three key patterns:

1. HANDOFF: Agents will transfer tasks between them with full context
2. REFLECTION: Code review cycles will be implemented to ensure quality
3. CODE EXECUTION: Solutions will be tested in a safe environment before integration

The flow will adapt the following steps according to the task type:
1. Analysis and planning by the Coordinator
2. Architectural advice when necessary
3. Data and security analysis as appropriate
4. Environment preparation by DevOps
5. Implementation by the development team
6. Review and reflection cycles by specialists
7. Final delivery and deployment by DevOps

This process automatically adapts to the task type, omitting unnecessary stages depending on context.

Coordinator, please begin by analyzing the task and generating a structured plan with create_task_context.
"""
    
    # Run the chat and show results
    await Console(
        group_chat.run_stream(
            task=initial_message
        )
    )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())