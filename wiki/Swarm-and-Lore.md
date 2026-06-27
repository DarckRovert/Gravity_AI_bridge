# Swarm Intelligence & Lore Expander

## 1. El Enjambre de Periodismo Dual (`reporter.json`)
En lugar de depender de un único llamado (Zero-Shot) para generar una noticia, Gravity utiliza **Swarm Intelligence**:

```mermaid
graph TD
    RSS[Radar de Alta Frecuencia] -->|Noticia Cruda| Oficial
    RSS -->|Noticia Cruda| Subversivo
    
    Oficial["Periodista Oficial"] -.->|Perspectiva Mainstream| Debate
    Subversivo["Periodista Analítico"] -.->|Visión Soberana| Debate
    
    Debate(("Colisión de Datos")) --> Editor["Editor en Jefe"]
    Editor --> Output["Social Media Kit"]
```

- **Nodo 1 (Postura Oficial):** Genera la visión mainstream de la noticia.
- **Nodo 2 (Postura Subversiva):** Genera una crítica profunda basada en la visión de "La Voluntad Soberana".
- **Nodo 3 (Síntesis del Editor):** Lee ambas posturas enfrentadas y redacta la versión definitiva.

El resultado se persiste localmente gracias al `FileWriterNode` que exporta un "Social Media Kit" para distribución manual.

## 2. Auto-Evolución de Filosofía (`lore_expander.json`)
El conocimiento del sistema no es estático.

```mermaid
sequenceDiagram
    participant RSS as Radar
    participant Bridge as Gravity Bridge
    participant Lore as Base de Conocimiento (TXT)
    
    RSS->>Bridge: Detecta evento global crítico
    Bridge->>Lore: Lee filosofía actual
    Bridge->>Bridge: Reflexiona (LLM) sobre el evento usando la filosofía
    Bridge->>Lore: Escribe un nuevo tomo/capítulo actualizado
```

Gravity implementa un ciclo de introspección:
1. `FileReader` lee el manifiesto actual (`libros_generados/La_Voluntad_Soberana_V3`).
2. Se inyectan las últimas noticias cubiertas como contexto.
3. Un `LLMQuery` especializado toma la filosofía base y redacta un nuevo capítulo o anexo explicando la situación actual a través de la óptica del sistema.
4. Un `FileWriter` graba este nuevo conocimiento en la base de datos de Lore, permitiendo a la entidad aprender permanentemente de su propia cobertura global.
