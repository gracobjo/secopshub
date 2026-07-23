# 04 — Instalación y uso de Kali Linux

Formación práctica para montar **Kali Linux** en máquina virtual y usarlo de forma segura en un laboratorio, en el contexto de SecOps Hub / operaciones SOC.

**Duración orientativa:** 3–4 h (instalación + primeros usos)  
**Nivel:** iniciación  
**Entorno recomendado:** Windows 10/11 + VirtualBox (o VMware Workstation Player)

---

## Objetivos

Al terminar esta formación serás capaz de:

1. Explicar qué es Kali y cuándo (y cuándo no) usarlo
2. Instalar Kali en una máquina virtual desde la ISO oficial
3. Actualizar el sistema y moverte por el escritorio y la terminal
4. Usar un conjunto mínimo de herramientas útiles en un lab SOC
5. Relacionar Kali con el flujo de SecOps Hub (triage, IOC, red)

---

## Aviso ético y legal (obligatorio)

Kali incluye herramientas de análisis de seguridad. **Solo** se pueden usar en:

- tu propia máquina / red de laboratorio,
- entornos autorizados por escrito (aula, empresa, CTF oficial),
- sistemas de prueba creados para formación.

**Prohibido** escanear, atacar o “probar” redes ajenas sin permiso explícito. En esta formación todo se hace **dentro de la VM** o contra **objetivos de lab** (p. ej. otra VM vulnerable autorizada).

Si dudas: **no lo hagas**.

---

## 1. Qué es Kali Linux

| Idea | Explicación |
|------|-------------|
| Distro | Linux basado en Debian, orientado a **seguridad ofensiva y defensiva** |
| Público | Analistas, pentesters, formadores, investigadores |
| No es | Un “sistema para navegar a diario” ni un sustituto del SIEM/EDR |
| En SecOps Hub | Herramienta de **laboratorio** para simular tráfico, analizar artefactos, practicar triage |

### Kali vs otras distros (visión rápida)

| Distro | Uso típico |
|--------|------------|
| Ubuntu / Debian | Servidores, escritorio general |
| Kali | Lab de seguridad, pruebas autorizadas |
| Windows Server | AD, servicios corporativos |

> SecOps Hub corre en Flask/React (Docker o bare metal). Kali **no sustituye** al Hub: es un puesto de práctica del analista.

---

## 2. Requisitos previos

### Hardware mínimo (host)

| Recurso | Mínimo | Recomendado |
|---------|--------|-------------|
| RAM libre para la VM | 2 GB | 4 GB |
| Disco | 25 GB | 40 GB |
| CPU | 2 núcleos | 2–4 núcleos |
| Virtualización | VT-x / AMD-V activada en BIOS | Sí |

### Software en el host (elige uno)

1. **Oracle VirtualBox** (gratuito) — recomendado en aula  
2. **VMware Workstation Player** (gratuito para uso personal)

### Descarga oficial de Kali

1. Entra en: https://www.kali.org/get-kali/
2. Elige **Installer Images** → arquitectura **64-bit**
3. Descarga el **ISO** (no uses torrents de terceros)
4. (Opcional) Verifica el hash SHA256 publicado en la misma página

**Alternativa más rápida:** en la misma web, **Virtual Machines** → imagen preinstalada para VirtualBox/VMware (`.ova` / `.vmx`). Ahorra la instalación guiada; sigue siendo válida para esta formación.

---

## 3. Instalación en VirtualBox (paso a paso)

### 3.1 Crear la máquina virtual

1. Abre VirtualBox → **Nueva**
2. Nombre: `Kali-Lab`
3. Tipo: **Linux** · Versión: **Debian (64-bit)** (o “Other Linux 64-bit”)
4. Memoria: **4096 MB** (mínimo 2048)
5. Disco duro: **VDI**, dinámico, **40 GB**
6. Ajustes → **Sistema** → Procesadores: **2**
7. Ajustes → **Pantalla** → Memoria de vídeo: **128 MB**
8. Ajustes → **Almacenamiento** → controlador óptico → selecciona el ISO de Kali
9. Ajustes → **Red** → Adaptador 1:
   - **NAT** → salida a Internet (actualizaciones, apt)
   - o **Red interna / Host-only** si el formador prepara un lab aislado

### 3.2 Arrancar e instalar

1. Inicia la VM
2. En el menú de arranque: **Graphical install** (o *Install*)
3. Idioma / teclado: **Español** (o el de tu preferencia)
4. Nombre del equipo: `kali-lab`
5. Usuario: crea un usuario **no root** (p. ej. `alumno`) con contraseña fuerte
6. Particionado: **Usar todo el disco** (en VM de lab está bien)
7. Cuando pida software: deja la selección por defecto (escritorio Xfce)
8. Instala el cargador **GRUB** en el disco de la VM
9. Reinicia y **expulsa / desmonta el ISO** para no volver a entrar al instalador

### 3.3 Si usaste imagen preinstalada (.ova)

1. VirtualBox → **Archivo** → **Importar servicio virtualizado**
2. Selecciona el `.ova` oficial
3. Ajusta RAM/CPU si hace falta
4. Arranca y cambia la contraseña por defecto (véase documentación Kali de esa imagen)

---

## 4. Primer arranque — checklist

Tras el login:

```bash
# Actualizar repositorios e instalar parches
sudo apt update
sudo apt full-upgrade -y

# Comprobar identidad y red
whoami
hostname
ip a
ping -c 3 1.1.1.1
```

| Comprobación | Resultado esperado |
|--------------|--------------------|
| `whoami` | tu usuario (no `root` en sesión gráfica habitual) |
| `ip a` | interfaz con IP (NAT suele ser `10.0.2.x` en VirtualBox) |
| `ping` | respuesta si hay Internet |

### Consejos de seguridad del lab

- Haz un **snapshot** en VirtualBox justo después del primer `full-upgrade` (“Kali limpia”)
- No compartas carpetas del host con malware de prueba sin aislamiento
- Guarda credenciales del lab fuera de capturas de pantalla públicas

---

## 5. Orientación del escritorio

Kali (Xfce) típico:

| Elemento | Para qué |
|----------|----------|
| Menú de aplicaciones | Buscar herramientas (`nmap`, `wireshark`…) |
| Terminal | Trabajo principal del analista |
| Navegador | Documentación, interfaces web del lab (SecOps Hub, etc.) |
| Gestor de archivos | Revisar capturas, exports, evidencias de práctica |

Atajos útiles:

| Atajo | Acción |
|-------|--------|
| `Ctrl+Alt+T` | Abrir terminal (según configuración) |
| `Tab` | Autocompletar en terminal |
| `Ctrl+C` | Cancelar comando en curso |
| `Ctrl+L` o `clear` | Limpiar pantalla |

---

## 6. Terminal Linux esencial (para Kali)

Practica estos comandos en orden:

```bash
# Dónde estoy y qué hay
pwd
ls -la
cd ~
mkdir -p ~/lab/{capturas,notas,exports}
cd ~/lab && ls

# Ayuda y manuales
man ls          # salir con q
nmap --help | head

# Permisos y sudo
sudo -v         # pide contraseña; valida privilegios
id

# Procesos y disco
df -h
free -h
ps aux | head
```

### Editar un fichero de notas

```bash
nano ~/lab/notas/sesion1.md
# Escribe: fecha, objetivo del lab, IP de la VM
# Guardar: Ctrl+O · Salir: Ctrl+X
```

---

## 7. Herramientas mínimas para un lab SOC

Todas las prácticas siguientes: **solo en tu lab**.

### 7.1 Inventario de red local de la VM

```bash
ip -br a
ip route
cat /etc/resolv.conf
```

### 7.2 Nmap — descubrimiento autorizado

Escanea **solo** la propia VM o un rango del lab:

```bash
# Puertos locales de la propia máquina
nmap -sT -F 127.0.0.1

# Si el formador te da una IP de lab (ejemplo ficticio):
# nmap -sV -p 22,80,443 192.168.56.10
```

| Opción | Significado |
|--------|-------------|
| `-F` | Escaneo rápido (puertos frecuentes) |
| `-sV` | Intentar detectar versión de servicio |
| `-p` | Puertos concretos |

### 7.3 Wireshark / tshark — captura de tráfico

```bash
# Listar interfaces
ip -br a

# Captura corta en terminal (sustituye eth0/wlan0/ens33 por la tuya)
sudo timeout 15 tcpdump -i any -c 20 -nn
```

En GUI: abre **Wireshark**, elige la interfaz, filtra p. ej. `http` o `dns` en un lab controlado.

### 7.4 Hashes e IOCs (enlace con SecOps Hub)

```bash
echo "contenido-de-prueba" > ~/lab/exports/muestra.txt
sha256sum ~/lab/exports/muestra.txt
md5sum ~/lab/exports/muestra.txt
```

Ese hash puedes usarlo después en el módulo de **IOCs** de SecOps Hub (notebook `02` o consola) para practicar enriquecimiento.

### 7.5 curl — hablar con APIs del lab

Si tienes SecOps Hub en el host o en Docker accesible desde la VM:

```bash
# Ejemplo: health (ajusta IP/puerto del lab)
curl -sS http://HOST_DEL_LAB:5000/api/health || true
```

> En VirtualBox, desde la VM con NAT, `10.0.2.2` suele ser la IP del host. Confírmalo con el formador.

### 7.6 Metapaquete útiles (opcional)

```bash
# Ver metapaquetes disponibles
apt-cache search kali-linux | head

# Ejemplo: herramientas de análisis forense (solo si el formador lo pide)
# sudo apt install -y kali-tools-forensics
```

No instales “todo Kali” de golpe: alarga descargas y superficie innecesaria.

---

## 8. Relación con SecOps Hub

```text
[ SIEM / sensores ] ---> webhook ---> [ SecOps Hub ] ---> playbooks
                              ^
                              |
         [ Kali lab ]  --- evidencias / IOC / pruebas de red ---
```

| En Kali practicas… | En SecOps Hub lo ves como… |
|--------------------|----------------------------|
| Extraer hash / IP sospechosa | Enriquecimiento IOC |
| Generar tráfico de lab | Alerta / incidente (si hay SIEM de práctica) |
| Revisar capturas pcap | Contexto para decidir un playbook |
| Documentar hallazgos | Notas de incidente / informe |

Material relacionado en este repo:

- `formacion/01_python_automatizacion_secops.ipynb`
- `formacion/02_enriquecimiento_ioc.ipynb`
- `formacion/03_pipeline_alerta_respuesta.ipynb`
- `docs/laboratorio-infraestructura.md`
- `docs/manual-laboratorio.md` (si existe en tu copia)

---

## 9. Ejercicios (entregables)

### Ejercicio A — Instalación (obligatorio)

1. VM Kali arrancable con usuario propio  
2. Snapshot “post-upgrade”  
3. Captura o texto con salida de: `hostname`, `whoami`, `ip -br a`

### Ejercicio B — Terminal

1. Crea `~/lab/{capturas,notas,exports}`  
2. Fichero `~/lab/notas/sesion1.md` con: objetivo, fecha, IP de la VM  
3. Calcula SHA-256 de un fichero de prueba en `exports/`

### Ejercicio C — Reconocimiento autorizado

1. `nmap -sT -F 127.0.0.1` y guarda la salida en `~/lab/exports/nmap-local.txt`  
2. Explica en 5 líneas qué puertos viste y si tiene sentido en una VM limpia

### Ejercicio D — Puente con SecOps Hub (opcional)

1. Toma una IP o hash de lab  
2. Introdúcelo en la consola SecOps Hub (IOC) o en el notebook 02  
3. Anota el veredicto / puntuación obtenida

---

## 10. Problemas frecuentes

| Síntoma | Qué probar |
|---------|------------|
| La VM es muy lenta | Sube RAM a 4 GB; activa virtualización en BIOS; cierra programas del host |
| No hay Internet en Kali | Red = NAT; `sudo apt update`; revisa proxy corporativo |
| Teclado mal mapeado | `setxkbmap es` o ajustes de teclado del escritorio |
| Pantalla negra / baja resolución | Instalar *Guest Additions* (VirtualBox) o *open-vm-tools* |
| “Permission denied” | Anteponer `sudo` solo cuando haga falta; no trabajes siempre como root |
| El ISO vuelve a arrancar | Quita el ISO del controlador óptico tras instalar |

Guest Additions (VirtualBox), tras arrancar Kali instalado:

```bash
sudo apt update
sudo apt install -y virtualbox-guest-x11
# Reinicia la VM
```

(Si tu versión de VirtualBox/Kali lo recomienda por otra vía, sigue la guía oficial de esa versión.)

---

## 11. Criterios de evaluación (rúbrica rápida)

| Criterio | OK |
|----------|----|
| Ética: declara que solo usará lab autorizado | ☐ |
| Kali instalado / importado y actualizado | ☐ |
| Snapshot de seguridad creado | ☐ |
| Domina `pwd`, `ls`, `cd`, `mkdir`, `nano`, `sudo apt` | ☐ |
| Ejecuta nmap solo contra objetivo autorizado | ☐ |
| Entrega notas + hash + salida nmap local | ☐ |
| Relaciona al menos 1 artefacto con SecOps Hub / IOC | ☐ |

---

## 12. Recursos oficiales

- Descargas y docs: https://www.kali.org/
- Documentación: https://www.kali.org/docs/
- Herramientas: https://www.kali.org/tools/

---

## Resumen en una frase

**Instala Kali en una VM, actualízalo, trabaja en terminal con herramientas de lab y úsalo para generar/analizar evidencias que luego triarás en SecOps Hub — siempre con autorización.**
