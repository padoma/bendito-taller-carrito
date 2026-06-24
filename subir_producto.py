# -*- coding: utf-8 -*-
import os
import sys
import sqlite3
import shutil
import re
import json
import unicodedata
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

# Intentar importar Pillow para previsualización y compresión de imágenes
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Mapeo de IDs de grupos combinables a nombres amigables en español
GROUP_NAMES_MAP = {
    "intercambiables": "Intercambiables (Corazones, Cruces, Altares originales)",
    "altares_nichos": "Altares y Nichos",
    "virgenes": "Vírgenes",
    "alebrijes_catrinas": "Alebrijes y Catrinas",
    "calaveras": "Calaveras",
    "composiciones_1_3": "Composiciones (1 a 3)",
    "fridas": "Fridas",
    "tienda_vintage": "Tienda Vintage",
    "grabados_gra": "Grabados (GRA)",
    "set_navideno": "Set Navideño",
    "casita_muneca_torre": "Casita de Muñecas / Torre",
    "composiciones_4_8_arabesco": "Composiciones (4 a 8) / Arabesco",
    "set_anillos": "Set de Anillos",
    "deco_infantil": "Deco Infantil",
    "animales": "Animales",
    "abejas_mariposas": "Abejas y Mariposas",
    "cuadros_c": "Cuadros (C)",
    "bienvenidos": "Letreros de Bienvenidos",
    "letreros": "Letreros",
    "colibri": "Colibríes",
    "eclipse": "Eclipses",
    "obras_3d": "Obras 3D",
    "corona_navidad_personajes": "Coronas Navideñas (Personajes)",
    "coronas_navidad_base": "Coronas Navideñas (Base/Especiales)",
    "cuadros_navidad": "Cuadros Navideños",
    "arboles_navidad_pino": "Pinos / Árboles de Navidad",
    "cajas_navidad": "Cajas Navideñas"
}

# Paleta de Colores "Bendito Taller"
COLOR_BG = "#fffcf8"       # Crema de fondo
COLOR_CARD = "#f5ece1"     # Arena suave para tarjetas
COLOR_TEXT = "#4b372d"     # Café oscuro
COLOR_BORDER = "#e5dacb"   # Borde beige claro
COLOR_ACCENT = "#7d8b63"   # Verde salvia
COLOR_ACCENT_HOVER = "#677351"
COLOR_DANGER = "#d9534f"   # Rojo suave
COLOR_DANGER_HOVER = "#b53f3a"
COLOR_WHITE = "#ffffff"

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Bendito Taller - Gestión de Productos")
        self.root.geometry("950x800")
        self.root.configure(bg=COLOR_BG)
        self.root.minsize(850, 600)

        # Ruta del proyecto (soporta PyInstaller)
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))

        # Cargar configuración local (ej. ruta de la base de datos de ventas)
        self.config_path = os.path.join(self.base_dir, "config.json")
        self.sales_db_path = None
        self.cargar_configuracion()

        # Resolver directorios de destino (soporte multi-repositorio)
        user_home = os.path.expanduser("~")
        self.target_dirs = [self.base_dir]
        
        for repo_name in ["bendito-taller-carrito", "bendito-taller-web"]:
            path = os.path.join(user_home, "Documents", "GitHub", repo_name)
            if os.path.exists(path) and os.path.isdir(path):
                path_abs = os.path.abspath(path)
                if path_abs not in [os.path.abspath(d) for d in self.target_dirs]:
                    self.target_dirs.append(path)

        # Cargar base de datos desde la ruta preferida (la más actualizada)
        self.productos_js_path = None
        self.cart_shared_js_path = None
        self.img_dir = None
        
        preferida = None
        max_mtime = 0
        for d in self.target_dirs:
            p_js = os.path.join(d, "productos.js")
            if os.path.exists(p_js):
                mtime = os.path.getmtime(p_js)
                if mtime > max_mtime:
                    max_mtime = mtime
                    preferida = d

        if preferida:
            self.productos_js_path = os.path.join(preferida, "productos.js")
            self.cart_shared_js_path = os.path.join(preferida, "cart-shared.js")
            self.img_dir = os.path.join(preferida, "img")
        else:
            self.productos_js_path = os.path.join(self.base_dir, "productos.js")
            self.cart_shared_js_path = os.path.join(self.base_dir, "cart-shared.js")
            self.img_dir = os.path.join(self.base_dir, "img")

        # Cargar base de datos existente
        self.productos_db = {}
        self.cargar_productos_db()

        # Cargar productos combinables existentes y mapear a sus grupos
        self.grupos_dict = {}
        self.combo_values = []
        self.display_to_code = {}
        self.obtener_productos_combinables()

        # --- VARIABLES PESTAÑA CREAR ---
        self.var_id = tk.StringVar()
        self.var_codigo = tk.StringVar()
        self.var_imagen_path = tk.StringVar()
        self.var_tipo = tk.StringVar(value="simple")
        self.var_es_combinable = tk.BooleanVar(value=False)
        self.var_filtro_combinables = tk.StringVar()
        self.combinables_widgets = [] # Lista de diccionarios {frame, var_grupo, combo}

        # Precios simples
        self.var_precio_mayor = tk.StringVar()
        self.var_precio_unitario = tk.StringVar()

        # Opciones/Medidas dinámicas
        self.opciones_widgets = [] # Lista de diccionarios {frame, medida_entry, mayor_entry, unitario_entry}

        # --- VARIABLES PESTAÑA MODIFICAR ---
        self.mod_var_id = tk.StringVar()
        self.mod_var_codigo = tk.StringVar()
        self.mod_var_imagen_path = tk.StringVar()
        self.mod_var_tipo = tk.StringVar(value="simple")
        self.mod_var_es_combinable = tk.BooleanVar(value=False)
        self.mod_combinables_widgets = []

        # Precios simples
        self.mod_var_precio_mayor = tk.StringVar()
        self.mod_var_precio_unitario = tk.StringVar()

        # Opciones/Medidas dinámicas
        self.mod_opciones_widgets = []

        # Variables de búsqueda
        self.var_busqueda = tk.StringVar()
        self.var_select_producto = tk.StringVar()

        self.setup_styles()
        self.build_ui()

        # Cargar lista para buscador
        self.actualizar_combo_buscar()

        # Binds para autogenerar ID y verificar duplicados (Pestaña Crear)
        self.var_codigo.trace_add("write", self.on_codigo_changed)
        self.var_id.trace_add("write", self.on_id_changed)

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Estilos generales para Combobox y otros widgets de ttk
        self.style.configure("TCombobox", 
                             fieldbackground=COLOR_WHITE,
                             background=COLOR_BORDER,
                             foreground=COLOR_TEXT,
                             bordercolor=COLOR_BORDER,
                             lightcolor=COLOR_BORDER,
                             darkcolor=COLOR_BORDER)
        self.root.option_add('*TCombobox*Listbox.background', COLOR_WHITE)
        self.root.option_add('*TCombobox*Listbox.foreground', COLOR_TEXT)
        self.root.option_add('*TCombobox*Listbox.selectBackground', COLOR_ACCENT)
        self.root.option_add('*TCombobox*Listbox.selectForeground', COLOR_WHITE)

    def cargar_productos_db(self):
        if not os.path.exists(self.productos_js_path):
            messagebox.showerror("Error", f"No se encontró el archivo productos.js en:\n{self.productos_js_path}")
            return
        
        try:
            with open(self.productos_js_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1:
                json_str = content[start:end+1]
                self.productos_db = json.loads(json_str)
            else:
                messagebox.showerror("Error", "El formato de productos.js no es válido. No se encontró el objeto de productos.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al leer productos.js:\n{str(e)}")

    def obtener_productos_combinables(self):
        self.grupos_dict = {}
        self.combo_values = []
        self.display_to_group_id = {}
        
        if not os.path.exists(self.cart_shared_js_path):
            return
            
        try:
            with open(self.cart_shared_js_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # 1. Parsear Set codigosIntercambiablesNorm
            set_match = re.search(r'const\s+codigosIntercambiablesNorm\s*=\s*new\s+Set\(\[\s*([\s\S]*?)\s*\]\);', content)
            if set_match:
                codes = [c.strip().strip('"').strip("'") for c in set_match.group(1).split(",") if c.strip()]
                for code in codes:
                    self.grupos_dict[code] = "intercambiables"
                    
            # 2. Parsear gruposCombinables
            m_array = re.search(r'const\s+gruposCombinables\s*=\s*\[([\s\S]*?)\];', content)
            if m_array:
                array_content = m_array.group(1)
                matches = re.finditer(r'\{\s*id:\s*["\']([^"\']+)["\'][\s\S]*?codigos:\s*\[([\s\S]*?)\]', array_content)
                for m in matches:
                    g_id = m.group(1)
                    if g_id not in GROUP_NAMES_MAP:
                        GROUP_NAMES_MAP[g_id] = g_id.replace("_", " ").title()
                    g_codes = [c.strip().strip('"').strip("'") for c in m.group(2).split(",") if c.strip()]
                    for code in g_codes:
                        self.grupos_dict[code] = g_id
        except Exception as e:
            print("Error al parsear productos combinables de cart-shared.js:", e)
            
        # Asociar con nombres descriptivos de productos.js
        for code, g_id in self.grupos_dict.items():
            name = self.obtener_nombre_de_producto(code)
            group_name = GROUP_NAMES_MAP.get(g_id, g_id.replace("_", " ").title())
            display = f"{name} ({group_name}) [{code}]"
            self.combo_values.append(display)
            self.display_to_code[display] = (code, g_id)
            
        self.combo_values.sort()

        # Agregar categorías especiales para selección rápida al inicio
        special_categories = [
            ("Categoría Corazones", "intercambiables"),
            ("Categoría Corazones Alados", "intercambiables"),
            ("Categoría Altares y Nichos", "altares_nichos")
        ]
        for name, g_id in reversed(special_categories):
            self.combo_values.insert(0, name)
            self.display_to_code[name] = (name, g_id)

    def obtener_nombre_de_producto(self, code):
        if code in self.productos_db:
            p = self.productos_db[code]
            if "parent" in p:
                parent_id = p["parent"]
                preselect = p.get("preselect", "")
                parent_name = self.productos_db.get(parent_id, {}).get("nombre", parent_id)
                return f"{parent_name} ({preselect})"
            return p.get("nombre", code)
            
        code_clean = code.lower().replace("[^a-z0-9]", "")
        for key, p in self.productos_db.items():
            if key.lower().replace("[^a-z0-9]", "") == code_clean:
                if "parent" in p:
                    parent_id = p["parent"]
                    preselect = p.get("preselect", "")
                    parent_name = self.productos_db.get(parent_id, {}).get("nombre", parent_id)
                    return f"{parent_name} ({preselect})"
                return p.get("nombre", key)
        return code

    def obtener_display_name_para_grupo(self, pid, grupo_id):
        if grupo_id == "intercambiables":
            pid_norm = pid.lower()
            if pid_norm.startswith("ca") or pid_norm.startswith("bc1") or pid_norm.startswith("bc2") or pid_norm.startswith("bc3"):
                return "Categoría Corazones Alados"
            else:
                return "Categoría Corazones"
        elif grupo_id == "altares_nichos":
            return "Categoría Altares y Nichos"
        else:
            return GROUP_NAMES_MAP.get(grupo_id, grupo_id.replace("_", " ").title())

    def find_git_executable(self):
        # 1. Intentar usar el git del PATH si está disponible
        try:
            subprocess.run(["git", "--version"], capture_output=True, check=True)
            return "git"
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass

        # 2. Rutas comunes en Windows
        user_home = os.path.expanduser("~")
        common_paths = [
            r"C:\Program Files\Git\cmd\git.exe",
            r"C:\Program Files\Git\bin\git.exe",
            r"C:\Program Files (x86)\Git\cmd\git.exe",
            os.path.join(user_home, r"AppData\Local\Programs\Git\cmd\git.exe")
        ]
        for p in common_paths:
            if os.path.exists(p):
                return p

        # 3. Intentar buscar en las carpetas de GitHub Desktop
        github_desktop_dir = os.path.join(user_home, r"AppData\Local\GitHubDesktop")
        if os.path.exists(github_desktop_dir):
            git_paths = []
            for root, dirs, files in os.walk(github_desktop_dir):
                if "git.exe" in files:
                    git_path = os.path.join(root, "git.exe")
                    if "\\cmd\\" in git_path:
                        git_paths.append(git_path)
            if git_paths:
                git_paths.sort(reverse=True)
                return git_paths[0]

        return "git"

    def cargar_configuracion(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.sales_db_path = config.get("sales_db_path")
            except Exception as e:
                print("Error al cargar config.json:", e)

    def guardar_configuracion(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump({"sales_db_path": self.sales_db_path}, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print("Error al guardar config.json:", e)

    def resolver_ruta_base_datos_ventas(self):
        # 1. Si ya se cargó desde la configuración y existe, usar esa
        if self.sales_db_path and os.path.exists(self.sales_db_path):
            return self.sales_db_path

        # 2. Buscar en ubicaciones comunes
        user_home = os.path.expanduser("~")
        search_roots = [
            os.path.dirname(self.base_dir),
            os.path.join(user_home, "Documents", "GitHub"),
            r"D:\\"
        ]
        for root in search_roots:
            if not os.path.exists(root) or not os.path.isdir(root):
                continue
            try:
                for name in os.listdir(root):
                    dir_path = os.path.join(root, name)
                    if os.path.isdir(dir_path) and "ventas" in name.lower() and "bendito" in name.lower():
                        db_candidate = os.path.join(dir_path, "data", "ventas_laser.db")
                        if os.path.exists(db_candidate):
                            self.sales_db_path = os.path.abspath(db_candidate)
                            self.guardar_configuracion()
                            return self.sales_db_path
            except Exception as e:
                print(f"Error buscando base de datos en {root}: {e}")
        return None

    def solicitar_ruta_ventas_db(self):
        messagebox.showinfo(
            "Configuración Necesaria",
            "No se encontró automáticamente la carpeta del programa de ventas 'ventas_bendito'.\n\n"
            "Por favor, selecciona la carpeta raíz del programa de ventas (ej: 'ventas_bendito 2.6') para poder sincronizar la base de datos."
        )
        folder = filedialog.askdirectory(title="Selecciona la carpeta de Ventas Bendito")
        if folder:
            db_candidate = os.path.join(folder, "data", "ventas_laser.db")
            if os.path.exists(db_candidate):
                self.sales_db_path = os.path.abspath(db_candidate)
                self.guardar_configuracion()
                messagebox.showinfo("Configuración Guardada", f"Base de datos de ventas vinculada con éxito:\n{self.sales_db_path}")
                return self.sales_db_path
            else:
                messagebox.showerror(
                    "Error",
                    f"No se encontró la base de datos en la carpeta seleccionada.\n"
                    f"Se esperaba encontrar el archivo:\n{os.path.join('data', 'ventas_laser.db')}"
                )
        return None

    def sincronizar_con_ventas_db(self, codigo_base, precios):
        db_path = self.resolver_ruta_base_datos_ventas()
        if not db_path:
            db_path = self.solicitar_ruta_ventas_db()
            if not db_path:
                print("No se configuró la base de datos de ventas. Sincronización omitida.")
                return False

        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            
            c.execute('''CREATE TABLE IF NOT EXISTS productos (
                        codigo TEXT PRIMARY KEY,
                        valor_unitario REAL,
                        valor_mayor REAL,
                        ruta_archivo TEXT)''')
            
            if precios["tipo"] == "simple":
                cod_db = codigo_base.upper().strip()
                unitario = float(precios["unitario"])
                mayor = float(precios["mayor"])
                
                c.execute("SELECT ruta_archivo FROM productos WHERE codigo=?", (cod_db,))
                row = c.fetchone()
                if row is not None:
                    c.execute("UPDATE productos SET valor_unitario=?, valor_mayor=? WHERE codigo=?",
                              (unitario, mayor, cod_db))
                else:
                    c.execute("INSERT INTO productos (codigo, valor_unitario, valor_mayor, ruta_archivo) VALUES (?, ?, ?, ?)",
                              (cod_db, unitario, mayor, ""))
            else:
                for opt in precios["opciones"]:
                    medida_val = opt["medida"].strip()
                    medida_limpia = medida_val.upper().replace(" ", "")
                    cod_db = f"{codigo_base.upper().strip()} {medida_limpia}"
                    unitario = float(opt["unitario"])
                    mayor = float(opt["mayor"])
                    
                    c.execute("SELECT ruta_archivo FROM productos WHERE codigo=?", (cod_db,))
                    row = c.fetchone()
                    if row is not None:
                        c.execute("UPDATE productos SET valor_unitario=?, valor_mayor=? WHERE codigo=?",
                                  (unitario, mayor, cod_db))
                    else:
                        c.execute("INSERT INTO productos (codigo, valor_unitario, valor_mayor, ruta_archivo) VALUES (?, ?, ?, ?)",
                                  (cod_db, unitario, mayor, ""))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print("Error al sincronizar con la base de datos de ventas:", e)
            messagebox.showwarning(
                "Advertencia de Sincronización",
                f"El producto se guardó para la web, pero hubo un problema al sincronizar con la base de datos de ventas:\n{str(e)}\n\n"
                f"No te preocupes, los cambios en la web se subirán a GitHub normalmente."
            )
            return False

    def normalize_string(self, text):
        normalized = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
        return re.sub(r'[^a-z0-9]', '', normalized.lower())

    def on_combo_keyrelease(self, event):
        value = event.widget.get().lower()
        if value == '':
            event.widget['values'] = self.combo_values
        else:
            data = []
            for item in self.combo_values:
                if value in item.lower():
                    data.append(item)
            event.widget['values'] = data

    def on_codigo_changed(self, *args):
        codigo = self.var_codigo.get()
        self.var_id.set(self.normalize_string(codigo))

    def on_id_changed(self, *args):
        pid = self.var_id.get().strip()
        if not pid:
            self.lbl_status_id.config(text="")
            self.btn_guardar.config(state="normal")
            self.lbl_auto_intercambiable.config(text="", fg=COLOR_TEXT)
            self.toggle_grupo_frame()
            return

        if pid in self.productos_db:
            prod = self.productos_db[pid]
            if "parent" in prod:
                det = f"(Hijo de: {prod['parent']})"
            else:
                det = f"({prod.get('nombre', 'Existente')})"
            self.lbl_status_id.config(text=f"⚠️ Este código ya existe {det}", fg=COLOR_DANGER)
        else:
            self.lbl_status_id.config(text="✓ Código disponible", fg="#2e7d32")

        # Detección automática para pre-seleccionar el grupo en el dropdown
        pid_norm = self.normalize_string(pid)
        grupo_auto = None
        if re.match(r"^co\d", pid_norm):
            grupo_auto = "Corazones"
        elif re.match(r"^ca\d", pid_norm):
            grupo_auto = "Corazones Alados"
        elif re.match(r"^cruz\d", pid_norm):
            grupo_auto = "Cruces"
        elif re.match(r"^(bc\d|florcora\d|setcorazones)", pid_norm):
            grupo_auto = "Corazones"

        if grupo_auto:
            self.var_es_combinable.set(True)
            self.toggle_grupo_frame()
            
            # Pre-seleccionar en el combobox de la primera fila
            if self.combinables_widgets:
                first_combo = self.combinables_widgets[0]
                first_combo["var_grupo"].set(grupo_auto)
            
            self.lbl_auto_intercambiable.config(
                text=f"✨ Prefijo detectado. Se ha pre-seleccionado el grupo '{grupo_auto}'.", 
                fg=COLOR_ACCENT
            )
        else:
            self.lbl_auto_intercambiable.config(text="", fg=COLOR_TEXT)
            self.toggle_grupo_frame()

    def build_ui(self):
        # Header principal de la App
        header_frame = tk.Frame(self.root, bg=COLOR_TEXT, height=60)
        header_frame.pack(fill="x", side="top")
        header_frame.pack_propagate(False)

        lbl_title = tk.Label(header_frame, text="BENDITO TALLER - GESTIÓN DE PRODUCTOS", 
                             font=("Outfit", 14, "bold"), fg=COLOR_BG, bg=COLOR_TEXT)
        lbl_title.pack(pady=15, padx=20)

        # Crear Notebook para Pestañas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # --- PESTAÑA 1: CREAR ---
        self.tab_crear = tk.Frame(self.notebook, bg=COLOR_BG)
        self.notebook.add(self.tab_crear, text="  Crear Producto  ")

        # Scrollbar y Canvas para Pestaña Crear
        self.canvas_crear = tk.Canvas(self.tab_crear, bg=COLOR_BG, highlightthickness=0)
        scrollbar_crear = ttk.Scrollbar(self.tab_crear, orient="vertical", command=self.canvas_crear.yview)
        
        self.scrollable_frame_crear = tk.Frame(self.canvas_crear, bg=COLOR_BG)
        self.scrollable_frame_crear.bind(
            "<Configure>",
            lambda e: self.canvas_crear.configure(scrollregion=self.canvas_crear.bbox("all"))
        )
        self.canvas_crear.create_window((0, 0), window=self.scrollable_frame_crear, anchor="nw")
        self.canvas_crear.configure(yscrollcommand=scrollbar_crear.set)

        self.canvas_crear.pack(side="left", fill="both", expand=True)
        scrollbar_crear.pack(side="right", fill="y")

        # --- PESTAÑA 2: MODIFICAR ---
        self.tab_modificar = tk.Frame(self.notebook, bg=COLOR_BG)
        self.notebook.add(self.tab_modificar, text="  Modificar Producto  ")

        # Scrollbar y Canvas para Pestaña Modificar
        self.canvas_mod = tk.Canvas(self.tab_modificar, bg=COLOR_BG, highlightthickness=0)
        scrollbar_mod = ttk.Scrollbar(self.tab_modificar, orient="vertical", command=self.canvas_mod.yview)
        
        self.scrollable_frame_mod = tk.Frame(self.canvas_mod, bg=COLOR_BG)
        self.scrollable_frame_mod.bind(
            "<Configure>",
            lambda e: self.canvas_mod.configure(scrollregion=self.canvas_mod.bbox("all"))
        )
        self.canvas_mod.create_window((0, 0), window=self.scrollable_frame_mod, anchor="nw")
        self.canvas_mod.configure(yscrollcommand=scrollbar_mod.set)

        self.canvas_mod.pack(side="left", fill="both", expand=True)
        scrollbar_mod.pack(side="right", fill="y")

        # Binds de scroll de ratón
        self.canvas_crear.bind_all("<MouseWheel>", self.on_mousewheel)

        # Construir contenido
        self.build_crear_tab_ui(self.scrollable_frame_crear)
        self.build_modificar_tab_ui(self.scrollable_frame_mod)

    def on_mousewheel(self, event):
        try:
            selected = self.notebook.select()
            if selected == str(self.tab_crear):
                self.canvas_crear.yview_scroll(int(-1 * (event.delta / 120)), "units")
            elif selected == str(self.tab_modificar):
                self.canvas_mod.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception as e:
            pass

    def build_crear_tab_ui(self, parent):
        # Contenedor principal de creación
        main_container = tk.Frame(parent, bg=COLOR_BG, padx=30, pady=20)
        main_container.pack(fill="both", expand=True)

        # ========================================================
        # SECCIÓN 1: DATOS BÁSICOS
        # ========================================================
        card_basicos = tk.LabelFrame(main_container, text=" Datos del Producto ", 
                                     font=("Segoe UI", 11, "bold"), fg=COLOR_TEXT, 
                                     bg=COLOR_BG, bd=2, relief="groove", padx=15, pady=15)
        card_basicos.pack(fill="x", pady=10)

        # Nombre en pedido
        tk.Label(card_basicos, text="Nombre de producto:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=0, column=0, sticky="w", pady=6)
        entry_codigo = tk.Entry(card_basicos, textvariable=self.var_codigo, font=("Segoe UI", 10),
                                relief="solid", bd=1, highlightthickness=0, bg=COLOR_WHITE)
        entry_codigo.grid(row=0, column=1, columnspan=2, sticky="ew", pady=6, padx=(10, 0))
        entry_codigo.focus()

        # ID de producto (Autogenerado)
        tk.Label(card_basicos, text="Código ID (sistema):", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=1, column=0, sticky="w", pady=6)
        entry_id = tk.Entry(card_basicos, textvariable=self.var_id, font=("Segoe UI", 10),
                            relief="solid", bd=1, highlightthickness=0, bg=COLOR_WHITE)
        entry_id.grid(row=1, column=1, sticky="ew", pady=6, padx=(10, 0))
        
        # Etiqueta de estado para ID duplicado
        self.lbl_status_id = tk.Label(card_basicos, text="", font=("Segoe UI", 9, "italic"), bg=COLOR_BG)
        self.lbl_status_id.grid(row=1, column=2, sticky="w", padx=10)

        # Imagen del producto
        tk.Label(card_basicos, text="Foto del Producto:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=3, column=0, sticky="w", pady=6)
        
        img_select_frame = tk.Frame(card_basicos, bg=COLOR_BG)
        img_select_frame.grid(row=3, column=1, columnspan=2, sticky="ew", pady=6, padx=(10, 0))
        
        entry_img = tk.Entry(img_select_frame, textvariable=self.var_imagen_path, font=("Segoe UI", 9),
                             state="readonly", relief="solid", bd=1, bg=COLOR_CARD)
        entry_img.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        btn_browse = tk.Button(img_select_frame, text="Buscar Imagen...", command=self.seleccionar_imagen,
                               bg=COLOR_TEXT, fg=COLOR_BG, activebackground="#362720", 
                               activeforeground=COLOR_BG, font=("Segoe UI", 9, "bold"), relief="flat", bd=0, padx=10)
        btn_browse.pack(side="right")

        card_basicos.grid_columnconfigure(1, weight=1)

        # ========================================================
        # SECCIÓN 2: COMBINACIÓN Y GRUPOS
        # ========================================================
        card_grupo = tk.LabelFrame(main_container, text=" Lógica de Precios por Mayor / Combinación ", 
                                   font=("Segoe UI", 11, "bold"), fg=COLOR_TEXT, 
                                   bg=COLOR_BG, bd=2, relief="groove", padx=15, pady=15)
        card_grupo.pack(fill="x", pady=10)

        # Checkbox para combinable
        chk_combinable = tk.Checkbutton(card_grupo, text="¿Es un producto combinable con otros para el precio por mayor?",
                                        variable=self.var_es_combinable, command=self.toggle_grupo_frame,
                                        font=("Segoe UI", 10, "bold"), fg=COLOR_TEXT, bg=COLOR_BG, 
                                        activebackground=COLOR_BG, activeforeground=COLOR_TEXT, selectcolor=COLOR_WHITE)
        chk_combinable.pack(anchor="w")

        # Label para indicar combinación automática
        self.lbl_auto_intercambiable = tk.Label(card_grupo, text="", font=("Segoe UI", 9, "italic"), bg=COLOR_BG)
        self.lbl_auto_intercambiable.pack(anchor="w", pady=(5, 0))

        # Contenedor para el dropdown del grupo
        self.grupo_select_frame = tk.Frame(card_grupo, bg=COLOR_BG, pady=10)

        # Buscador/Filtro para combinaciones
        tk.Label(self.grupo_select_frame, text="Filtrar productos compatibles:", 
                 font=("Segoe UI", 10, "bold"), fg=COLOR_TEXT, bg=COLOR_BG).pack(anchor="w", pady=(0, 2))
        
        entry_filtro = tk.Entry(self.grupo_select_frame, textvariable=self.var_filtro_combinables, font=("Segoe UI", 10),
                                relief="solid", bd=1, highlightthickness=0, bg=COLOR_WHITE)
        entry_filtro.pack(fill="x", pady=(0, 10))
        self.var_filtro_combinables.trace_add("write", self.on_filtro_combinables_changed)

        tk.Label(self.grupo_select_frame, text="Selecciona los productos con los que se combina:", 
                 font=("Segoe UI", 10, "bold"), fg=COLOR_TEXT, bg=COLOR_BG).pack(anchor="w", pady=(5, 5))

        # Contenedor para las filas dinámicas
        self.combinables_container = tk.Frame(self.grupo_select_frame, bg=COLOR_BG)
        self.combinables_container.pack(fill="x")

        # Botón para agregar otra combinación
        self.btn_add_combinable = tk.Button(self.grupo_select_frame, text="+ Agregar otra categoría compatible", 
                                            command=self.agregar_fila_combinable,
                                            bg=COLOR_TEXT, fg=COLOR_BG, activebackground="#362720", 
                                            activeforeground=COLOR_BG, font=("Segoe UI", 9, "bold"), relief="flat", bd=0, padx=12, pady=6)
        self.btn_add_combinable.pack(anchor="w", pady=10)

        # ========================================================
        # SECCIÓN 3: PRECIOS Y VARIANTES
        # ========================================================
        self.card_precios = tk.LabelFrame(main_container, text=" Precios y Formatos ", 
                                          font=("Segoe UI", 11, "bold"), fg=COLOR_TEXT, 
                                          bg=COLOR_BG, bd=2, relief="groove", padx=15, pady=15)
        self.card_precios.pack(fill="x", pady=10)

        # Selector de Tipo (Simple vs Medidas)
        type_selector_frame = tk.Frame(self.card_precios, bg=COLOR_BG, pady=5)
        type_selector_frame.pack(fill="x")

        tk.Label(type_selector_frame, text="Tipo de Formato:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).pack(side="left", padx=(0, 20))

        rb_simple = tk.Radiobutton(type_selector_frame, text="Producto Único / Simple", variable=self.var_tipo, 
                                   value="simple", command=self.on_tipo_changed, font=("Segoe UI", 10),
                                   fg=COLOR_TEXT, bg=COLOR_BG, activebackground=COLOR_BG, selectcolor=COLOR_WHITE)
        rb_simple.pack(side="left", padx=10)

        rb_medidas = tk.Radiobutton(type_selector_frame, text="Con Medidas u Opciones", variable=self.var_tipo, 
                                    value="medidas", command=self.on_tipo_changed, font=("Segoe UI", 10),
                                    fg=COLOR_TEXT, bg=COLOR_BG, activebackground=COLOR_BG, selectcolor=COLOR_WHITE)
        rb_medidas.pack(side="left", padx=10)

        # Frame contenedor para controles de precio según tipo
        self.precios_content_frame = tk.Frame(self.card_precios, bg=COLOR_BG, pady=10)
        self.precios_content_frame.pack(fill="x")

        # Cargar interfaz inicial para tipo simple
        self.mostrar_campos_precio_simple()

        # ========================================================
        # BOTÓN GUARDAR Y ACCIONES
        # ========================================================
        btn_frame = tk.Frame(main_container, bg=COLOR_BG, pady=15)
        btn_frame.pack(fill="x")

        self.btn_guardar = tk.Button(btn_frame, text="💾 Guardar Producto", command=self.guardar_producto,
                                bg=COLOR_ACCENT, fg=COLOR_WHITE, activebackground=COLOR_ACCENT_HOVER, 
                                activeforeground=COLOR_WHITE, font=("Segoe UI", 11, "bold"), relief="flat", bd=0, padx=25, pady=12)
        self.btn_guardar.pack(side="left", padx=(0, 15))

        btn_cancelar = tk.Button(btn_frame, text="✕ Limpiar Campos", command=self.limpiar_formulario,
                                  bg=COLOR_CARD, fg=COLOR_TEXT, activebackground=COLOR_BORDER, 
                                  activeforeground=COLOR_TEXT, font=("Segoe UI", 10, "bold"), relief="flat", bd=0, padx=15, pady=10)
        btn_cancelar.pack(side="left")

    def toggle_grupo_frame(self):
        if self.var_es_combinable.get():
            self.grupo_select_frame.pack(fill="x")
            if not self.combinables_widgets:
                self.agregar_fila_combinable()
        else:
            self.grupo_select_frame.pack_forget()

    def agregar_fila_combinable(self):
        row_frame = tk.Frame(self.combinables_container, bg=COLOR_BG, pady=4)
        row_frame.pack(fill="x")

        var_grupo = tk.StringVar()

        filtro = self.var_filtro_combinables.get().lower()
        valores_combo = self.combo_values
        if filtro:
            valores_combo = [item for item in self.combo_values if filtro in item.lower()]

        combo = ttk.Combobox(row_frame, values=valores_combo, textvariable=var_grupo, 
                             state="normal", font=("Segoe UI", 10))
        combo.pack(side="left", fill="x", expand=True, padx=(0, 10))
        combo.bind("<KeyRelease>", self.on_combo_keyrelease)

        if valores_combo:
            combo.current(0)

        # Botón para remover fila
        btn_remove = tk.Button(row_frame, text="✕", command=lambda: self.remover_fila_combinable(row_frame),
                               bg=COLOR_CARD, fg=COLOR_DANGER, activebackground=COLOR_BORDER,
                               activeforeground=COLOR_DANGER, font=("Segoe UI", 9, "bold"), relief="flat", bd=0, padx=6)
        btn_remove.pack(side="right")

        self.combinables_widgets.append({
            "frame": row_frame,
            "var_grupo": var_grupo,
            "combo": combo
        })

    def remover_fila_combinable(self, frame_to_remove):
        if len(self.combinables_widgets) <= 1:
            messagebox.showwarning("Advertencia", "Si el producto es combinable, debe tener al menos una combinación.")
            return

        for item in self.combinables_widgets:
            if item["frame"] == frame_to_remove:
                item["frame"].destroy()
                self.combinables_widgets.remove(item)
                break

    def on_filtro_combinables_changed(self, *args):
        filtro = self.var_filtro_combinables.get().lower()
        if not filtro:
            valores_combo = self.combo_values
        else:
            valores_combo = [item for item in self.combo_values if filtro in item.lower()]

        for item in self.combinables_widgets:
            item["combo"]['values'] = valores_combo

    def toggle_grupo_frame_mod(self):
        if self.mod_var_es_combinable.get():
            self.mod_grupo_select_frame.pack(fill="x")
            if not self.mod_combinables_widgets:
                self.agregar_fila_combinable_mod()
        else:
            self.mod_grupo_select_frame.pack_forget()

    def agregar_fila_combinable_mod(self):
        row_frame = tk.Frame(self.mod_combinables_container, bg=COLOR_BG, pady=4)
        row_frame.pack(fill="x")

        var_grupo = tk.StringVar()

        combo = ttk.Combobox(row_frame, values=self.combo_values, textvariable=var_grupo, 
                             state="normal", font=("Segoe UI", 10))
        combo.pack(side="left", fill="x", expand=True, padx=(0, 10))
        combo.bind("<KeyRelease>", self.on_combo_keyrelease)

        if self.combo_values:
            combo.current(0)

        # Botón para remover fila
        btn_remove = tk.Button(row_frame, text="✕", command=lambda: self.remover_fila_combinable_mod(row_frame),
                               bg=COLOR_CARD, fg=COLOR_DANGER, activebackground=COLOR_BORDER,
                               activeforeground=COLOR_DANGER, font=("Segoe UI", 9, "bold"), relief="flat", bd=0, padx=6)
        btn_remove.pack(side="right")

        self.mod_combinables_widgets.append({
            "frame": row_frame,
            "var_grupo": var_grupo,
            "combo": combo
        })

    def remover_fila_combinable_mod(self, frame_to_remove):
        if len(self.mod_combinables_widgets) <= 1:
            messagebox.showwarning("Advertencia", "Si el producto es combinable, debe tener al menos una combinación.")
            return

        for item in self.mod_combinables_widgets:
            if item["frame"] == frame_to_remove:
                item["frame"].destroy()
                self.mod_combinables_widgets.remove(item)
                break

    def on_tipo_changed(self):
        for child in self.precios_content_frame.winfo_children():
            child.destroy()
        self.opciones_widgets.clear()

        tipo = self.var_tipo.get()
        if tipo == "simple":
            self.mostrar_campos_precio_simple()
        else:
            self.mostrar_campos_precio_medidas()

    def mostrar_campos_precio_simple(self):
        lbl_info = tk.Label(self.precios_content_frame, text="Ingresa los valores numéricos correspondientes:",
                            font=("Segoe UI", 9, "italic"), bg=COLOR_BG, fg="#7f6c60")
        lbl_info.pack(anchor="w", pady=(0, 10))

        form_frame = tk.Frame(self.precios_content_frame, bg=COLOR_BG)
        form_frame.pack(fill="x")

        # Precio Unitario
        tk.Label(form_frame, text="Precio Unitario ($):", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=0, column=0, sticky="w", pady=6)
        entry_unitario = tk.Entry(form_frame, textvariable=self.var_precio_unitario, font=("Segoe UI", 10),
                                  relief="solid", bd=1, highlightthickness=0, bg=COLOR_WHITE, width=20)
        entry_unitario.grid(row=0, column=1, sticky="w", pady=6, padx=(10, 30))

        # Precio Mayorista
        tk.Label(form_frame, text="Precio Mayorista ($):", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=0, column=2, sticky="w", pady=6)
        entry_mayor = tk.Entry(form_frame, textvariable=self.var_precio_mayor, font=("Segoe UI", 10),
                               relief="solid", bd=1, highlightthickness=0, bg=COLOR_WHITE, width=20)
        entry_mayor.grid(row=0, column=3, sticky="w", pady=6, padx=(10, 0))

    def mostrar_campos_precio_medidas(self):
        lbl_info = tk.Label(self.precios_content_frame, 
                            text="Ingresa las medidas del producto (ej: '20 cm', '30 cm', '3 mm') y sus respectivos precios:",
                            font=("Segoe UI", 9, "italic"), bg=COLOR_BG, fg="#7f6c60")
        lbl_info.pack(anchor="w", pady=(0, 10))

        # Cabecera de la tabla
        self.table_header = tk.Frame(self.precios_content_frame, bg=COLOR_BG)
        self.table_header.pack(fill="x")

        tk.Label(self.table_header, text="Medida / Opción", font=("Segoe UI", 9, "bold"), fg=COLOR_TEXT, bg=COLOR_BG, width=22, anchor="w").grid(row=0, column=0, padx=5, pady=2)
        tk.Label(self.table_header, text="Precio Mayor ($)", font=("Segoe UI", 9, "bold"), fg=COLOR_TEXT, bg=COLOR_BG, width=16, anchor="w").grid(row=0, column=1, padx=5, pady=2)
        tk.Label(self.table_header, text="Precio Unitario ($)", font=("Segoe UI", 9, "bold"), fg=COLOR_TEXT, bg=COLOR_BG, width=16, anchor="w").grid(row=0, column=2, padx=5, pady=2)
        
        # Contenedor para las filas dinámicas
        self.rows_container = tk.Frame(self.precios_content_frame, bg=COLOR_BG)
        self.rows_container.pack(fill="x")

        # Botón para agregar una nueva fila
        btn_add_opt = tk.Button(self.precios_content_frame, text="+ Agregar Medida / Opción", command=self.agregar_fila_opcion,
                                bg=COLOR_TEXT, fg=COLOR_BG, activebackground="#362720", 
                                activeforeground=COLOR_BG, font=("Segoe UI", 9, "bold"), relief="flat", bd=0, padx=12, pady=6)
        btn_add_opt.pack(anchor="w", pady=10)

        # Agregar las primeras dos filas por defecto
        self.agregar_fila_opcion()
        self.agregar_fila_opcion()
        
        if len(self.opciones_widgets) >= 2:
            self.opciones_widgets[0]["medida_entry"].insert(0, "20 cm")
            self.opciones_widgets[1]["medida_entry"].insert(0, "30 cm")

    def agregar_fila_opcion(self):
        row_frame = tk.Frame(self.rows_container, bg=COLOR_BG, pady=4)
        row_frame.pack(fill="x")

        entry_medida = tk.Entry(row_frame, font=("Segoe UI", 10), relief="solid", bd=1, bg=COLOR_WHITE, width=22)
        entry_medida.grid(row=0, column=0, padx=5)

        entry_mayor = tk.Entry(row_frame, font=("Segoe UI", 10), relief="solid", bd=1, bg=COLOR_WHITE, width=16)
        entry_mayor.grid(row=0, column=1, padx=5)

        entry_unitario = tk.Entry(row_frame, font=("Segoe UI", 10), relief="solid", bd=1, bg=COLOR_WHITE, width=16)
        entry_unitario.grid(row=0, column=2, padx=5)

        # Botón para remover fila
        btn_remove = tk.Button(row_frame, text="✕", command=lambda: self.remover_fila_opcion(row_frame),
                               bg=COLOR_CARD, fg=COLOR_DANGER, activebackground=COLOR_BORDER,
                               activeforeground=COLOR_DANGER, font=("Segoe UI", 9, "bold"), relief="flat", bd=0, padx=6)
        btn_remove.grid(row=0, column=3, padx=10)

        self.opciones_widgets.append({
            "frame": row_frame,
            "medida_entry": entry_medida,
            "mayor_entry": entry_mayor,
            "unitario_entry": entry_unitario
        })

    def remover_fila_opcion(self, frame_to_remove):
        if len(self.opciones_widgets) <= 1:
            messagebox.showwarning("Advertencia", "Un producto con medidas debe tener al menos una opción.")
            return

        for item in self.opciones_widgets:
            if item["frame"] == frame_to_remove:
                item["frame"].destroy()
                self.opciones_widgets.remove(item)
                break

    def seleccionar_imagen(self):
        file_path = filedialog.askopenfilename(
            title="Seleccionar foto del producto",
            filetypes=[("Archivos de Imagen", "*.jpg *.jpeg *.png *.webp"), ("Todos los archivos", "*.*")]
        )
        if file_path:
            self.var_imagen_path.set(file_path)

    def limpiar_formulario(self):
        if messagebox.askyesno("Confirmar", "¿Seguro que deseas limpiar todos los campos del formulario?"):
            self.var_id.set("")
            self.var_codigo.set("")
            self.var_imagen_path.set("")
            self.var_tipo.set("simple")
            self.var_es_combinable.set(False)
            self.var_precio_mayor.set("")
            self.var_precio_unitario.set("")
            self.var_filtro_combinables.set("")
            self.lbl_auto_intercambiable.config(text="")
            
            for item in self.combinables_widgets:
                item["frame"].destroy()
            self.combinables_widgets.clear()

            self.toggle_grupo_frame()
            self.on_tipo_changed()

    def validar_datos(self):
        pid = self.var_id.get().strip()
        if not pid:
            messagebox.showerror("Error de Validación", "El campo 'Código ID' es requerido.")
            return False
        
        if not re.match("^[a-z0-9]+$", pid):
            messagebox.showerror("Error de Validación", "El Código ID sólo puede contener letras minúsculas y números (sin espacios ni acentos).")
            return False

        codigo = self.var_codigo.get().strip()
        if not codigo:
            messagebox.showerror("Error de Validación", "El campo 'Nombre de producto' es requerido.")
            return False

        imagen = self.var_imagen_path.get().strip()
        if not imagen or not os.path.exists(imagen):
            messagebox.showerror("Error de Validación", "Debes seleccionar una imagen válida del producto.")
            return False

        tipo = self.var_tipo.get()
        if tipo == "simple":
            try:
                unitario = int(self.var_precio_unitario.get().strip())
                mayor = int(self.var_precio_mayor.get().strip())
                if unitario <= 0 or mayor <= 0:
                    raise ValueError()
            except ValueError:
                messagebox.showerror("Error de Validación", "Los precios Mayorista y Unitario deben ser números enteros positivos mayores a cero.")
                return False
        else:
            if not self.opciones_widgets:
                messagebox.showerror("Error de Validación", "Debes ingresar al menos una Medida/Opción.")
                return False

            for idx, item in enumerate(self.opciones_widgets):
                medida = item["medida_entry"].get().strip()
                if not medida:
                    messagebox.showerror("Error de Validación", f"El campo 'Medida' en la fila {idx + 1} está vacío.")
                    return False
                
                try:
                    mayor = int(item["mayor_entry"].get().strip())
                    unitario = int(item["unitario_entry"].get().strip())
                    if unitario <= 0 or mayor <= 0:
                        raise ValueError()
                except ValueError:
                    messagebox.showerror("Error de Validación", f"Los precios en la fila {idx + 1} ('{medida}') deben ser números enteros positivos.")
                    return False

        if self.var_es_combinable.get():
            if not self.combinables_widgets:
                messagebox.showerror("Error de Validación", "Has marcado el producto como combinable pero no has agregado ninguna combinación.")
                return False
            for idx, item in enumerate(self.combinables_widgets):
                display_name = item["var_grupo"].get().strip()
                if not display_name:
                    messagebox.showerror("Error de Validación", f"El campo de combinación en la fila {idx + 1} está vacío.")
                    return False

        return True

    def guardar_producto(self):
        if not self.validar_datos():
            return

        nombre = self.var_codigo.get().strip()
        pid = self.var_id.get().strip()
        codigo = self.var_codigo.get().strip()
        src_imagen = self.var_imagen_path.get().strip()
        tipo = self.var_tipo.get()
        es_combinable = self.var_es_combinable.get()

        grupos_a_actualizar = set()
        if es_combinable:
            for idx, item in enumerate(self.combinables_widgets):
                display_name = item["var_grupo"].get().strip()
                grupo_id = None
                if display_name in self.display_to_code:
                    selected_code, grupo_id = self.display_to_code[display_name]
                else:
                    matched = False
                    for disp, (code, g_id) in self.display_to_code.items():
                        if disp.lower() == display_name.lower() or code.lower() == display_name.lower():
                            selected_code, grupo_id = code, g_id
                            matched = True
                            break
                    if not matched:
                        all_group_ids = set(self.grupos_dict.values())
                        if display_name in GROUP_NAMES_MAP or display_name in all_group_ids:
                            grupo_id = display_name
                        else:
                            messagebox.showerror("Error de Combinación", f"El producto o categoría '{display_name}' en la fila {idx + 1} no es válido.\nPor favor, selecciona un producto de la lista.")
                            return
                if grupo_id:
                    grupos_a_actualizar.add(grupo_id)

        _, ext = os.path.splitext(src_imagen.lower())
        dest_filename = f"{pid}.jpg"

        for d in self.target_dirs:
            i_dir = os.path.join(d, "img")
            if not os.path.exists(i_dir):
                os.makedirs(i_dir)
            dest_imagen_path = os.path.join(i_dir, dest_filename)
            
            if os.path.exists(src_imagen) and os.path.exists(dest_imagen_path) and os.path.samefile(src_imagen, dest_imagen_path):
                continue

            success_img = False
            if HAS_PIL:
                try:
                    img = Image.open(src_imagen)
                    if img.mode in ("RGBA", "P", "LA"):
                        background = Image.new("RGBA", img.size, (255, 255, 255, 255))
                        alpha_composite = Image.alpha_composite(background, img.convert("RGBA"))
                        img = alpha_composite.convert("RGB")
                    else:
                        img = img.convert("RGB")

                    max_w_h = 800
                    if img.width > max_w_h or img.height > max_w_h:
                        img.thumbnail((max_w_h, max_w_h), Image.Resampling.LANCZOS)
                    
                    img.save(dest_imagen_path, "JPEG", quality=85)
                    success_img = True
                except Exception as e:
                    print(f"Error de Pillow al guardar imagen en {d}, intentando copia directa:", e)
            
            if not success_img:
                try:
                    shutil.copy(src_imagen, dest_imagen_path)
                except Exception as e:
                    print(f"Error al copiar imagen en {d}:", e)

        js_image_path = f"img/{dest_filename}"

        nuevo_producto = {
            "codigo": codigo,
            "nombre": nombre,
            "imagen": js_image_path,
            "tipo": tipo
        }

        productos_hijos = {}

        if tipo == "simple":
            nuevo_producto["unitario"] = int(self.var_precio_unitario.get().strip())
            nuevo_producto["mayor"] = int(self.var_precio_mayor.get().strip())
        else:
            nuevo_producto["opciones"] = []
            for item in self.opciones_widgets:
                medida_val = item["medida_entry"].get().strip()
                mayor_val = int(item["mayor_entry"].get().strip())
                unitario_val = int(item["unitario_entry"].get().strip())
                
                nuevo_producto["opciones"].append({
                    "medida": medida_val,
                    "mayor": mayor_val,
                    "unitario": unitario_val
                })

                medida_limpia = self.normalize_string(medida_val)
                child_id = f"{pid}{medida_limpia}"
                productos_hijos[child_id] = {
                    "parent": pid,
                    "preselect": medida_val
                }

        try:
            self.actualizar_productos_js(pid, nuevo_producto, productos_hijos)
            self.productos_db[pid] = nuevo_producto
            for cid, cdata in productos_hijos.items():
                self.productos_db[cid] = cdata
        except Exception as e:
            messagebox.showerror("Error al Guardar", f"Error al reescribir productos.js:\n{str(e)}")
            return

        cart_shared_modificado = False
        if es_combinable and grupos_a_actualizar:
            try:
                for grupo_id in grupos_a_actualizar:
                    codigos_a_agregar = []
                    if grupo_id == "intercambiables":
                        if tipo == "medidas":
                            for child_id in productos_hijos.keys():
                                codigos_a_agregar.append(child_id)
                        else:
                            codigos_a_agregar.append(pid)
                    else:
                        codigos_a_agregar.append(pid)

                    self.actualizar_cart_shared_js(grupo_id, codigos_a_agregar)
                cart_shared_modificado = True
            except Exception as e:
                messagebox.showerror("Advertencia", f"El producto se creó con éxito, pero no se pudo actualizar cart-shared.js automáticamente:\n{str(e)}")

        # Sincronizar con la base de datos de ventas local
        precios_sinc = {"tipo": tipo}
        if tipo == "simple":
            precios_sinc["unitario"] = int(self.var_precio_unitario.get().strip())
            precios_sinc["mayor"] = int(self.var_precio_mayor.get().strip())
        else:
            precios_sinc["opciones"] = []
            for item in self.opciones_widgets:
                precios_sinc["opciones"].append({
                    "medida": item["medida_entry"].get().strip(),
                    "unitario": int(item["unitario_entry"].get().strip()),
                    "mayor": int(item["mayor_entry"].get().strip())
                })
        self.sincronizar_con_ventas_db(codigo, precios_sinc)

        self.obtener_productos_combinables()
        self.actualizar_combo_buscar()
        self.subir_a_github_async(nombre, pid, dest_filename, cart_shared_modificado, es_modificacion=False)

    def limpiar_despues_de_guardar(self):
        self.var_id.set("")
        self.var_codigo.set("")
        self.var_imagen_path.set("")
        self.var_precio_unitario.set("")
        self.var_precio_mayor.set("")
        self.var_es_combinable.set(False)
        self.var_filtro_combinables.set("")
        self.lbl_auto_intercambiable.config(text="")

        for item in self.combinables_widgets:
            item["frame"].destroy()
        self.combinables_widgets.clear()

        self.obtener_productos_combinables()
        self.toggle_grupo_frame()
        self.on_tipo_changed()

    # ========================================================
    # MÉTODOS DE LA PESTAÑA MODIFICAR
    # ========================================================
    def build_modificar_tab_ui(self, parent):
        main_container = tk.Frame(parent, bg=COLOR_BG, padx=30, pady=20)
        main_container.pack(fill="both", expand=True)

        # ========================================================
        # BUSCADOR
        # ========================================================
        search_card = tk.LabelFrame(main_container, text=" Buscar Producto Existente ", 
                                    font=("Segoe UI", 11, "bold"), fg=COLOR_TEXT, 
                                    bg=COLOR_BG, bd=2, relief="groove", padx=15, pady=15)
        search_card.pack(fill="x", pady=10)

        # Filtrar
        tk.Label(search_card, text="Filtrar por nombre/código:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=0, column=0, sticky="w", pady=6)
        
        entry_filtrar = tk.Entry(search_card, textvariable=self.var_busqueda, font=("Segoe UI", 10),
                                 relief="solid", bd=1, highlightthickness=0, bg=COLOR_WHITE)
        entry_filtrar.grid(row=0, column=1, sticky="ew", pady=6, padx=(10, 0))
        self.var_busqueda.trace_add("write", self.on_busqueda_changed)

        # Seleccionar
        tk.Label(search_card, text="Seleccionar producto:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=1, column=0, sticky="w", pady=6)
        
        self.combo_buscar = ttk.Combobox(search_card, textvariable=self.var_select_producto, font=("Segoe UI", 10), state="readonly")
        self.combo_buscar.grid(row=1, column=1, sticky="ew", pady=6, padx=(10, 0))
        self.combo_buscar.bind("<<ComboboxSelected>>", self.on_product_to_edit_selected)

        search_card.grid_columnconfigure(1, weight=1)

        # Placeholder
        self.lbl_select_placeholder = tk.Label(main_container, text="🔍 Por favor, busca y selecciona un producto arriba para comenzar a editar.",
                                               font=("Segoe UI", 12, "italic"), fg="#7f6c60", bg=COLOR_BG, pady=40)
        self.lbl_select_placeholder.pack(fill="x")

        # Edit Form Frame (inicialmente oculto)
        self.edit_form_frame = tk.Frame(main_container, bg=COLOR_BG)

        # --- SECCIONES INTERNAS DE EDIT FORM FRAME ---
        # SECCIÓN 1: DATOS BÁSICOS
        card_basicos = tk.LabelFrame(self.edit_form_frame, text=" Datos del Producto (Modificación) ", 
                                     font=("Segoe UI", 11, "bold"), fg=COLOR_TEXT, 
                                     bg=COLOR_BG, bd=2, relief="groove", padx=15, pady=15)
        card_basicos.pack(fill="x", pady=10)

        # Nombre en pedido
        tk.Label(card_basicos, text="Nombre de producto:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=0, column=0, sticky="w", pady=6)
        entry_codigo = tk.Entry(card_basicos, textvariable=self.mod_var_codigo, font=("Segoe UI", 10),
                                relief="solid", bd=1, highlightthickness=0, bg=COLOR_WHITE)
        entry_codigo.grid(row=0, column=1, columnspan=2, sticky="ew", pady=6, padx=(10, 0))

        # ID de producto (Deshabilitado en edición)
        tk.Label(card_basicos, text="Código ID (sistema):", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=1, column=0, sticky="w", pady=6)
        self.mod_entry_id = tk.Entry(card_basicos, textvariable=self.mod_var_id, font=("Segoe UI", 10),
                                    state="disabled", relief="solid", bd=1, highlightthickness=0, bg=COLOR_CARD)
        self.mod_entry_id.grid(row=1, column=1, sticky="ew", pady=6, padx=(10, 0))

        # Imagen del producto
        tk.Label(card_basicos, text="Foto del Producto:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=3, column=0, sticky="w", pady=6)
        
        img_select_frame = tk.Frame(card_basicos, bg=COLOR_BG)
        img_select_frame.grid(row=3, column=1, columnspan=2, sticky="ew", pady=6, padx=(10, 0))
        
        entry_img = tk.Entry(img_select_frame, textvariable=self.mod_var_imagen_path, font=("Segoe UI", 9),
                             state="readonly", relief="solid", bd=1, bg=COLOR_CARD)
        entry_img.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        btn_browse = tk.Button(img_select_frame, text="Cambiar Imagen...", command=self.seleccionar_imagen_mod,
                               bg=COLOR_TEXT, fg=COLOR_BG, activebackground="#362720", 
                               activeforeground=COLOR_BG, font=("Segoe UI", 9, "bold"), relief="flat", bd=0, padx=10)
        btn_browse.pack(side="right")

        card_basicos.grid_columnconfigure(1, weight=1)

        # ========================================================
        # SECCIÓN 2: COMBINACIÓN Y GRUPOS (Modificación)
        # ========================================================
        card_grupo = tk.LabelFrame(self.edit_form_frame, text=" Lógica de Precios por Mayor / Combinación ", 
                                   font=("Segoe UI", 11, "bold"), fg=COLOR_TEXT, 
                                   bg=COLOR_BG, bd=2, relief="groove", padx=15, pady=15)
        card_grupo.pack(fill="x", pady=10)

        # Checkbox para combinable
        chk_combinable = tk.Checkbutton(card_grupo, text="¿Es un producto combinable con otros para el precio por mayor?",
                                        variable=self.mod_var_es_combinable, command=self.toggle_grupo_frame_mod,
                                        font=("Segoe UI", 10, "bold"), fg=COLOR_TEXT, bg=COLOR_BG, 
                                        activebackground=COLOR_BG, activeforeground=COLOR_TEXT, selectcolor=COLOR_WHITE)
        chk_combinable.pack(anchor="w")

        # Contenedor para el dropdown del grupo
        self.mod_grupo_select_frame = tk.Frame(card_grupo, bg=COLOR_BG, pady=10)

        tk.Label(self.mod_grupo_select_frame, text="Selecciona los productos con los que se combina:", 
                 font=("Segoe UI", 10, "bold"), fg=COLOR_TEXT, bg=COLOR_BG).pack(anchor="w", pady=(0, 5))

        # Contenedor para las filas dinámicas
        self.mod_combinables_container = tk.Frame(self.mod_grupo_select_frame, bg=COLOR_BG)
        self.mod_combinables_container.pack(fill="x")

        # Botón para agregar otra combinación
        self.mod_btn_add_combinable = tk.Button(self.mod_grupo_select_frame, text="+ Agregar otro producto compatible", 
                                            command=self.agregar_fila_combinable_mod,
                                            bg=COLOR_TEXT, fg=COLOR_BG, activebackground="#362720", 
                                            activeforeground=COLOR_BG, font=("Segoe UI", 9, "bold"), relief="flat", bd=0, padx=12, pady=6)
        self.mod_btn_add_combinable.pack(anchor="w", pady=10)

        # SECCIÓN 3: PRECIOS Y VARIANTES
        self.mod_card_precios = tk.LabelFrame(self.edit_form_frame, text=" Precios y Formatos ", 
                                          font=("Segoe UI", 11, "bold"), fg=COLOR_TEXT, 
                                          bg=COLOR_BG, bd=2, relief="groove", padx=15, pady=15)
        self.mod_card_precios.pack(fill="x", pady=10)

        # Selector de Tipo (Simple vs Medidas)
        type_selector_frame = tk.Frame(self.mod_card_precios, bg=COLOR_BG, pady=5)
        type_selector_frame.pack(fill="x")

        tk.Label(type_selector_frame, text="Tipo de Formato:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).pack(side="left", padx=(0, 20))

        rb_simple = tk.Radiobutton(type_selector_frame, text="Producto Único / Simple", variable=self.mod_var_tipo, 
                                   value="simple", command=self.on_tipo_changed_mod, font=("Segoe UI", 10),
                                   fg=COLOR_TEXT, bg=COLOR_BG, activebackground=COLOR_BG, selectcolor=COLOR_WHITE)
        rb_simple.pack(side="left", padx=10)

        rb_medidas = tk.Radiobutton(type_selector_frame, text="Con Medidas u Opciones", variable=self.mod_var_tipo, 
                                    value="medidas", command=self.on_tipo_changed_mod, font=("Segoe UI", 10),
                                    fg=COLOR_TEXT, bg=COLOR_BG, activebackground=COLOR_BG, selectcolor=COLOR_WHITE)
        rb_medidas.pack(side="left", padx=10)

        # Frame contenedor para controles de precio según tipo
        self.mod_precios_content_frame = tk.Frame(self.mod_card_precios, bg=COLOR_BG, pady=10)
        self.mod_precios_content_frame.pack(fill="x")

        # Cargar interfaz inicial para tipo simple
        self.mostrar_campos_precio_simple_mod()

        # BOTONES
        btn_frame = tk.Frame(self.edit_form_frame, bg=COLOR_BG, pady=15)
        btn_frame.pack(fill="x")

        self.mod_btn_guardar = tk.Button(btn_frame, text="💾 Guardar Cambios", command=self.guardar_producto_mod,
                                bg=COLOR_ACCENT, fg=COLOR_WHITE, activebackground=COLOR_ACCENT_HOVER, 
                                activeforeground=COLOR_WHITE, font=("Segoe UI", 11, "bold"), relief="flat", bd=0, padx=25, pady=12)
        self.mod_btn_guardar.pack(side="left", padx=(0, 15))

        self.mod_btn_eliminar = tk.Button(btn_frame, text="🗑️ Eliminar Producto", command=self.eliminar_producto,
                                bg=COLOR_DANGER, fg=COLOR_WHITE, activebackground=COLOR_DANGER_HOVER, 
                                activeforeground=COLOR_WHITE, font=("Segoe UI", 10, "bold"), relief="flat", bd=0, padx=15, pady=10)
        self.mod_btn_eliminar.pack(side="left", padx=(0, 15))

        btn_cancelar = tk.Button(btn_frame, text="✕ Cancelar Edición", command=lambda: self.limpiar_formulario_mod(confirm=True),
                                  bg=COLOR_CARD, fg=COLOR_TEXT, activebackground=COLOR_BORDER, 
                                  activeforeground=COLOR_TEXT, font=("Segoe UI", 10, "bold"), relief="flat", bd=0, padx=15, pady=10)
        btn_cancelar.pack(side="left")

    def actualizar_combo_buscar(self):
        self.buscar_combo_values = []
        self.display_to_id_buscar = {}
        
        for pid, p in self.productos_db.items():
            if "parent" not in p:
                nombre = p.get("nombre", pid)
                display = f"{nombre} [{pid}]"
                self.buscar_combo_values.append(display)
                self.display_to_id_buscar[display] = pid
                
        self.buscar_combo_values.sort()
        if hasattr(self, 'combo_buscar'):
            self.combo_buscar['values'] = self.buscar_combo_values

    def on_busqueda_changed(self, *args):
        val = self.var_busqueda.get().lower()
        if not val:
            self.combo_buscar['values'] = self.buscar_combo_values
        else:
            filtered = [item for item in self.buscar_combo_values if val in item.lower()]
            self.combo_buscar['values'] = filtered

    def on_product_to_edit_selected(self, event):
        display = self.var_select_producto.get()
        pid = self.display_to_id_buscar.get(display)
        if pid:
            self.cargar_producto_edicion(pid)

    def cargar_producto_edicion(self, pid):
        if pid not in self.productos_db:
            return

        p = self.productos_db[pid]
        
        # 1. Habilitar ID temporalmente para asignarle el valor
        self.mod_entry_id.config(state="normal")
        self.mod_var_id.set(pid)
        self.mod_entry_id.config(state="disabled")

        # 2. Asignar resto de variables básicas
        self.mod_var_codigo.set(p.get("codigo", p.get("nombre", pid)))
        self.mod_var_imagen_path.set(p.get("imagen", ""))
        self.mod_var_tipo.set(p.get("tipo", "simple"))

        # 3. Disparar el cambio de interfaz de precios
        self.on_tipo_changed_mod()

        # 4. Rellenar precios
        if self.mod_var_tipo.get() == "simple":
            self.mod_var_precio_unitario.set(str(p.get("unitario", "")))
            self.mod_var_precio_mayor.set(str(p.get("mayor", "")))
        else:
            # Eliminar filas antiguas
            for item in self.mod_opciones_widgets:
                item["frame"].destroy()
            self.mod_opciones_widgets.clear()

            # Rellenar opciones nuevas
            for option in p.get("opciones", []):
                self.agregar_fila_opcion_mod()
                self.mod_opciones_widgets[-1]["medida_entry"].insert(0, option.get("medida", ""))
                self.mod_opciones_widgets[-1]["mayor_entry"].insert(0, str(option.get("mayor", "")))
                self.mod_opciones_widgets[-1]["unitario_entry"].insert(0, str(option.get("unitario", "")))

        # 5. Escanear combinables
        grupos_encontrados = []
        if pid in self.grupos_dict:
            grupos_encontrados.append(self.grupos_dict[pid])
        
        # Buscar posibles códigos de hijos de medidas
        hijos_ids = [k for k, v in self.productos_db.items() if isinstance(v, dict) and v.get("parent") == pid]
        for hid in hijos_ids:
            if hid in self.grupos_dict:
                g_id = self.grupos_dict[hid]
                if g_id not in grupos_encontrados:
                    grupos_encontrados.append(g_id)

        # Destruir widgets antiguos de combinación
        for item in self.mod_combinables_widgets:
            item["frame"].destroy()
        self.mod_combinables_widgets.clear()

        if grupos_encontrados:
            self.mod_var_es_combinable.set(True)
            self.toggle_grupo_frame_mod()
            
            # Limpiar fila vacía por defecto que agrega automáticamente toggle_grupo_frame_mod
            for item in self.mod_combinables_widgets:
                item["frame"].destroy()
            self.mod_combinables_widgets.clear()
            
            for grupo_id in grupos_encontrados:
                self.agregar_fila_combinable_mod()
                display_name = self.obtener_display_name_para_grupo(pid, grupo_id)
                self.mod_combinables_widgets[-1]["var_grupo"].set(display_name)
        else:
            self.mod_var_es_combinable.set(False)
            self.toggle_grupo_frame_mod()

        # 6. Mostrar el formulario de edición y ocultar placeholder
        self.lbl_select_placeholder.pack_forget()
        self.edit_form_frame.pack(fill="both", expand=True)

    def on_tipo_changed_mod(self):
        for child in self.mod_precios_content_frame.winfo_children():
            child.destroy()
        self.mod_opciones_widgets.clear()

        tipo = self.mod_var_tipo.get()
        if tipo == "simple":
            self.mostrar_campos_precio_simple_mod()
        else:
            self.mostrar_campos_precio_medidas_mod()

    def mostrar_campos_precio_simple_mod(self):
        lbl_info = tk.Label(self.mod_precios_content_frame, text="Ingresa los valores numéricos correspondientes:",
                            font=("Segoe UI", 9, "italic"), bg=COLOR_BG, fg="#7f6c60")
        lbl_info.pack(anchor="w", pady=(0, 10))

        form_frame = tk.Frame(self.mod_precios_content_frame, bg=COLOR_BG)
        form_frame.pack(fill="x")

        # Precio Unitario
        tk.Label(form_frame, text="Precio Unitario ($):", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=0, column=0, sticky="w", pady=6)
        entry_unitario = tk.Entry(form_frame, textvariable=self.mod_var_precio_unitario, font=("Segoe UI", 10),
                                  relief="solid", bd=1, highlightthickness=0, bg=COLOR_WHITE, width=20)
        entry_unitario.grid(row=0, column=1, sticky="w", pady=6, padx=(10, 30))

        # Precio Mayorista
        tk.Label(form_frame, text="Precio Mayorista ($):", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=0, column=2, sticky="w", pady=6)
        entry_mayor = tk.Entry(form_frame, textvariable=self.mod_var_precio_mayor, font=("Segoe UI", 10),
                               relief="solid", bd=1, highlightthickness=0, bg=COLOR_WHITE, width=20)
        entry_mayor.grid(row=0, column=3, sticky="w", pady=6, padx=(10, 0))

    def mostrar_campos_precio_medidas_mod(self):
        lbl_info = tk.Label(self.mod_precios_content_frame, 
                            text="Ingresa las medidas del producto (ej: '20 cm', '30 cm', '3 mm') y sus respectivos precios:",
                            font=("Segoe UI", 9, "italic"), bg=COLOR_BG, fg="#7f6c60")
        lbl_info.pack(anchor="w", pady=(0, 10))

        # Cabecera de la tabla
        self.mod_table_header = tk.Frame(self.mod_precios_content_frame, bg=COLOR_BG)
        self.mod_table_header.pack(fill="x")

        tk.Label(self.mod_table_header, text="Medida / Opción", font=("Segoe UI", 9, "bold"), fg=COLOR_TEXT, bg=COLOR_BG, width=22, anchor="w").grid(row=0, column=0, padx=5, pady=2)
        tk.Label(self.mod_table_header, text="Precio Mayor ($)", font=("Segoe UI", 9, "bold"), fg=COLOR_TEXT, bg=COLOR_BG, width=16, anchor="w").grid(row=0, column=1, padx=5, pady=2)
        tk.Label(self.mod_table_header, text="Precio Unitario ($)", font=("Segoe UI", 9, "bold"), fg=COLOR_TEXT, bg=COLOR_BG, width=16, anchor="w").grid(row=0, column=2, padx=5, pady=2)
        
        # Contenedor para las filas dinámicas
        self.mod_rows_container = tk.Frame(self.mod_precios_content_frame, bg=COLOR_BG)
        self.mod_rows_container.pack(fill="x")

        # Botón para agregar una nueva fila
        btn_add_opt = tk.Button(self.mod_precios_content_frame, text="+ Agregar Medida / Opción", command=self.agregar_fila_opcion_mod,
                                bg=COLOR_TEXT, fg=COLOR_BG, activebackground="#362720", 
                                activeforeground=COLOR_BG, font=("Segoe UI", 9, "bold"), relief="flat", bd=0, padx=12, pady=6)
        btn_add_opt.pack(anchor="w", pady=10)

    def agregar_fila_opcion_mod(self):
        row_frame = tk.Frame(self.mod_rows_container, bg=COLOR_BG, pady=4)
        row_frame.pack(fill="x")

        entry_medida = tk.Entry(row_frame, font=("Segoe UI", 10), relief="solid", bd=1, bg=COLOR_WHITE, width=22)
        entry_medida.grid(row=0, column=0, padx=5)

        entry_mayor = tk.Entry(row_frame, font=("Segoe UI", 10), relief="solid", bd=1, bg=COLOR_WHITE, width=16)
        entry_mayor.grid(row=0, column=1, padx=5)

        entry_unitario = tk.Entry(row_frame, font=("Segoe UI", 10), relief="solid", bd=1, bg=COLOR_WHITE, width=16)
        entry_unitario.grid(row=0, column=2, padx=5)

        # Botón para remover fila
        btn_remove = tk.Button(row_frame, text="✕", command=lambda: self.remover_fila_opcion_mod(row_frame),
                               bg=COLOR_CARD, fg=COLOR_DANGER, activebackground=COLOR_BORDER,
                               activeforeground=COLOR_DANGER, font=("Segoe UI", 9, "bold"), relief="flat", bd=0, padx=6)
        btn_remove.grid(row=0, column=3, padx=10)

        self.mod_opciones_widgets.append({
            "frame": row_frame,
            "medida_entry": entry_medida,
            "mayor_entry": entry_mayor,
            "unitario_entry": entry_unitario
        })

    def remover_fila_opcion_mod(self, frame_to_remove):
        if len(self.mod_opciones_widgets) <= 1:
            messagebox.showwarning("Advertencia", "Un producto con medidas debe tener al menos una opción.")
            return

        for item in self.mod_opciones_widgets:
            if item["frame"] == frame_to_remove:
                item["frame"].destroy()
                self.mod_opciones_widgets.remove(item)
                break

    def seleccionar_imagen_mod(self):
        file_path = filedialog.askopenfilename(
            title="Seleccionar foto del producto",
            filetypes=[("Archivos de Imagen", "*.jpg *.jpeg *.png *.webp"), ("Todos los archivos", "*.*")]
        )
        if file_path:
            self.mod_var_imagen_path.set(file_path)

    def limpiar_formulario_mod(self, confirm=True):
        if confirm:
            if not messagebox.askyesno("Confirmar", "¿Seguro que deseas cancelar la edición y limpiar los campos?"):
                return
        
        self.var_busqueda.set("")
        self.var_select_producto.set("")
        self.mod_var_id.set("")
        self.mod_var_codigo.set("")
        self.mod_var_imagen_path.set("")
        self.mod_var_tipo.set("simple")
        self.mod_var_es_combinable.set(False)
        self.mod_var_precio_unitario.set("")
        self.mod_var_precio_mayor.set("")

        for item in self.mod_combinables_widgets:
            item["frame"].destroy()
        self.mod_combinables_widgets.clear()

        # Ocultar formulario de edición y mostrar placeholder
        self.edit_form_frame.pack_forget()
        self.lbl_select_placeholder.pack(fill="x", pady=40)

    def validar_datos_mod(self):
        pid = self.mod_var_id.get().strip()
        if not pid:
            messagebox.showerror("Error de Validación", "El campo 'Código ID' es requerido.")
            return False

        codigo = self.mod_var_codigo.get().strip()
        if not codigo:
            messagebox.showerror("Error de Validación", "El campo 'Nombre de producto' es requerido.")
            return False

        imagen = self.mod_var_imagen_path.get().strip()
        if not imagen:
            messagebox.showerror("Error de Validación", "Debes seleccionar una imagen para el producto.")
            return False
            
        if imagen.startswith("img/"):
            # Imagen existente del proyecto, validar que exista en el subdirectorio img
            full_img_path = os.path.join(self.base_dir, imagen)
            if not os.path.exists(full_img_path):
                messagebox.showerror("Error de Validación", f"La imagen existente '{imagen}' no se encuentra en la carpeta del proyecto.")
                return False
        else:
            # Imagen local nueva
            if not os.path.exists(imagen):
                messagebox.showerror("Error de Validación", f"La imagen seleccionada no existe en tu computadora:\n{imagen}")
                return False

        tipo = self.mod_var_tipo.get()
        if tipo == "simple":
            try:
                unitario = int(self.mod_var_precio_unitario.get().strip())
                mayor = int(self.mod_var_precio_mayor.get().strip())
                if unitario <= 0 or mayor <= 0:
                    raise ValueError()
            except ValueError:
                messagebox.showerror("Error de Validación", "Los precios Mayorista y Unitario deben ser números enteros positivos mayores a cero.")
                return False
        else:
            if not self.mod_opciones_widgets:
                messagebox.showerror("Error de Validación", "Debes ingresar al menos una Medida/Opción.")
                return False

            for idx, item in enumerate(self.mod_opciones_widgets):
                medida = item["medida_entry"].get().strip()
                if not medida:
                    messagebox.showerror("Error de Validación", f"El campo 'Medida' en la fila {idx + 1} está vacío.")
                    return False
                
                try:
                    mayor = int(item["mayor_entry"].get().strip())
                    unitario = int(item["unitario_entry"].get().strip())
                    if unitario <= 0 or mayor <= 0:
                        raise ValueError()
                except ValueError:
                    messagebox.showerror("Error de Validación", f"Los precios en la fila {idx + 1} ('{medida}') deben ser números enteros positivos.")
                    return False

        if self.mod_var_es_combinable.get():
            if not self.mod_combinables_widgets:
                messagebox.showerror("Error de Validación", "Has marcado el producto como combinable pero no has agregado ninguna combinación.")
                return False
            for idx, item in enumerate(self.mod_combinables_widgets):
                display_name = item["var_grupo"].get().strip()
                if not display_name:
                    messagebox.showerror("Error de Validación", f"El campo de combinación en la fila {idx + 1} está vacío.")
                    return False

        return True

    def limpiar_codigos_de_cart_shared_js(self, codes_to_remove):
        for d in self.target_dirs:
            c_js = os.path.join(d, "cart-shared.js")
            if not os.path.exists(c_js):
                continue
            
            with open(c_js, "r", encoding="utf-8") as f:
                content = f.read()

            # 1. Limpiar de Set codigosIntercambiablesNorm
            pattern = r'(const\s+codigosIntercambiablesNorm\s*=\s*new\s+Set\(\[\s*)([\s\S]*?)(\s*\]\);)'
            match = re.search(pattern, content)
            if match:
                prefix = match.group(1)
                items_str = match.group(2)
                suffix = match.group(3)

                existing_items = [c.strip().strip('"').strip("'") for c in items_str.split(",") if c.strip()]
                new_items = [item for item in existing_items if item not in codes_to_remove]

                if len(new_items) != len(existing_items):
                    lines = []
                    for i in range(0, len(new_items), 6):
                        chunk = new_items[i:i+6]
                        line = ", ".join(f'"{item}"' for item in chunk)
                        lines.append("    " + line)
                    
                    new_items_str = ",\n".join(lines)
                    new_block = prefix + "\n" + new_items_str + "\n" + suffix
                    content = content.replace(match.group(0), new_block)

            # 2. Limpiar de gruposCombinables en gruposCombinables
            m_array = re.search(r'const\s+gruposCombinables\s*=\s*\[([\s\S]*?)\];', content)
            if m_array:
                array_content = m_array.group(1)
                matches = list(re.finditer(r'\{\s*id:\s*["\']([^"\']+)["\'][\s\S]*?codigos:\s*\[([\s\S]*?)\]', array_content))
                for m in matches:
                    g_id = m.group(1)
                    codigos_str = m.group(2)
                    
                    existing_codes = [c.strip().strip('"').strip("'") for c in codigos_str.split(",") if c.strip()]
                    new_codes = [c for c in existing_codes if c not in codes_to_remove]
                    
                    if len(new_codes) != len(existing_codes):
                        group_pattern = rf'({{\s*id:\s*["\']{g_id}["\'][\s\S]*?codigos:\s*\[)([^\]]*?)(\s*\])'
                        g_match = re.search(group_pattern, content)
                        if g_match:
                            g_prefix = g_match.group(1)
                            g_suffix = g_match.group(3)
                            indent = "            "
                            new_codigos_str = "\n" + ",\n".join(f'{indent}"{c}"' for c in new_codes) + "\n        "
                            new_group_block = g_prefix + new_codigos_str + g_suffix
                            content = content.replace(g_match.group(0), new_group_block)

            with open(c_js, "w", encoding="utf-8") as f:
                f.write(content)

    def guardar_producto_mod(self):
        if not self.validar_datos_mod():
            return

        nombre = self.mod_var_codigo.get().strip()
        pid = self.mod_var_id.get().strip()
        codigo = self.mod_var_codigo.get().strip()
        src_imagen = self.mod_var_imagen_path.get().strip()
        tipo = self.mod_var_tipo.get()
        es_combinable = self.mod_var_es_combinable.get()

        grupos_a_actualizar = set()
        if es_combinable:
            for idx, item in enumerate(self.mod_combinables_widgets):
                display_name = item["var_grupo"].get().strip()
                grupo_id = None
                if display_name in self.display_to_code:
                    selected_code, grupo_id = self.display_to_code[display_name]
                else:
                    matched = False
                    for disp, (code, g_id) in self.display_to_code.items():
                        if disp.lower() == display_name.lower() or code.lower() == display_name.lower():
                            selected_code, grupo_id = code, g_id
                            matched = True
                            break
                    if not matched:
                        all_group_ids = set(self.grupos_dict.values())
                        if display_name in GROUP_NAMES_MAP or display_name in all_group_ids:
                            grupo_id = display_name
                        else:
                            messagebox.showerror("Error de Combinación", f"El producto o categoría '{display_name}' en la fila {idx + 1} no es válido.\nPor favor, selecciona un producto de la lista.")
                            return
                if grupo_id:
                    grupos_a_actualizar.add(grupo_id)

        old_children_ids = [k for k, v in self.productos_db.items() if isinstance(v, dict) and v.get("parent") == pid]
        all_old_codes = [pid] + old_children_ids

        # 2. Limpiar de cart-shared.js los códigos viejos antes de guardar
        try:
            self.limpiar_codigos_de_cart_shared_js(all_old_codes)
        except Exception as e:
            print("Error al limpiar códigos antiguos de cart-shared.js:", e)

        # 3. Procesar imagen si es nueva
        img_is_new = not src_imagen.startswith("img/")
        dest_filename = f"{pid}.jpg"

        if img_is_new:
            _, ext = os.path.splitext(src_imagen.lower())
            for d in self.target_dirs:
                i_dir = os.path.join(d, "img")
                if not os.path.exists(i_dir):
                    os.makedirs(i_dir)
                dest_imagen_path = os.path.join(i_dir, dest_filename)
                
                if os.path.exists(src_imagen) and os.path.exists(dest_imagen_path) and os.path.samefile(src_imagen, dest_imagen_path):
                    continue

                success_img = False
                if HAS_PIL:
                    try:
                        img = Image.open(src_imagen)
                        if img.mode in ("RGBA", "P", "LA"):
                            background = Image.new("RGBA", img.size, (255, 255, 255, 255))
                            alpha_composite = Image.alpha_composite(background, img.convert("RGBA"))
                            img = alpha_composite.convert("RGB")
                        else:
                            img = img.convert("RGB")

                        max_w_h = 800
                        if img.width > max_w_h or img.height > max_w_h:
                            img.thumbnail((max_w_h, max_w_h), Image.Resampling.LANCZOS)
                        
                        img.save(dest_imagen_path, "JPEG", quality=85)
                        success_img = True
                    except Exception as e:
                        print(f"Error de Pillow en {d}, intentando copia directa:", e)
                
                if not success_img:
                    try:
                        shutil.copy(src_imagen, dest_imagen_path)
                    except Exception as e:
                        print(f"Error al copiar imagen en {d}:", e)
            js_image_path = f"img/{dest_filename}"
        else:
            js_image_path = src_imagen

        # Asegurar que la imagen del producto existe en todos los repositorios de destino
        for d in self.target_dirs:
            i_dir = os.path.join(d, "img")
            dest_imagen_path = os.path.join(i_dir, dest_filename)
            src_lookup = None
            for od in self.target_dirs:
                potential_src = os.path.join(od, js_image_path)
                if os.path.exists(potential_src):
                    src_lookup = potential_src
                    break
            if src_lookup and not os.path.exists(dest_imagen_path):
                try:
                    if not os.path.exists(i_dir):
                        os.makedirs(i_dir)
                    shutil.copy(src_lookup, dest_imagen_path)
                except Exception as e:
                    print(f"Error al sincronizar imagen existente a {d}:", e)

        # 4. Crear el objeto del producto principal
        nuevo_producto = {
            "codigo": codigo,
            "nombre": nombre,
            "imagen": js_image_path,
            "tipo": tipo
        }

        productos_hijos = {}

        if tipo == "simple":
            nuevo_producto["unitario"] = int(self.mod_var_precio_unitario.get().strip())
            nuevo_producto["mayor"] = int(self.mod_var_precio_mayor.get().strip())
        else:
            nuevo_producto["opciones"] = []
            for item in self.mod_opciones_widgets:
                medida_val = item["medida_entry"].get().strip()
                mayor_val = int(item["mayor_entry"].get().strip())
                unitario_val = int(item["unitario_entry"].get().strip())
                
                nuevo_producto["opciones"].append({
                    "medida": medida_val,
                    "mayor": mayor_val,
                    "unitario": unitario_val
                })

                medida_limpia = self.normalize_string(medida_val)
                child_id = f"{pid}{medida_limpia}"
                productos_hijos[child_id] = {
                    "parent": pid,
                    "preselect": medida_val
                }

        # 5. Modificar productos.js
        try:
            self.actualizar_productos_js(pid, nuevo_producto, productos_hijos)
            # Actualizar base de datos en memoria local
            for hk in old_children_ids:
                if hk in self.productos_db:
                    del self.productos_db[hk]
            self.productos_db[pid] = nuevo_producto
            for cid, cdata in productos_hijos.items():
                self.productos_db[cid] = cdata
        except Exception as e:
            messagebox.showerror("Error al Guardar", f"Error al reescribir productos.js:\n{str(e)}")
            return

        # 6. Re-agregar a cart-shared.js de forma automática si pertenecía a algún grupo
        cart_shared_modificado = False
        if es_combinable and grupos_a_actualizar:
            try:
                for grupo_id in grupos_a_actualizar:
                    codigos_a_agregar = []
                    if grupo_id == "intercambiables":
                        if tipo == "medidas":
                            for child_id in productos_hijos.keys():
                                codigos_a_agregar.append(child_id)
                        else:
                            codigos_a_agregar.append(pid)
                    else:
                        codigos_a_agregar.append(pid)

                    self.actualizar_cart_shared_js(grupo_id, codigos_a_agregar)
                cart_shared_modificado = True
            except Exception as e:
                messagebox.showerror("Advertencia", f"El producto se modificó con éxito, pero no se pudo actualizar cart-shared.js automáticamente:\n{str(e)}")

        # Sincronizar con la base de datos de ventas local
        precios_sinc = {"tipo": tipo}
        if tipo == "simple":
            precios_sinc["unitario"] = int(self.mod_var_precio_unitario.get().strip())
            precios_sinc["mayor"] = int(self.mod_var_precio_mayor.get().strip())
        else:
            precios_sinc["opciones"] = []
            for item in self.mod_opciones_widgets:
                precios_sinc["opciones"].append({
                    "medida": item["medida_entry"].get().strip(),
                    "unitario": int(item["unitario_entry"].get().strip()),
                    "mayor": int(item["mayor_entry"].get().strip())
                })
        self.sincronizar_con_ventas_db(codigo, precios_sinc)

        self.obtener_productos_combinables()
        self.actualizar_combo_buscar()
        self.subir_a_github_async(nombre, pid, os.path.basename(js_image_path), cart_shared_modificado, es_modificacion=True)

    def eliminar_producto(self):
        pid = self.mod_var_id.get().strip()
        if not pid or pid not in self.productos_db:
            messagebox.showerror("Error", "No hay ningún producto seleccionado para eliminar.")
            return

        nombre = self.mod_var_codigo.get().strip()
        
        # Confirmar eliminación
        if not messagebox.askyesno("Confirmar Eliminación", 
                                   f"⚠️ ¿Seguro que deseas eliminar permanentemente el producto '{nombre}' ({pid})?\n\n"
                                   f"Esto borrará sus datos en productos.js, sus combinaciones en cart-shared.js y su imagen del proyecto."):
            return

        # 1. Obtener códigos a eliminar (padre e hijos)
        old_children_ids = [k for k, v in self.productos_db.items() if isinstance(v, dict) and v.get("parent") == pid]
        all_codes = [pid] + old_children_ids

        # 2. Eliminar de cart-shared.js
        try:
            self.limpiar_codigos_de_cart_shared_js(all_codes)
        except Exception as e:
            print("Error al limpiar de cart-shared.js:", e)

        # 3. Eliminar imagen física
        p = self.productos_db[pid]
        img_path = p.get("imagen")
        image_filename = ""
        if img_path and img_path.startswith("img/"):
            image_filename = os.path.basename(img_path)
            full_img_path = os.path.join(self.base_dir, img_path)
            if os.path.exists(full_img_path):
                try:
                    os.remove(full_img_path)
                except Exception as e:
                    print("Error al eliminar archivo de imagen:", e)

        # 4. Eliminar de productos.js
        try:
            self.eliminar_producto_de_js(pid, old_children_ids)
            
            # Eliminar localmente de productos_db
            if pid in self.productos_db:
                del self.productos_db[pid]
            for hk in old_children_ids:
                if hk in self.productos_db:
                    del self.productos_db[hk]
        except Exception as e:
            messagebox.showerror("Error al Eliminar", f"No se pudo completar la eliminación en productos.js:\n{str(e)}")
            return

        # 5. Refrescar datos
        self.obtener_productos_combinables()
        self.actualizar_combo_buscar()
        
        # 6. Subir cambios a GitHub asíncronamente
        self.subir_a_github_async_eliminar(nombre, pid, image_filename)

    def eliminar_producto_de_js(self, pid, child_ids):
        for d in self.target_dirs:
            p_js = os.path.join(d, "productos.js")
            if not os.path.exists(p_js):
                continue
            with open(p_js, "r", encoding="utf-8") as f:
                content = f.read()

            start = content.find("{")
            end = content.rfind("}")
            json_str = content[start:end+1]
            try:
                data = json.loads(json_str)
            except:
                data = {}

            if pid in data:
                del data[pid]
            for cid in child_ids:
                if cid in data:
                    del data[cid]

            new_json_str = json.dumps(data, indent=4, ensure_ascii=False)
            new_content = f"const productos = {new_json_str};\n"

            with open(p_js, "w", encoding="utf-8") as f:
                f.write(new_content)

    def subir_a_github_async_eliminar(self, nombre, pid, image_filename):
        loading_popup = tk.Toplevel(self.root)
        loading_popup.title("Eliminando de Internet...")
        loading_popup.geometry("400x160")
        loading_popup.configure(bg=COLOR_BG)
        loading_popup.resizable(False, False)
        
        loading_popup.transient(self.root)
        loading_popup.grab_set()
        
        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 200
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 80
        loading_popup.geometry(f"+{x}+{y}")
        
        lbl_msg = tk.Label(
            loading_popup, 
            text="🗑️ Eliminando y subiendo a GitHub...", 
            font=("Segoe UI", 12, "bold"), 
            fg=COLOR_TEXT, 
            bg=COLOR_BG
        )
        lbl_msg.pack(pady=(25, 10))
        
        lbl_sub = tk.Label(
            loading_popup, 
            text="Conectando con servidores de GitHub. Por favor espera...", 
            font=("Segoe UI", 9, "italic"), 
            fg="#7f6c60", 
            bg=COLOR_BG
        )
        lbl_sub.pack()
        
        def run_git():
            git_exe = self.find_git_executable()
            success_count = 0
            errors = []
            
            for d in self.target_dirs:
                if not os.path.exists(os.path.join(d, ".git")):
                    continue
                try:
                    files_to_commit = ["productos.js", "cart-shared.js"]
                    if image_filename:
                        img_path_rel = f"img/{image_filename}"
                        if not os.path.exists(os.path.join(d, img_path_rel)):
                            subprocess.run([git_exe, "rm", img_path_rel], cwd=d, capture_output=True)
                        else:
                            subprocess.run([git_exe, "add", img_path_rel], cwd=d, capture_output=True)
                    
                    subprocess.run([git_exe, "add"] + files_to_commit, cwd=d, check=True, capture_output=True)
                    
                    commit_msg = f"Eliminar producto: {nombre} ({pid})"
                    subprocess.run([git_exe, "commit", "-m", commit_msg], cwd=d, check=True, capture_output=True)
                    
                    # git pull --rebase para evitar rechazos si la rama remota está más avanzada
                    subprocess.run([git_exe, "pull", "--rebase"], cwd=d, check=True, capture_output=True)
                    
                    subprocess.run([git_exe, "push"], cwd=d, check=True, capture_output=True)
                    success_count += 1
                except subprocess.CalledProcessError as e:
                    err_out = e.stderr.decode("utf-8", errors="ignore") if e.stderr else str(e)
                    errors.append(f"{os.path.basename(d)}: {err_out.strip()}")
                except Exception as e:
                    errors.append(f"{os.path.basename(d)}: {str(e)}")
            
            if errors:
                err_msg = "\n".join(errors)
                if success_count > 0:
                    err_msg = f"Se eliminó en algunos repositorios, pero falló en otros:\n\n{err_msg}"
                self.root.after(0, lambda: self.on_delete_error(loading_popup, nombre, err_msg))
            else:
                self.root.after(0, lambda: self.on_delete_success(loading_popup, nombre))

        threading.Thread(target=run_git, daemon=True).start()

    def on_delete_success(self, popup, nombre):
        popup.destroy()
        messagebox.showinfo(
            "¡Éxito!",
            f"✓ ¡El producto '{nombre}' ha sido eliminado de la base de datos y de Internet con éxito!\n\n"
            f"Los cambios ya están publicados en la página web."
        )
        self.limpiar_formulario_mod(confirm=False)

    def on_delete_error(self, popup, nombre, err_msg):
        popup.destroy()
        messagebox.showwarning(
            "Guardado Localmente",
            f"El producto '{nombre}' se eliminó en tu computadora, pero no se pudieron subir los cambios a Internet.\n\n"
            f"Detalles del error:\n{err_msg}\n\n"
            f"No te preocupes, puedes abrir GitHub Desktop más tarde para subir los cambios manualmente."
        )
        self.limpiar_formulario_mod(confirm=False)

    # ========================================================
    # MÉTODOS COMPARTIDOS Y GIT
    # ========================================================
    def subir_a_github_async(self, nombre, pid, image_filename, cart_shared_modified, es_modificacion=False):
        loading_popup = tk.Toplevel(self.root)
        loading_popup.title("Subiendo a Internet...")
        loading_popup.geometry("400x160")
        loading_popup.configure(bg=COLOR_BG)
        loading_popup.resizable(False, False)
        
        loading_popup.transient(self.root)
        loading_popup.grab_set()
        
        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 200
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 80
        loading_popup.geometry(f"+{x}+{y}")
        
        lbl_msg = tk.Label(
            loading_popup, 
            text="🚀 Subiendo cambios a GitHub...", 
            font=("Segoe UI", 12, "bold"), 
            fg=COLOR_TEXT, 
            bg=COLOR_BG
        )
        lbl_msg.pack(pady=(25, 10))
        
        lbl_sub = tk.Label(
            loading_popup, 
            text="Conectando con servidores de GitHub. Por favor espera...", 
            font=("Segoe UI", 9, "italic"), 
            fg="#7f6c60", 
            bg=COLOR_BG
        )
        lbl_sub.pack()
        
        def run_git():
            git_exe = self.find_git_executable()
            success_count = 0
            errors = []
            
            for d in self.target_dirs:
                if not os.path.exists(os.path.join(d, ".git")):
                    continue
                try:
                    files_to_add = ["productos.js"]
                    img_path_rel = f"img/{image_filename}"
                    if os.path.exists(os.path.join(d, img_path_rel)):
                        files_to_add.append(img_path_rel)
                    if cart_shared_modified:
                        files_to_add.append("cart-shared.js")
                    
                    # git add
                    subprocess.run([git_exe, "add"] + files_to_add, cwd=d, check=True, capture_output=True)
                    
                    # git commit
                    verb = "Modificar" if es_modificacion else "Agregar"
                    commit_msg = f"{verb} producto: {nombre} ({pid})"
                    subprocess.run([git_exe, "commit", "-m", commit_msg], cwd=d, check=True, capture_output=True)
                    
                    # git pull --rebase para evitar rechazos si la rama remota está más avanzada
                    subprocess.run([git_exe, "pull", "--rebase"], cwd=d, check=True, capture_output=True)
                    
                    # git push
                    subprocess.run([git_exe, "push"], cwd=d, check=True, capture_output=True)
                    success_count += 1
                except subprocess.CalledProcessError as e:
                    err_out = e.stderr.decode("utf-8", errors="ignore") if e.stderr else str(e)
                    errors.append(f"{os.path.basename(d)}: {err_out.strip()}")
                except Exception as e:
                    errors.append(f"{os.path.basename(d)}: {str(e)}")
            
            if errors:
                err_msg = "\n".join(errors)
                if success_count > 0:
                    err_msg = f"Se subió con éxito a algunos repositorios, pero falló en otros:\n\n{err_msg}"
                self.root.after(0, lambda: self.on_upload_error(loading_popup, nombre, err_msg, es_modificacion))
            else:
                self.root.after(0, lambda: self.on_upload_success(loading_popup, nombre, es_modificacion))

        threading.Thread(target=run_git, daemon=True).start()

    def on_upload_success(self, popup, nombre, es_modificacion):
        popup.destroy()
        verb = "modificado" if es_modificacion else "guardado"
        messagebox.showinfo(
            "¡Éxito!",
            f"✓ ¡El producto '{nombre}' ha sido {verb} y publicado en Internet con éxito!\n\n"
            f"Ya está disponible en la página web."
        )
        if es_modificacion:
            self.limpiar_formulario_mod(confirm=False)
        else:
            self.limpiar_despues_de_guardar()

    def on_upload_error(self, popup, nombre, err_msg, es_modificacion):
        popup.destroy()
        verb = "modificó" if es_modificacion else "guardó"
        messagebox.showwarning(
            "Guardado Localmente",
            f"El producto '{nombre}' se {verb} en tu computadora, pero no se pudo subir automáticamente a Internet.\n\n"
            f"Detalles del error:\n{err_msg}\n\n"
            f"No te preocupes, puedes abrir GitHub Desktop más tarde para subir los cambios manualmente."
        )
        if es_modificacion:
            self.limpiar_formulario_mod(confirm=False)
        else:
            self.limpiar_despues_de_guardar()

    def actualizar_productos_js(self, pid, nuevo_prod, hijos):
        for d in self.target_dirs:
            p_js = os.path.join(d, "productos.js")
            if not os.path.exists(p_js):
                # Si no existe, podemos crear uno vacío básico
                with open(p_js, "w", encoding="utf-8") as f:
                    f.write("const productos = {};\n")

            with open(p_js, "r", encoding="utf-8") as f:
                content = f.read()

            start = content.find("{")
            end = content.rfind("}")
            json_str = content[start:end+1]
            try:
                data = json.loads(json_str)
            except:
                data = {}

            hijos_a_eliminar = [k for k, v in data.items() if isinstance(v, dict) and v.get("parent") == pid]
            for hk in hijos_a_eliminar:
                if hk in data:
                    del data[hk]

            data[pid] = nuevo_prod
            for cid, cdata in hijos.items():
                data[cid] = cdata

            new_json_str = json.dumps(data, indent=4, ensure_ascii=False)
            new_content = f"const productos = {new_json_str};\n"

            with open(p_js, "w", encoding="utf-8") as f:
                f.write(new_content)

    def actualizar_cart_shared_js(self, grupo_id, codigos):
        for d in self.target_dirs:
            c_js = os.path.join(d, "cart-shared.js")
            if not os.path.exists(c_js):
                continue
            
            with open(c_js, "r", encoding="utf-8") as f:
                content = f.read()

            if grupo_id == "intercambiables":
                pattern = r'(const\s+codigosIntercambiablesNorm\s*=\s*new\s+Set\(\[\s*)([\s\S]*?)(\s*\]\);)'
                match = re.search(pattern, content)
                if match:
                    prefix = match.group(1)
                    items_str = match.group(2)
                    suffix = match.group(3)

                    existing_items = [c.strip().strip('"').strip("'") for c in items_str.split(",") if c.strip()]
                    
                    added = False
                    for code in codigos:
                        if code not in existing_items:
                            existing_items.append(code)
                            added = True
                    
                    if added:
                        lines = []
                        for i in range(0, len(existing_items), 6):
                            chunk = existing_items[i:i+6]
                            line = ", ".join(f'"{item}"' for item in chunk)
                            lines.append("    " + line)
                        
                        new_items_str = ",\n".join(lines)
                        new_block = prefix + "\n" + new_items_str + "\n" + suffix
                        content = content.replace(match.group(0), new_block)
            else:
                pattern = rf'({{\s*id:\s*["\']{grupo_id}["\'][\s\S]*?codigos:\s*\[)([^\]]*?)(\s*\])'
                match = re.search(pattern, content)
                if match:
                    prefix = match.group(1)
                    codigos_str = match.group(2)
                    suffix = match.group(3)

                    existing_codes = [c.strip().strip('"').strip("'") for c in codigos_str.split(",") if c.strip()]
                    
                    added = False
                    for code in codigos:
                        if code not in existing_codes:
                            existing_codes.append(code)
                            added = True
                    
                    if added:
                        indent = "            "
                        new_codigos_str = "\n" + ",\n".join(f'{indent}"{c}"' for c in existing_codes) + "\n        "
                        new_block = prefix + new_codigos_str + suffix
                        content = content.replace(match.group(0), new_block)

            with open(c_js, "w", encoding="utf-8") as f:
                f.write(content)

if __name__ == "__main__":
    # Ajuste de DPI en Windows para evitar que se vea borroso
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass

    root = tk.Tk()
    app = App(root)
    root.mainloop()
