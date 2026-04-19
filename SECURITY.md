# 🛡️ Matriz de Seguridad y Mitigación de Ecosistema (V10.1+)

El despliegue local que permite el Gravity AI Bridge no lo exonera de ataques LAN agresivos o fugas termales destructivas para sus clústeres. Todo servidor Windows o Instancia host que hospede el Bridge obedece estas políticas.

## 1. Defensa contra Fugas VRAM (Engine Watchdog)
No existe exposición directa del modelo Local. 
Cualquier petición en la suite es forzada dinámicamente por la clase cruzada del `Env Optimizer` que intercepta qué hardware provee la base. Si un intrusista LAN con acceso en `/v1/chat` manda context-windows monstruosos que superarían el tope térmico/físico de NVIDIA CUDA u OS M-Series de la IA hosteadora, el Optimizador desactiva y resetea dinámicamente la ventana forzando seguridad para que los Drivers de video de la máquina matriz no crasheen.

## 2. Prevención de Gastos (Cost Tracker Lock)
Las APIs Cloud conectadas accidental o estratégicamente en tus `.env` no drenarán infinitur.
Obligatorio en todo subproceso de cobro: Un logueo forzado al instante por token de entrada y de salida (`_cost_log.json`). 
- **Límite Diario Estricto:** Si las cuotas permean el umbral, los subprocesos de la API Cloud devuelven 403 Forbidden y caen un escalón buscando inteligencias gratis base Ollama de forma automática. 

## 3. Seguridad de Datos Persistentes y Memoria
1. **Truncamiento SQLite Forzado Foráneo**: Base y Metadatos de Session / Config operan en SQLite. Para evitar fugas de subprocesos inactivos con bloqueos fantasma, al Boot se fuerza el protocolo `"PRAGMA wal_checkpoint(TRUNCATE)"` matando memorias basura desahuciadas de previas corridas rotas. A coste mínimo recorta 1 MB de inflamiento de base de datos diariamente.
2. **Auto Mysql Backups para WoW**: Nadie apaga el World of Warcraft local sin que Gravity Bridge expulse primero un Popen agresivo corriendo `mysqldump` a toda tu DB de "Characters". Todo se encripta silenciosamente para que tus progresos resistan un crash FATAL de Windows OS.

## 4. Auditoría HTTP Endpoints y Rate Limiter
1. Tasa Limitante por defecto global inyectada en Header Level: **120 Peticiones / 60 Segundos**. El sistema HTTP corta de raíz solicitudes repetidas desde una IP de la red ignorando el body del parseador interno (Evita colapso de CPU interno por sobreesfuerzo de HTTP Parsing malioso).
2. Cada solicitud se imprime en `_audit_log.jsonl`. Con auto rotación física (`maxBytes` a 5 Millones de caracteres) para no llenar los discos de 500GB hosteadores.

Este módulo corporativo está construido para defender sus operaciones con resiliencia máxima y zero down-time. Las peticiones desautorizadas por favor se dirigen y apelan internamente a las directrices de [DarckRovert](https://github.com/DarckRovert).
