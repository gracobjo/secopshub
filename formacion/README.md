# Formación — Python para automatización SOC (SecOps Hub)

Material práctico para ejecutar en **VS Code / Cursor** con Jupyter.

## Objetivo

Entender **cómo SecOps Hub usa Python** para automatizar operaciones de ciberseguridad:

1. Ingesta de alertas (webhook SIEM)
2. Triaje / enriquecimiento de IOCs
3. Orquestación de respuesta (playbooks)
4. Métricas y visualización de resultados

## Requisitos

1. Extensión **Jupyter** en VS Code/Cursor (`ms-toolsai.jupyter`)
2. Python 3.11+ (puedes usar el venv del backend)

```powershell
cd formacion
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-notebooks.txt
```

En VS Code: selecciona el kernel `.venv` de esta carpeta (o el de `backend/venv` tras instalar las deps de notebooks).

## Notebooks

| # | Archivo | Contenido |
|---|---------|-----------|
| 01 | `01_python_automatizacion_secops.ipynb` | Rol de Python, librerías del proyecto, mapa de módulos |
| 02 | `02_enriquecimiento_ioc.ipynb` | Código real de detección/simulación IOC + gráficos |
| 03 | `03_pipeline_alerta_respuesta.ipynb` | Pipeline alerta → incidente → playbook + métricas |

Ejecuta las celdas **en orden** (`Shift+Enter`).

## Cómo se usa Python en SecOps Hub (resumen)

| Operación SOC | Módulo Python | Librerías clave |
|---------------|---------------|-----------------|
| API REST / auth | `app/routes/*`, JWT | `flask`, `flask-jwt-extended`, `werkzeug` |
| Webhook SIEM | `routes/webhooks.py` | `flask`, SQLAlchemy |
| Enriquecimiento IOC | `ioc_enrichment.py`, `ioc_service.py`, `external_clients.py` | `hashlib`, `re`, `requests` |
| Playbooks | `playbook_runners.py` | `requests` |
| Threat intel live | `external_clients.py` | `requests` |
| MFA | `routes/auth.py` | `pyotp` |
| LDAP / OIDC | `ldap_auth.py`, `oidc_auth.py` | `ldap3`, `requests` |
| Informes PDF | `pdf_report.py` | `reportlab` |
| Métricas | `metrics.py` | `prometheus_client` |
| BD / migraciones | modelos + Alembic | `flask-sqlalchemy`, `psycopg`, `alembic` |

SecOps Hub **no sustituye** SIEM/EDR: Python orquesta la consola (ingesta → triaje → respuesta).

## Relación con el código del repositorio

Los notebooks **reproducen la lógica esencial** de:

- `backend/app/services/ioc_enrichment.py`
- `backend/app/services/ioc_service.py`
- `backend/app/routes/webhooks.py` (flujo conceptual)
- `backend/app/services/playbook_runners.py` (modo simulado)

Sin necesidad de arrancar Flask para las prácticas 01–03.
