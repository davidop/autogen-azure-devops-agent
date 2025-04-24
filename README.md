# Autogen Azure DevOps Agent (DevContainer)

Este proyecto implementa un agente de IA autónomo usando [Autogen de Microsoft](https://microsoft.github.io/autogen/), diseñado para leer y modificar código fuente en un repositorio alojado en Azure DevOps. El agente puede clonar el repo, navegar por el código, realizar cambios y crear Pull Requests automáticamente, todo desde un entorno de desarrollo reproducible con DevContainer.

---

## Características principales

- DevContainer listo para usar en VS Code o GitHub Codespaces.
- Agente multirol: Planner + Coder + Tool Agent (con funciones externas).
- Integración real con Azure DevOps para:
  - Clonado del repositorio.
  - Creación de ramas.
  - Commit y push de cambios.
  - Creación de Pull Requests.
- Manipulación directa del sistema de archivos.
- Uso de GPT-4 via OpenAI o Azure OpenAI.

---

## Requisitos

- Python 3.11+
- Docker
- VS Code con la extensión DevContainers **o** GitHub Codespaces
- Un Personal Access Token (PAT) de Azure DevOps con los permisos:
  - Code (Read & Write)
  - Work Items (Read)
  - Pull Requests (Read & Write)

---

## Configuración

1. **Clona este repositorio en tu entorno local o Codespace:**

   ```bash
   git clone https://github.com/tu-usuario/autogen-agent-dev.git
   cd autogen-agent-dev
   ```

2. **Abre el proyecto en VS Code y selecciona “Reabrir en contenedor”.**

3. **Configura tus variables de entorno:**

   - Crea un archivo `.env` o usa la configuración `remoteEnv` en `.devcontainer/devcontainer.json`.

   ```env
   AZDO_PAT=tu_token_azure_devops
   ```

4. **Instala las dependencias (se hace automáticamente):**

   ```bash
   pip install -r requirements.txt
   ```

---

## Uso

1. Asegúrate de definir en `tools.py` tus valores reales:

   ```python
   AZDO_ORG = "tu-org"
   AZDO_PROJECT = "tu-proyecto"
   AZDO_REPO = "tu-repo"
   ```

2. Ejecuta el agente:

   ```bash
   python autogen_agent/main.py
   ```

3. El agente iniciará una conversación entre:

   - `Planner`: analiza el bug.
   - `Coder`: navega por el repo usando `list_files`, `read_file`, etc.
   - El flujo termina generando un `pull request` real con los cambios sugeridos.

---

## Estructura del proyecto

```
.autogen-agent-dev/
├── .devcontainer/
│   ├── devcontainer.json
│   └── Dockerfile
├── autogen_agent/
│   ├── main.py
│   ├── tools.py
│   └── repositorio/        # Carpeta para el repo clonado
├── requirements.txt
└── README.md
```

---

## Extensiones futuras

- Indexación con embeddings para navegar repos grandes.
- Integración con Azure Cognitive Search.
- Validación automática con test suites.
- Feedback loop con PR reviewer basado en IA.

---

## Licencia

MIT

---

## Contacto

Desarrollado por David Oliva. Para soporte o mejoras, abre un issue o pull request en GitHub.