import tkinter as tk
from tkinter import filedialog, messagebox
import re
import os
import pandas as pd

# Mapea el nombre de bloque a los sufijos deseados
SUFFIX_MAP = {
    'block': 'block',
    'data': 'data',
    'krige': 'krige',
    'soft': 'soft',
    'spec': 'spec',
    'str_cutoff': 'str_cutoff'
}

def get_suffix(block_name: str) -> str:
    """
    Dado un block_name como 'block_centroid' o 'str_cutoff_mn',
    devuelve el sufijo deseado: 'block' o 'str_cutoff'.
    Si no está en SUFFIX_MAP, toma la primera parte antes de '_'.
    """
    for key in SUFFIX_MAP:
        if block_name.startswith(key):
            return SUFFIX_MAP[key]
    # si no coincide con ninguno, usar todo hasta el primer '_'
    return block_name.split('_', 1)[0]

def parse_bef(filepath):
    """
    Lee el .bef y agrupa TODOS los parámetros de cada configuración
    en UNA SOLA instancia (fila), añadiendo sufijos según el bloque.
    """
    data = {}          # cfg -> {suffix: {param: val}}
    order = []         # orden de aparición de cfg
    current_cfg = None
    current_block = None

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.rstrip('\n')
            # Detectar inicio de bloque: BEGIN$DEF <CONFIG>_<BLOCKNAME>
            m = re.match(r'BEGIN\$DEF\s+(\w+?)_([^\s]+)', line)
            if m:
                cfg, block_name = m.group(1), m.group(2)
                current_cfg = cfg
                suffix = get_suffix(block_name)
                current_block = suffix
                if cfg not in data:
                    data[cfg] = {}
                    order.append(cfg)
                if suffix not in data[cfg]:
                    data[cfg][suffix] = {}
                continue

            # Detectar fin de bloque
            if line.strip() == 'END$DEF':
                current_block = None
                continue

            # Dentro de un bloque, extraer parámetros "key=val"
            if current_cfg and current_block and '=' in line:
                key, val = [s.strip() for s in line.split('=', 1)]
                # eliminar comillas
                val = val.strip("'\"")
                data[current_cfg][current_block][key] = val

    # Construir instancias planas
    instances = []
    for cfg in order:
        inst = {
            'file_name': os.path.basename(filepath),
            'config': cfg
        }
        for suffix, params in data[cfg].items():
            for key, val in params.items():
                col = f"{key}_{suffix}"
                inst[col] = val
        instances.append(inst)

    return instances

def generate_csv(input_path, output_path):
    """
    Parsea el .bef y escribe un CSV con:
      - file_name
      - config
      - todos los parámetros de cada bloque, con sufijos
    """
    instances = parse_bef(input_path)
    df = pd.DataFrame(instances)
    df.to_csv(output_path, index=False)

class App:
    def __init__(self, root):
        root.title("Generador de Instancias .bef")
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()

        # Selector de archivo .bef
        tk.Label(root, text="Archivo .bef:")\
            .grid(row=0, column=0, sticky='e', padx=5, pady=5)
        tk.Entry(root, textvariable=self.input_path, width=50)\
            .grid(row=0, column=1, padx=5, pady=5)
        tk.Button(root, text="Examinar", command=self.browse_input)\
            .grid(row=0, column=2, padx=5, pady=5)

        # Selector de salida CSV
        tk.Label(root, text="Archivo de salida CSV:")\
            .grid(row=1, column=0, sticky='e', padx=5, pady=5)
        tk.Entry(root, textvariable=self.output_path, width=50)\
            .grid(row=1, column=1, padx=5, pady=5)
        tk.Button(root, text="Examinar", command=self.browse_output)\
            .grid(row=1, column=2, padx=5, pady=5)

        # Botón de generación
        tk.Button(root, text="Generar Instancias", command=self.run)\
            .grid(row=2, column=1, pady=10)

    def browse_input(self):
        file = filedialog.askopenfilename(
            title="Selecciona archivo .bef",
            filetypes=[("Bef Files","*.bef"),("Todos","*.*")])
        if file:
            self.input_path.set(file)

    def browse_output(self):
        file = filedialog.asksaveasfilename(
            title="Guardar como CSV",
            defaultextension=".csv",
            filetypes=[("CSV Files","*.csv"),("Todos","*.*")])
        if file:
            self.output_path.set(file)

    def run(self):
        inp = self.input_path.get()
        out = self.output_path.get()
        if not inp or not out:
            messagebox.showerror("Error",
                "Seleccione archivo de entrada y de salida")
            return
        try:
            generate_csv(inp, out)
            messagebox.showinfo("Éxito",
                f"CSV generado en:\n{out}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    # Requisitos: pip install pandas
    root = tk.Tk()
    App(root)
    root.mainloop()
