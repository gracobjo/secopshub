# Guía de carpetas del proyecto (lenguaje sencillo)

Este documento explica **qué hay dentro de cada carpeta** de SecOps Hub **sin asumir conocimientos de informática**.

Piensa en el proyecto como un **edificio de un centro de seguridad**:

| Analogía | Carpetas |
|----------|----------|
| La **oficina donde trabajan los analistas** (pantallas, botones, gráficos) | `frontend/` |
| El **cerebro / archivo / centralita** que procesa alertas y decide | `backend/` |
| El **manual de instrucciones** del edificio | `docs/` |
| El **aula de formación** con ejercicios prácticos | `formacion/` |
| Los **planos de instalación** (cómo montarlo en un servidor real) | `deploy/` |
| Las **herramientas auxiliares** (scripts de apoyo) | `scripts/` |

---

## Vista rápida de la raíz del proyecto

```
secopsHub/
├── frontend/     → Lo que se ve en el navegador (la consola)
├── backend/      → La lógica y los datos (Python)
├── docs/         → Documentación y manuales
├── formacion/    → Clases prácticas con notebooks
├── deploy/       → Cómo instalarlo en producción
├── scripts/      → Utilidades de prueba / apoyo
├── README.md     → Puerta de entrada del proyecto
└── docker-compose.yml → Receta para arrancar todo junto (opcional)
```

---

## 1. `frontend/` — La pantalla (lo que usa el analista)

**En una frase:** es la **aplicación web** que abren los analistas en el navegador (dashboard, IOCs, vulnerabilidades, playbooks).

| Subcarpeta / elemento | Qué es (en lenguaje sencillo) |
|-----------------------|-------------------------------|
| `src/` | El “diseño y comportamiento” de las pantallas (botones, menús, gráficos). |
| `src/pages/` | Cada **página** de la consola (Login, Dashboard, IOCs…). |
| `src/components/` | Piezas reutilizables (menú lateral, ventanas emergentes…). |
| `public/` | Archivos estáticos (por ejemplo el icono / favicon). |
| `Dockerfile` / `nginx.conf` | Instrucciones para empaquetar y servir la web en un servidor. |

**¿Quién la usa?** Analistas y administradores (usuarios finales).  
**¿Hay que tocarla a diario?** No, solo si se cambia la interfaz.

---

## 2. `backend/` — El cerebro (lo que hace el trabajo)

**En una frase:** es el **servidor escrito en Python** que recibe alertas, guarda incidentes, enriquece indicadores y ejecuta playbooks.

| Subcarpeta / elemento | Qué es (en lenguaje sencillo) |
|-----------------------|-------------------------------|
| `app/` | El núcleo de la aplicación. |
| `app/routes/` | Las “ventanillas” o puertas de entrada (login, alertas, IOCs…). Cada una atiende un tipo de petición. |
| `app/services/` | La **lógica de negocio**: enriquecer IOCs, lanzar playbooks, métricas, LDAP… |
| `app/models/` | Cómo se organizan los **datos** (usuarios, incidentes, vulnerabilidades…). |
| `migrations/` | Historial de cambios en la base de datos (como versiones del archivo). |
| `tests/` | Pruebas automáticas para comprobar que no se rompe lo importante. |
| `scripts/` | Utilidades del servidor (p. ej. crear el primer administrador). |
| `requirements.txt` | Lista de **librerías Python** que necesita el proyecto. |
| `.env.example` | Plantilla de secretos y configuración (claves, base de datos…). |

**¿Quién la usa?** Desarrolladores y, indirectamente, todo el mundo (sin backend no hay consola útil).  
**Analogía:** si el frontend es el mostrador de un banco, el backend es la caja fuerte y el personal que procesa las solicitudes.

---

## 3. `docs/` — Los manuales y la documentación

**En una frase:** aquí está **toda la documentación**: cómo usar la consola, cómo conectarla a la red, glosario, diagramas, etc.

| Documento / tipo | Para qué sirve | ¿Para quién? |
|------------------|----------------|--------------|
| `manual-usuario.md` | Cómo manejar la consola día a día | Analistas, admins |
| `manual-laboratorio.md` | Ejercicios paso a paso en aula | Estudiantes |
| `laboratorio-infraestructura.md` | Montar un lab completo (Hub + SIEM de práctica) | Formadores, técnicos |
| `manual-desarrollador.md` | Cómo está construido el software | Desarrolladores |
| `diccionario.md` | Glosario de términos (SIEM, IOC, firewall…) | **Todos** |
| `integracion-red.md` | Cómo conectar Splunk, firewall, EDR… | Equipos de seguridad |
| `infraestructura_red_secops_hub.svg` | **Dibujo** de Internet / perímetro / LAN | Todos (visual) |
| `flujo_red_secops_hub.svg` | **Dibujo** de cómo habla el Hub con SIEM/EDR | Todos (visual) |
| `proyecto-institucional.md` | Contexto formativo del prototipo | Formadores, dirección |
| `roadmap-integracion.md` | Plan por fases (qué falta por conectar) | Coordinación técnica |
| `README.md` (dentro de docs) | Índice de toda la documentación | Todos |

**Consejo:** si no eres técnico, empieza por el **diccionario**, el **manual de usuario** y los **diagramas SVG**.

---

## 4. `formacion/` — El aula práctica (notebooks)

**En una frase:** material de **clase** para aprender cómo Python automatiza ciberseguridad, con ejercicios que se ejecutan celda a celda.

| Archivo | Qué aprenderás |
|---------|----------------|
| `01_python_automatizacion_secops.ipynb` | Qué librerías usa el proyecto y para qué |
| `02_enriquecimiento_ioc.ipynb` | Cómo se analiza un indicador (IP, hash…) y se puntúa el riesgo |
| `03_pipeline_alerta_respuesta.ipynb` | De la alerta al playbook (bloqueo, aislamiento…) con gráficos |
| `README.md` | Cómo instalar el entorno y abrir los notebooks |
| `requirements-notebooks.txt` | Lista de paquetes necesarios solo para la formación |

**¿Quién la usa?** Alumnado y profesorado.  
**No es** la aplicación en producción: es el **cuaderno de prácticas**.

---

## 5. `deploy/` — Cómo instalarlo “de verdad”

**En una frase:** instrucciones y ficheros para **poner SecOps Hub en un servidor** de la empresa (HTTPS, proxy, métricas…).

| Subcarpeta | Qué contiene |
|------------|--------------|
| `nginx/` | Configuración del “portero” web (HTTPS, reenvío a la API). |
| `caddy/` | Alternativa al portero anterior (también con certificados). |
| `systemd/` | Cómo arrancar el servicio al encender el servidor. |
| `prometheus/` / `grafana/` | Monitorización (gráficas de salud del sistema). |
| `scripts/` | Scripts para compilar / preparar la instalación. |
| `README.md` | Guía paso a paso de despliegue. |

**¿Quién la usa?** Administradores de sistemas / DevSecOps.  
**Analogía:** planos de fontanería y electricidad del edificio, no las oficinas.

---

## 6. `scripts/` (en la raíz)

**En una frase:** utilidades sueltas de apoyo (por ejemplo scripts de prueba de escenarios).

No es el núcleo del producto; son **ayudas** para laboratorios o demos.

---

## 7. Archivos importantes en la raíz (no son carpetas)

| Archivo | Qué es |
|---------|--------|
| `README.md` | Presentación general del proyecto (lo primero que se lee en GitHub). |
| `docker-compose.yml` | “Receta” para levantar varios servicios juntos (base de datos, API, web…). |
| `.env.docker.example` | Ejemplo de variables secretas para Docker (hay que copiarlo y cambiar valores). |
| `.gitignore` | Lista de cosas que **no** se suben a GitHub (contraseñas locales, carpetas temporales…). |

---

## Mapa “¿Qué abro según mi rol?”

| Si eres… | Empieza por… |
|----------|--------------|
| Dirección / no técnico | Este documento + `docs/proyecto-institucional.md` + diagramas SVG |
| Analista SOC | `docs/manual-usuario.md` + la aplicación web (`frontend`) |
| Estudiante | `formacion/` + `docs/manual-laboratorio.md` + `docs/diccionario.md` |
| Formador | `docs/` + `formacion/` + `docs/laboratorio-infraestructura.md` |
| Desarrollador | `backend/` + `frontend/` + `docs/manual-desarrollador.md` |
| Admin de sistemas | `deploy/` + `docker-compose.yml` |

---

## Resumen en una frase por carpeta

| Carpeta | Una frase |
|---------|-----------|
| **frontend** | La consola que se ve en el navegador. |
| **backend** | El motor Python que procesa alertas y respuestas. |
| **docs** | Todos los manuales, glosarios y diagramas. |
| **formacion** | Ejercicios de clase con notebooks Jupyter. |
| **deploy** | Cómo instalarlo en un servidor corporativo. |
| **scripts** | Herramientas auxiliares de prueba. |

---

## Relación entre carpetas (visión simple)

```
  [ Analista abre el navegador ]
              |
              v
         frontend/     ← pantallas
              |
              v
          backend/     ← decide, guarda, automatiza
              |
     +--------+--------+
     |                 |
   docs/           deploy/
 (entender)      (instalar en servidor)

  formacion/  ← aprender el “por qué” con prácticas
```

Si algo de este documento no queda claro, el siguiente sitio a consultar es el [diccionario de términos](diccionario.md).
