import os
import datetime
from git import Repo
import traceback
import shutil
from flask import Flask, request, jsonify

# ==============================
# CONFIGURACIÓN DE LA APLICACIÓN
# ==============================
app = Flask(__name__)

# Configuración de rutas (igual que antes)
REPO_PATH = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(REPO_PATH, 'reports')
INDEX_FILE = os.path.join(REPO_PATH, 'index.html')
LINK_MARKER = '<!-- LOS NUEVOS ENLACES SE INSERTARÁN AQUÍ -->'

# Una clave secreta para asegurar que solo n8n puede llamar a esta API
# ¡CAMBIA ESTO POR ALGO SECRETO Y ÚNICO!
API_SECRET_KEY = os.environ.get("API_SECRET_KEY", "MI_CLAVE_SECRETA_POR_DEFECTO")

# ==============================
# ENDPOINT PARA HEALTH CHECK
# ==============================
@app.route('/', methods=['GET'])
def health_check():
    # Esta ruta simple le dice a EasyPanel que la app está viva.
    return "API del Dashboard de Informes funcionando correctamente.", 200

# ==============================
# EL ENDPOINT DE LA API (VERSIÓN MEJORADA PARA ACEPTAR ARCHIVOS)
# ==============================
@app.route('/trigger-report', methods=['POST'])
def trigger_report_update():
    # --- 1. Seguridad: Verificar la clave secreta ---
    if request.headers.get('X-API-KEY') != API_SECRET_KEY:
        return jsonify({"error": "No autorizado"}), 401

    # --- 2. Recibir el ARCHIVO desde n8n ---
    # El cambio clave está aquí. Buscamos un archivo en la petición.
    if 'reportFile' not in request.files:
        return jsonify({"error": "No se encontró el archivo en la petición"}), 400

    file = request.files['reportFile']
    html_content = file.read().decode('utf-8')

    if not html_content:
        return jsonify({"error": "El archivo HTML está vacío"}), 400

    # --- 3. Guardar el HTML recibido en un archivo ---
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    # Usamos un nombre de archivo único para evitar sobrescribir si se ejecuta varias veces
    timestamp = datetime.datetime.now().strftime('%H%M%S')
    report_filename = f'informe-{today_str}-{timestamp}.html'
    report_filepath = os.path.join(REPORTS_DIR, report_filename)
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    with open(report_filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"Informe recibido de n8n y guardado en: {report_filepath}")

    # --- 4. Actualizar el index.html ---
    with open(INDEX_FILE, 'r+', encoding='utf-8') as f:
        index_content = f.read()
        new_link = f'<li><a href="reports/{report_filename}">Informe del {today_str} ({timestamp})</a></li>\n'
        
        if LINK_MARKER in index_content:
            parts = index_content.split(LINK_MARKER)
            updated_content = parts[0] + LINK_MARKER + '\n            ' + new_link + parts[1]
            f.seek(0)
            f.write(updated_content)
            f.truncate()
            print("index.html actualizado.")
        else:
            print("Marcador no encontrado en index.html")

    # ==============================
    # 5. Automatizar Git (Commit y Push)
    # ==============================
    try:
        github_token = os.environ.get('GITHUB_TOKEN')
        if not github_token:
            raise Exception("La variable de entorno GITHUB_TOKEN no está configurada.")

        remote_url = f"https://{github_token}@github.com/gabrieloliveiracarballo-cmd/informes-diarios.git"
        branch_name = 'main'

        print("Inicializando repositorio Git en /app...")
        repo = Repo.init(REPO_PATH)

        # Renombramos la rama actual si es necesario
        if repo.active_branch.name != branch_name:
            repo.active_branch.rename(branch_name)

        # Configuramos la identidad del autor
        repo.config_writer().set_value("user", "name", "Bot de Informes").release()
        repo.config_writer().set_value("user", "email", "bot@example.com").release()
        
        print("Añadiendo todos los cambios...")
        repo.git.add(A=True)
        
        print("Realizando el commit...")
        commit_msg = f"Reporte automático para {today_str} a las {timestamp}"
        repo.index.commit(commit_msg)

        # Configuramos el remoto 'origin'
        if 'origin' in repo.remotes:
            remote = repo.remotes.origin
            remote.set_url(remote_url)
        else:
            remote = repo.create_remote('origin', remote_url)

        print(f"Enviando cambios a la rama '{branch_name}'...")
        remote.push(refspec=f'{branch_name}:{branch_name}', force=True)
        
        print("¡Cambios enviados correctamente!")
        return jsonify({"message": "Informe procesado y desplegado con éxito"}), 200

    except Exception as e:
        import traceback
        error_message = f"Fallo en el proceso de Git: {traceback.format_exc()}"
        print(error_message)
        return jsonify({"error": error_message}), 500