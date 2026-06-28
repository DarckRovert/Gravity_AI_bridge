"""
Módulo 2: HUD Overlay Transparente (Protocolo J.A.R.V.I.S)
Renderiza una interfaz gráfica transparente y 'click-through' en la esquina de la pantalla.
Muestra la telemetría vital del sistema de forma flotante.
"""

import tkinter as tk
import ctypes
import psutil
import time
import os
import sys

def set_clickthrough(hwnd):
    # Windows API constants
    GWL_EXSTYLE = -20
    WS_EX_LAYERED = 0x00080000
    WS_EX_TRANSPARENT = 0x00000020
    
    GetWindowLong = ctypes.windll.user32.GetWindowLongW
    SetWindowLong = ctypes.windll.user32.SetWindowLongW
    
    ex_style = GetWindowLong(hwnd, GWL_EXSTYLE)
    SetWindowLong(hwnd, GWL_EXSTYLE, ex_style | WS_EX_LAYERED | WS_EX_TRANSPARENT)

class JarvisHUD:
    def __init__(self, root):
        self.root = root
        self.root.overrideredirect(True) # Frameless
        self.root.wm_attributes("-topmost", True) # Always on top
        
        bg_color = '#050505'
        self.root.configure(bg=bg_color)
        self.root.wm_attributes("-transparentcolor", bg_color)
        
        # Dimensions
        self.hud_width = 350
        self.hud_height = 250
        
        # Position: Top Right corner
        screen_w = self.root.winfo_screenwidth()
        x_pos = screen_w - self.hud_width - 20
        y_pos = 40
        self.root.geometry(f'{self.hud_width}x{self.hud_height}+{x_pos}+{y_pos}')
        
        # Style Configuration
        title_font = ("Consolas", 11, "bold")
        data_font = ("Consolas", 10)
        self.color_normal = "#00ffff" # Cyan
        self.color_warn = "#ffcc00"   # Yellow
        self.color_crit = "#ff3333"   # Red
        self.bg_color = bg_color
        
        # Layout
        self.title_label = tk.Label(root, text="GRAVITY V16.7 [OVERWATCH]", font=title_font, fg=self.color_normal, bg=bg_color)
        self.title_label.pack(anchor="ne", pady=(10, 5), padx=10)
        
        # Hardware Frame
        self.hw_frame = tk.Frame(root, bg=bg_color)
        self.hw_frame.pack(anchor="ne", padx=10)
        
        self.cpu_label = tk.Label(self.hw_frame, text="APU_CPU: CALIBRATING...", font=data_font, fg="#ffffff", bg=bg_color)
        self.cpu_label.pack(anchor="e")
        
        self.ram_label = tk.Label(self.hw_frame, text="APU_RAM: CALIBRATING...", font=data_font, fg="#ffffff", bg=bg_color)
        self.ram_label.pack(anchor="e")
        
        # OODA/Network Frame
        self.net_frame = tk.Frame(root, bg=bg_color)
        self.net_frame.pack(anchor="ne", padx=10, pady=(10,0))
        
        self.ooda_label = tk.Label(self.net_frame, text="OODA LOOP: LISTENING", font=data_font, fg="#ffffff", bg=bg_color)
        self.ooda_label.pack(anchor="e")
        
        self.status_label = tk.Label(root, text="SHIELD: ACTIVE", font=data_font, fg="#00ff00", bg=bg_color)
        self.status_label.pack(anchor="ne", padx=10, pady=(10,0))
        
        # Start Updates
        self.update_telemetry()
        
    def apply_clickthrough(self):
        self.root.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
        if not hwnd:
            hwnd = self.root.winfo_id()
        set_clickthrough(hwnd)

    def update_telemetry(self):
        try:
            # CPU and RAM
            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory().percent
            
            cpu_color = self.color_normal if cpu < 60 else (self.color_warn if cpu < 85 else self.color_crit)
            ram_color = self.color_normal if ram < 70 else (self.color_warn if ram < 90 else self.color_crit)
            
            self.cpu_label.config(text=f"APU_CPU: {cpu:04.1f}%", fg=cpu_color)
            self.ram_label.config(text=f"APU_RAM: {ram:04.1f}%", fg=ram_color)
            
            # Animate OODA text slightly to show it's alive
            t = int(time.time())
            dots = "." * (t % 4)
            self.ooda_label.config(text=f"OODA LOOP: ACTIVE{dots:<3}")
            
        except Exception as e:
            self.status_label.config(text="ERROR", fg=self.color_crit)
            
        self.root.after(1000, self.update_telemetry)

def start_hud():
    root = tk.Tk()
    app = JarvisHUD(root)
    # Give Tkinter time to render before making click-through
    root.after(150, app.apply_clickthrough)
    root.mainloop()

if __name__ == "__main__":
    start_hud()
