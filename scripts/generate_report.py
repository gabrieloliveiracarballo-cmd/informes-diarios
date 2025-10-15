import os
import datetime
from git import Repo
import shutil # Importamos la librería para copiar archivos

# ==============================
# 1. Definir constantes de configuración
# ==============================

# Ruta raíz del repositorio (sube un nivel desde 'scripts')
REPO_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
REPORTS_DIR = os.path.join(REPO_PATH, 'reports')
INDEX_FILE = os.path.join(REPO_PATH, 'index.html')
LINK_MARKER = '<!-- LOS NUEVOS ENLACES SE INSERTARÁN AQUÍ -->'

# ==============================
# 2. Usar un informe HTML existente
# ==============================

# Obtenemos la fecha de hoy para usarla en el nombre del archivo y en los mensajes
today_str = datetime.date.today().strftime('%Y-%m-%d')

# ATENCIÓN: Asegúrate de que un archivo llamado 'informe_de_hoy.html' exista en la raíz del proyecto
source_html_path = os.path.join(REPO_PATH, 'informe_de_hoy.html')

# Nombre que tendrá el archivo de destino en la carpeta 'reports'
report_filename = f'informe-{today_str}.html'
report_filepath = os.path.join(REPORTS_DIR, report_filename)

# Crear la carpeta 'reports' si no existe
os.makedirs(REPORTS_DIR, exist_ok=True)

# Copiar el archivo real a la carpeta de informes con el nombre correcto
try:
    shutil.copy(source_html_path, report_filepath)
    print(f"Informe real copiado a: {report_filepath}")
except FileNotFoundError:
    print(f"ERROR: No se encontró el archivo 'informe_de_hoy.html' en la raíz del proyecto. Por favor, créalo o colócalo allí.")
    exit() # Detenemos el script si no se encuentra el archivo

# ==============================
# 3. Actualizar el index.html
# ==============================

with open(INDEX_FILE, 'r', encoding='utf-8') as f:
    index_content = f.read()

# --- LÍNEA CORREGIDA ---
# Usamos 'today_str' en lugar de 'report_data["fecha"]'
new_link = f'<li><a href="reports/{report_filename}">Informe del {today_str}</a></li>\n'

if LINK_MARKER in index_content:
    parts = index_content.split(LINK_MARKER)
    # Insertamos el enlace justo después del marcador
    updated_content = parts[0] + LINK_MARKER + '\n            ' + new_link + parts[1]
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    print("index.html actualizado con el nuevo informe.")
else:
    print("No se encontró el marcador de enlaces en index.html. No se insertó el enlace.")

# ==============================
# 4. Automatizar Git (Commit y Push)
# ==============================

try:
    print("Inicializando repositorio Git...")
    repo = Repo(REPO_PATH)
    
    # Añadir todos los cambios
    repo.git.add(A=True)
    
    # --- LÍNEA CORREGIDA ---
    # Usamos 'today_str' en lugar de 'report_data['fecha']'
    commit_msg = f"Reporte automático para {today_str}"
    
    # Realizar el commit
    repo.index.commit(commit_msg)
    print("Commit realizado. Enviando cambios a GitHub...")
    
    # Detectar la rama principal para hacer el push
    branch = 'main' if 'main' in repo.heads else 'master'
    
    # Enviar los cambios
    repo.git.push('origin', branch)
    print("¡Cambios enviados correctamente!")

except Exception as e:
    print(f"Error durante el proceso de Git: {e}")