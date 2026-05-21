# Guía de Despliegue Externo: WoW Server + Gravity AI (VPS) ☁️

Desplegar tu servidor de World of Warcraft y el puente de control **Gravity AI Bridge V15.0 PRO** en un **VPS (Virtual Private Server)** o Servidor Dedicado en la nube te permite tener una infraestructura de juego en línea estable las 24 horas del día, los 7 días de la semana, con capacidades de automatización autónoma sin necesidad de tener tu ordenador personal encendido todo el tiempo.

Gracias al diseño agnóstico y autónomo de Gravity V15.0 PRO, el puente actúa como el orquestador y panel de administración principal del servidor, facilitando el control de los procesos de juego, la visualización de logs en tiempo real, la creación de cuentas de jugadores y el firewall automatizado en un entorno cloud de alto rendimiento.

---

## 🖥️ 1. Requisitos de Hardware Cloud Sugeridos

Para ejecutar de forma fluida el Servidor WoW Vanilla (MaNGOS) con soporte para hasta **200 jugadores simultáneos** junto con el motor de control y automatización de Gravity AI Bridge V15.0 PRO en modo pasivo:

- **Sistema Operativo**: Windows Server 2022/2019 de 64 bits. (Recomendado para una migración instantánea de tipo copiar y pegar, ya que los binarios compilados `.exe` y la base de datos portable de MySQL se ejecutan de manera nativa sin necesidad de capas de compatibilidad complejas).
- **Procesador (CPU)**: 2 a 4 vCores de alta frecuencia.
- **Memoria RAM**: 4 GB mínimo (WoW consume ~1.2 GB, MySQL ~500 MB, el backend y los buffers de logs de Python ~150 MB). Se recomiendan **8 GB** si planeas usar los bots de generación de contenido local.
- **Almacenamiento**: 40 GB NVMe o SSD de alto rendimiento para garantizar escrituras de base de datos ultrarrápidas.
- **Proveedores de Nube Recomendados**: Contabo (Excelente balance de costo, almacenamiento NVMe y alta capacidad de RAM), Hetzner, DigitalOcean o Vultr.

---

## 🚀 2. Guía Paso a Paso de Migración a Windows Server VPS

Al adquirir tu VPS con Windows Server, el proveedor te suministrará una dirección IP pública y credenciales de acceso administrador. Conéctate al servidor mediante la herramienta nativa **Conexión a Escritorio Remoto (RDP)** de tu sistema operativo Windows local.

### Paso A: Transferencia y Despliegue de Archivos
1.  Comprime tus carpetas de desarrollo local:
    - Tu core de juego completo (ej: `F:\Project_Anarchy_Core\MaNGOS` o la carpeta que contenga tus archivos `mangosd.exe`, `realmd.exe`, logs y base de datos portátil).
    - Tu directorio del orquestador `f:\Gravity_AI_bridge`.
2.  Sube el archivo comprimido a una nube temporal (Google Drive, Mega, Dropbox) o transfiérelo a través de la redirección de unidades de disco locales habilitada en RDP.
3.  Descomprime los archivos en tu VPS manteniendo la misma estructura de directorios preferiblemente (ej. unidad `F:` o adaptando las rutas absolutas dentro del archivo de configuración `config.yaml` del VPS).
4.  Instala **Python 3.10+** (o la versión recomendada) en el VPS, asegurándote de marcar la casilla **"Add Python to PATH"** en el instalador.
5.  Navega al directorio de Gravity y ejecuta el instalador del puente de dependencias:
    ```cmd
    INSTALAR.bat
    ```

### Paso B: Configuración de Seguridad y Cifrado DPAPI
1.  En el VPS, abre el archivo `config.yaml` y ajusta las rutas absolutas del bloque `game_servers.wow_vanilla` para que apunten a los directorios del disco duro reales del VPS.
2.  **Seguridad de API Keys**: Cuando inicies Gravity por primera vez en el VPS, las API keys sensibles de tus proveedores (OpenAI, Anthropic, Firecrawl, etc.) que introduzcas en el panel de configuración se encriptarán automáticamente utilizando la API de Protección de Datos de Windows (**DPAPI**). Esto asegura que si algún atacante obtiene acceso a tu archivo `config.yaml` en disco, no podrá leer tus credenciales en texto plano.

### Paso C: Exposición WAN y Reglas de Firewall Automáticas
A diferencia de tu red doméstica, en un entorno cloud empresarial no cuentas con un enrutador físico para redirección de puertos, sino con firewalls de software del sistema operativo y firewalls de red proporcionados por tu proveedor cloud.

1.  Inicia el servidor del puente de Gravity ejecutando:
    ```cmd
    ARRANCAR.bat
    ```
    El backend de control se levantará escuchando en `http://0.0.0.0:7860`.
2.  **Automatizar Apertura de Puertos**: Realiza una solicitud HTTP POST al endpoint de exposición WAN de Gravity. Puedes hacerlo rápidamente abriendo una ventana de terminal de comandos PowerShell/CMD en el propio VPS y ejecutando:
    ```bash
    curl -X POST http://localhost:7860/v1/gameserver/expose_wan -H "Content-Type: application/json" -d "{\"server\":\"wow_vanilla\", \"public_address\":\"TU_IP_PUBLICA_DEL_VPS\"}"
    ```
    *   **¿Qué hace esta llamada automáticamente?**
        - Invoca llamadas de sistema avanzadas de `netsh advfirewall` para inyectar una regla entrante persistente llamada `Gravity_WoW_MANGOS`, abriendo de par en par los puertos TCP **8085** (conexión de juego) y **3724** (conexión de autenticación realmd) en el firewall de Windows Server.
        - Se conecta a la base de datos de autenticación MySQL (`realmd`) y reescribe la tabla `realmlist` con la IP pública provista para que los clientes reconozcan hacia dónde enrutar el tráfico de juego de forma automática.

### Paso D: Configurar Reglas de Red del Proveedor Cloud
La mayoría de los proveedores modernos (como Contabo, Hetzner o AWS) tienen un firewall externo adicional antes de llegar al VPS. Asegúrate de ingresar a la consola de administración web de tu proveedor e incluir reglas de entrada TCP y UDP para permitir tráfico en los siguientes puertos:
-   `3724` (WoW Auth Server)
-   `8085` (WoW World Server)
-   `7860` (Gravity AI Bridge Dashboard — *Opcional: Permite acceder al panel de control desde tu navegador personal en casa. Si haces esto, se recomienda encarecidamente utilizar un reverse proxy con autenticación básica de seguridad o restringir el tráfico entrante de este puerto solo a tu IP doméstica.*)

---

## 🎮 3. Flujo Operativo para Jugadores Finales

Una vez que tu servidor esté corriendo de manera exitosa en el VPS y expuesto a la red WAN:

1.  **Configurar el Cliente**: Los jugadores de tu comunidad deben abrir la carpeta de su instalación limpia de World of Warcraft 1.12.1, buscar el archivo `/Data/esES/realmlist.wtf` (o idioma equivalente) y reescribirlo para que apunte a tu VPS:
    ```text
    set realmlist TU_IP_PUBLICA_DEL_VPS
    ```
2.  **Creación de Cuentas de Forma Autónoma**: Los jugadores entran desde su navegador web preferido al portal de registro automático alojado en el puente:
    ```text
    http://TU_IP_PUBLICA_DEL_VPS:7860/v1/gameserver/registro
    ```
3.  **Procesamiento Criptográfico Seguro**: La interfaz web interactiva envía los datos encriptados de forma interna al endpoint `/v1/gameserver/register`. El puente encripta la contraseña de forma asíncrona usando **SRP-6a** o **SHA1** (según soporte de tu base de datos) y la guarda directamente en la base de datos MySQL local del VPS, garantizando que el registro se complete en menos de un segundo y previniendo colisiones de nombres de usuario duplicados de forma nativa.
4.  **Ingresar al Servidor**: Los jugadores abren su archivo `WoW.exe`, ingresan el usuario y contraseña registrados en el portal y entran directamente al juego en el VPS de forma inmediata.

---

## 🌐 4. Integración de Nombre de Dominio (DNS A-Record)

Para una presentación profesional e institucional, se recomienda utilizar un nombre de dominio (ejemplo: `wow.tudominio.com`) en lugar de exponer la dirección IP numérica directa de tu servidor VPS:

1.  Inicia sesión en tu registrador de dominios (Namecheap, GoDaddy, Hostinger, Cloudflare).
2.  Accede a la pestaña de administración de zonas DNS y añade un nuevo registro de tipo **A**:
    -   **Host / Subdominio**: `wow` (o `@` si deseas usar el dominio raíz).
    -   **Valor / Dirección IP**: Introduce la dirección IP pública de tu VPS Cloud.
    -   **TTL**: Mantén el valor predeterminado (o 5 minutos para propagación rápida).
3.  Una vez guardado, re-ejecuta el comando de exposición WAN en tu VPS para actualizar las bases de datos internas del realm, utilizando el dominio como parámetro:
    ```bash
    curl -X POST http://localhost:7860/v1/gameserver/expose_wan -H "Content-Type: application/json" -d "{\"server\":\"wow_vanilla\", \"public_address\":\"wow.tudominio.com\"}"
    ```
4.  A partir de este momento, tus jugadores podrán utilizar una configuración elegante y memorable en sus archivos locales:
    ```text
    set realmlist wow.tudominio.com
    ```
    Y el portal de registro interactivo estará accesible públicamente a través de la dirección web:
    ```text
    http://wow.tudominio.com:7860/v1/gameserver/registro
    ```

---
*Manual de Despliegue de Servidores en la Nube — Gravity AI Bridge V15.0 PRO.*
