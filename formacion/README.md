# Formación — SecOps Hub

Material práctico del repositorio: notebooks Jupyter (automatización SOC) y guías Kali / LabEx.

## Objetivo general

1. Entender **cómo SecOps Hub usa Python** (ingesta → IOC → playbooks)
2. Montar **Kali Linux** en laboratorio autorizado
3. Resolver el catálogo de ejercicios **LabEx Kali** con plan y soluciones de estudio

## Requisitos (notebooks 01–03)

1. Extensión **Jupyter** en VS Code/Cursor (`ms-toolsai.jupyter`)
2. Python 3.11+

```powershell
cd formacion
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-notebooks.txt
```

Selecciona el kernel `.venv` de esta carpeta.

## Contenido de la carpeta `formacion/`

| # | Archivo | Tipo | Contenido |
|---|---------|------|-----------|
| — | `README.md` | Índice | Este fichero |
| — | `requirements-notebooks.txt` | Deps | Paquetes Python para notebooks |
| 01 | `01_python_automatizacion_secops.ipynb` | Notebook | Rol de Python, librerías, mapa de módulos |
| 02 | `02_enriquecimiento_ioc.ipynb` | Notebook | Detección/simulación IOC + gráficos |
| 03 | `03_pipeline_alerta_respuesta.ipynb` | Notebook | Alerta → incidente → playbook + métricas |
| 04 | `04_kali_linux_instalacion_uso.md` | Guía | Instalar y usar Kali en VM (ética, apt, nmap local) |
| 04 | `04_kali_linux_instalacion_uso.ipynb` | Notebook | Checklist de clase + clasificar IOC |
| 05 | `05_labex_kali_ejercicios.md` | Guía | Análisis LabEx, plan de realización, **soluciones** LX-01…15 |
| — | `entregas_kali/` | Local | Checklists del alumno (**no** versionado) |

### Orden recomendado

```text
01 → 02 → 03 → 04 (VM Kali) → 05 (ejercicios LabEx / equivalentes locales)
```

### Cómo se usa Python en SecOps Hub (resumen)

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

## Formación 04 — Kali Linux

Guía: [`04_kali_linux_instalacion_uso.md`](04_kali_linux_instalacion_uso.md).

## Formación 05 — LabEx Kali

Análisis del catálogo [labex.io/es/exercises/kali](https://labex.io/es/exercises/kali), cronograma, y soluciones LX-01…LX-15:

[`05_labex_kali_ejercicios.md`](05_labex_kali_ejercicios.md)

Solo laboratorio autorizado (LabEx, VM propia o red de aula).

## Relación con el código del repositorio

Los notebooks **01–03** reproducen lógica de:

- `backend/app/services/ioc_enrichment.py`
- `backend/app/services/ioc_service.py`
- `backend/app/routes/webhooks.py` (flujo conceptual)
- `backend/app/services/playbook_runners.py` (modo simulado)

Sin necesidad de arrancar Flask para las prácticas 01–03.

### Nota sobre la celda opcional del notebook 02

No uses `from app.services...` con el kernel de `formacion/.venv`: al importar el paquete `app` se carga Flask y fallará (`ModuleNotFoundError: flask_jwt_extended`).

El notebook carga `backend/app/services/ioc_enrichment.py` **como fichero** (via `importlib`).
