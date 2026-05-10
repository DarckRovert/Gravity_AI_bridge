import os
import sys
import json
import logging
import subprocess
from pathlib import Path

# Configurar logger
logger = logging.getLogger("RemotionEngine")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class RemotionEngine:
    """
    Motor encargado de conectar Gravity AI Bridge con el entorno de React/Remotion.
    Permite enviar payloads (JSON) y renderizar videos programáticamente.
    """
    def __init__(self, workspace_path: str = None):
        if workspace_path is None:
            # Por defecto busca la carpeta remotion_workspace en la raíz de Gravity
            root = Path(__file__).resolve().parent.parent
            self.workspace = root / "remotion_workspace"
        else:
            self.workspace = Path(workspace_path)
            
        if not self.workspace.exists():
            logger.error(f"Workspace de Remotion no encontrado en {self.workspace}")
            raise FileNotFoundError(f"Remotion workspace not found: {self.workspace}")

        # Ruta donde se exportan los videos
        self.out_dir = self.workspace / "out"
        self.out_dir.mkdir(exist_ok=True)

    def render_composition(self, composition_id: str, output_name: str, props: dict) -> str:
        """
        Renderiza una composición de Remotion pasándole un payload de datos.
        Devuelve la ruta absoluta del MP4 renderizado.
        """
        logger.info(f"Iniciando render para composición: {composition_id}")
        
        # 0. Copiar assets a public/ para evadir Chromium CORS/Security
        import shutil
        public_dir = self.workspace / "public"
        public_dir.mkdir(exist_ok=True)
        
        # Crear un subdirectorio único temporal para evitar colisiones
        temp_dir_name = f"temp_{output_name}"
        temp_dir = public_dir / temp_dir_name
        temp_dir.mkdir(exist_ok=True)
        
        def _localize_path(original_path: str, prefix: str) -> str:
            if not original_path or not os.path.isfile(original_path):
                return original_path # Dejar original si no es archivo (ej. http)
            basename = os.path.basename(original_path)
            new_name = f"{prefix}_{basename}"
            new_path = temp_dir / new_name
            shutil.copy2(original_path, new_path)
            return f"{temp_dir_name}/{new_name}"

        # Migrar video principal si existe
        original_video = props.get("videoPath", "")
        if original_video and os.path.isfile(original_video):
            props["videoPath"] = _localize_path(original_video, "vid")
            
        # Migrar assets de las escenas (LongTemplate)
        if "scenes" in props and isinstance(props["scenes"], list):
            for idx, scene in enumerate(props["scenes"]):
                if "imagePath" in scene:
                    scene["imagePath"] = _localize_path(scene["imagePath"], f"s{idx}")
                if "audioPath" in scene:
                    scene["audioPath"] = _localize_path(scene["audioPath"], f"s{idx}")
        
        # 1. Guardar props temporales en un JSON
        props_path = self.workspace / f"temp_props_{output_name}.json"
        with open(props_path, "w", encoding="utf-8") as f:
            json.dump(props, f, ensure_ascii=False, indent=2)
            
        output_mp4 = self.out_dir / f"{output_name}.mp4"
        
        # 2. Ejecutar npx remotion render
        cmd = [
            "npx", "remotion", "render",
            "src/index.ts",  # entry point default de Remotion
            composition_id,
            str(output_mp4),
            f"--props={str(props_path)}"
        ]
        
        # En Windows a veces npx necesita shell=True o ser llamado como npx.cmd
        npx_cmd = "npx.cmd" if sys.platform == "win32" else "npx"
        cmd[0] = npx_cmd

        logger.info(f"Ejecutando: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.workspace),
                check=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                shell=(sys.platform == "win32"),
                timeout=2700,  # 45 min máximo por render
            )
            logger.info("Renderizado exitoso.")
            if result.stdout:
                logger.debug(result.stdout[-2000:])
        except subprocess.TimeoutExpired:
            logger.error("Remotion render excedió el timeout de 45 minutos.")
            raise RuntimeError("Remotion render timeout (45 min)")
        except subprocess.CalledProcessError as e:
            stderr_tail = (e.stderr or "")[-3000:]
            logger.error(f"Error renderizando video:\n{stderr_tail}")
            raise RuntimeError(f"Remotion render failed: {stderr_tail}")
        finally:
            # 3. Limpiar archivo de props temporal y los assets copiados
            if props_path.exists():
                props_path.unlink()
            if temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                except Exception as ex:
                    logger.warning(f"No se pudo borrar el subdirectorio temporal {temp_dir_name}: {ex}")
                
        if not output_mp4.exists():
            raise FileNotFoundError("El MP4 no se generó a pesar de que el proceso terminó sin error.")
            
        return str(output_mp4)

if __name__ == "__main__":
    # Prueba del motor si se ejecuta directamente
    engine = RemotionEngine()
    test_props = {
        "title": "TOP 3 IA TOOLS",
        "subtitle": "Para mejorar tu productividad",
        "themeColor": "#f43f5e" # Rose color
    }
    try:
        mp4_path = engine.render_composition(
            composition_id="ShortTemplate", 
            output_name="test_short", 
            props=test_props
        )
        print(f"Video generado en: {mp4_path}")
    except Exception as e:
        print(f"Fallo la prueba: {e}")
