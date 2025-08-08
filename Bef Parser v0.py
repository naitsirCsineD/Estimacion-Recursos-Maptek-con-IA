import os
import glob
import re
import pandas as pd

__all__ = [
    "parse_bef",
    "parse_all_bef",
    "save_all_to_csv",
    "generate_bef_from_instances",
]

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
    Determina el sufijo para un bloque dado basándose en SUFFIX_MAP.
    Si no encuentra una coincidencia, toma la parte antes del primer '_'.
    """
    for key in SUFFIX_MAP:
        if block_name.startswith(key):
            return SUFFIX_MAP[key]
    return block_name.split('_', 1)[0]


def parse_bef(filepath: str) -> list[dict]:
    """
    Lee un archivo .bef y devuelve una lista de instancias (diccionarios),
    una por cada configuración, con parámetros aplanados y sufijados.

    Parámetros:
    - filepath: Ruta al archivo .bef

    Retorna:
    - List[dict]: Cada dict contiene keys: 'file_name', 'config', y parámetros sufijados.
    """
    data = {}
    order = []
    current_cfg = None
    current_block = None

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.rstrip('\n')
            # Detectar inicio de bloque
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

            # Extraer parámetros dentro del bloque
            if current_cfg and current_block and '=' in line:
                key, val = [s.strip() for s in line.split('=', 1)]
                val = val.strip("'\"")
                data[current_cfg][current_block][key] = val

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


def parse_all_bef(dir_path: str | None = None) -> pd.DataFrame:
    """
    Busca todos los archivos .bef en el directorio indicado (o el del script)
    y retorna un DataFrame con todas las instancias.

    Parámetros:
    - dir_path: Directorio donde buscar. Si es None, usa el directorio del script.

    Retorna:
    - pandas.DataFrame: Filas por configuración y columnas aplanadas.
    """
    if dir_path is None:
        dir_path = os.path.dirname(os.path.abspath(__file__))
    pattern = os.path.join(dir_path, '*.bef')
    file_list = glob.glob(pattern)

    all_instances = []
    for filepath in file_list:
        all_instances.extend(parse_bef(filepath))

    return pd.DataFrame(all_instances)


def save_all_to_csv(output_path: str, dir_path: str | None = None) -> None:
    """
    Genera un CSV con todas las instancias extraídas de los .bef encontrados.

    Parámetros:
    - output_path: Ruta de salida del archivo CSV.
    - dir_path: Directorio donde buscar archivos .bef.
    """
    df = parse_all_bef(dir_path)
    df.to_csv(output_path, index=False)


def generate_bef_from_instances(instances: pd.DataFrame, output_path: str = None) -> None:
    """
    Toma un DataFrame de instancias (columnas: 'config' y parameters sufijados)
    y genera un archivo .bef con nombre 'estimadores.bef' o el indicado.

    Parámetros:
    - instances: DataFrame con columnas 'config' y parámetros sufijados.
    - output_path: Ruta de salida. Si None, usa '<script_dir>/estimadores.bef'.
    """
    # Determinar ruta de salida
    if output_path is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(script_dir, 'estimadores.bef')

    # Agrupar columnas por sufijo
    pattern = re.compile(r'^(?P<param>.+)_(?P<suffix>[^_]+)$')
    # Por cada fila, reconstruir bloques
    lines = []
    for _, row in instances.iterrows():
        cfg = row['config']
        # Agrupar parámetros
        blocks = {}
        for col, val in row.items():
            if col in ('file_name', 'config') or pd.isna(val):
                continue
            m = pattern.match(col)
            if not m:
                continue
            param = m.group('param')
            suffix = m.group('suffix')
            blocks.setdefault(suffix, {})[param] = val
        # Escribir bloques al archivo
        for suffix, params in blocks.items():
            lines.append(f"BEGIN$DEF {cfg}_{suffix}")
            for key, v in params.items():
                lines.append(f"{key}={v}")
            lines.append("END$DEF")
            lines.append("")  # línea en blanco

    # Guardar en archivo
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))


if __name__ == '__main__':
    # Ejemplo de uso rápido
    df_all = parse_all_bef()
    save_all_to_csv('all_instances.csv')
    df_usado= df_all[df_all['config'] == '25CU00']| df_all[df_all['config'] == '25CU01']| df_all[df_all['config'] == '25CU02']| df_all[df_all['config'] == '25CU03']| df_all[df_all['config'] == '25ag00']| df_all[df_all['config'] == '25ag01']| df_all[df_all['config'] == '25ag02']| df_all[df_all['config'] == '25ag03']
    generate_bef_from_instances(df_all)  # Creará estimadores.bef
