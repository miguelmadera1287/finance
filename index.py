import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import tkinter as tk
from tkinter import messagebox, filedialog

# Configuración de gráficos más estéticos
sns.set_style("darkgrid")

# Función para obtener datos de la acción
def get_stock_data(ticker, start_date, end_date):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date, auto_adjust=True)

        if df.empty:
            messagebox.showerror("Error", f"No hay datos para {ticker}. Verifica el ticker o las fechas.")
            return None

        return df
    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un problema al obtener los datos: {e}")
        return None

# Función para calcular indicadores técnicos
def add_indicators(df):
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['SMA_200'] = df['Close'].rolling(window=200).mean()
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['Daily Return'] = df['Close'].pct_change()

    # MACD
    short_ema = df['Close'].ewm(span=12, adjust=False).mean()
    long_ema = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = short_ema - long_ema
    df['Signal Line'] = df['MACD'].ewm(span=9, adjust=False).mean()

    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # Bollinger Bands
    df['Upper Band'] = df['SMA_50'] + (df['Close'].rolling(20).std() * 2)
    df['Lower Band'] = df['SMA_50'] - (df['Close'].rolling(20).std() * 2)

    # VWAP
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()

    # ADX (Average Directional Index)
    df['TR'] = df['High'].combine(df['Low'], max) - df['Low']
    df['ATR'] = df['TR'].rolling(window=14).mean()
    df['ADX'] = (df['ATR'].rolling(window=14).mean() / df['ATR']) * 100

    # Alertas de Trading
    df['Buy Signal'] = (df['RSI'] < 30) & (df['MACD'] > df['Signal Line'])
    df['Sell Signal'] = (df['RSI'] > 70) & (df['MACD'] < df['Signal Line'])

    return df

# Función para guardar datos en Excel y CSV
def save_data(df, ticker):
    file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx"), ("CSV Files", "*.csv")])
    if file_path:
        if file_path.endswith(".xlsx"):
            df.to_excel(file_path)
        else:
            df.to_csv(file_path)
        messagebox.showinfo("Éxito", f"Datos guardados en {file_path}")

# Función para graficar datos con indicador de carga
def plot_data():
    ticker = entry_ticker.get().strip().upper()
    start_date = entry_start.get().strip()
    end_date = entry_end.get().strip()

    if not ticker or not start_date or not end_date:
        messagebox.showwarning("Advertencia", "Por favor, completa todos los campos.")
        return

    # Mostrar mensaje de carga y deshabilitar botón
    status_label.config(text="Cargando datos...", fg="blue")
    btn_analyze.config(state=tk.DISABLED)
    root.update()  # Actualizar la interfaz

    df = get_stock_data(ticker, start_date, end_date)

    if df is not None:
        df = add_indicators(df)

        # Guardar datos automáticamente
        save_data(df, ticker)

        # Gráfico de Precio con Medias Móviles
        plt.figure(figsize=(12, 6))
        plt.plot(df.index, df['Close'], label='Precio de Cierre', color='blue')
        plt.plot(df.index, df['SMA_50'], label='SMA 50', color='orange')
        plt.plot(df.index, df['SMA_200'], label='SMA 200', color='red')
        plt.title(f'Precio y Medias Móviles de {ticker}')
        plt.xlabel('Fecha')
        plt.ylabel('Precio')
        plt.legend()
        plt.show()

        # Gráfico de MACD
        plt.figure(figsize=(12, 6))
        plt.plot(df.index, df['MACD'], label='MACD', color='purple')
        plt.plot(df.index, df['Signal Line'], label='Línea de Señal', color='black')
        plt.axhline(0, linestyle='--', color='gray')
        plt.title(f'MACD de {ticker}')
        plt.xlabel('Fecha')
        plt.legend()
        plt.show()

        # Gráfico de RSI
        plt.figure(figsize=(12, 6))
        plt.plot(df.index, df['RSI'], label='RSI', color='green')
        plt.axhline(70, linestyle='--', color='red', alpha=0.5)
        plt.axhline(30, linestyle='--', color='blue', alpha=0.5)
        plt.title(f'RSI de {ticker}')
        plt.xlabel('Fecha')
        plt.legend()
        plt.show()

    # Restablecer mensaje y botón
    status_label.config(text="Listo ✅", fg="green")
    btn_analyze.config(state=tk.NORMAL)

# Crear ventana con Tkinter
root = tk.Tk()
root.title("Análisis de Acciones")
root.geometry("400x380")
root.resizable(False, False)

# Crear menú
menubar = tk.Menu(root)
file_menu = tk.Menu(menubar, tearoff=0)
file_menu.add_command(label="Guardar Datos", command=lambda: save_data(get_stock_data(entry_ticker.get().upper(), entry_start.get().strip(), entry_end.get().strip()), entry_ticker.get().upper()))
file_menu.add_command(label="Salir", command=root.quit)
menubar.add_cascade(label="Archivo", menu=file_menu)
root.config(menu=menubar)

# Etiquetas y campos de entrada
tk.Label(root, text="Símbolo de la Acción:").pack(pady=5)
entry_ticker = tk.Entry(root)
entry_ticker.pack()

tk.Label(root, text="Fecha de Inicio (YYYY-MM-DD):").pack(pady=5)
entry_start = tk.Entry(root)
entry_start.pack()

tk.Label(root, text="Fecha de Fin (YYYY-MM-DD):").pack(pady=5)
entry_end = tk.Entry(root)
entry_end.pack()

# Etiqueta de estado (cargando)
status_label = tk.Label(root, text="", font=("Arial", 10, "bold"))
status_label.pack(pady=5)

# Botón para analizar
btn_analyze = tk.Button(root, text="Analizar", command=plot_data)
btn_analyze.pack(pady=20)

# Iniciar la interfaz gráfica
root.mainloop()
