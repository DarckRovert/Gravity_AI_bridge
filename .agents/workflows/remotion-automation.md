# Workflow: Automatización y Desarrollo con Remotion

Este workflow documenta las reglas y pasos necesarios para que Gravity AI Bridge o cualquier Agente IA pueda crear o modificar componentes de **Remotion** (React) de manera exitosa para la Content Factory.

## Principios Base

- Remotion genera video a partir de componentes de React. No es interactivo, es secuencial.
- El estado no debe depender de interacciones del usuario (clicks), sino del `frame` actual usando `useCurrentFrame()`.
- Nunca usar variables de estado asíncronas para renderizado visual sin el componente `continueRender` de Remotion.

## Estructura del Workspace

El proyecto vive en `remotion_workspace/`:
- `src/Root.tsx`: Define las composiciones (`<Composition />`). Aquí se registran todos los videos generados.
- `src/index.ts`: Entry point principal.
- `src/[Componente].tsx`: Los archivos de video individuales (ej. `ShortTemplate.tsx`).

## Cómo Crear un Nuevo Formato de Video

1. Crea el archivo del componente React en `src/`.
2. Utiliza `AbsoluteFill` para posicionar elementos y fondos.
3. Importa `useCurrentFrame` y `useVideoConfig` de `"remotion"`.
4. Utiliza funciones matemáticas como `interpolate` y `spring` para crear animaciones fluidas basadas en el frame actual.

**Ejemplo Básico de Animación:**
```tsx
const frame = useCurrentFrame();
const { fps } = useVideoConfig();
// Aparecer progresivamente en 15 frames
const opacity = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: "clamp" });
```

5. **Registro:** Ve a `src/Root.tsx` e importa el nuevo componente. Declara su `<Composition />` dándole un `id`, `fps`, `width`, `height`, y definiendo `defaultProps` para previsualizaciones locales.

## Integración con Python (Gravity Core)

Cuando modifiques el engine principal de Gravity, recuerda:
- Los renderizados se delegan a `core/remotion_engine.py`.
- Llama a `engine.render_composition(id, name, props)` pasándole el Payload en forma de diccionario de Python.
- Asegúrate de que el dict en Python hace "match" con la interfaz de TypeScript del componente de Remotion.

## Comandos Útiles

Si necesitas probar algo por terminal:
- **Previsualización Local:** `cd remotion_workspace && npm run dev`
- **Renderizado Local:** `npx remotion render src/index.ts <CompositionID> out/video.mp4`
