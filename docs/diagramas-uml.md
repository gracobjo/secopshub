# Diagramas UML — SecOps Hub

Colección de diagramas UML en notación **Mermaid**, renderizables en GitHub, GitLab, VS Code y Cursor.

---

## 1. Diagrama de casos de uso

Representa las interacciones entre actores y el sistema.

```mermaid
graph TB
    subgraph Actores
        A[Administrador]
        AN[Analista]
        EXT[Sistema Externo SIEM/EDR]
    end

    subgraph SecOps Hub
        UC1((Iniciar sesión))
        UC2((Cerrar sesión))
        UC3((Consultar dashboard))
        UC4((Enriquecer IOC))
        UC5((Bloquear IOC))
        UC6((Consultar vulnerabilidades))
        UC7((Ejecutar playbook))
        UC8((Consultar playbooks))
        UC9((Registrar usuario))
        UC10((Enviar alerta webhook))
    end

    A --> UC1
    AN --> UC1
    A --> UC2
    AN --> UC2
    A --> UC3
    AN --> UC3
    A --> UC4
    AN --> UC4
    A --> UC5
    AN --> UC5
    A --> UC6
    AN --> UC6
    A --> UC7
    A --> UC8
    AN --> UC8
    A --> UC9
    EXT --> UC10

    UC7 -.include.-> UC8
    UC4 -.extend.-> UC5
```

**Leyenda:**
- **Include:** Ejecutar playbook incluye consultar catálogo
- **Extend:** Bloquear IOC extiende enriquecimiento (opcional tras análisis)

---

## 2. Diagrama de clases (dominio)

Modelo de datos y relaciones principales del dominio.

```mermaid
classDiagram
    class User {
        +int id
        +string username
        +string email
        +string password_hash
        +string role
        +datetime created_at
        +set_password(password)
        +check_password(password) bool
        +to_dict() dict
    }

    class Incident {
        +int id
        +string title
        +string description
        +string severity
        +string status
        +string source
        +string assigned_to
        +datetime created_at
        +datetime updated_at
        +to_dict() dict
    }

    class IOC {
        +int id
        +string value
        +string ioc_type
        +int risk_score
        +string verdict
        +bool blocked
        +string source
        +datetime created_at
        +to_dict() dict
    }

    class Vulnerability {
        +int id
        +string cve_id
        +string title
        +string severity
        +float cvss_score
        +bool is_kev
        +string affected_systems
        +string status
        +datetime discovered_at
        +to_dict() dict
    }

    class AuditLog {
        +int id
        +int user_id
        +string username
        +string action
        +string details
        +datetime created_at
        +to_dict() dict
    }

    User "1" --> "0..*" AuditLog : genera
```

**Archivo fuente:** `backend/app/models/__init__.py`

---

## 3. Diagrama de clases (capa de servicios)

```mermaid
classDiagram
    class IOEnrichmentService {
        +detect_ioc_type(value) string
        +simulate_abuseipdb(ip) dict
        +simulate_virustotal(value, type) dict
        +enrich_ioc(value) dict
        +run_playbook(id, params) dict
    }

    class SeedService {
        +seed_database() void
    }

    class AuthService {
        +login(username, password) token
        +register(data) user
        +get_profile(user_id) user
    }

    class AuditHelper {
        +log_action(action, details) void
    }

    IOEnrichmentService ..> IOC : persiste
    AuthService ..> User : gestiona
    AuditHelper ..> AuditLog : crea
    SeedService ..> User : inicializa
    SeedService ..> Incident : inicializa
```

**Archivos:** `services/ioc_enrichment.py`, `services/seed.py`, `routes/auth.py`, `utils/helpers.py`

---

## 4. Diagrama de secuencia — Login (CU-01)

```mermaid
sequenceDiagram
    actor U as Usuario
    participant LP as LoginPage
    participant AC as AuthContext
    participant API as Axios /api
    participant AUTH as auth.py
    participant DB as SQLite

    U->>LP: Introduce credenciales
    LP->>AC: login(username, password)
    AC->>API: POST /auth/login
    API->>AUTH: Validar credenciales
    AUTH->>DB: User.query.filter_by(username)
    DB-->>AUTH: User
    AUTH->>AUTH: check_password()
    AUTH->>AUTH: create_access_token()
    AUTH-->>API: { access_token, user }
    API-->>AC: Response 200
    AC->>AC: setToken(localStorage)
    AC->>AC: setUser(user)
    AC-->>LP: OK
    LP->>U: Redirect Dashboard
```

---

## 5. Diagrama de secuencia — Enriquecimiento IOC (CU-04)

```mermaid
sequenceDiagram
    actor A as Analista
    participant IP as IOCsPage
    participant API as Flask /api/iocs
    participant ENR as ioc_enrichment.py
    participant DB as SQLite
    participant AUD as AuditLog

    A->>IP: Pegar IOC + Enriquecer
    IP->>API: POST /enrich { value }
    API->>API: @jwt_required + @analyst_or_admin
    API->>ENR: enrich_ioc(value)
    ENR->>ENR: detect_ioc_type()
    ENR->>ENR: simulate_virustotal()
    ENR->>ENR: simulate_abuseipdb() [si IP]
    ENR-->>API: { risk_score, verdict, ... }
    API->>DB: INSERT/UPDATE iocs
    API->>AUD: log_action()
    API-->>IP: Resultado JSON
    IP->>A: Panel de análisis
```

---

## 6. Diagrama de secuencia — Webhook de alerta (CU-08)

```mermaid
sequenceDiagram
    actor SIEM as Sistema Externo
    participant WH as webhooks.py
    participant CFG as Config
    participant DB as SQLite

    SIEM->>WH: POST /webhooks/alert
    Note over SIEM,WH: Header X-API-Key
    WH->>CFG: Validar WEBHOOK_API_KEY
    alt API Key inválida
        WH-->>SIEM: 401 Unauthorized
    else API Key válida
        WH->>DB: INSERT Incident
        WH-->>SIEM: 201 { incident }
    end
```

---

## 7. Diagrama de secuencia — Ejecutar playbook (CU-07)

```mermaid
sequenceDiagram
    actor AD as Admin
    participant PP as PlaybooksPage
    participant API as playbooks.py
    participant PB as run_playbook()
    participant AUD as AuditLog

    AD->>PP: Ejecutar playbook
    PP->>API: POST /run { playbook_id, params }
    API->>API: @admin_required
    alt Rol != admin
        API-->>PP: 403 Forbidden
    else Rol admin
        API->>PB: run_playbook(id, params)
        PB-->>API: { status, result }
        API->>AUD: log_action()
        API-->>PP: 200 Resultado
        PP->>AD: Panel resultados
    end
```

---

## 8. Diagrama de componentes

Arquitectura de componentes del sistema desacoplado.

```mermaid
graph TB
    subgraph Cliente
        Browser[Navegador Web]
    end

    subgraph Frontend React :5173
        Router[React Router]
        AuthCtx[AuthContext]
        Pages[Pages Dashboard/IOCs/Vulns/Playbooks]
        Axios[Axios + Interceptores]
        UI[Tailwind + Recharts + Lucide]
    end

    subgraph Backend Flask :5000
        Blueprints[Blueprints REST]
        JWT[JWT Manager]
        RBAC[Decoradores RBAC]
        Services[Services Enrichment/Seed]
        ORM[SQLAlchemy ORM]
        Static[Frontend Static dist/]
    end

    subgraph Persistencia
        SQLite[(SQLite secops_hub.db)]
    end

    subgraph Externos
        SIEM[SIEM / EDR Webhook]
        VT[AbuseIPDB / VirusTotal simulado]
    end

    Browser --> Router
    Router --> AuthCtx
    Router --> Pages
    Pages --> Axios
    Pages --> UI
    Axios -->|/api JWT| Blueprints
    Blueprints --> JWT
    Blueprints --> RBAC
    Blueprints --> Services
    Blueprints --> ORM
    Services --> VT
    ORM --> SQLite
    SIEM -->|X-API-Key| Blueprints
    Browser -->|/:5000| Static
```

---

## 9. Diagrama de despliegue

```mermaid
graph TB
    subgraph Estación de trabajo
        Browser[Browser Chrome/Firefox/Edge]
    end

    subgraph Servidor desarrollo local
        subgraph Node.js
            Vite[Vite Dev Server :5173]
        end
        subgraph Python 3.11+
            Flask[Flask App :5000]
            Gunicorn[Gunicorn/Waitress producción]
        end
        subgraph Filesystem
            DB[(instance/secops_hub.db)]
            Dist[frontend/dist/]
        end
    end

    subgraph Sistemas externos
        WebhookSrc[SIEM / Splunk / EDR]
    end

    Browser -->|HTTP dev| Vite
    Vite -->|Proxy /api| Flask
    Browser -->|HTTP prod| Flask
    Flask --> DB
    Flask --> Dist
    WebhookSrc -->|HTTPS POST + API Key| Flask
    Gunicorn -.->|Reemplaza Flask dev| Flask
```

---

## 10. Diagrama de actividad — Flujo de triaje IOC

```mermaid
flowchart TD
    A[Analista accede a /iocs] --> B{¿Autenticado?}
    B -->|No| C[Redirect /login]
    B -->|Sí| D{¿Rol analyst/admin?}
    D -->|No| E[403 Forbidden]
    D -->|Sí| F[Introduce valor IOC]
    F --> G{¿Valor vacío?}
    G -->|Sí| H[Error 400]
    G -->|No| I[detect_ioc_type]
    I --> J[Simular VirusTotal]
    J --> K{¿Es IP?}
    K -->|Sí| L[Simular AbuseIPDB]
    K -->|No| M[Calcular risk_score]
    L --> M
    M --> N{¿Score >= 75?}
    N -->|Sí| O[verdict = malicious]
    N -->|No| P{¿Score >= 40?}
    P -->|Sí| Q[verdict = suspicious]
    P -->|No| R[verdict = clean]
    O --> S[Persistir en BD]
    Q --> S
    R --> S
    S --> T[Registrar audit log]
    T --> U[Mostrar resultado]
    U --> V{¿Malicious y no bloqueado?}
    V -->|Sí| W[Opción Bloquear]
    V -->|No| X[Fin]
    W --> Y[POST /block]
    Y --> X
```

---

## 11. Diagrama de actividad — Autenticación y acceso

```mermaid
flowchart TD
    Start([Usuario accede a ruta]) --> A{¿Ruta /login?}
    A -->|Sí| B{¿Ya autenticado?}
    B -->|Sí| C[Redirect /]
    B -->|No| D[Mostrar LoginPage]
    A -->|No| E[ProtectedRoute]
    E --> F{¿Token en localStorage?}
    F -->|No| G[Redirect /login]
    F -->|Sí| H[GET /auth/me]
    H --> I{¿Token válido?}
    I -->|No| J[removeToken + /login]
    I -->|Sí| K[Renderizar Layout + Page]
    K --> L{¿Petición API?}
    L -->|Sí| M[Interceptor añade Bearer]
    M --> N{¿Respuesta 401?}
    N -->|Sí| J
    N -->|No| O[Continuar]
    L -->|No| O
    O --> End([Fin])
```

---

## 12. Diagrama entidad-relación (ERD)

```mermaid
erDiagram
    USERS {
        int id PK
        string username UK
        string email UK
        string password_hash
        string role
        datetime created_at
    }

    INCIDENTS {
        int id PK
        string title
        text description
        string severity
        string status
        string source
        string assigned_to
        datetime created_at
        datetime updated_at
    }

    IOCS {
        int id PK
        string value
        string ioc_type
        int risk_score
        string verdict
        bool blocked
        string source
        datetime created_at
    }

    VULNERABILITIES {
        int id PK
        string cve_id UK
        string title
        string severity
        float cvss_score
        bool is_kev
        text affected_systems
        string status
        datetime discovered_at
    }

    AUDIT_LOGS {
        int id PK
        int user_id FK
        string username
        string action
        text details
        datetime created_at
    }

    USERS ||--o{ AUDIT_LOGS : "realiza"
```

---

## 13. Diagrama de paquetes (backend)

```mermaid
graph TB
    subgraph app
        subgraph routes
            auth_r[auth.py]
            inc_r[incidents.py]
            ioc_r[iocs.py]
            vuln_r[vulns.py]
            pb_r[playbooks.py]
            wh_r[webhooks.py]
            fe_r[frontend.py]
        end
        subgraph services
            enrich_s[ioc_enrichment.py]
            seed_s[seed.py]
        end
        subgraph utils
            dec_u[decorators.py]
            help_u[helpers.py]
        end
        models[models/__init__.py]
        init[__init__.py factory]
    end
    config[config.py]
    run[run.py]

    run --> init
    init --> routes
    init --> models
    init --> seed_s
    routes --> services
    routes --> utils
    routes --> models
    init --> config
```

---

## 14. Diagrama de estados — Incidente

```mermaid
stateDiagram-v2
    [*] --> open : Webhook / Seed / Manual
    open --> investigating : Analista investiga
    investigating --> resolved : Incidente resuelto
    investigating --> open : Reabierto
    open --> resolved : Cierre directo
    resolved --> [*]
```

---

## 15. Diagrama de estados — IOC

```mermaid
stateDiagram-v2
    [*] --> pending : Enriquecimiento solicitado
    pending --> clean : score < 40
    pending --> suspicious : 40 <= score < 75
    pending --> malicious : score >= 75
    malicious --> blocked : POST /block
    suspicious --> blocked : Bloqueo manual
    clean --> [*]
    blocked --> [*]
```

---

## 16. Referencia rápida de diagramas

| Diagrama | Uso principal | Sección |
|----------|---------------|---------|
| Casos de uso | Alcance funcional y actores | §1 |
| Clases dominio | Modelo de datos | §2 |
| Clases servicios | Lógica de negocio | §3 |
| Secuencia Login | Flujo autenticación | §4 |
| Secuencia IOC | Triaje de indicadores | §5 |
| Secuencia Webhook | Integración externa | §6 |
| Secuencia Playbook | Respuesta automatizada | §7 |
| Componentes | Arquitectura software | §8 |
| Despliegue | Infraestructura | §9 |
| Actividad IOC | Proceso operativo | §10 |
| Actividad Auth | Control de acceso | §11 |
| ERD | Base de datos | §12 |
| Paquetes | Organización código | §13 |
| Estados Incidente | Ciclo de vida | §14 |
| Estados IOC | Ciclo de vida | §15 |

---

## 17. Cómo visualizar

Los diagramas Mermaid se renderizan automáticamente en:

- GitHub / GitLab (vista previa Markdown)
- VS Code / Cursor con extensión Markdown Preview
- [Mermaid Live Editor](https://mermaid.live)

Para exportar a PNG/SVG, pegue el código en Mermaid Live Editor y use **Export**.
