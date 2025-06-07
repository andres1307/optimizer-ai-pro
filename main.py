import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import psutil
import threading
import time
import os
import ctypes
from ctypes import wintypes
from PIL import Image, ImageTk
import wmi
import sqlite3
import pandas as pd
from db_manager import DataBase
from ai_predictive import PredictiveAI
from notifier import Notifier
from cleaner import Cleaner
import tempfile
import sys
import fnmatch

# ========== SOLUCIÓN PARA ERRORES WINDOWS ==========
def fix_wndproc_errors():
    """Corrige los errores WNDPROC y WPARAM en Windows"""
    if os.name == 'nt':
        try:
            wintypes.LRESULT = wintypes.LONG
            wintypes.WPARAM = wintypes.UINT
            wintypes.LPARAM = wintypes.LONG
            ctypes.windll.user32.SetWindowLongW.restype = wintypes.LONG
            ctypes.windll.user32.SetWindowLongW.argtypes = [
                wintypes.HWND, 
                ctypes.c_int, 
                wintypes.LONG
            ]
        except Exception as e:
            print(f"Error configurando WNDPROC: {e}")

# ========== CLASE PRINCIPAL ==========
class OptimizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Optimizer AI PRO - By ISAMEL TRUJILLO")
        self.root.geometry("900x750")
        self.root.configure(bg='#121212')
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Inicializar componentes
        self.setup_styles()
        self.create_widgets()
        self.setup_tabs()
        
        # Sistema y modelos
        self.db = DataBase("system_monitor.db")
        self.predictive_ai = PredictiveAI(self.db.db_path)
        self.notifier = Notifier()
        self.cleaner = Cleaner()
        self.db_lock = threading.Lock()
        
        # Estado UI para el parpadeo
        self.blinking = False
        self.blink_state = False
        self.blink_color = 'normal'
        
        # Cargar imágenes del alien con manejo robusto (CORREGIDO)
        self.alien_images = {}  # Inicializado antes de cualquier uso
        self.load_alien_images()
        
        # Variables de estado
        self.running = True
        self.monitor_thread = None
        
        # Iniciar servicios
        self.start_services()
        
        # Configuración inicial
        self.update_temperature_bar()
        self.update_ui()

    def load_alien_images(self):
        """Carga las imágenes del alien con manejo robusto (CORREGIDO)"""
        image_files = {
            'normal': 'alien_estado_normal.png',
            'green': 'alien_estado_analizando.png',  # Usando nombres reales de tus archivos
            'blue': 'alien_estado_limpiando.png',
            'red': 'alien_estado_alerta.png'
        }
        
        for state, filename in image_files.items():
            try:
                base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
                img_path = os.path.join(base_path, filename)
                
                if os.path.exists(img_path):
                    img = Image.open(img_path).resize((100, 100))
                    self.alien_images[state] = ImageTk.PhotoImage(img)
                else:
                    raise FileNotFoundError(f"Archivo de imagen no encontrado: {filename}")
            except Exception as e:
                print(f"Error cargando imagen {filename}: {str(e)}")
                # Crear imagen de respaldo
                img = Image.new('RGB', (100, 100), color='#121212')
                self.alien_images[state] = ImageTk.PhotoImage(img)

    def setup_styles(self):
        """Configura los estilos visuales"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configurar estilos
        style.configure('.', background='#121212', foreground='white')
        style.configure('TFrame', background='#121212')
        style.configure('TLabel', background='#121212', foreground='white', font=('Arial', 10))
        style.configure('TButton', background='#333333', foreground='white', font=('Arial', 10))
        style.configure('TNotebook', background='#121212')
        style.configure('TNotebook.Tab', background='#333333', foreground='white')
        style.map('TButton', background=[('active', '#444444')])
        
        # Estilos para la barra de progreso
        style.configure("green.Horizontal.TProgressbar", troughcolor='black', background='#4CAF50')
        style.configure("yellow.Horizontal.TProgressbar", troughcolor='black', background='#FFC107')
        style.configure("red.Horizontal.TProgressbar", troughcolor='black', background='#F44336')

    def create_widgets(self):
        """Crea los widgets principales"""
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Alien status (CORREGIDO)
        self.alien_label = tk.Label(self.main_frame, bg='#121212')
        self.alien_label.pack(side=tk.BOTTOM, pady=10)
        self.change_alien_color('normal')

        # Barra de estado
        self.status_bar = ttk.Label(
            self.main_frame, 
            text="Sistema: Iniciando...",
            relief=tk.SUNKEN,
            font=('Arial', 9)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def setup_tabs(self):
        """Configura el sistema de pestañas"""
        self.tab_control = ttk.Notebook(self.main_frame)
        
        # Crear pestañas
        self.tab_monitor = ttk.Frame(self.tab_control)
        self.tab_graphs = ttk.Frame(self.tab_control)
        self.tab_settings = ttk.Frame(self.tab_control)
        
        # Configurar contenido de pestañas
        self.setup_monitor_tab()
        self.setup_graphs_tab()
        self.setup_settings_tab()
        
        # Añadir pestañas al control
        self.tab_control.add(self.tab_monitor, text='Monitor')
        self.tab_control.add(self.tab_graphs, text='Gráficos')
        self.tab_control.add(self.tab_settings, text='Configuración')
        self.tab_control.pack(expand=1, fill="both")

    def setup_monitor_tab(self):
        """Configura la pestaña de monitorización"""
        frame = ttk.Frame(self.tab_monitor)
        frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        # Área de alertas
        self.alerts_text = scrolledtext.ScrolledText(
            frame, 
            height=12, 
            width=90,
            bg='#1E1E1E',
            fg='white',
            font=('Consolas', 9)
        )
        self.alerts_text.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Métricas del sistema
        metrics_frame = ttk.Frame(frame)
        metrics_frame.pack(fill=tk.X, pady=5)
        
        self.cpu_var = tk.StringVar(value="CPU: 0%")
        ttk.Label(metrics_frame, textvariable=self.cpu_var, width=12).pack(side=tk.LEFT)
        
        self.ram_var = tk.StringVar(value="RAM: 0%")
        ttk.Label(metrics_frame, textvariable=self.ram_var, width=12).pack(side=tk.LEFT)
        
        self.disk_var = tk.StringVar(value="Disco: 0%")
        ttk.Label(metrics_frame, textvariable=self.disk_var, width=12).pack(side=tk.LEFT)
        
        # Barra de temperatura
        self.temp_bar = ttk.Progressbar(
            frame, 
            orient="horizontal", 
            length=400, 
            mode="determinate"
        )
        self.temp_bar.pack(pady=5)
        
        # Botones de acción
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)
        
        ttk.Button(
            btn_frame, 
            text="🔍 Analizar Sistema", 
            command=lambda: [self.start_blinking_alien('green'), self.run_analysis_thread()]
        ).grid(row=0, column=0, padx=5)
        
        ttk.Button(
            btn_frame, 
            text="🧹 Limpieza Avanzada", 
            command=lambda: [self.start_blinking_alien('blue'), self.advanced_clean()]
        ).grid(row=0, column=1, padx=5)
        
        ttk.Button(
            btn_frame, 
            text="🧬 Info del Sistema", 
            command=self.show_system_info
        ).grid(row=0, column=2, padx=5)

    def setup_graphs_tab(self):
        """Configura la pestaña de gráficos"""
        frame = ttk.Frame(self.tab_graphs)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configuración del gráfico
        self.fig = Figure(figsize=(8, 4), dpi=100, facecolor='#1E1E1E')
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#1E1E1E')
        
        # Estilo del gráfico
        for spine in self.ax.spines.values():
            spine.set_color('white')
        self.ax.tick_params(colors='white')
        self.ax.xaxis.label.set_color('white')
        self.ax.yaxis.label.set_color('white')
        self.ax.title.set_color('white')
        
        # Canvas para el gráfico
        self.canvas = FigureCanvasTkAgg(self.fig, master=frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Controles del gráfico
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(control_frame, text="Mostrar:").pack(side=tk.LEFT)
        self.graph_var = tk.StringVar(value='cpu')
        ttk.Radiobutton(control_frame, text="CPU", variable=self.graph_var, value='cpu').pack(side=tk.LEFT)
        ttk.Radiobutton(control_frame, text="RAM", variable=self.graph_var, value='ram').pack(side=tk.LEFT)
        ttk.Radiobutton(control_frame, text="Disco", variable=self.graph_var, value='disk').pack(side=tk.LEFT)
        
        ttk.Button(control_frame, text="Actualizar", command=self.update_graph).pack(side=tk.RIGHT)

    def setup_settings_tab(self):
        """Configura la pestaña de configuración"""
        frame = ttk.Frame(self.tab_settings)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Configuración del modelo predictivo
        ttk.Label(frame, text="Modelo Predictivo", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        
        ttk.Label(frame, text="Sensibilidad:").pack(anchor=tk.W, pady=(10,0))
        self.contamination_slider = ttk.Scale(
            frame,
            from_=0.01,
            to=0.3,
            value=0.05,
            command=lambda v: self.predictive_ai.update_hyperparameters(contamination=float(v))
        )
        self.contamination_slider.pack(fill=tk.X, pady=5)
        
        # Opciones de limpieza
        ttk.Label(frame, text="Opciones de Limpieza", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(20,0))
        
        self.clean_prefetch = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="Limpiar Prefetch", variable=self.clean_prefetch).pack(anchor=tk.W)
        
        self.clean_logs = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="Limpiar Logs del Sistema", variable=self.clean_logs).pack(anchor=tk.W)

    # ========== MÉTODOS DE CONTROL ==========
    def start_services(self):
        """Inicia los servicios en segundo plano"""
        self.monitor_thread = threading.Thread(target=self.background_monitor, daemon=True)
        self.monitor_thread.start()

    def on_close(self):
        """Maneja el cierre de la aplicación"""
        self.running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1)
        self.root.destroy()

    # ========== MÉTODOS DE ANÁLISIS ==========
    def run_analysis_thread(self):
        """Inicia el análisis en un hilo separado"""
        threading.Thread(target=self.analyze_system, daemon=True).start()

    def analyze_system(self):
        """Realiza el análisis completo del sistema"""
        try:
            # Obtener métricas del sistema
            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent
            
            # Actualizar UI
            self.cpu_var.set(f"CPU: {cpu:.1f}%")
            self.ram_var.set(f"RAM: {ram:.1f}%")
            self.disk_var.set(f"Disco: {disk:.1f}%")
            self.status_bar.config(text=f"CPU: {cpu:.1f}% | RAM: {ram:.1f}% | Disco: {disk:.1f}%")
            
            # Guardar en base de datos
            with self.db_lock:
                errors = self.db.count_recent_errors()
                self.db.insert_system_stats(cpu, ram, disk, errors)
            
            # Generar alertas
            alerts = []
            if cpu > 80:
                alerts.append({"message": f"CPU alta ({cpu:.1f}%)", "severity": "HIGH" if cpu > 90 else "MEDIUM"})
            if ram > 85:
                alerts.append({"message": f"RAM alta ({ram:.1f}%)", "severity": "HIGH" if ram > 90 else "MEDIUM"})
            if disk > 90:
                alerts.append({"message": f"Disco lleno ({disk:.1f}%)", "severity": "HIGH"})
            
            # Análisis predictivo
            predictive_alerts = self.predictive_ai.analyze_predictive(cpu, ram, disk, errors)
            alerts.extend(predictive_alerts)
            
            # Mostrar alertas
            self.show_alerts(alerts)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error en análisis: {str(e)}")
        finally:
            self.stop_blinking_alien()

    def show_alerts(self, alerts):
        """Muestra las alertas en el área de texto"""
        self.alerts_text.delete(1.0, tk.END)
        
        if not alerts:
            self.alerts_text.insert(tk.END, "✅ Sistema estable\n", "normal")
            self.alerts_text.tag_config("normal", foreground="#50FA7B")
            return
            
        for alert in alerts:
            color = "#FF5555" if alert.get("severity") == "HIGH" else "#FFB86C"
            self.alerts_text.insert(tk.END, f"⚠️ {alert['message']}\n", alert["severity"])
            self.alerts_text.tag_config(alert["severity"], foreground=color)
            
            # Enviar notificación
            self.notifier.send_notification("Alerta del Sistema", alert["message"])
            
            # Registrar en base de datos
            with self.db_lock:
                self.db.insert_alert(alert["message"], alert.get("severity", "MEDIUM"))
        
        # Cambiar color del alien si hay alertas graves
        if any(a.get("severity") == "HIGH" for a in alerts):
            self.start_blinking_alien('red')

    # ========== MÉTODOS DE LIMPIEZA ==========
    def advanced_clean(self):
        """Ejecuta la limpieza avanzada del sistema"""
        progress_win = tk.Toplevel(self.root)
        progress_win.title("Limpieza Avanzada")
        progress_win.geometry("500x120")
        progress_win.resizable(False, False)
        
        # Configurar ventana de progreso
        ttk.Label(progress_win, text="Limpiando archivos temporales...").pack(pady=10)
        progress = ttk.Progressbar(progress_win, orient="horizontal", length=450, mode="determinate")
        progress.pack(pady=5)
        status = ttk.Label(progress_win, text="Preparando...")
        status.pack()

        def do_clean():
            """Función que realiza la limpieza en segundo plano"""
            targets = [tempfile.gettempdir()]
            
            # Agregar prefetch si está habilitado
            if self.clean_prefetch.get():
                prefetch = os.path.join(os.environ.get('SystemRoot', r'C:\Windows'), 'Prefetch')
                if os.path.exists(prefetch):
                    targets.append(prefetch)
            
            # Agregar logs si está habilitado
            if self.clean_logs.get():
                logs = os.path.join(os.environ.get('SystemRoot', r'C:\Windows'), 'Logs')
                if os.path.exists(logs):
                    targets.append(logs)
            
            total = len(targets)
            deleted = 0
            
            # Procesar cada objetivo
            for i, target in enumerate(targets):
                status.config(text=f"Limpiando: {os.path.basename(target)}...")
                progress['value'] = (i / total) * 50
                progress_win.update()
                
                deleted += self.cleaner.clean_directory(target)
                progress['value'] = 50 + (i / total) * 50
                progress_win.update()
            
            # Finalizar
            status.config(text=f"✅ Listo! Eliminados {deleted} archivos")
            self.notifier.send_notification("Optimizer AI", "Limpieza completada")
            time.sleep(1.5)
            progress_win.destroy()
            self.stop_blinking_alien()

        # Ejecutar en un hilo separado
        threading.Thread(target=do_clean, daemon=True).start()

    # ========== MÉTODOS DE VISUALIZACIÓN ==========
    def update_graph(self):
        """Actualiza el gráfico con datos históricos"""
        metric = self.graph_var.get()
        
        try:
            # Obtener datos de la base de datos
            conn = sqlite3.connect(self.db.db_path)
            query = f"""
                SELECT timestamp, {metric} 
                FROM system_stats 
                WHERE timestamp >= datetime('now', '-7 days')
                ORDER BY timestamp
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if not df.empty:
                # Procesar datos
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                self.ax.clear()
                
                # Configurar colores según la métrica
                color = "#BD93F9" if metric == 'cpu' else "#FF79C6" if metric == 'ram' else "#8BE9FD"
                
                # Dibujar gráfico
                self.ax.plot(df['timestamp'], df[metric], color=color, linewidth=2)
                self.ax.set_title(f"Uso de {metric.upper()} (7 días)", pad=15)
                self.ax.set_ylabel("Porcentaje (%)")
                self.ax.grid(color='#444444', linestyle='--')
                
                # Actualizar canvas
                self.canvas.draw()
                
        except Exception as e:
            print(f"Error al actualizar gráfico: {str(e)}")

    def show_system_info(self):
        """Muestra información detallada del sistema"""
        try:
            c = wmi.WMI()
            
            # Obtener información del sistema
            bios = c.Win32_BIOS()[0]
            os_info = c.Win32_OperatingSystem()[0]
            cpu = c.Win32_Processor()[0]
            gpu = c.Win32_VideoController()[0]
            
            # Formatear información
            info = f"""
            🖥️ Información del Sistema:
            
            • Sistema Operativo:
              {os_info.Caption}
              Versión: {os_info.Version}
            
            • Hardware:
              CPU: {cpu.Name}
              Núcleos: {cpu.NumberOfCores}
              GPU: {gpu.Caption}
            
            • BIOS:
              {bios.Manufacturer}
              Versión: {bios.SMBIOSBIOSVersion}
            """
            
            # Mostrar ventana de información
            messagebox.showinfo("Información del Sistema", info.strip())
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo obtener información: {str(e)}")

    # ========== MÉTODOS DE ACTUALIZACIÓN ==========
    def update_ui(self):
        """Actualización periódica de la interfaz"""
        if not self.running:
            return
            
        self.update_graph()
        self.root.after(30000, self.update_ui)

    def update_temperature_bar(self):
        """Actualiza la barra de temperatura/uso de CPU"""
        try:
            cpu_usage = psutil.cpu_percent()
            self.temp_bar['value'] = cpu_usage
            
            # Cambiar color según el uso
            if cpu_usage < 60:
                self.temp_bar.configure(style='green.Horizontal.TProgressbar')
            elif 60 <= cpu_usage < 80:
                self.temp_bar.configure(style='yellow.Horizontal.TProgressbar')
            else:
                self.temp_bar.configure(style='red.Horizontal.TProgressbar')
                
        except Exception as e:
            print(f"Monitor de recursos: {str(e)}")
        finally:
            if self.running:
                self.root.after(5000, self.update_temperature_bar)

    # ========== MÉTODOS DE MONITOREO ==========
    def background_monitor(self):
        """Monitoreo continuo en segundo plano"""
        while self.running:
            idle_time = self.get_idle_time()
            
            # Ejecutar análisis y limpieza después de 2 horas de inactividad
            if idle_time > 7200:  
                self.run_analysis_thread()
                self.advanced_clean()
                
            time.sleep(600)

    def get_idle_time(self):
        """Obtiene el tiempo de inactividad del sistema (Windows)"""
        if os.name != 'nt':
            return 0
            
        try:
            class LASTINPUTINFO(ctypes.Structure):
                _fields_ = [('cbSize', ctypes.c_uint), ('dwTime', ctypes.c_uint)]
                
            info = LASTINPUTINFO()
            info.cbSize = ctypes.sizeof(LASTINPUTINFO)
            
            if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info)):
                millis = ctypes.windll.kernel32.GetTickCount() - info.dwTime
                return millis / 1000.0
            return 0
        except:
            return 0

    # ========== MÉTODOS DEL ALIEN ==========
    def start_blinking_alien(self, color):
        """Inicia el efecto de parpadeo del alien"""
        if not self.blinking:
            self.blinking = True
            self.blink_color = color
            self._blink_alien()

    def _blink_alien(self):
        """Controla el ciclo de parpadeo"""
        if self.blinking:
            self.blink_state = not self.blink_state
            current_color = self.blink_color if self.blink_state else 'normal'
            self.change_alien_color(current_color)
            self.root.after(500, self._blink_alien)

    def stop_blinking_alien(self):
        """Detiene el parpadeo del alien"""
        self.blinking = False
        self.change_alien_color('normal')

    def change_alien_color(self, state):
        """Cambia el color del alien con manejo seguro (CORREGIDO)"""
        try:
            if hasattr(self, 'alien_images') and state in self.alien_images:
                self.alien_label.config(image=self.alien_images[state])
            else:
                print(f"Estado '{state}' no encontrado en alien_images")
        except Exception as e:
            print(f"Error cambiando estado alien: {str(e)}")

# ========== FUNCIONES DE INICIO ==========
def is_admin():
    """Verifica si el programa tiene privilegios de administrador"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if __name__ == "__main__":
    # Corregir problemas de Windows
    fix_wndproc_errors()
    
    # Solicitar elevación si es necesario
    if os.name == 'nt' and not is_admin():
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            sys.exit()
        except Exception as e:
            print(f"Error solicitando elevación: {str(e)}")
            sys.exit()
    
    # Iniciar aplicación
    root = tk.Tk()
    app = OptimizerApp(root)
    root.mainloop()