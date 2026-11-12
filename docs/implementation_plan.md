# Plan Maestro de Refactorización Arquitectónica: Gravity AI Bridge V30.1 (Auditoría Empírica L9)

## 1. Auditoría Adversarial: ¿Qué supuestos iniciales fueron corregidos?

Antes de tocar una sola línea de código, se realizó una auditoría empírica cruzada entre el código fuente, los cargadores dinámicos y el estado en disco. Se detectaron **3 riesgos críticos** que un enfoque precipitado habría roto:

| Elemento | Riesgo Identificado | Hallazgo Empírico en Código | Corrección en el Plan |
| :--- | :--- | :--- | :--- |
| **`ask_deepseek.py` en raíz** | Parecía un script suelto de prueba. | `bridge_server.py:61` invoca explícitamente: `SessionSpawner(sys.executable, os.path.join(_BASE, "ask_deepseek.py"))`. | **NO se elimina ni se mueve.** Es un worker de sub-sesiones multi-agente en producción. |
| **Bases de datos en raíz (`.sqlite`, `.db`)** | Parecían ser las bases de datos activas del sistema. | `core/db_migrator.py:40-45` redirige toda persistencia real a `%LOCALAPPDATA%\Gravity\Databases\`. | Las BDs en la raíz del repo son copias históricas huérfanas. Se archivan sin riesgo de alterar el estado real del usuario. |
| **Módulos de `core/` (~100 archivos)** | Moverlos a subcarpetas (`core/media/`, etc.) rompería el sistema. | `service_loader.py:28` usa `importlib.import_module("core.image_queue")`. Los 244 tests unitarios importan rutas fijas. | **NO se altera la ruta física de los módulos de `core/`.** Se refactorizan internamente (concurrencia, tipado, dependencias circulares) sin romper contratos externos. |

---

## 2. Plan Quirúrgico en 4 Fases (Sin Regresiones)

```
┌────────────────────────────────────────────────────────────────────────┐
│                   PIPELINE DE REFACTORIZACIÓN SEGURA                   │
├───────────────────────────────┬────────────────────────────────────────┤
│ Fase 1: Limpieza de Raíz      │ Archivar parches 2026 en _archivo/     │
│                               │ Eliminar api/routers/ (100% muerto)    │
│                               │ Ignorar ffmpeg (1.4 GB) en .gitignore  │
├───────────────────────────────┼────────────────────────────────────────┤
│ Fase 2: Blindaje SQLite       │ Migrar 27 llamadas sqlite3.connect     │
│                               │ hacia core.db_manager (WAL + Retry)    │
├───────────────────────────────┼────────────────────────────────────────┤
│ Fase 3: Desacoplamiento API   │ Modularizar api/routes/ (Mixins)       │
│                               │ Endpoints con validación JSON robusta  │
├───────────────────────────────┼────────────────────────────────────────┤
│ Fase 4: Verificación Integral │ Suite de 244 tests unitarios (pytest)  │
│                               │ Arranque de bridge_server en :7860     │
└───────────────────────────────┴────────────────────────────────────────┘
```

---

### Fase 1: Saneamiento de Raíz y Eliminación de Código Muerto

1. **Eliminación del Directorio Huérfano `api/routers/`:**
   * Evidencia: `bridge_server.py` y el resto de la aplicación importan exclusivamente desde `api.routes`. `api/routers/` es una copia abandonada idéntica.
2. **Archivado de Parches Históricos Sueltos:**
   * Mover a `_archivo/legacy_patches/`:
     `patch_all_metrics_qa.py`, `patch_clean_response.py`, `patch_fiction_qa.py`, `patch_fiction_writer.py`, `patch_hitl.py`, `patch_metrics.py`, `patch_separators.py`, `patch_separators_2.py`, `fix_hitl_signatures.py`, `refactor_md5.py`, `refactor_md5_safe.py`.
3. **Limpieza de Archivos Temporales de Prueba:**
   * Mover a `_basura/`:
     `elbingo2050*.txt`, `flm_*.txt`, `test_ask.txt`, `test_out.txt`, `_test_apis.py`, `bandit_results*.json`, `exhaustive_results*.json`.
4. **Archivado de Bases de Datos Huérfanas de Raíz:**
   * Mover a `_archivo/legacy_dbs/`:
     `_image_queue (2).sqlite*`, `test_tinka.db`, `tinka_history*.db`, `video_jobs.db`, `gravity.db` (dejando intacto `%LOCALAPPDATA%\Gravity\Databases\`).
5. **Optimización de `.gitignore`:**
   * Añadir `ffmpeg-master-latest-win64-gpl/` para no saturar el control de versiones con 1.4 GB de binarios precompilados.

---

### Fase 2: Blindaje de Concurrencia SQLite en `core/`

Actualmente existen **27 llamadas directas** a `sqlite3.connect(...)` dispersas en `core/` que omiten el gestor resiliente (`core/db_manager.py`). Bajo Windows, esto genera excepciones `sqlite3.OperationalError: database is locked`.

* **Acción:**
  Sustituir las conexiones directas en:
  * `core/cache_engine.py`
  * `core/image_queue.py`
  * `core/video_pipeline.py`
  * `core/strategic_memory.py`
  * `core/tiktok_radar.py`
  por el wrapper oficial:
  ```python
  from core.db_manager import get_connection, sqlite_retry, SafeDBContext
  ```
  Esto garantiza que toda transacción use `PRAGMA journal_mode=WAL`, `busy_timeout=30000` y reintentos automáticos con retroceso exponencial.

---

### Fase 3: Desacoplamiento y Robustecimiento de `api/routes/`

1. **Gestión de Errores en Mixins:**
   * En `mixin_post.py` y `mixin_get.py`, envolver la lectura del cuerpo de la petición (`self.rfile.read`) en bloques seguros con manejo explícito de `json.JSONDecodeError` para devolver HTTP 400 limpio en lugar de HTTP 500 no controlado.
2. **CORS & Headers Atómicos:**
   * Centralizar las cabeceras de respuesta y CORS en `api/state.py` para evitar divergencias entre rutas GET, POST y eventos SSE.

---

### Fase 4: Certificación y Pruebas de Regresión

1. **Ejecución Local de Pytest:**
   * Ejecutar la suite completa de 244 tests (`python -m pytest`).
   * Meta de aceptación: **244 passed, 0 failed, 0 warnings de importación**.
2. **Prueba de Humo en Servidor:**
   * Iniciar `bridge_server.py` y verificar respuesta HTTP 200 en `http://127.0.0.1:7860/api/models` y `http://127.0.0.1:7860/api/providers`.
3. **Prueba de Inferencia con el Servidor LM Studio Activo:**
   * Confirmar que el flujo local hacia el puerto 1234 y la interfaz web Open WebUI en el puerto 8080 operan de forma ininterrumpida.

---

## 3. Criterio de Seguridad Absoluta
* Cero eliminación destructiva a ciegas: todo archivo no esencial se archiva con respaldo en `_archivo/` o `_basura/`.
* Cero ruptura de APIs públicas ni de imports de tests.
* Costo $0.00 permanente sin runners externos.
