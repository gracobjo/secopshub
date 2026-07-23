# Documentación SecOps Hub

Índice central de la documentación del proyecto.

| Documento | Descripción | Audiencia |
|-----------|-------------|-----------|
| [Contexto formativo](proyecto-institucional.md) | Objetivos educativos del prototipo SOC | Todos, formadores |
| [Manual de usuario](manual-usuario.md) | Guía de uso de la consola SOC | Analistas, administradores |
| [Manual de laboratorio](manual-laboratorio.md) | Ejercicios prácticos paso a paso (uso de la consola) | Estudiantes, formación SOC |
| [Laboratorio de infraestructura](laboratorio-infraestructura.md) | Montar desde cero Hub + SIEM lab (Wazuh) + webhook sin stack corporativo | DevSecOps, formadores |
| [Manual de desarrollador](manual-desarrollador.md) | Arquitectura, API, despliegue y convenciones | Desarrolladores |
| [Requisitos](requisitos.md) | Requisitos funcionales y no funcionales | Producto, QA, desarrollo |
| [Casos de uso](casos-de-uso.md) | Casos de uso, flujos e implementación | Analistas, desarrolladores |
| [Diagramas UML](diagramas-uml.md) | Diagramas de casos de uso, clases, secuencia, componentes, despliegue, actividad y ERD | Arquitectos, desarrolladores |
| [Integración en red](integracion-red.md) | Conectar Splunk, QRadar, firewall y EDR | SOC, DevSecOps, administradores |
| [Diagrama flujo de red](flujo_red_secops_hub.svg) | Cuatro direcciones de comunicación en red corporativa | Arquitectos, SOC |
| [Roadmap de integración](roadmap-integracion.md) | Evolución simulado → producción por fases | DevSecOps, arquitectos |
| [Threat intel](threat-intel.md) | AbuseIPDB/VirusTotal: claves, cuotas y buenas prácticas | SOC, DevSecOps |
| [Runbook operativo](runbook-operacion.md) | Docker, MFA, LDAP, rotación webhook, métricas | SOC, DevSecOps |
| [Despliegue producción](../deploy/README.md) | Nginx/Caddy, Gunicorn, TLS, firewall | DevSecOps, sysadmins |
| [Diccionario de términos](diccionario.md) | Glosario SOC, técnico y de productos | Todos |
| [Ejemplos prácticos y casos de prueba](ejemplos-practicos.md) | Escenarios SOC ejecutables y matriz TC-01–TC-15 | Formación, QA |

## Acceso rápido

- **Aplicación (desarrollo):** http://localhost:5173
- **API + build estático:** http://localhost:5000
- **Credenciales demo:** `admin` / `admin123` · `analyst` / `analyst123` (solo con `ENABLE_SEED=true`)
- **Producción sin seed:** `BOOTSTRAP_ADMIN_*` o `python scripts/create_admin.py`
