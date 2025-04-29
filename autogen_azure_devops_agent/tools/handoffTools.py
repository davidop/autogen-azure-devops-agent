from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json
import datetime
from enum import Enum

class TaskStatus(Enum):
    """Estados posibles de una tarea."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"

class AgentType(Enum):
    """Tipos de agentes en el sistema."""
    COORDINATOR = "Coordinator"
    ARCHITECT = "ArchitectAgent"
    CODER = "CoderAgent"
    QA = "QAAgent"
    SECURITY = "SecurityAgent"
    DATABASE = "DatabaseAgent"
    DEVOPS = "DevOpsAgent"

@dataclass
class TaskContext:
    """
    Representa el contexto completo de una tarea para transferir entre agentes.
    """
    task_id: str
    title: str
    description: str
    status: TaskStatus
    assigned_to: AgentType
    previous_agent: Optional[AgentType]
    created_at: str
    updated_at: str
    artifacts: Dict[str, Any]
    history: List[Dict[str, Any]]
    metadata: Dict[str, Any]

def create_task_context(
    title: str,
    description: str,
    assigned_to: AgentType,
    artifacts: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Crea un nuevo contexto de tarea para iniciar un flujo de trabajo.
    
    Args:
        title: Título de la tarea
        description: Descripción detallada de la tarea
        assigned_to: Agente al que se asigna inicialmente la tarea
        artifacts: Artefactos iniciales asociados a la tarea (opcional)
        metadata: Metadatos adicionales de la tarea (opcional)
        
    Returns:
        Diccionario con el contexto de tarea completo
    """
    now = datetime.datetime.now().isoformat()
    task_id = f"task_{now.replace(':', '').replace('.', '')}"
    
    context = TaskContext(
        task_id=task_id,
        title=title,
        description=description,
        status=TaskStatus.PENDING,
        assigned_to=assigned_to,
        previous_agent=None,
        created_at=now,
        updated_at=now,
        artifacts=artifacts or {},
        history=[],
        metadata=metadata or {}
    )
    
    # Convertir a diccionario para facilitar la serialización
    return {
        "task_id": context.task_id,
        "title": context.title,
        "description": context.description,
        "status": context.status.value,
        "assigned_to": context.assigned_to.value,
        "previous_agent": context.previous_agent.value if context.previous_agent else None,
        "created_at": context.created_at,
        "updated_at": context.updated_at,
        "artifacts": context.artifacts,
        "history": context.history,
        "metadata": context.metadata
    }

def handoff_task(
    task_context: Dict[str, Any],
    to_agent: AgentType,
    status: TaskStatus = TaskStatus.IN_PROGRESS,
    artifacts_update: Optional[Dict[str, Any]] = None,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Transfiere una tarea de un agente a otro, actualizando su contexto.
    
    Args:
        task_context: El contexto actual de la tarea
        to_agent: El agente al que se transfiere la tarea
        status: El nuevo estado de la tarea (por defecto: IN_PROGRESS)
        artifacts_update: Actualización de artefactos a añadir al contexto
        notes: Notas sobre la transferencia
        
    Returns:
        Contexto actualizado de la tarea
    """
    now = datetime.datetime.now().isoformat()
    from_agent = AgentType(task_context["assigned_to"])
    
    # Crear registro histórico de la transferencia
    history_entry = {
        "timestamp": now,
        "action": "handoff",
        "from_agent": from_agent.value,
        "to_agent": to_agent.value,
        "status_change": f"{task_context['status']} -> {status.value}",
        "notes": notes or "Transferencia estándar de tarea"
    }
    
    # Actualizar artefactos si se proporcionan
    updated_artifacts = task_context["artifacts"].copy()
    if artifacts_update:
        updated_artifacts.update(artifacts_update)
    
    # Actualizar el contexto de la tarea
    updated_context = task_context.copy()
    updated_context.update({
        "status": status.value,
        "assigned_to": to_agent.value,
        "previous_agent": from_agent.value,
        "updated_at": now,
        "artifacts": updated_artifacts,
        "history": task_context["history"] + [history_entry]
    })
    
    return updated_context

def add_code_artifact(
    task_context: Dict[str, Any],
    code: str,
    file_path: str,
    description: str,
    agent: Optional[AgentType] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Añade un artefacto de código al contexto de una tarea.
    
    Args:
        task_context: El contexto actual de la tarea
        code: El código a añadir
        file_path: La ruta del archivo asociado
        description: Descripción del código
        agent: El agente que añade el artefacto (opcional, se toma del asignado)
        metadata: Metadatos adicionales del artefacto
        
    Returns:
        Contexto actualizado de la tarea
    """
    now = datetime.datetime.now().isoformat()
    agent_name = agent.value if agent else task_context["assigned_to"]
    
    artifact_id = f"code_{len([k for k in task_context['artifacts'].keys() if k.startswith('code_')])}"
    
    # Crear el artefacto
    code_artifact = {
        "type": "code",
        "content": code,
        "file_path": file_path,
        "description": description,
        "created_by": agent_name,
        "created_at": now,
        "metadata": metadata or {}
    }
    
    # Crear registro histórico
    history_entry = {
        "timestamp": now,
        "action": "add_artifact",
        "agent": agent_name,
        "artifact_id": artifact_id,
        "artifact_type": "code",
        "file_path": file_path
    }
    
    # Actualizar el contexto de la tarea
    updated_context = task_context.copy()
    updated_artifacts = task_context["artifacts"].copy()
    updated_artifacts[artifact_id] = code_artifact
    
    updated_context.update({
        "artifacts": updated_artifacts,
        "updated_at": now,
        "history": task_context["history"] + [history_entry]
    })
    
    return updated_context

def add_review_artifact(
    task_context: Dict[str, Any],
    review_data: Dict[str, Any],
    related_artifact_id: str,
    agent: Optional[AgentType] = None
) -> Dict[str, Any]:
    """
    Añade un artefacto de revisión al contexto de una tarea.
    
    Args:
        task_context: El contexto actual de la tarea
        review_data: Datos de la revisión
        related_artifact_id: ID del artefacto que se está revisando
        agent: El agente que añade la revisión (opcional, se toma del asignado)
        
    Returns:
        Contexto actualizado de la tarea
    """
    now = datetime.datetime.now().isoformat()
    agent_name = agent.value if agent else task_context["assigned_to"]
    
    artifact_id = f"review_{len([k for k in task_context['artifacts'].keys() if k.startswith('review_')])}"
    
    # Crear el artefacto de revisión
    review_artifact = {
        "type": "review",
        "review_data": review_data,
        "related_artifact_id": related_artifact_id,
        "created_by": agent_name,
        "created_at": now
    }
    
    # Crear registro histórico
    history_entry = {
        "timestamp": now,
        "action": "add_review",
        "agent": agent_name,
        "artifact_id": artifact_id,
        "related_artifact_id": related_artifact_id
    }
    
    # Actualizar el contexto de la tarea
    updated_context = task_context.copy()
    updated_artifacts = task_context["artifacts"].copy()
    updated_artifacts[artifact_id] = review_artifact
    
    updated_context.update({
        "artifacts": updated_artifacts,
        "updated_at": now,
        "history": task_context["history"] + [history_entry]
    })
    
    return updated_context

def get_task_status_report(task_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Genera un informe de estado de la tarea basado en su contexto.
    
    Args:
        task_context: El contexto actual de la tarea
        
    Returns:
        Un diccionario con el informe de estado
    """
    code_artifacts = [a for k, a in task_context["artifacts"].items() if a["type"] == "code"]
    review_artifacts = [a for k, a in task_context["artifacts"].items() if a["type"] == "review"]
    
    last_update = task_context["updated_at"]
    duration = (datetime.datetime.fromisoformat(last_update) - 
               datetime.datetime.fromisoformat(task_context["created_at"])).total_seconds() / 60.0
    
    # Analizar la secuencia de agentes
    agent_sequence = []
    for entry in task_context["history"]:
        if entry["action"] == "handoff":
            agent_sequence.append(f"{entry['from_agent']} → {entry['to_agent']}")
    
    return {
        "task_id": task_context["task_id"],
        "title": task_context["title"],
        "status": task_context["status"],
        "current_agent": task_context["assigned_to"],
        "duration_minutes": round(duration, 2),
        "artifact_counts": {
            "code": len(code_artifacts),
            "review": len(review_artifacts),
            "total": len(task_context["artifacts"])
        },
        "agent_sequence": agent_sequence,
        "history_length": len(task_context["history"])
    }