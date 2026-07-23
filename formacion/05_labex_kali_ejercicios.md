# 05 — Ejercicios LabEx Kali: análisis, plan y soluciones

Fuente analizada: [LabEx — Kali Linux Ejercicios](https://labex.io/es/exercises/kali)  
Complemento local: [04 — Instalación y uso de Kali](04_kali_linux_instalacion_uso.md)

**Propósito:** mapear el catálogo LabEx, plantear cómo realizarlo (LabEx cloud o VM propia) y documentar **soluciones de estudio** para lab autorizado.

> **Ética:** solo en entornos LabEx, CTF oficiales o tu VM/laboratorio con permiso. No usar estas técnicas contra sistemas ajenos.

> **Atribución:** los enunciados y entornos interactivos pertenecen a LabEx. Este documento es material formativo propio de SecOps Hub (guía de estudio + equivalentes locales), no una copia del runtime de LabEx.

---

## 1. Análisis del catálogo

LabEx ofrece retos/labs etiquetados **Kali Linux** orientados a:

| Eje | Qué practicas | Herramientas típicas |
|-----|---------------|----------------------|
| Reconocimiento | Hosts, puertos, servicios | Nmap |
| Criptografía básica | Confidencialidad de ficheros | OpenSSL |
| Autenticación débil | Fuerza bruta en lab | Hydra, John |
| Red | Canales TCP/UDP, transferencias | Netcat |
| Web ofensivo (intro) | Manipulación de peticiones | Hackbar (Firefox) |
| Explotación controlada | Flujo Metasploit en lab | msfconsole |
| Defensa / SOC | CIA, malware indicators, políticas | chmod, hashes, journalctl/auth.log |

### Inventario (página de ejercicios Kali)

Orden pedagógico propuesto (no el de la web):

| ID | Título LabEx (ES) | Tipo | Bloque |
|----|-------------------|------|--------|
| LX-01 | Escaneo básico de vulnerabilidades con Nmap | Lab | Nmap |
| LX-02 | Usar Nmap para escanear puertos de red comunes | Lab | Nmap |
| LX-03 | Cómo escanear múltiples direcciones IP simultáneamente con Nmap | Lab | Nmap |
| LX-04 | Cómo analizar los resultados de escaneo de Nmap en formato XML | Lab | Nmap |
| LX-05 | Conceptos fundamentales de seguridad (tríada CIA) en Linux | Lab | Defensa |
| LX-06 | Introducción al cifrado con OpenSSL | Lab | Crypto |
| LX-07 | Descifrado de un documento de alto secreto | Challenge | Crypto |
| LX-08 | Descifrado de una cuenta de usuario específica | Challenge | Auth |
| LX-09 | Uso de Netcat para comunicación de red básica | Lab | Red |
| LX-10 | Uso de Hydra para descifrar contraseñas | Lab | Auth |
| LX-11 | Atacar servicios habilitados con SSL con Hydra | Lab | Auth |
| LX-12 | ¿Cómo usar Hackbar para pruebas de seguridad? | Lab | Web |
| LX-13 | Explotación en Kali con Metasploit | Lab | Exploit lab |
| LX-14 | Identificación de indicadores de malware en Linux | Lab | Defensa/SOC |
| LX-15 | Políticas de contraseñas y detección de ataques en Linux | Lab | Defensa/SOC |

Curso relacionado (Skill Tree / Beginners): setup Kali, ficheros, users, Nikto, sqlmap, iptables, John, etc. — ver §6.

### Relación con SecOps Hub

| LabEx | En SecOps Hub / formación local |
|-------|----------------------------------|
| Nmap / puertos | Evidencia de exposición → incidente / IOC IP |
| Hashes / OpenSSL | Integridad → notebook 02 (IOC hash) |
| Hydra / fallos de login | Detección fuerza bruta → alertas / políticas |
| Malware indicators | Triage → pipeline notebook 03 |
| Metasploit (lab) | Contexto de amenaza; Hub orquesta respuesta, no sustituye EDR |

---

## 2. Plan de realización

### 2.1 Dos vías

| Vía | Cuándo | Ventaja | Límite |
|-----|--------|---------|--------|
| **A — LabEx en navegador** | Aula sin VM potente | Entorno listo, validación automática | Dependencia de cuenta/plataforma |
| **B — Kali VM local** | Tras guía 04 | Control total, enlaza con Hub | Hay que montar servicios de lab |

**Recomendación SecOps Hub:** completar **04** (VM) y hacer **LX-01…LX-09 y LX-14…LX-15** en local; LX-10…LX-13 preferible primero en LabEx (servicios ya preparados) y luego replicar en lab aislado.

### 2.2 Cronograma sugerido (aula)

| Sesión | Contenido | IDs | Horas |
|--------|-----------|-----|-------|
| 0 | Ética + instalar Kali | Guía 04 | 3–4 |
| 1 | Nmap (local → multi-IP → XML) | LX-01…04 | 2–3 |
| 2 | CIA + OpenSSL + challenges crypto | LX-05…08 | 2 |
| 3 | Netcat + lectura de logs / políticas | LX-09, 14, 15 | 2 |
| 4 | Hydra solo vs servicios locales de lab | LX-10, 11 | 2 |
| 5 | Hackbar + Metasploit intro (lab) | LX-12, 13 | 2–3 |
| 6 | Puente evidencias → SecOps Hub | Notebooks 02–03 | 1 |

### 2.3 Preparación VM (antes de soluciones locales)

```bash
sudo apt update && sudo apt full-upgrade -y
mkdir -p ~/labex-local/{nmap,crypto,netcat,hydra,notas,exports}
# Snapshot VirtualBox: "kali-pre-labex"
```

Servicios de lab (solo si el formador lo autoriza en red aislada):

```bash
# Ejemplo: HTTP simple para practicar nmap -p 80
python3 -m http.server 8080 --bind 127.0.0.1 &
```

---

## 3. Soluciones detalladas (estudio / lab autorizado)

Convención: comandos pensados para **127.0.0.1**, rangos de loopback o IP que te dé el formador. En LabEx, sustituye rutas (`~/project`) por las del enunciado.

---

### LX-01 — Escaneo básico de vulnerabilidades con Nmap

**Objetivo:** instalar/usar Nmap, escanear localhost, interpretar puertos abiertos.

**Realización**

```bash
nmap --version
nmap -sT -F 127.0.0.1
nmap -sV -p 22,80,443,8080 127.0.0.1 -oN ~/labex-local/nmap/lx01.txt
```

**Solución / qué entregar**

1. Salida guardada en `lx01.txt`
2. Tabla: puerto | estado | servicio (si `-sV`)
3. Conclusión: en VM limpia suele haber pocos/ningún puerto; si levantaste `http.server`, verás **8080/tcp open**

**Criterio OK:** sabes distinguir `open` / `closed` / `filtered` y no escaneas fuera del lab.

---

### LX-02 — Escanear puertos de red comunes

**Objetivo:** entender puertos frecuentes (22, 80, 443…) y documentar riesgo.

**Realización**

```bash
# Servidor web de lab (terminal 1)
python3 -m http.server 80 --bind 127.0.0.1   # puede requerir sudo; si falla usa 8080

# Escaneo (terminal 2)
nmap -sT -p 21,22,23,25,80,443,3306,8080 127.0.0.1 -oN ~/labex-local/nmap/lx02-common.txt
```

**Solución esperada (ejemplo con HTTP en 8080)**

| Puerto | Estado típico lab | Implicación |
|--------|-------------------|-------------|
| 22 | open si SSH activo | Superficie de fuerza bruta |
| 80/8080 | open si hay web | Exposición HTTP |
| 21/23 | closed en Kali limpia | Bien si no necesitas FTP/Telnet |

**Documenta:** “puerto abierto ≠ explotado; es superficie a gestionar”.

---

### LX-03 — Escanear múltiples IPs simultáneamente

**Objetivo:** rangos, CIDR, `-iL`, descubrimiento `-sn`.

**Realización**

```bash
# Rango loopback
nmap -sT -F 127.0.0.1-3 -oN ~/labex-local/nmap/lx03-range.txt

# CIDR (descubrimiento, sin puertos)
nmap -sn 127.0.0.0/29 -oN ~/labex-local/nmap/lx03-cidr.txt

# Lista de objetivos
printf '127.0.0.1\n127.0.0.2\n' > ~/labex-local/nmap/targets.txt
nmap -iL ~/labex-local/nmap/targets.txt -F -oN ~/labex-local/nmap/lx03-list.txt

# Combinado + timing (lab pequeño)
nmap -T4 -F 127.0.0.1 127.0.0.2 -oN ~/labex-local/nmap/lx03-multi.txt
```

**Solución clave**

| Método | Sintaxis | Cuándo |
|--------|----------|--------|
| Rango | `a.b.c.1-50` | Contiguos |
| CIDR | `a.b.c.0/24` | Subred |
| Archivo | `-iL targets.txt` | No contiguos |
| Solo hosts up | `-sn` | Inventario rápido |

---

### LX-04 — Analizar resultados Nmap en XML

**Objetivo:** generar XML y extraer datos (puertos, hosts).

**Realización**

```bash
nmap -sT -F 127.0.0.1 -oX ~/labex-local/nmap/scan.xml -oN ~/labex-local/nmap/scan.txt

# Inspección rápida
head -n 40 ~/labex-local/nmap/scan.xml
grep -E 'port protocol|state=' ~/labex-local/nmap/scan.xml | head

# Con Python (en la VM o en formacion/.venv)
python3 - <<'PY'
import xml.etree.ElementTree as ET
from pathlib import Path
root = ET.parse(Path.home()/"labex-local/nmap/scan.xml").getroot()
for host in root.findall("host"):
    addr = host.find("address").get("addr")
    ports = []
    for p in host.findall(".//port"):
        state = p.find("state").get("state")
        if state == "open":
            ports.append(p.get("portid"))
    print(addr, "open:", ",".join(ports) or "(ninguno)")
PY
```

**Solución:** XML sirve para automatizar (scripts, SIEM, importación). En SecOps Hub el paralelo es normalizar alertas JSON del webhook, no XML de Nmap — misma idea: **parsear → estructura → decisión**.

---

### LX-05 — Tríada CIA en Linux

**Objetivo:** Confidencialidad (`chmod`), Integridad (hashes), Disponibilidad (servicios).

**Realización / solución**

```bash
# Confidencialidad
echo "dato sensible de lab" > ~/labex-local/exports/secreto.txt
chmod 600 ~/labex-local/exports/secreto.txt
ls -l ~/labex-local/exports/secreto.txt   # -rw------- 

# Integridad
sha256sum ~/labex-local/exports/secreto.txt | tee ~/labex-local/exports/secreto.sha256
# Tras un cambio deliberado, el hash no coincidirá:
echo x >> ~/labex-local/exports/secreto.txt
sha256sum -c ~/labex-local/exports/secreto.sha256 || echo "INTEGRIDAD ROTA (esperado)"

# Restaura y recalcula hash limpio para el entregable
echo "dato sensible de lab" > ~/labex-local/exports/secreto.txt
sha256sum ~/labex-local/exports/secreto.txt > ~/labex-local/exports/secreto.sha256

# Disponibilidad (monitorizar un servicio)
systemctl is-active ssh || true
ps aux | head
```

| Pilar | Comando demo | Analogía Hub |
|-------|--------------|--------------|
| C | `chmod 600` | Roles JWT / MFA |
| I | `sha256sum` | IOC hash |
| A | estado de servicios | health / métricas |

---

### LX-06 — Introducción al cifrado con OpenSSL

**Objetivo:** cifrar/descifrar simétrico AES-256-CBC + PBKDF2.

**Realización / solución**

```bash
cd ~/labex-local/crypto
echo "mensaje secreto de laboratorio" > secret.txt

openssl enc -aes-256-cbc -salt -pbkdf2 \
  -in secret.txt -out secret.enc
# Introduce una passphrase de lab (ej. LabPass-SoloPractica)

openssl enc -d -aes-256-cbc -pbkdf2 \
  -in secret.enc -out secret.dec.txt

diff secret.txt secret.dec.txt && echo "OK: descifrado correcto"
```

**Notas:** sin la passphrase no hay recuperación práctica; no reutilices passphrases de lab en sistemas reales.

---

### LX-07 — Challenge: documento de alto secreto

**Enunciado tipo LabEx** ([referencia](https://labex.io/tutorials/linux-decrypting-top-secret-document-415952)): descifrar `classified.enc` con AES-256-CBC + PBKDF2.

En LabEx la passphrase del challenge público documentado es del estilo: `S3cur3P@ssw0rd!` (usa la del enunciado si cambia).

**Solución patrón**

```bash
cd ~/project   # o la ruta del lab
openssl enc -d -aes-256-cbc -pbkdf2 \
  -in classified.enc -out decrypted.txt \
  -pass pass:'S3cur3P@ssw0rd!'
# Verifica checksum si el lab lo indica (md5sum/sha256sum decrypted.txt)
```

**Equivalente local (auto-reto):**

```bash
cd ~/labex-local/crypto
echo "TOP SECRET LAB" > plain.txt
openssl enc -aes-256-cbc -salt -pbkdf2 -in plain.txt -out classified.enc -pass pass:'S3cur3P@ssw0rd!'
rm plain.txt
openssl enc -d -aes-256-cbc -pbkdf2 -in classified.enc -out decrypted.txt -pass pass:'S3cur3P@ssw0rd!'
cat decrypted.txt
```

---

### LX-08 — Challenge: cuenta de usuario específica

**Objetivo típico:** obtener el hash de un usuario de lab y romperlo con **John** (wordlist corta del enunciado).

**Solución patrón (solo lab)**

```bash
# En LabEx suelen dar un fichero hash o un shadow de práctica
# Ejemplo genérico:
echo 'alumno:$6$salt$hash...' > ~/labex-local/crypto/user.hash   # usa el hash del lab

# Wordlist del lab (o rockyou recortada SOLO en lab)
printf 'password\n123456\nlabex\nalumno\n' > ~/labex-local/crypto/wordlist.txt

john --wordlist=~/labex-local/crypto/wordlist.txt ~/labex-local/crypto/user.hash
john --show ~/labex-local/crypto/user.hash
```

Si el challenge es ZIP: `zip2john archivo.zip > zip.hash` → `john --wordlist=... zip.hash`.

**Defensa (mensaje para el alumno):** políticas fuertes + MFA (como en SecOps Hub) mitigan este escenario.

---

### LX-09 — Netcat: comunicación básica

**Objetivo:** listener, cliente, transferencia de fichero; opcional cifrado con OpenSSL.

**Solución**

```bash
# Terminal A — servidor
nc -l -p 9001

# Terminal B — cliente
nc 127.0.0.1 9001
# Escribe mensajes; Ctrl+C para salir
```

Transferencia:

```bash
# A — receptor
nc -l -p 9002 > ~/labex-local/netcat/recibido.txt

# B — emisor
echo "evidencia de lab" > ~/labex-local/netcat/envio.txt
nc 127.0.0.1 9002 < ~/labex-local/netcat/envio.txt
```

Canal cifrado (patrón educativo):

```bash
# A
openssl s_server -quiet -accept 9443 -cert lab.crt -key lab.key
# B
openssl s_client -quiet -connect 127.0.0.1:9443
```

(Genera cert de lab con `openssl req -x509 -newkey rsa:2048 -keyout lab.key -out lab.crt -days 1 -nodes`.)

---

### LX-10 — Hydra (contraseñas) — solo servicio local de lab

**Objetivo:** entender fuerza bruta HTTP/SSH/FTP **contra un servicio que tú levantas** con credenciales débiles de prueba.

**Montaje mínimo HTTP básico (ejemplo formativo)**

```bash
# Wordlists de lab
printf 'admin\nuser\n' > ~/labex-local/hydra/users.txt
printf 'admin\npassword\n123456\nlabex\n' > ~/labex-local/hydra/pass.txt
```

Patrón Hydra (ajusta módulo al servicio del lab LabEx o local):

```bash
# Ejemplo SSH local (solo si tienes usuario de lab con password débil conocida)
# hydra -L users.txt -P pass.txt ssh://127.0.0.1 -t 4 -f

# Ejemplo HTTP-POST formulario de lab (ruta/form del enunciado LabEx)
# hydra -L users.txt -P pass.txt 127.0.0.1 http-post-form \
#   "/login:user=^USER^&pass=^PASS^:F=invalid" -f
```

**Solución pedagógica:** Hydra muestra la pareja válida; el entregable incluye captura + **recomendación defensiva** (lockout, MFA, rate limit — como en requisitos del Hub).

**Prohibido:** apuntar Hydra a hosts de Internet o de la organización sin autorización escrita.

---

### LX-11 — Hydra contra servicios SSL (`-S`)

**Objetivo:** mismo flujo con TLS (`hydra -S` / módulo https).

```bash
# Patrón (lab con HTTPS local):
# hydra -L users.txt -P pass.txt -S https-get://127.0.0.1/ \
#   o el módulo http-post-form con -S según enunciado LabEx
# Opción -O solo si el lab pide probar stacks SSL antiguos (entorno controlado)
```

**Solución:** confirmar en la salida `login: ... password: ...` y anotar que TLS **no** evita credenciales débiles.

---

### LX-12 — Hackbar (pruebas web)

**Objetivo:** extensión Firefox para manipular query/POST en apps de lab (DVWA, página de prueba LabEx).

**Realización**

1. En LabEx/Firefox del lab: instalar/activar Hackbar  
2. Cargar URL de la app vulnerable de **lab**  
3. Modificar parámetros (p. ej. `id=1` → `id=1'`) **solo en ese entorno**  
4. Observar respuestas (error SQL, reflejo XSS de lab, etc.)

**Solución / entregable:** captura antes/después + explicación de por qué la app no valida entrada.  
**No** es un tutorial de explotación contra sitios reales.

---

### LX-13 — Metasploit en Kali (lab)

**Objetivo:** flujo `msfconsole` sobre **máquina vulnerable de laboratorio** (p. ej. Metasploitable / entorno LabEx), no Internet.

**Realización patrón**

```bash
msfconsole -q
# Dentro de msf:
# search type:exploit name:....
# use exploit/...
# show options
# set RHOSTS <IP_LAB_AUTORIZADA>
# set LHOST <IP_KALI_EN_LAB>
# check
# run / exploit
# sessions -i 1   # si hay Meterpreter de lab
```

**Solución de estudio (qué debe quedar claro)**

1. Selección de módulo acorde al servicio detectado por Nmap  
2. `RHOSTS` = objetivo de lab; `LHOST` = tu Kali en la misma red de lab  
3. Tras sesión: documentar evidencia y **contención** (aislar host) — puente a playbooks del Hub  
4. Cerrar sesión y revertir snapshot

No se documentan aquí payloads ni exploits concretos contra CVEs públicos como receta ofensiva reutilizable fuera de lab.

---

### LX-14 — Indicadores de malware en Linux

**Objetivo:** procesos raros, ficheros modificados, logs anómalos.

**Solución práctica**

```bash
# Procesos
ps aux --sort=-%cpu | head
ps aux | grep -Ei 'crypto|miner|nc -|ncat' | grep -v grep || true

# Ficheros recientes / sospechosos en home
find ~ -type f -mtime -1 2>/dev/null | head
find /tmp -type f 2>/dev/null | head

# Hashes de un binario de lab
sha256sum /bin/ls

# Strings (IOC textuales)
strings -n 8 /bin/ls | head

# Logs de autenticación (ruta según distro)
sudo grep -i "failed\|invalid\|accepted" /var/log/auth.log 2>/dev/null | tail -n 30 \
  || sudo journalctl -u ssh --no-pager | tail -n 30
```

**Entregable:** 3 indicadores + hipótesis (falso positivo vs sospechoso) + qué harías en el Hub (IOC / incidente).

---

### LX-15 — Políticas de contraseña y detección de ataques

**Objetivo:** endurecer política y detectar fuerza bruta en logs.

**Solución**

```bash
# Ver política actual
grep -E '^PASS_|^ENCRYPT' /etc/login.defs | head
sudo chage -l "$(whoami)"

# Contar fallos de login (señal de hydra/brute)
sudo grep "Failed password" /var/log/auth.log 2>/dev/null \
  | awk '{print $(NF-3)}' | sort | uniq -c | sort -nr | head \
  || sudo journalctl -u ssh | grep -i failed | tail

# Tras un hydra de LAB contra tu propio SSH, deberías ver picos de Failed password
```

**Recomendaciones a documentar:** `PASS_MIN_LEN`, caducidad (`chage`), fail2ban/lockout, MFA (RF del Hub).

---

## 4. Rúbrica de entrega (por ejercicio)

| Campo | Contenido |
|-------|-----------|
| ID | LX-0x |
| Entorno | LabEx / Kali VM |
| Comandos | Historial o script en `~/labex-local/` |
| Evidencia | Captura o fichero en `exports/` |
| Hallazgo | 3–5 líneas |
| Puente Hub | IOC / incidente / playbook / N/A |
| Ética | Confirmación lab autorizado |

Plantilla:

```markdown
## LX-XX — título
- Fecha:
- Entorno:
- Evidencias: exports/...
- Hallazgo:
- Relación SecOps Hub:
```

---

## 5. Checklist global

- [ ] Guía 04 completada (VM + snapshot)
- [ ] LX-01…04 Nmap
- [ ] LX-05…08 CIA/crypto
- [ ] LX-09 Netcat
- [ ] LX-14…15 defensa/SOC
- [ ] LX-10…13 solo tras autorización y en lab aislado/LabEx
- [ ] Al menos 1 artefacto (IP/hash) llevado a notebook 02 o consola Hub

---

## 6. Mapa ampliado (curso Kali for Beginners / Security Labs)

Útil si el alumno sigue también [Kali Linux for Beginners](https://labex.io/courses/kali-linux-for-beginners):

| Tema LabEx | Equivalente local |
|------------|-------------------|
| Setting Up / Verify version | Guía 04 + `cat /etc/os-release` |
| Navigating files / tool dirs | `mkdir ~/lab/...`, `pwd`, `ls` |
| Basic networking | `ip`, `ping`, `curl` |
| Scan ports Nmap | LX-01…03 |
| Start Metasploit | LX-13 |
| Users / create account | `sudo adduser`, `id` |
| Recon Nmap+DNS | `nmap` + `dig`/`nslookup` lab |
| John / Hydra | LX-08, LX-10 |
| iptables | lab avanzado (fuera de este doc) |
| Nikto / sqlmap | solo apps vulnerables de lab |

---

## 7. Índice de `formacion/` (documentación de la carpeta)

| Archivo | Rol |
|---------|-----|
| `README.md` | Cómo montar el entorno Jupyter y mapa de materiales |
| `requirements-notebooks.txt` | Deps Python de notebooks 01–03 |
| `01_python_automatizacion_secops.ipynb` | Python en el Hub |
| `02_enriquecimiento_ioc.ipynb` | IOC / scoring |
| `03_pipeline_alerta_respuesta.ipynb` | Alerta → playbook |
| `04_kali_linux_instalacion_uso.md` | Instalar/usar Kali en VM |
| `04_kali_linux_instalacion_uso.ipynb` | Checklist Kali + IOC bridge |
| `05_labex_kali_ejercicios.md` | **Este doc:** LabEx → plan + soluciones |
| `entregas_kali/` | Entregas locales (gitignored) |

Ruta de aprendizaje recomendada: **01 → 02 → 03 → 04 → 05 (LabEx)**.

---

## 8. Referencias

- Catálogo: https://labex.io/es/exercises/kali  
- OpenSSL intro: https://labex.io/tutorials/linux-introduction-to-encryption-with-openssl-415957  
- Challenge documento: https://labex.io/tutorials/linux-decrypting-top-secret-document-415952  
- Nmap multi-IP: https://labex.io/tutorials/nmap-how-to-scan-multiple-ip-addresses-simultaneously-using-nmap-in-cybersecurity-414798  
- Kali.org docs: https://www.kali.org/docs/
