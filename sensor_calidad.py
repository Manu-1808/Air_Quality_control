import threading
import queue
import time
import tkinter as tk
import customtkinter as ctk
import re
import serial

ctk.set_appearance_mode("dark")  # "light", "dark", "system"
ctk.set_default_color_theme("green")  # "blue", "green", "dark-blue", "custom"

class sensor_calidad(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Control de Calidad del Aire (AQC)")
        self.geometry("900x700")
        self.minsize(800, 600)

        self.data_queue = queue.Queue()
        self.running = True
        self.alerta_mostrada = False

        # Buffer para valores MQ135 (últimos 50)
        self.mq135_values = []

        self.setup_ui()

        # Intentar conexión con puertos blutu o usb
        puertos = ['/dev/rfcomm0', '/dev/ttyUSB0', '/dev/ttyACM0']
        self.ser = None
        for puerto in puertos:
            try:
                self.ser = serial.Serial(puerto, 9600, timeout=1)
                print(f"Conectado a {puerto}")
                break
            except serial.SerialException:
                continue

        if not self.ser:
            print("No se pudo conectar a ningún puerto serial.")

        if self.ser:
            self.thread = threading.Thread(target=self.leer_datos, daemon=True)
            self.thread.start()

        self.after(100, self.actualizar_ui)

    def setup_ui(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header_frame.pack(pady=(10, 5), fill=tk.X)

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="AIR QUALITY CONTROL (AQC)",
            font=("Arial", 20, "bold")
        )
        self.title_label.pack()

        self.metrics_frame = ctk.CTkFrame(self.main_frame)
        self.metrics_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Temperatura
        self.temp_frame = ctk.CTkFrame(self.metrics_frame)
        self.temp_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.temp_icon = ctk.CTkLabel(self.temp_frame, text="🌡️", font=("Arial", 40))
        self.temp_icon.pack(pady=(10, 0))
        self.temp_label = ctk.CTkLabel(self.temp_frame, text="--.- °C", font=("Arial", 24, "bold"))
        self.temp_label.pack()
        ctk.CTkLabel(self.temp_frame, text="Temperatura", font=("Arial", 14), text_color="gray").pack()

        # Humedad
        self.hum_frame = ctk.CTkFrame(self.metrics_frame)
        self.hum_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.hum_icon = ctk.CTkLabel(self.hum_frame, text="💧", font=("Arial", 40))
        self.hum_icon.pack(pady=(10, 0))
        self.hum_label = ctk.CTkLabel(self.hum_frame, text="--.- %", font=("Arial", 24, "bold"))
        self.hum_label.pack()
        ctk.CTkLabel(self.hum_frame, text="Humedad", font=("Arial", 14), text_color="gray").pack()

        # Calidad del Aire
        self.air_frame = ctk.CTkFrame(self.metrics_frame)
        self.air_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")
        self.air_icon = ctk.CTkLabel(self.air_frame, text="🍃", font=("Arial", 40))
        self.air_icon.pack(pady=(10, 0))
        self.air_label = ctk.CTkLabel(self.air_frame, text="---", font=("Arial", 24, "bold"))
        self.air_label.pack()
        ctk.CTkLabel(self.air_frame, text="Calidad del Aire", font=("Arial", 14), text_color="gray").pack()

        # Gráfico MQ135
        self.chart_frame = ctk.CTkFrame(self.main_frame, height=200)
        self.chart_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        self.chart_label = ctk.CTkLabel(self.chart_frame, text="Histórico MQ135 (Calidad Aire)", font=("Arial", 16))
        self.chart_label.pack(pady=10)

        self.canvas = tk.Canvas(self.chart_frame, bg="#f0f0f0", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.metrics_frame.grid_columnconfigure(0, weight=1)
        self.metrics_frame.grid_columnconfigure(1, weight=1)
        self.metrics_frame.grid_columnconfigure(2, weight=1)

        self.status_bar = ctk.CTkLabel(self.main_frame, text="Desarrollado por: Pelon's Team | v1.2", font=("Arial", 10), text_color="gray")
        self.status_bar.pack(side=tk.BOTTOM, pady=(0, 10))

    def leer_datos(self):
        while self.running:
            try:
                if self.ser.in_waiting:
                    linea = self.ser.readline().decode('utf-8').strip()
                    if linea:
                        self.procesar_linea(linea)
                time.sleep(0.1)
            except Exception as e:
                print("Error leyendo serial:", e)

    def procesar_linea(self, linea):
        self.data_queue.put(linea)

    def actualizar_ui(self):
        try:
            while not self.data_queue.empty():
                data = self.data_queue.get_nowait()
                self.procesar_datos(data)
        except queue.Empty:
            pass

        self.after(100, self.actualizar_ui)

    def procesar_datos(self, data):
        pattern = r"Temp:([\d.]+),Hum:([\d.]+),MQ135:(\d+),Calidad:(\w+)"
        match = re.search(pattern, data)

        if not match:
            print(f"Datos no reconocidos: {data}")
            return

        try:
            temp = match.group(1)
            hum = match.group(2)
            mq135 = int(match.group(3))  # valor entero
            calidad = match.group(4)

            self.temp_label.configure(text=f"{temp} °C")
            self.hum_label.configure(text=f"{hum} %")
            self.air_label.configure(text=calidad)

            # Actualizar buffer MQ135
            self.mq135_values.append(mq135)
            if len(self.mq135_values) > 50:
                self.mq135_values.pop(0)

            # Cambiar color y emoji según calidad
            if calidad == "Excelente":
                self.air_label.configure(text_color="#2ecc71")
                self.air_icon.configure(text="😊")
            elif calidad == "Buena":
                self.air_label.configure(text_color="#27ae60")
                self.air_icon.configure(text="🙂")
            elif calidad == "Moderada":
                self.air_label.configure(text_color="#f39c12")
                self.air_icon.configure(text="😐")
            elif calidad == "Mala":
                self.air_label.configure(text_color="#e74c3c")
                self.air_icon.configure(text="😷")
                if not self.alerta_mostrada:
                    self.alerta_mostrada = True
                    self.mostrar_alerta("¡Alerta!", "Calidad del aire mala. Ventila el área.")
            elif calidad == "Peligrosa":
                self.air_label.configure(text_color="#c0392b")
                self.air_icon.configure(text="⚠️")
                if not self.alerta_mostrada:
                    self.alerta_mostrada = True
                    self.mostrar_alerta("¡Peligro!", "Calidad del aire peligrosa. Evita el área.")

            self.dibujar_grafico()

        except Exception as e:
            print(f"Error procesando datos: {e}")

    def dibujar_grafico(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()

        # Ejes
        margin_left = 50
        margin_bottom = 50
        margin_top = 20
        margin_right = 20

        # Eje X
        self.canvas.create_line(margin_left, h - margin_bottom, w - margin_right, h - margin_bottom, width=2)
        # Eje Y
        self.canvas.create_line(margin_left, margin_top, margin_left, h - margin_bottom, width=2)

        if len(self.mq135_values) < 2:
            return  # No hay suficientes datos para graficar

        max_val = max(self.mq135_values)
        min_val = min(self.mq135_values)

        # Para evitar división por cero si todos valores iguales
        rango = max_val - min_val if max_val != min_val else 1

        puntos = []
        num_puntos = len(self.mq135_values)
        ancho_grafico = w - margin_left - margin_right
        paso_x = ancho_grafico / (num_puntos - 1)

        for i, val in enumerate(self.mq135_values):
            x = margin_left + i * paso_x
            # Escalar y al alto del canvas invertido (mayor valor arriba)
            y = h - margin_bottom - ((val - min_val) / rango) * (h - margin_bottom - margin_top)
            puntos.append((x, y))

        # Dibujar líneas entre puntos
        for i in range(len(puntos) - 1):
            self.canvas.create_line(puntos[i][0], puntos[i][1], puntos[i+1][0], puntos[i+1][1], fill="green", width=2)

        # Dibujar puntos
        for (x, y) in puntos:
            self.canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="green", outline="")

        # Etiquetas de eje Y
        for i in range(5):
            val = min_val + i * rango / 4
            y = h - margin_bottom - i * (h - margin_bottom - margin_top) / 4
            self.canvas.create_text(margin_left - 30, y, text=f"{int(val)}", fill="black")

        # Etiqueta de eje X
        self.canvas.create_text(w / 2, h - margin_bottom + 30, text="Muestras recientes", fill="black")

    def mostrar_alerta(self, titulo, mensaje):
        alerta = ctk.CTkToplevel(self)
        alerta.geometry("300x150")
        alerta.title(titulo)
        alerta.grab_set()

        label = ctk.CTkLabel(alerta, text=mensaje, font=("Arial", 14))
        label.pack(pady=20)

        boton = ctk.CTkButton(alerta, text="Cerrar", command=lambda: (alerta.destroy(), self.reset_alerta()))
        boton.pack(pady=10)

    def reset_alerta(self):
        self.alerta_mostrada = False

    def on_close(self):
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.destroy()

if __name__ == "__main__":
    app = sensor_calidad()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
