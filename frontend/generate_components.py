import os

BASE_DIR = r'F:\Gravity_AI_bridge\frontend\src\components'
os.makedirs(BASE_DIR, exist_ok=True)

components = {
    'VisionStudio': ('Palette', 'Interfaz base para Fooocus. Genera prompts optimizados o testea variaciones rápidas.'),
    'ImageQueue': ('Image', 'Cola de renderizado de Fooocus. Imágenes pendientes de generación.'),
    'VideoStudio': ('Video', 'Pipeline de generación de video con FFMPEG y TTS.'),
    'ImageLab': ('Palette', 'Laboratorio avanzado para Pruebas A/B y estilos paramétricos.'),
    'DeployManager': ('Rocket', 'Pipeline de integración continua y despliegue a Netlify/VPS.'),
    'GameServers': ('Gamepad2', 'Controlador de instancias locales de MaNGOS WoW 3.3.5a.'),
    'MultiAgent': ('Bot', 'Comparativa paralela de inferencia entre N proveedores.'),
    'HardwareMonitor': ('Cpu', 'Telemetría profunda de VRAM, CUDA/ROCm y carga NPU.'),
    'CostCenter': ('DollarSign', 'Auditoría de tokens y facturación en USD por sesión.'),
    'Watchdog': ('Activity', 'Guardián de auto-reconexión de proveedores caídos.'),
    'Sessions': ('Save', 'Gestor de memoria, branching y estados guardados locales.'),
    'RagIndex': ('BookOpen', 'Vectorización de documentos locales y embeddings.'),
    'MCPServers': ('Plug', 'Integraciones nativas con Model Context Protocol.'),
    'Tools': ('Wrench', 'Herramientas estándar: ejecución aislada, terminal básica.'),
    'ToolsPro': ('Zap', 'Herramientas premium: manipulación GIT, Grep Regex nativo.'),
    'Firecrawl': ('Bug', 'Scraping web profundo y bypass de cloudflare.'),
    'HITLApproval': ('ShieldAlert', 'Autorización obligatoria para comandos destructivos.'),
    'SystemStatus': ('Wifi', 'Vista de latencia e IPs enrutadas activas.'),
    'Security': ('Shield', 'Log de detecciones del Zero-Trust y baneos automáticos.'),
    'AuditLog': ('FileText', 'Registro inmutable de prompts y acciones del sistema.'),
    'Settings': ('Settings', 'Configuraciones de entorno, claves DPAPI y variables locales.')
}

template = """import { {icon} } from 'lucide-react';

export const {name} = () => {
  return (
    <div className="h-full overflow-y-auto p-8 scrollbar-hide animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="max-w-5xl mx-auto space-y-6">
        <div className="glass-panel rounded-2xl p-8 border border-border-subtle relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-64 h-64 bg-accent-primary/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>
          <div className="relative z-10">
            <div className="flex items-center gap-4 mb-6">
              <div className="p-3 rounded-xl bg-surface border border-border-subtle group-hover:border-accent-primary transition-colors duration-500">
                <{icon} className="text-accent-primary" size={28} />
              </div>
              <div>
                <h1 className="text-3xl font-extrabold tracking-tight text-text-primary">{name}</h1>
                <p className="text-text-muted mt-1 font-medium">{desc}</p>
              </div>
            </div>
            
            <div className="p-6 rounded-xl bg-card border border-border-subtle">
              <div className="flex flex-col items-center justify-center py-12 text-center space-y-4">
                <div className="w-16 h-16 rounded-full bg-surface border border-border-subtle flex items-center justify-center animate-pulse">
                  <span className="text-xl text-accent-secondary">⚡</span>
                </div>
                <div>
                  <h3 className="text-lg font-bold text-text-primary">Módulo Interconectado V12</h3>
                  <p className="text-sm text-text-muted max-w-md mx-auto mt-2">
                    Este panel consume la API REST de Gravity Bridge. Su lógica está lista para conectarse a los endpoints `/v1/` locales.
                  </p>
                </div>
                <button className="px-6 py-2 rounded-lg bg-accent-primary/10 text-accent-primary font-bold border border-accent-primary/20 hover:bg-accent-primary hover:text-white transition-all mt-4">
                  Probar Conexión
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
"""

for name, (icon, desc) in components.items():
    file_path = os.path.join(BASE_DIR, f'{name}.tsx')
    content = template.replace('{name}', name).replace('{icon}', icon).replace('{desc}', desc)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

print(f'Generados {len(components)} componentes exitosamente.')
