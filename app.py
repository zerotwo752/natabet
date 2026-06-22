import simpy
import random
import tkinter as tk
from tkinter import ttk
import threading
import queue
import time

# --- IMPORTACIONES PARA GRÁFICOS ---
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# --- CONFIGURACIÓN DE LA SIMULACIÓN AS IS ---
SEMILLA = 42
TIEMPO_SIMULACION = 28800  # 8 horas de jornada en segundos: 8:00 a. m. - 4:00 p. m.
MEDIA_ENTRADA = 18  # AS IS semi automático: llega más demanda de la que el cuello manual puede absorber.
DESVIACION_ENTRADA = 4
PROBABILIDAD_BOTELLON_BUENO = 0.95
PROBABILIDAD_BOTELLON_RETRASO = 0.04  # Botellas aprobadas visualmente, pero detectadas tarde como defectuosas.
TIEMPO_RETRASO_DEFECTO = 75  # Tiempo perdido promedio por botella defectuosa detectada en proceso.
LITROS_POR_BOTELLON = 6

CAPACIDAD_INSPECCION = 3
CAPACIDAD_LAVADO_MANUAL = 4
CAPACIDAD_ENJUAGUE = 4
CAPACIDAD_LLENADO = 2
CAPACIDAD_SELLADO = 2

TIEMPO_INSPECCION = 8
TIEMPO_LAVADO_MANUAL = 90
TIEMPO_ENJUAGUE = 40
TIEMPO_LLENADO = 35
TIEMPO_SELLADO = 15

class EmbotelladoraAsIsGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulador Planta Embotelladora - Panel de Rendimiento Avanzado")
        self.root.geometry("1200x750")
        self.root.configure(bg="#111416")  
        
        self.root.resizable(True, True)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # --- CONFIGURACIÓN DE ESTILOS ---
        style = ttk.Style()
        style.theme_use('default')
        style.configure('TNotebook', background='#111416', borderwidth=0)
        style.configure('TNotebook.Tab', background='#23272a', foreground='#99aab5', 
                        font=('Segoe UI', 10, 'bold'), padding=[15, 5])
        style.map('TNotebook.Tab', background=[('selected', '#1a1d20')], foreground=[('selected', '#57f287')])
        
        self.var_tiempo = tk.StringVar(value="00:00:00")
        self.var_llegaron = tk.StringVar(value="0")
        self.var_exito = tk.StringVar(value="0")         
        self.var_defectos = tk.StringVar(value="0")      
        self.var_mermas = tk.StringVar(value="0")        
        self.var_retrasos = tk.StringVar(value="0")
        self.var_modo_vel = tk.StringVar(value="Velocidad: Normal (1s/s)")
        
        self.resumen_metrics = {
            "GENERAL": {"eficiencia": tk.StringVar(value="0.0%"), "descarte": tk.StringVar(value="0.0%"), "tiempo_promedio": tk.StringVar(value="0.0 s")},
            "MANUAL": {"cola": tk.StringVar(value="0"), "uso": tk.StringVar(value="0/4 Op"), "tiempo_promedio": tk.StringVar(value="0.0 s")},
            "RETRASO": {"cola": tk.StringVar(value="0"), "uso": tk.StringVar(value="0"), "tiempo_promedio": tk.StringVar(value="0.0 s")},
            "ENJUAGUE": {"cola": tk.StringVar(value="0"), "uso": tk.StringVar(value="0/4 Op"), "tiempo_promedio": tk.StringVar(value="0.0 s")},
            "LLENADO": {"cola": tk.StringVar(value="0"), "uso": tk.StringVar(value="0/2 Op"), "tiempo_promedio": tk.StringVar(value="0.0 s")},
            "SELLADO": {"cola": tk.StringVar(value="0"), "uso": tk.StringVar(value="0/2 Op"), "tiempo_promedio": tk.StringVar(value="0.0 s")}
        }
        
        self.total_llegaron = 0
        self.botellas_defectuosas_inicio = 0
        self.botellas_exito = 0
        self.mermas_agua = 0
        self.botellas_con_retraso = 0
        self.tiempo_total_retrasos = 0.0
        self.tiempo_total_botellas_exitosas = 0.0
        
        self.historico_tiempo = []
        self.historico_procesados = []
        self.historico_colas = {"MANUAL": [], "ENJUAGUE": [], "LLENADO": [], "SELLADO": [], "RETRASO": []}
        self.contador_estaciones = {"MANUAL": 0, "ENJUAGUE": 0, "LLENADO": 0, "SELLADO": 0}
        self.tiempo_total_estaciones = {"MANUAL": 0.0, "ENJUAGUE": 0.0, "LLENADO": 0.0, "SELLADO": 0.0}
        self.historico_estaciones = {"MANUAL": [], "ENJUAGUE": [], "LLENADO": [], "SELLADO": [], "RETRASO": []}
        self.contador_muestreo = 0
        
        self.simulacion_activa = False
        self.simulacion_pausada = False 
        self.hilo_iniciado = False
        
        self.cola_mensajes_gui = queue.Queue(maxsize=2000) 
        self.mapeo_bolitas = {}
        
        self.slots_inspeccion = [False] * CAPACIDAD_INSPECCION
        self.slots_manual = [False] * CAPACIDAD_LAVADO_MANUAL
        self.slots_enjuague = [False] * CAPACIDAD_ENJUAGUE
        self.slots_llenado = [False] * CAPACIDAD_LLENADO
        self.slots_sellado = [False] * CAPACIDAD_SELLADO
        self.conteo_colas_visuales = {"MANUAL": 0, "ENJUAGUE": 0, "LLENADO": 0, "SELLADO": 0}
        
        self.main_container = tk.Frame(self.root, bg="#111416")
        self.main_container.grid(row=0, column=0, sticky="nsew")
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(1, weight=0)
        self.main_container.grid_columnconfigure(0, weight=1)

        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 0))
        
        self.tab_simulacion = tk.Frame(self.notebook, bg="#111416")
        self.tab_datos = tk.Frame(self.notebook, bg="#111416")
        
        self.notebook.add(self.tab_simulacion, text=" 💻 APARTADO: SIMULACIÓN ")
        self.notebook.add(self.tab_datos, text=" 📊 APARTADO: DATOS Y RENDIMIENTO ")
        
        self.crear_barra_controles_global()
        self.crear_interfaz_simulacion()
        self.crear_interfaz_datos()

    def crear_barra_controles_global(self):
        frame_controls = tk.Frame(self.main_container, bg="#111416", height=80)
        frame_controls.grid(row=1, column=0, sticky="ew", padx=15, pady=10)
        frame_controls.pack_propagate(False)
        
        frame_speed = tk.Frame(frame_controls, bg="#1a1d20", padx=15, pady=5, bd=1, relief="solid")
        frame_speed.pack(side="left", fill="y", padx=5)
        
        tk.Label(frame_speed, text="⚡ ESCALA ACELERADORA DE TIEMPO (JORNADA)", 
                 font=("Segoe UI", 8, "bold"), fg="#ffffff", bg="#1a1d20").pack(anchor="w")
        
        self.sld_velocidad = tk.Scale(frame_speed, from_=1, to=4, orient=tk.HORIZONTAL, 
                                      bg="#1a1d20", fg="#57f287", highlightthickness=0, 
                                      length=250, showvalue=False, command=self.actualizar_texto_velocidad)
        self.sld_velocidad.pack(side="left", pady=2)
        self.sld_velocidad.set(1)
        
        self.lbl_modo = tk.Label(frame_speed, textvariable=self.var_modo_vel, 
                                 font=("Segoe UI", 9, "bold"), fg="#57f287", bg="#1a1d20", width=25, anchor="w")
        self.lbl_modo.pack(side="left", padx=10)
        
        self.btn_run = tk.Button(frame_controls, text="▶ INICIAR JORNADA", 
                                 font=("Segoe UI", 10, "bold"), bg="#2ecc71", fg="white", 
                                 bd=0, padx=25, cursor="hand2", command=self.comenzar)
        self.btn_run.pack(side="right", fill="y", padx=5, pady=5)

        self.btn_pause = tk.Button(frame_controls, text="⏸ PAUSAR", 
                                   font=("Segoe UI", 10, "bold"), bg="#e67e22", fg="white", 
                                   bd=0, padx=25, cursor="hand2", command=self.pausar)
        self.btn_pause.pack(side="right", fill="y", padx=5, pady=5)
        self.btn_pause.config(state="disabled")

    def crear_interfaz_simulacion(self):
        self.tab_simulacion.grid_rowconfigure(0, weight=0)
        self.tab_simulacion.grid_rowconfigure(1, weight=1)
        self.tab_simulacion.grid_columnconfigure(0, weight=1)

        frame_top = tk.Frame(self.tab_simulacion, bg="#1a1d20", padx=15, pady=8)
        frame_top.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        self.crear_tarjeta_stat(frame_top, "⏱️ RELOJ EN VIVO (HH:MM:SS)", self.var_tiempo, "#5865f2", 0)
        self.crear_tarjeta_stat(frame_top, "📥 INGRESADOS A PLANTA", self.var_llegaron, "#ffffff", 1)
        self.crear_tarjeta_stat(frame_top, "✅ BOTELLONES PROCESADOS", self.var_exito, "#57f287", 2)
        self.crear_tarjeta_stat(frame_top, "🗑️ DESCARTADOS INICIALES", self.var_defectos, "#ed4245", 3)
        self.crear_tarjeta_stat(frame_top, "💧 MERMA DE AGUA (LITROS)", self.var_mermas, "#fee75c", 4)
        self.crear_tarjeta_stat(frame_top, "⚠️ BOTELLAS CON RETRASO", self.var_retrasos, "#faa61a", 5)

        self.canvas = tk.Canvas(self.tab_simulacion, bg="#1a1d20", highlightthickness=0)
        self.canvas.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        self.disenar_entorno_planta()

    def crear_interfaz_datos(self):
        self.tab_datos.grid_rowconfigure(0, weight=1)
        self.tab_datos.grid_columnconfigure(0, weight=0) 
        self.tab_datos.grid_columnconfigure(1, weight=1) 

        self.sidebar_rendimiento = tk.Frame(self.tab_datos, bg="#1a1d20", width=280, padx=5, pady=5)
        self.sidebar_rendimiento.grid(row=0, column=0, sticky="nsw", padx=(10, 5), pady=10)
        self.sidebar_rendimiento.pack_propagate(False)
        
        tk.Label(self.sidebar_rendimiento, text=" Rendimiento de Planta", font=("Segoe UI", 11, "bold"), fg="#ffffff", bg="#1a1d20").pack(anchor="w", pady=10, padx=5)
        
        self.botones_categoria = {}
        self.categoria_actual = "GENERAL"
        
        categorias = [
            ("GENERAL", "📈 Resumen General", self.resumen_metrics["GENERAL"]["tiempo_promedio"], "Prom. total: "),
            ("MANUAL", "🧼 Lavado Manual", self.resumen_metrics["MANUAL"]["tiempo_promedio"], "Promedio: "),
            ("RETRASO", "⚠️ Botellas con retraso", self.resumen_metrics["RETRASO"]["tiempo_promedio"], "Tiempo perdido: "),
            ("ENJUAGUE", "🚿 Módulo Enjuague", self.resumen_metrics["ENJUAGUE"]["tiempo_promedio"], "Promedio: "),
            ("LLENADO", "⚡ Módulo Llenado", self.resumen_metrics["LLENADO"]["tiempo_promedio"], "Promedio: "),
            ("SELLADO", "🏷️ Módulo Sellado", self.resumen_metrics["SELLADO"]["tiempo_promedio"], "Promedio: ")
        ]
        
        for clave, titulo, var_v, prefijo in categorias:
            btn = tk.Frame(self.sidebar_rendimiento, bg="#23272a", height=55, cursor="hand2", bd=0)
            btn.pack(fill="x", pady=2, padx=5)
            btn.pack_propagate(False)
            
            lbl_tit = tk.Label(btn, text=titulo, font=("Segoe UI", 9, "bold"), fg="#ffffff", bg="#23272a")
            lbl_tit.pack(anchor="w", padx=10, pady=(6, 2))
            
            frame_sub = tk.Frame(btn, bg="#23272a")
            frame_sub.pack(fill="x", padx=10)
            tk.Label(frame_sub, text=prefijo, font=("Segoe UI", 8), fg="#99aab5", bg="#23272a").pack(side="left")
            tk.Label(frame_sub, textvariable=var_v, font=("Consolas", 9, "bold"), fg="#57f287" if clave=="GENERAL" else "#ed4245", bg="#23272a").pack(side="left")
            
            for widget in (btn, lbl_tit, frame_sub):
                widget.bind("<Button-1>", lambda e, k=clave: self.cambiar_categoria_grafico(k))
            
            self.botones_categoria[clave] = btn
            
        self.resaltar_categoria_activa()

        self.frame_detalle_grafico = tk.Frame(self.tab_datos, bg="#111416")
        self.frame_detalle_grafico.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        self.frame_detalle_grafico.grid_rowconfigure(3, weight=1)
        self.frame_detalle_grafico.grid_columnconfigure(0, weight=1)
        
        self.lbl_detalle_titulo = tk.Label(self.frame_detalle_grafico, text="MÓDULO: RESUMEN GENERAL", font=("Segoe UI", 14, "bold"), fg="#57f287", bg="#111416")
        self.lbl_detalle_titulo.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        self.lbl_sub_info = tk.Label(self.frame_detalle_grafico, text="Visualización de métricas críticas en tiempo real", font=("Segoe UI", 9), fg="#99aab5", bg="#111416")
        self.lbl_sub_info.grid(row=1, column=0, sticky="w", pady=(0, 10))

        self.frame_tiempos_promedio = tk.Frame(self.frame_detalle_grafico, bg="#111416")
        self.frame_tiempos_promedio.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        self.frame_tiempos_promedio.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        self.lbls_tiempos_promedio = {}
        estaciones_tiempo = [
            ("GENERAL", "📈 Total", "#57f287"),
            ("MANUAL", "🧼 Manual", "#3498db"),
            ("RETRASO", "⚠️ Retraso", "#ed4245"),
            ("ENJUAGUE", "🚿 Enjuague", "#fee75c"),
            ("LLENADO", "⚡ Llenado", "#faa61a"),
            ("SELLADO", "🏷️ Sellado", "#e67e22"),
        ]
        for col, (clave, titulo, color) in enumerate(estaciones_tiempo):
            frame_tiempo = tk.Frame(self.frame_tiempos_promedio, bg="#1a1d20", padx=8, pady=6)
            frame_tiempo.grid(row=0, column=col, sticky="ew", padx=3)
            tk.Label(frame_tiempo, text=titulo, font=("Segoe UI", 8, "bold"), fg=color, bg="#1a1d20").pack(anchor="w")
            lbl_valor = tk.Label(frame_tiempo, textvariable=self.resumen_metrics[clave]["tiempo_promedio"], font=("Consolas", 12, "bold"), fg="#ffffff", bg="#1a1d20")
            lbl_valor.pack(anchor="w")
            self.lbls_tiempos_promedio[clave] = lbl_valor
        
        self.fig, self.ax = plt.subplots(figsize=(7, 4))
        self.fig.patch.set_facecolor('#1a1d20')
        self.ax.set_facecolor('#111416')
        self.ax.grid(True, color='#2c2f33', linestyle='--')
        self.ax.tick_params(colors='white', labelsize=8)
        self.ax.set_title("Evolución Temporal", color="white", fontsize=10, fontweight="bold")
        
        self.linea_grafica, = self.ax.plot([], [], color='#57f287', linewidth=2)
        self.fig.tight_layout()
        
        self.canvas_graficos = FigureCanvasTkAgg(self.fig, master=self.frame_detalle_grafico)
        self.canvas_graficos.get_tk_widget().grid(row=3, column=0, sticky="nsew")

    def cambiar_categoria_grafico(self, clave):
        self.categoria_actual = clave
        self.resaltar_categoria_activa()
        
        titulos = {
            "GENERAL": ("MÓDULO: RESUMEN GENERAL", "#57f287"),
            "MANUAL": ("ESTACIÓN: LAVADO MANUAL DE ENVASE", "#3498db"),
            "RETRASO": ("ALERTA: BOTELLAS DEFECTUOSAS QUE GENERAN RETRASO", "#ed4245"),
            "ENJUAGUE": ("ESTACIÓN DE SANEAMIENTO: ENJUAGUE LÍQUIDO", "#fee75c"),
            "LLENADO": ("PUNTO CRÍTICO: LLENADORA DE BOTELLONES", "#faa61a"),
            "SELLADO": ("FASE FINAL: SELLADORA Y TAPONADORA", "#e67e22")
        }
        text, color = titulos[clave]
        self.lbl_detalle_titulo.config(text=text, fg=color)
        self.actualizar_graficos_matplotlib()

    def resaltar_categoria_activa(self):
        for k, f in self.botones_categoria.items():
            if k == self.categoria_actual:
                f.config(bg="#1a1d20")
                for w in f.winfo_children(): w.config(bg="#1a1d20")
            else:
                f.config(bg="#23272a")
                for w in f.winfo_children(): w.config(bg="#23272a")

    def actualizar_graficos_matplotlib(self):
        if len(self.historico_tiempo) == 0:
            return
            
        self.ax.clear()
        self.ax.set_facecolor('#111416')
        self.ax.grid(True, color='#2c2f33', linestyle='--')
        self.ax.tick_params(colors='white', labelsize=8)
        
        x_data = self.historico_tiempo if self.categoria_actual == "GENERAL" else list(range(len(self.historico_tiempo)))
        
        if self.categoria_actual == "GENERAL":
            self.ax.plot(x_data, self.historico_procesados, color='#57f287', linewidth=2, label="Botellones Listos")
            self.ax.set_title("Evolución de Producción Acumulada Real (Planta)", color='white', fontsize=10, fontweight='bold')
            self.ax.set_xlabel("Tiempo Simulado (Segundos)", color='#99aab5', fontsize=8)
            self.ax.set_ylabel("Unidades Finalizadas", color='#99aab5', fontsize=8)
        else:
            cola_data = self.historico_colas[self.categoria_actual]
            flujo_data = self.historico_estaciones[self.categoria_actual]
            colores = {"MANUAL": "#3498db", "RETRASO": "#ed4245", "ENJUAGUE": "#fee75c", "LLENADO": "#faa61a", "SELLADO": "#e67e22"}
            color = colores[self.categoria_actual]
            self.ax.plot(x_data, flujo_data, color=color, linewidth=2, label=f"Botellones que pasaron por {self.categoria_actual}")
            self.ax.plot(x_data, cola_data, color="#ed4245", linewidth=1.5, linestyle="--", label=f"Fila de espera {self.categoria_actual}")
            self.ax.set_title(f"Flujo acumulado y cola: {self.categoria_actual}", color='white', fontsize=10, fontweight='bold')
            self.ax.set_xlabel("Índice de Muestreos Operativos", color='#99aab5', fontsize=8)
            self.ax.set_ylabel("Cantidad de Botellones", color='#99aab5', fontsize=8)
            
        self.ax.legend(facecolor='#1a1d20', edgecolor='none', labelcolor='white', fontsize=8, loc='upper left')
        self.fig.tight_layout()
        self.canvas_graficos.draw_idle()

    def actualizar_texto_velocidad(self, valor):
        opciones = {
            "1": ("Velocidad: Normal (1s/s)", 1), 
            "2": ("Velocidad: Rápida (10s/s)", 10), 
            "3": ("Velocidad: Turbo (30s/s)", 30), 
            "4": ("Velocidad: Súper Alta (60s/s)", 60)
        }
        texto, _ = opciones.get(str(valor), ("Velocidad: Normal (1s/s)", 1))
        self.var_modo_vel.set(texto)

    def get_factor_velocidad(self):
        opciones = {"1": 1, "2": 10, "3": 30, "4": 60}
        return opciones.get(str(self.sld_velocidad.get()), 1)

    def crear_tarjeta_stat(self, parent, titulo, variable, color, col):
        frame = tk.Frame(parent, bg="#23272a", padx=10, pady=6)
        frame.grid(row=0, column=col, padx=5, sticky="nsew")
        parent.grid_columnconfigure(col, weight=1)
        tk.Label(frame, text=titulo, font=("Segoe UI", 7, "bold"), fg="#99aab5", bg="#23272a").pack(anchor="w")
        tk.Label(frame, textvariable=variable, font=("Consolas", 13, "bold"), fg=color, bg="#23272a").pack(anchor="w", pady=(2, 0))

    def disenar_entorno_planta(self):
        self.y_faja_ref = 160
        y = self.y_faja_ref
        self.canvas.create_line(20, y, 220, y, fill="#2c2f33", width=8, dash=(4, 2))
        self.canvas.create_line(150, y, 150, y + 110, fill="#ed4245", width=4, arrow=tk.LAST)
        self.canvas.create_line(220, y, 260, y - 70, fill="#2c2f33", width=6)
        self.canvas.create_line(260, y - 70, 460, y - 70, fill="#34495e", width=12) 
        self.canvas.create_line(460, y - 70, 500, y, fill="#2c2f33", width=6)
        self.canvas.create_line(500, y, 690, y, fill="#34495e", width=12) 
        self.canvas.create_line(690, y, 850, y, fill="#34495e", width=12) 
        self.canvas.create_line(850, y, 990, y, fill="#34495e", width=12) 
        self.canvas.create_line(990, y, 1080, y, fill="#2c2f33", width=8, dash=(4,2))

        self.op_inspeccion = [self.canvas.create_oval(45+i*25-10, y-45, 45+i*25+10, y-25, fill="#2ecc71", outline="#ffffff", width=2) for i in range(CAPACIDAD_INSPECCION)]
        self.canvas.create_text(70, y + 35, text=f"INSPECCIÓN\n({CAPACIDAD_INSPECCION} Op.)", fill="#ffffff", font=("Segoe UI", 8, "bold"))
        self.canvas.create_polygon(130, y + 110, 170, y + 110, 180, y + 135, 120, y + 135, fill="#2c2f33", outline="#ed4245")

        self.ops_manual = [self.canvas.create_oval(300+i*45-10, y-115, 300+i*45+10, y-95, fill="#2ecc71", outline="#ffffff", width=2) for i in range(CAPACIDAD_LAVADO_MANUAL)]
        self.canvas.create_text(370, y - 130, text=f"Lavado Manual ({CAPACIDAD_LAVADO_MANUAL} Op.)", fill="#959da5", font=("Segoe UI", 8, "bold"))
        self.canvas.create_text(355, y + 55, text="AS IS: lavado manual\nsin tambor automático", fill="#99aab5", font=("Segoe UI", 8, "bold"))

        self.ops_enjuague = [self.canvas.create_oval(540+i*35-10, y-45, 540+i*35+10, y-25, fill="#2ecc71", outline="#ffffff", width=2) for i in range(CAPACIDAD_ENJUAGUE)]
        self.canvas.create_text(595, y - 60, text=f"🚿 Enjuague ({CAPACIDAD_ENJUAGUE} Op.)", fill="#1abc9c", font=("Segoe UI", 8, "bold"))
        self.ops_llenado = [self.canvas.create_oval(750+i*50-10, y-45, 750+i*50+10, y-25, fill="#2ecc71", outline="#ffffff", width=2) for i in range(CAPACIDAD_LLENADO)]
        self.canvas.create_text(775, y - 60, text=f"⚡ Llenado ({CAPACIDAD_LLENADO} Op.)", fill="#faa61a", font=("Segoe UI", 8, "bold"))
        self.ops_sellado = [self.canvas.create_oval(900+i*50-10, y-45, 900+i*50+10, y-25, fill="#2ecc71", outline="#ffffff", width=2) for i in range(CAPACIDAD_SELLADO)]
        self.canvas.create_text(925, y - 60, text=f"🏷️ Sellado ({CAPACIDAD_SELLADO} Op.)", fill="#e67e22", font=("Segoe UI", 8, "bold"))

        self.txt_q_manual = self.canvas.create_text(205, y - 55, text="Cola: 0", fill="#ae9e8d", font=("Segoe UI", 8, "bold"))
        self.txt_q_enjuague = self.canvas.create_text(485, y - 20, text="Cola: 0", fill="#ae9e8d", font=("Segoe UI", 8, "bold"))
        self.txt_q_llenado = self.canvas.create_text(670, y - 20, text="Cola: 0", fill="#ae9e8d", font=("Segoe UI", 8, "bold"))
        self.txt_q_sellado = self.canvas.create_text(830, y - 20, text="Cola: 0", fill="#ae9e8d", font=("Segoe UI", 8, "bold"))

    def despachar_movimiento(self, id_botella, x_origen, y_origen, x_destino, y_destino, duracion_espera=0, estado="CAMINANDO", y_proceso=None, canal_cola=None):
        if not self.simulacion_activa: return
        try:
            self.cola_mensajes_gui.put_nowait(("MOVER", (id_botella, x_origen, y_origen, x_destino, y_destino, duracion_espera, estado, y_proceso, canal_cola)))
        except queue.Full:
            pass

    def actualizar_texto_cola_directo(self, canal, valor):
        try:
            self.cola_mensajes_gui.put_nowait(("FORZAR_COLA", (canal, valor)))
        except queue.Full:
            pass

    def comenzar(self):
        self.simulacion_pausada = False
        self.simulacion_activa = True
        self.btn_run.config(state="disabled", bg="#4f545c", text="▶ REPRODUCIENDO")
        self.btn_pause.config(state="normal", bg="#e67e22", text="⏸ PAUSAR")
        if not self.hilo_iniciado:
            random.seed(SEMILLA)
            self.hilo_iniciado = True
            threading.Thread(target=self.ejecutar_simpy_backend, daemon=True).start()
            self.procesar_logica_visual()

    def pausar(self):
        if self.simulacion_activa and not self.simulacion_pausada:
            self.simulacion_pausada = True
            self.btn_pause.config(state="disabled", bg="#4f545c", text="⏸ PAUSADO")
            self.btn_run.config(state="normal", bg="#2ecc71", text="▶ REANUDAR")

    def registrar_tiempo_estacion(self, estacion, inicio):
        self.tiempo_total_estaciones[estacion] += max(0, self.env.now - inicio)

    def formatear_promedio_estacion(self, estacion):
        cantidad = self.contador_estaciones[estacion]
        if cantidad == 0:
            return "0.0 s"
        promedio = self.tiempo_total_estaciones[estacion] / cantidad
        return f"{promedio:.1f} s"

    def formatear_promedio_total(self):
        if self.botellas_exito == 0:
            return "0.0 s"
        promedio = self.tiempo_total_botellas_exitosas / self.botellas_exito
        return f"{promedio:.1f} s"

    def formatear_promedio_retraso(self):
        if self.botellas_con_retraso == 0:
            return "0.0 s"
        promedio = self.tiempo_total_retrasos / self.botellas_con_retraso
        return f"{promedio:.1f} s"

    def ejecutar_simpy_backend(self):
        env = simpy.Environment()
        self.env = env
        self.res_inspeccion = simpy.Resource(env, capacity=CAPACIDAD_INSPECCION)
        self.res_lav_manual = simpy.Resource(env, capacity=CAPACIDAD_LAVADO_MANUAL)
        self.res_enjuague = simpy.Resource(env, capacity=CAPACIDAD_ENJUAGUE)
        self.res_llenado = simpy.Resource(env, capacity=CAPACIDAD_LLENADO)
        self.res_sellado = simpy.Resource(env, capacity=CAPACIDAD_SELLADO)
        
        env.process(self.generador_botellas(env))
        
        while env.now < TIEMPO_SIMULACION and self.simulacion_activa:
            if self.simulacion_pausada:
                time.sleep(0.1)
                continue
            
            factor_vel = self.get_factor_velocidad()
            paso_tiempo = max(1, factor_vel)
            env.run(until=min(TIEMPO_SIMULACION, env.now + paso_tiempo))
            
            segundos_totales = int(env.now)
            h = segundos_totales // 3600
            m = (segundos_totales % 3600) // 60
            s = segundos_totales % 60
            
            try:
                self.cola_mensajes_gui.put_nowait(("STATS", (
                    f"{h:02d}:{m:02d}:{s:02d}", self.total_llegaron, self.botellas_exito,
                    self.botellas_defectuosas_inicio, self.mermas_agua, self.botellas_con_retraso,
                    len(self.res_lav_manual.queue),
                    len(self.res_enjuague.queue), len(self.res_llenado.queue), len(self.res_sellado.queue),
                    self.res_inspeccion.count, self.res_lav_manual.count,
                    self.res_enjuague.count, self.res_llenado.count, self.res_sellado.count,
                    self.formatear_promedio_total(), self.formatear_promedio_estacion("MANUAL"), self.formatear_promedio_retraso(),
                    self.formatear_promedio_estacion("ENJUAGUE"), self.formatear_promedio_estacion("LLENADO"),
                    self.formatear_promedio_estacion("SELLADO"), segundos_totales
                )))
            except queue.Full:
                pass
                
            time.sleep(0.005 if factor_vel >= 30 else 0.02)
            
        if not self.simulacion_pausada: 
            self.cola_mensajes_gui.put(("FIN", None))

    def generador_botellas(self, env):
        id_b = 0
        while True:
            yield env.timeout(max(1, random.normalvariate(MEDIA_ENTRADA, DESVIACION_ENTRADA)))
            while self.simulacion_pausada: yield env.timeout(0.1)
            self.total_llegaron += 1
            id_b += 1
            env.process(self.flujo_botella(env, id_b))

    def flujo_botella(self, env, id_b):
        y = self.y_faja_ref
        inicio_flujo = env.now
        
        self.despachar_movimiento(id_b, 20, y, 45, y, estado="CAMINANDO")
        yield env.timeout(2)  
        
        with self.res_inspeccion.request() as req:
            yield req
            idx_insp = next(i for i in range(CAPACIDAD_INSPECCION) if not self.slots_inspeccion[i])
            self.slots_inspeccion[idx_insp] = True
            x_insp = 45 + (idx_insp * 25)
            self.despachar_movimiento(id_b, 45, y, x_insp, y, duracion_espera=TIEMPO_INSPECCION, estado="EN_PROCESO", y_proceso=y-15)
            yield env.timeout(TIEMPO_INSPECCION)
            self.slots_inspeccion[idx_insp] = False
        
        if random.random() > PROBABILIDAD_BOTELLON_BUENO:
            self.botellas_defectuosas_inicio += 1
            self.despachar_movimiento(id_b, 70, y, 150, y)
            yield env.timeout(2)
            self.despachar_movimiento(id_b, 150, y, 150, y + 120)
            return  

        self.despachar_movimiento(id_b, 70, y, 220, y)
        yield env.timeout(4)  

        self.despachar_movimiento(id_b, 220, y, 240, y-70, estado="CAMINANDO", canal_cola="MANUAL")
        yield env.timeout(3)
        self.actualizar_texto_cola_directo("MANUAL", len(self.res_lav_manual.queue) + 1)
        inicio_estacion = env.now
        with self.res_lav_manual.request() as req:
            yield req
            self.contador_estaciones["MANUAL"] += 1
            self.actualizar_texto_cola_directo("MANUAL", len(self.res_lav_manual.queue))
            idx_op = next(i for i in range(CAPACIDAD_LAVADO_MANUAL) if not self.slots_manual[i])
            self.slots_manual[idx_op] = True
            x_op = 300 + (idx_op * 45)
            self.despachar_movimiento(id_b, 240, y-70, x_op, y-70, duracion_espera=TIEMPO_LAVADO_MANUAL, estado="EN_PROCESO", y_proceso=y-85)
            yield env.timeout(TIEMPO_LAVADO_MANUAL)
            self.slots_manual[idx_op] = False
            self.registrar_tiempo_estacion("MANUAL", inicio_estacion)
        
        self.despachar_movimiento(id_b, x_op, y-70, 460, y-70)
        yield env.timeout(4)
        self.despachar_movimiento(id_b, 460, y-70, 500, y)
            
        yield env.timeout(3) 

        self.despachar_movimiento(id_b, 500, y, 485, y, estado="CAMINANDO", canal_cola="ENJUAGUE")
        yield env.timeout(3)
        self.actualizar_texto_cola_directo("ENJUAGUE", len(self.res_enjuague.queue) + 1)
        inicio_estacion = env.now
        with self.res_enjuague.request() as req:
            yield req
            self.contador_estaciones["ENJUAGUE"] += 1
            self.actualizar_texto_cola_directo("ENJUAGUE", len(self.res_enjuague.queue))
            idx_op = next(i for i in range(CAPACIDAD_ENJUAGUE) if not self.slots_enjuague[i])
            self.slots_enjuague[idx_op] = True
            x_op = 540 + (idx_op * 35)
            self.despachar_movimiento(id_b, 485, y, x_op, y, duracion_espera=TIEMPO_ENJUAGUE, estado="EN_PROCESO", y_proceso=y-15)
            yield env.timeout(TIEMPO_ENJUAGUE)
            self.slots_enjuague[idx_op] = False
            self.registrar_tiempo_estacion("ENJUAGUE", inicio_estacion)
            
        self.despachar_movimiento(id_b, x_op, y, 690, y)
        yield env.timeout(4)

        if random.random() < PROBABILIDAD_BOTELLON_RETRASO:
            self.botellas_con_retraso += 1
            self.tiempo_total_retrasos += TIEMPO_RETRASO_DEFECTO
            self.despachar_movimiento(id_b, 690, y, 690, y + 55, duracion_espera=TIEMPO_RETRASO_DEFECTO, estado="EN_PROCESO", y_proceso=y + 45)
            yield env.timeout(TIEMPO_RETRASO_DEFECTO)
            self.despachar_movimiento(id_b, 690, y + 55, 150, y + 120)
            return

        self.despachar_movimiento(id_b, 690, y, 670, y, estado="CAMINANDO", canal_cola="LLENADO")
        yield env.timeout(3)
        self.actualizar_texto_cola_directo("LLENADO", len(self.res_llenado.queue) + 1)
        inicio_estacion = env.now
        with self.res_llenado.request() as req:
            yield req
            self.contador_estaciones["LLENADO"] += 1
            self.actualizar_texto_cola_directo("LLENADO", len(self.res_llenado.queue))
            idx_op = next(i for i in range(CAPACIDAD_LLENADO) if not self.slots_llenado[i])
            self.slots_llenado[idx_op] = True
            x_op = 750 + (idx_op * 50)
            self.despachar_movimiento(id_b, 670, y, x_op, y, duracion_espera=TIEMPO_LLENADO, estado="EN_PROCESO", y_proceso=y-15)
            yield env.timeout(TIEMPO_LLENADO)
            self.slots_llenado[idx_op] = False
            self.registrar_tiempo_estacion("LLENADO", inicio_estacion)
            if random.random() < 0.002: self.mermas_agua += LITROS_POR_BOTELLON; return
            
        self.despachar_movimiento(id_b, x_op, y, 850, y)
        yield env.timeout(4)

        self.despachar_movimiento(id_b, 850, y, 830, y, estado="CAMINANDO", canal_cola="SELLADO")
        yield env.timeout(3)
        self.actualizar_texto_cola_directo("SELLADO", len(self.res_sellado.queue) + 1)
        inicio_estacion = env.now
        with self.res_sellado.request() as req:
            yield req
            self.contador_estaciones["SELLADO"] += 1
            self.actualizar_texto_cola_directo("SELLADO", len(self.res_sellado.queue))
            idx_op = next(i for i in range(CAPACIDAD_SELLADO) if not self.slots_sellado[i])
            self.slots_sellado[idx_op] = True
            x_op = 900 + (idx_op * 50)
            self.despachar_movimiento(id_b, 830, y, x_op, y, duracion_espera=TIEMPO_SELLADO, estado="EN_PROCESO", y_proceso=y-15)
            yield env.timeout(TIEMPO_SELLADO)
            self.slots_sellado[idx_op] = False
            self.registrar_tiempo_estacion("SELLADO", inicio_estacion)
        
        self.despachar_movimiento(id_b, x_op, y, 1060, y)
        yield env.timeout(5)
        self.botellas_exito += 1
        self.tiempo_total_botellas_exitosas += env.now - inicio_flujo

    def procesar_logica_visual(self):
        try:
            # Aumentamos la tasa de procesamiento por ciclo de la interfaz
            for _ in range(60):
                tipo, datos = self.cola_mensajes_gui.get_nowait()
                if tipo == "MOVER":
                    self.ejecutar_animacion_recorrido(*datos)
                elif tipo == "FORZAR_COLA":
                    canal, val = datos
                    self.conteo_colas_visuales[canal] = val
                    txt_map = {"MANUAL": self.txt_q_manual, "ENJUAGUE": self.txt_q_enjuague, "LLENADO": self.txt_q_llenado, "SELLADO": self.txt_q_sellado}
                    self.canvas.itemconfig(txt_map[canal], text=f"Cola: {val}", fill="#ed4245" if val > 0 else "#ae9e8d")
                elif tipo == "STATS":
                    t, lleg, ex, df, mr, retraso, q_mn, q_ej, q_ll, q_sl, c_in, c_mn, c_ej, c_ll, c_sl, avg_total, avg_mn, avg_retraso, avg_ej, avg_ll, avg_sl, segs = datos
                    self.var_tiempo.set(t)
                    self.var_llegaron.set(str(lleg))
                    self.var_exito.set(str(ex))
                    self.var_defectos.set(str(df))
                    self.var_mermas.set(str(mr))
                    self.var_retrasos.set(str(retraso))
                    
                    if lleg > 0:
                        self.resumen_metrics["GENERAL"]["eficiencia"].set(f"{(ex / lleg) * 100:.1f}%")
                        self.resumen_metrics["GENERAL"]["descarte"].set(f"{(df / lleg) * 100:.1f}%")
                    self.resumen_metrics["MANUAL"]["cola"].set(str(q_mn))
                    self.resumen_metrics["RETRASO"]["cola"].set(str(retraso))
                    self.resumen_metrics["ENJUAGUE"]["cola"].set(str(q_ej))
                    self.resumen_metrics["LLENADO"]["cola"].set(str(q_ll))
                    self.resumen_metrics["SELLADO"]["cola"].set(str(q_sl))
                    self.resumen_metrics["GENERAL"]["tiempo_promedio"].set(avg_total)
                    self.resumen_metrics["MANUAL"]["tiempo_promedio"].set(avg_mn)
                    self.resumen_metrics["RETRASO"]["tiempo_promedio"].set(avg_retraso)
                    self.resumen_metrics["ENJUAGUE"]["tiempo_promedio"].set(avg_ej)
                    self.resumen_metrics["LLENADO"]["tiempo_promedio"].set(avg_ll)
                    self.resumen_metrics["SELLADO"]["tiempo_promedio"].set(avg_sl)
                    
                    self.contador_muestreo += 1
                    frecuencia = 50 if self.get_factor_velocidad() >= 30 else 5
                    if self.contador_muestreo % frecuencia == 0:  
                        self.historico_tiempo.append(segs)
                        self.historico_procesados.append(ex)
                        self.historico_colas["MANUAL"].append(q_mn)
                        self.historico_colas["RETRASO"].append(retraso)
                        self.historico_colas["ENJUAGUE"].append(q_ej)
                        self.historico_colas["LLENADO"].append(q_ll)
                        self.historico_colas["SELLADO"].append(q_sl)
                        for estacion, total in self.contador_estaciones.items():
                            self.historico_estaciones[estacion].append(total)
                        self.historico_estaciones["RETRASO"].append(retraso)
                        self.actualizar_graficos_matplotlib()
                    
                    for i in range(CAPACIDAD_INSPECCION): self.canvas.itemconfig(self.op_inspeccion[i], fill="#00bfff" if i < c_in else "#2ecc71")
                    for i in range(CAPACIDAD_LAVADO_MANUAL): self.canvas.itemconfig(self.ops_manual[i], fill="#00bfff" if i < c_mn else "#2ecc71")
                    for i in range(CAPACIDAD_ENJUAGUE): self.canvas.itemconfig(self.ops_enjuague[i], fill="#00bfff" if i < c_ej else "#2ecc71")
                    for i in range(CAPACIDAD_LLENADO): self.canvas.itemconfig(self.ops_llenado[i], fill="#00bfff" if i < c_ll else "#2ecc71")
                    for i in range(CAPACIDAD_SELLADO): self.canvas.itemconfig(self.ops_sellado[i], fill="#00bfff" if i < c_sl else "#2ecc71")
                elif tipo == "FIN":
                    self.simulacion_activa = False
                    self.btn_run.config(state="disabled", bg="#4f545c", text="▶ JORNADA COMPLETA")
                    self.btn_pause.config(state="disabled", bg="#4f545c")
                    self.actualizar_graficos_matplotlib()
                    return
        except queue.Empty: pass
        if self.simulacion_activa: self.root.after(10, self.procesar_logica_visual)

    def ejecutar_animacion_recorrido(self, id_botella, x0, y0, x1, y1, espera, estado, y_proceso=None, canal_cola=None):
        factor_vel = self.get_factor_velocidad()
        
        # Corrección: El bypass de renderizado ya no aborta el flujo; solo limpia el canvas para que los datos sigan fluyendo
        if factor_vel >= 30:
            if id_botella in self.mapeo_bolitas:
                self.canvas.delete(self.mapeo_bolitas[id_botella])
                self.mapeo_bolitas.pop(id_botella, None)
            return

        if id_botella not in self.mapeo_bolitas:
            v_id = self.canvas.create_oval(x0-5, y0-5, x0+5, y0+5, fill="#00ffff", outline="#ffffff", width=1)
            self.mapeo_bolitas[id_botella] = v_id
        else: v_id = self.mapeo_bolitas[id_botella]

        if estado == "EN_PROCESO" and y_proceso is not None:
            self.canvas.itemconfig(v_id, fill="#fee75c") 
            def desplazar_a_puesto(cx, cy):
                if self.simulacion_pausada:
                    self.root.after(15, lambda: desplazar_a_puesto(cx, cy)); return
                completado = True
                paso_píxel = max(1, int(2 * (factor_vel / 5 if factor_vel > 1 else 1)))
                if cx < x1: cx = min(x1, cx + paso_píxel); completado = False
                elif cx > x1: cx = max(x1, cx - paso_píxel); completado = False
                if cy < y_proceso: cy = min(y_proceso, cy + paso_píxel); completado = False
                elif cy > y_proceso: cy = max(y_proceso, cy - paso_píxel); completado = False
                self.canvas.coords(v_id, cx-5, cy-5, cx+5, cy+5)
                if not completado: self.root.after(15, lambda: desplazar_a_puesto(cx, cy))
                else:
                    tiempo_real = int((espera * 1000) / (factor_vel * 15))
                    def finalizar_espera():
                        if self.simulacion_pausada: self.root.after(15, finalizar_espera)
                        else:
                            if id_botella in self.mapeo_bolitas: self.canvas.itemconfig(v_id, fill="#00ffff")
                    self.root.after(max(10, tiempo_real), finalizar_espera)
            desplazar_a_puesto(x0, y0)
            return

        def paso(cx, cy):
            if not self.simulacion_activa: return
            if self.simulacion_pausada: self.root.after(15, lambda: paso(cx, cy)); return
            target_x, target_y = x1, y1
            if canal_cola and self.conteo_colas_visuales.get(canal_cola, 0) > 0:
                pos_en_fila = max(0, self.conteo_colas_visuales[canal_cola] - 1)
                if canal_cola == "MANUAL": target_x = x1 - (pos_en_fila * 10); target_y = y1 + (pos_en_fila * 12)
                elif canal_cola in ["ENJUAGUE", "LLENADO", "SELLADO"]: target_x = x1 - (pos_en_fila * 12); target_y = y1

            llegó_x = (cx >= target_x) if target_x >= x0 else (cx <= target_x)
            llegó_y = (cy >= target_y) if target_y >= y0 else (cy <= target_y)

            if llegó_x and llegó_y:
                self.canvas.coords(v_id, target_x-5, target_y-5, target_x+5, target_y+5)
                if target_x >= 1050 or cy > 250:
                    self.canvas.delete(v_id)
                    self.mapeo_bolitas.pop(id_botella, None)
                return

            paso_píxel = max(1, int(2 * (factor_vel / 5 if factor_vel > 1 else 1)))
            if cx < target_x: cx = min(target_x, cx + paso_píxel)
            elif cx > target_x: cx = max(target_x, cx - paso_píxel)
            if cy < target_y: cy = min(target_y, cy + paso_píxel)
            elif cy > target_y: cy = max(target_y, cy - paso_píxel)
            self.canvas.coords(v_id, cx-5, cy-5, cx+5, cy+5)
            self.root.after(15, lambda: paso(cx, cy))

        paso(x0, y0)

if __name__ == "__main__":
    root = tk.Tk()
    app = EmbotelladoraAsIsGUI(root)
    root.mainloop()
