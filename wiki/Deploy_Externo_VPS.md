# Guía de Despliegue Externo: WoW Server + Gravity AI (VPS) ☁️

Si bien jugar en local es perfecto para círculos reducidos, un servidor estable 24/7 de World of Warcraft requiere alquilar un **VPS (Virtual Private Server)** o Servidor Dedicado.

Con la V10.0 de Gravity, no necesitas saber de Linux ni instalar Apache para tener un servidor o crear cuentas. Gravity funciona como el orquestador principal.

---

## 1. Requisitos de Hardware Cloud
Para un servidor WoW MaNGOS Vanilla con hasta 200 jugadores y el Bridge de Gravity corriendo en modo pasivo:
- **SO**: Windows Server 2022/2019 (Si mantienes los .exe) o Ubuntu 22.04 LTS (si compilas MaNGOS nativamente). *Se recomienda Windows si deseas migrar de F: a la nube copiando y pegando*.
- **CPU**: 2 o 4 vCores.
- **RAM**: 4 GB mínimo. (El WoW gasta ~1.2GB; MySQL 500MB; Python 100MB).
- **Almacenamiento**: 40 GB NVMe/SSD.
- **Proveedores sugeridos**: Contabo (Opción económica y con mucha RAM), DigitalOcean o Hetzner.

---

## 2. Pasos de Migración a Windows Server VPS

Al adquirir tu VPS, recibirás una IP y contraseña para conectar por **Escritorio Remoto (RDP)**.

### Paso A: Transferencia de Archivos
1. Sube tu carpeta `Project_Anarchy_Core` completa (Base de datos MySQL portable portátil y exes) a un .ZIP y súbelo a Google Drive temporalmente.
2. Descárgalo en el escritorio del VPS.
3. Instala Python 3.10+ en el VPS marcando "Add to PATH".
4. Sube la carpeta `Gravity_AI_bridge` y ejecuta `INSTALAR.bat`.

### Paso B: Apertura de Puertos (VPS Firewall)
A diferencia de tu casa, en un VPS no hay "router", solo Firewall de software:
1. Simplemente ejecuta Gravity como Administrador.
2. Abre una terminal y lanza el comando automático: `curl -X POST http://localhost:7860/v1/gameserver/expose -d "{\"server\":\"wow_vanilla\", \"public_address\":\"TU_IP_DEL_VPS\"}"`.
\* *Esto abrirá automáticamente los puertos 8085 (World) y 3724 (Auth) usando `netsh` y actualizará tu base de datos MySQL.*

### Paso C: Arrancar Todo
1. Entra a Gravity Dashboard: `http://localhost:7860/` localmente en el VPS.
2. Inicia tu Servidor WoW desde la pestaña Game Servers. Gravity empezará el ciclo del Watchdog automáticamente 24/7.
- **Nota**: El servidor web de portales web ahora está vivo en `http://TU_IP_DEL_VPS:7860/registro`. 
- Si no abre externamente, asegúrate de añadir la regla TCP 7860 en el firewall del proveedor Cloud.

---

## 3. Flujo para Jugadores Finales

Una vez desplegado:
1. Los jugadores cambian su **realmlist.wtf** a: `set realmlist TU_IP_DEL_VPS`.
2. Para crearse una cuenta, ingresan a su navegador: `http://TU_IP_DEL_VPS:7860/registro`.
3. Ingresan credenciales, Gravity hashea la data en Python y guarda en MySQL bloqueando duplicados.
4. Entran al WoW y listos para jugar.

---

## 4. Uso de Dominio en vez de IP (Opcional)
Si compras un dominio (ej. `miserverwow.com` en Namecheap):
- Crea un registro tipo **A** (DNS) que apunte a tu IP Pública del VPS.
- En Gravity, ejecuta el expose nuevamente: `{"public_address":"miserverwow.com"}`.
- Ahora los jugadores pondrán `set realmlist miserverwow.com`.
