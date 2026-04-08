# Guía de Contribución — Gravity AI Bridge

¡Gracias por tu interés en contribuir a **Gravity AI Bridge**!

## 📋 Antes de Empezar

1. Lee el [Código de Conducta](CODE_OF_CONDUCT.md).
2. Revisa los [Issues abiertos](https://github.com/DarckRovert/Gravity_AI_bridge/issues) para evitar trabajo duplicado.
3. Para cambios grandes, abre primero un Issue para discutir el enfoque.

## 🔧 Proceso de Contribución

### 1. Fork y Clonación
```bash
git clone https://github.com/TU_USUARIO/Gravity_AI_bridge.git
cd Gravity_AI_bridge
pip install -r requirements.txt
```

### 2. Crear una Rama
```bash
git checkout -b feature/mi-nueva-funcionalidad
# o
git checkout -b fix/descripcion-del-bug
```

### 3. Estándares de Código

- **Python 3.10+** con type hints explícitos. Prohibido `Any`.
- Formato: `black` / `flake8`.
- Sin placeholders en el código (`# ... resto del código`).
- Bloques completos siempre.
- Comentarios en español.
- Docstrings en inglés (convención interna del proyecto).

### 4. Proveedores Nuevos

Para añadir un nuevo proveedor de IA:
1. Crea `providers/cloud/mi_proveedor.py` heredando de `providers.base.BaseProvider`.
2. Implementa `scan()`, `stream()`, `complete()`.
3. Registra en `providers/registry.py`.
4. Añade tests en `tests/`.

### 5. Tests

```bash
pytest tests/ -v
```

### 6. Pull Request

- Título claro: `[feat] Añadir soporte Mistral AI` o `[fix] Corregir TTFT en cache hit`.
- Describe el problema que resuelve.
- Adhunde cambios al CHANGELOG.md bajo `[Unreleased]`.
- Asegúrate de que los tests pasen.

## 🏷️ Tipos de Cambio

| Prefijo | Uso |
|---------|-----|
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de bug |
| `docs` | Solo documentación |
| `refactor` | Refactorización sin cambio de API |
| `perf` | Mejora de rendimiento |
| `test` | Añadir o corregir tests |

## 📬 Contacto

- Issues: [github.com/DarckRovert/Gravity_AI_bridge/issues](https://github.com/DarckRovert/Gravity_AI_bridge/issues)
- Stream en vivo: [twitch.tv/darckrovert](https://twitch.tv/darckrovert)
