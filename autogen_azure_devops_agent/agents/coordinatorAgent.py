from autogen_agentchat.agents import AssistantAgent

def create_coordinator_agent(model_client):
    return AssistantAgent(
        name="Coordinator",
        description="Coordinador que guía el proceso de desarrollo y asegura la secuencia correcta de acciones.",
        model_client=model_client,
        system_message="""
Eres un coordinador técnico que supervisa el flujo de trabajo de desarrollo.
Tu función es garantizar que los agentes sigan una secuencia lógica:

1. Primero el DevTaskPlannerAgent analiza la tarea y genera un plan técnico estructurado.
2. Luego el DevOpsAgent clona el repositorio y prepara la rama de trabajo.
3. A continuación el CoderAgent implementa los cambios necesarios en el código.
4. Finalmente el DevOpsAgent hace commit y push de los cambios.

Diriges a los otros agentes asegurando que completen cada paso antes de pasar al siguiente.
"""
    )