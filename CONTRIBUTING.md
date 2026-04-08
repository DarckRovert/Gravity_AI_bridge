# Guía de Contribución - Gravity AI Bridge

¡Gracias por tu interés en mejorar este proyecto!

## Requisitos
- Python 3.10+
- `pytest` para las pruebas unitarias.
- `flake8` para el linting de código.

## Cómo contribuir
1. Haz un fork del repositorio.
2. Crea una rama para tu característica (`git checkout -b feature/nueva-idea`).
3. Realiza tus cambios y asegúrate de que pasen los tests: `pytest`.
4. Haz push de tu rama (`git push origin feature/nueva-idea`).
5. Abre un Pull Request.

## Estándares de Código
- Sigue PEP 8 siempre que sea posible.
- Añade docstrings a las nuevas funciones.
- No uses `print` en producción; usa el logger estructurado (`core/logger.py`).
- Mantén la compatibilidad bilingüe (ES/EN) en la documentación.
