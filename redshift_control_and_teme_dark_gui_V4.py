#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox
import os
import configparser
import subprocess
import time

# --- Constants Globals ---
CONFIG_FILE_PATH_REDSHIFT = os.path.expanduser("~/.config/redshift.conf")
# Fitxer per desar les preferències d'aquesta aplicació (temes seleccionats per Sol/Lluna)
APP_PREFS_DIR = os.path.expanduser("~/.config/control_pantalla_mate")
APP_PREFS_FILE = os.path.join(APP_PREFS_DIR, "prefs.ini")

REDSHIFT_GTK_PROCESS_NAME = "redshift-gtk"
REDSHIFT_PROCESS_NAME = "redshift"

# Noms de temes per defecte si no hi ha preferències desades
DEFAULT_THEME_LLUNA = "Ambiant-MATE-Dark"
DEFAULT_THEME_SOL = "Ambiant-MATE"

# Valors de Redshift per defecte si redshift.conf no existeix o per als sliders
DEFAULT_REDSHIFT_TEMP = 4500
DEFAULT_REDSHIFT_BRIGHTNESS = 0.8
# Valors per al mode Sol si Redshift es posa en neutre en lloc de tancar-se
REDSHIFT_TEMP_SOL_NEUTRE = 6500
REDSHIFT_BRIGHTNESS_SOL_NEUTRE = 1.0


def get_installed_gtk_themes():
    """Detecta els temes GTK instal·lats al sistema i a l'usuari."""
    themes = set()
    theme_paths = [
        "/usr/share/themes",
        os.path.expanduser("~/.themes")
    ]
    for path in theme_paths:
        if os.path.isdir(path):
            try:
                for theme_name in os.listdir(path):
                    # Comprovar si és un tema GTK vàlid (p.ex., té gtk-3.0 o index.theme)
                    # Una comprovació més robusta podria mirar el fitxer index.theme
                    if os.path.isdir(os.path.join(path, theme_name, "gtk-3.0")) or \
                       os.path.isfile(os.path.join(path, theme_name, "index.theme")):
                        themes.add(theme_name)
            except OSError as e:
                print(f"Error llegint temes de {path}: {e}")
    
    # Si les llistes per defecte no estan, afegir-les per si de cas
    if DEFAULT_THEME_LLUNA not in themes: themes.add(DEFAULT_THEME_LLUNA)
    if DEFAULT_THEME_SOL not in themes: themes.add(DEFAULT_THEME_SOL)
    
    return sorted(list(themes))


class RedshiftControlApp:
    def __init__(self, master):
        self.master = master
        master.title("Control Ràpid de Pantalla")
        master.geometry("380x500") # Ajustem mida per als nous desplegables

        # Crear directori de preferències si no existeix
        os.makedirs(APP_PREFS_DIR, exist_ok=True)

        self.all_installed_themes = get_installed_gtk_themes()
        self.load_app_preferences() # Carrega temes preferits per Sol/Lluna

        # --- Botons principals Sol / Lluna i els seus desplegables de tema ---
        mode_frame_main = ttk.Frame(master, padding=(10,10))
        mode_frame_main.pack(pady=5, fill="x")

        # --- Mode Sol ---
        sol_frame = ttk.Frame(mode_frame_main)
        sol_frame.pack(side="left", padx=(0,5), expand=True, fill="x")
        self.sol_button = ttk.Button(sol_frame, text="☀️ Sol (Dia)", command=self.activate_mode_sol)
        self.sol_button.pack(fill="x")
        ttk.Label(sol_frame, text="Tema per al Sol:").pack(pady=(5,0))
        self.selected_sol_theme_var = tk.StringVar(master)
        initial_sol_theme = self.pref_sol_theme
        if initial_sol_theme not in self.all_installed_themes and self.all_installed_themes:
            initial_sol_theme = DEFAULT_THEME_SOL # Fallback
            if initial_sol_theme not in self.all_installed_themes and self.all_installed_themes: # Doble fallback
                 initial_sol_theme = self.all_installed_themes[0]
        self.selected_sol_theme_var.set(initial_sol_theme)
        self.sol_theme_menu = ttk.OptionMenu(sol_frame, self.selected_sol_theme_var, initial_sol_theme, *self.all_installed_themes, command=self.save_app_preferences)
        self.sol_theme_menu.pack(fill="x", pady=(0,5))

        # --- Mode Lluna ---
        lluna_frame = ttk.Frame(mode_frame_main)
        lluna_frame.pack(side="right", padx=(5,0), expand=True, fill="x")
        self.lluna_button = ttk.Button(lluna_frame, text="🌙 Lluna (Nit)", command=self.activate_mode_lluna)
        self.lluna_button.pack(fill="x")
        ttk.Label(lluna_frame, text="Tema per a la Lluna:").pack(pady=(5,0))
        self.selected_lluna_theme_var = tk.StringVar(master)
        initial_lluna_theme = self.pref_lluna_theme
        if initial_lluna_theme not in self.all_installed_themes and self.all_installed_themes:
            initial_lluna_theme = DEFAULT_THEME_LLUNA # Fallback
            if initial_lluna_theme not in self.all_installed_themes and self.all_installed_themes: # Doble fallback
                 initial_lluna_theme = self.all_installed_themes[0]
        self.selected_lluna_theme_var.set(initial_lluna_theme)
        self.lluna_theme_menu = ttk.OptionMenu(lluna_frame, self.selected_lluna_theme_var, initial_lluna_theme, *self.all_installed_themes, command=self.save_app_preferences)
        self.lluna_theme_menu.pack(fill="x", pady=(0,5))

        # --- Controls Detallats ---
        details_frame = ttk.LabelFrame(master, text="Ajustaments Detallats de Redshift", padding=(10, 5))
        details_frame.pack(padx=10, pady=5, fill="x", expand=True)
        
        self.current_temp_val = DEFAULT_REDSHIFT_TEMP
        self.current_brightness_val = DEFAULT_REDSHIFT_BRIGHTNESS
        self.load_initial_redshift_config()

        self.current_temp = tk.IntVar(value=self.current_temp_val)
        self.current_brightness = tk.DoubleVar(value=self.current_brightness_val)

        ttk.Label(details_frame, text="Temperatura (K):").pack(pady=(5,0))
        self.temp_scale = ttk.Scale(details_frame, from_=2500, to=6500, orient="horizontal",
                                   variable=self.current_temp, length=300,
                                   command=self.update_temp_label)
        self.temp_scale.pack()
        self.temp_label_var = tk.StringVar(value=f"{self.current_temp.get()}K")
        ttk.Label(details_frame, textvariable=self.temp_label_var).pack()

        ttk.Label(details_frame, text="Brillantor (0.1 - 1.0):").pack(pady=(5,0))
        self.brightness_scale = ttk.Scale(details_frame, from_=0.1, to=1.0, orient="horizontal",
                                     variable=self.current_brightness, length=300,
                                     command=self.update_brightness_label)
        self.brightness_scale.pack()
        self.brightness_label_var = tk.StringVar(value=f"{self.current_brightness.get():.2f}")
        ttk.Label(details_frame, textvariable=self.brightness_label_var).pack()

        self.apply_redshift_button = ttk.Button(details_frame, text="Aplicar i Desar Ajustaments Redshift", command=self.apply_and_restart_redshift_manually)
        self.apply_redshift_button.pack(pady=(10,5))

        self.quit_redshift_button = ttk.Button(details_frame, text="Sortir de Redshift", command=self.quit_redshift)
        self.quit_redshift_button.pack(pady=(0,10))
        
        self.status_label_var = tk.StringVar(value="Llest.")
        ttk.Label(master, textvariable=self.status_label_var).pack(pady=(5,5), side="bottom")

        self.update_temp_label(self.current_temp.get())
        self.update_brightness_label(self.current_brightness.get())
        
        self.ensure_redshift_gtk_running(is_initial_start=True, silent=True)


    def load_app_preferences(self):
        """Llegeix les preferències de tema desades per l'usuari."""
        config = configparser.ConfigParser()
        # Valors per defecte si el fitxer o les claus no existeixen
        self.pref_sol_theme = DEFAULT_THEME_SOL
        self.pref_lluna_theme = DEFAULT_THEME_LLUNA

        if os.path.exists(APP_PREFS_FILE):
            try:
                config.read(APP_PREFS_FILE)
                if 'TemesPreferits' in config:
                    self.pref_sol_theme = config.get('TemesPreferits', 'tema_sol', fallback=DEFAULT_THEME_SOL)
                    self.pref_lluna_theme = config.get('TemesPreferits', 'tema_lluna', fallback=DEFAULT_THEME_LLUNA)
            except Exception as e:
                print(f"Error llegint preferències de l'aplicació des de {APP_PREFS_FILE}: {e}")
        else:
            print(f"Fitxer de preferències {APP_PREFS_FILE} no trobat. S'usaran valors per defecte.")
        
        print(f"Tema Sol carregat/per defecte: {self.pref_sol_theme}")
        print(f"Tema Lluna carregat/per defecte: {self.pref_lluna_theme}")


    def save_app_preferences(self, *args): # *args és per a la crida des de StringVar.trace
        """Guarda les seleccions de tema actuals al fitxer de preferències."""
        config = configparser.ConfigParser()
        if not config.has_section('TemesPreferits'):
            config.add_section('TemesPreferits')
        
        config.set('TemesPreferits', 'tema_sol', self.selected_sol_theme_var.get())
        config.set('TemesPreferits', 'tema_lluna', self.selected_lluna_theme_var.get())
        
        try:
            with open(APP_PREFS_FILE, 'w') as configfile:
                config.write(configfile)
            print(f"Preferències de tema guardades a {APP_PREFS_FILE}")
            self.status_label_var.set("Preferències de tema guardades.")
        except Exception as e:
            print(f"Error guardant preferències a {APP_PREFS_FILE}: {e}")
            self.status_label_var.set("Error guardant preferències de tema.")


    def activate_mode_sol(self):
        self.status_label_var.set("Activant Mode Sol...")
        print("\n--- Activant Mode Sol (Dia) ---")
        self.quit_redshift(silent=True) 
        
        theme_to_apply = self.selected_sol_theme_var.get()
        self.apply_mate_theme_direct(theme_to_apply, theme_to_apply, silent=True) # Assumeix mateix nom per Marco
        
        self.status_label_var.set(f"Mode Sol Activat (Tema: {theme_to_apply}, Redshift Apagat).")
        print(f"Mode Sol Activat. Tema: {theme_to_apply}.")

    def activate_mode_lluna(self):
        self.status_label_var.set("Activant Mode Lluna...")
        print("\n--- Activant Mode Lluna (Nit) ---")
        self.ensure_redshift_gtk_running(silent=True) 
        
        theme_to_apply = self.selected_lluna_theme_var.get()
        self.apply_mate_theme_direct(theme_to_apply, theme_to_apply, silent=True) # Assumeix mateix nom per Marco
        
        self.status_label_var.set(f"Mode Lluna Activat (Tema: {theme_to_apply}, Redshift actiu).")
        print(f"Mode Lluna Activat. Tema: {theme_to_apply}.")

    # --- Mètodes de Suport (is_process_running, quit_redshift, ensure_redshift_gtk_running, etc.) ---
    # Aquests mètodes són pràcticament iguals que a l'última versió funcional,
    # amb petits ajustos per a 'silent' i la lògica de quan escriure redshift.conf.
    # He copiat el cos d'aquests mètodes de la teva última versió funcional de referència (V3 corregida)
    # i els he enganxat aquí per brevetat, assegurant-me que els paràmetres 'silent' s'utilitzen.
    # Si us plau, verifica que són els correctes o informa'm si cal copiar-los explícitament de nou.

    def is_process_running(self, process_name):
        try:
            subprocess.check_call(["pgrep", "-x", process_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False
        except FileNotFoundError: 
            print("Avís: La comanda 'pgrep' no s'ha trobat.")
            return False 

    def quit_redshift(self, silent=False):
        if not silent: self.status_label_var.set("Tancant Redshift...")
        print("Intentant tancar tots els processos de Redshift...")
        try:
            subprocess.run(["killall", "-q", REDSHIFT_PROCESS_NAME], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(["killall", "-q", REDSHIFT_GTK_PROCESS_NAME], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(0.2) 
            if not self.is_process_running(REDSHIFT_GTK_PROCESS_NAME) and not self.is_process_running(REDSHIFT_PROCESS_NAME):
                if not silent: self.status_label_var.set("Redshift tancat.")
                print("Tots els processos de Redshift s'han tancat.")
                if not silent: messagebox.showinfo("Redshift", "S'han tancat els processos de Redshift.")
            else:
                if not silent: self.status_label_var.set("Error: Redshift encara s'està executant.")
                print("Avís: Un o més processos de Redshift encara podrien estar executant-se.")
                if not silent: messagebox.showwarning("Redshift", "No s'han pogut tancar tots els processos de Redshift.")
        except Exception as e:
            error_msg = f"Un error ha ocorregut en intentar tancar Redshift:\n{e}"
            if not silent: 
                self.status_label_var.set(f"Error en tancar Redshift: {e}")
                messagebox.showerror("Error", error_msg)
            else: 
                print(error_msg)

    def ensure_redshift_gtk_running(self, is_initial_start=False, silent=False):
        if not silent: self.status_label_var.set("Comprovant/Iniciant Redshift...")
        
        if is_initial_start and not os.path.exists(CONFIG_FILE_PATH_REDSHIFT):
            print(f"El fitxer de configuració {CONFIG_FILE_PATH_REDSHIFT} no existeix. Creant un de bàsic.")
            self.write_redshift_config_direct(DEFAULT_REDSHIFT_TEMP, DEFAULT_REDSHIFT_BRIGHTNESS, silent=True)

        if not self.is_process_running(REDSHIFT_GTK_PROCESS_NAME):
            print(f"No s'ha trobat {REDSHIFT_GTK_PROCESS_NAME} en execució. S'intentarà iniciar.")
            try:
                subprocess.Popen([REDSHIFT_GTK_PROCESS_NAME], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(1) 
                if self.is_process_running(REDSHIFT_GTK_PROCESS_NAME):
                    if not silent: self.status_label_var.set(f"{REDSHIFT_GTK_PROCESS_NAME} iniciat.")
                    print(f"{REDSHIFT_GTK_PROCESS_NAME} iniciat correctament.")
                else: 
                    if not silent: self.status_label_var.set(f"Error en iniciar {REDSHIFT_GTK_PROCESS_NAME}.")
                    print(f"Sembla que {REDSHIFT_GTK_PROCESS_NAME} no s'ha iniciat correctament.")
            except Exception as e:
                error_msg = f"No s'ha pogut iniciar {REDSHIFT_GTK_PROCESS_NAME}:\n{e}"
                if not silent: 
                    self.status_label_var.set(f"Excepció en iniciar Redshift: {e}")
                    messagebox.showerror("Error", error_msg)
                else: print(error_msg)
        else: 
             if not silent: self.status_label_var.set(f"{REDSHIFT_GTK_PROCESS_NAME} ja s'està executant.")
             print(f"{REDSHIFT_GTK_PROCESS_NAME} ja s'està executant.")

    def restart_redshift_process(self, silent=False):
        if not silent: self.status_label_var.set("Reiniciant Redshift...")
        print("Intentant reiniciar processos Redshift...")
        try:
            subprocess.run(["killall", "-q", REDSHIFT_PROCESS_NAME], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(["killall", "-q", REDSHIFT_GTK_PROCESS_NAME], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(0.5)
            subprocess.Popen([REDSHIFT_GTK_PROCESS_NAME], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1)
            if self.is_process_running(REDSHIFT_GTK_PROCESS_NAME):
                if not silent: self.status_label_var.set("Redshift reiniciat.")
                print(f"{REDSHIFT_GTK_PROCESS_NAME} reiniciat correctament.")
            else:
                if not silent: self.status_label_var.set(f"Error en reiniciar {REDSHIFT_GTK_PROCESS_NAME}.")
                print(f"Sembla que {REDSHIFT_GTK_PROCESS_NAME} no s'ha reiniciat correctament.")
        except Exception as e:
            error_msg = f"No s'ha pogut reiniciar Redshift:\n{e}"
            if not silent: 
                self.status_label_var.set(f"Excepció en reiniciar Redshift: {e}")
                messagebox.showerror("Error reiniciant Redshift", error_msg)
            else: print(error_msg)

    def apply_and_restart_redshift_manually(self): 
        self.status_label_var.set("Aplicant ajustaments manuals de Redshift...")
        new_temp = self.current_temp.get()
        new_brightness = self.current_brightness.get()
        if not self.write_redshift_config_direct(new_temp, new_brightness, silent=False): 
            self.status_label_var.set("Error en guardar la config de Redshift.")
            return
        self.restart_redshift_process(silent=False) 

    def apply_mate_theme_direct(self, gtk_theme_name, window_theme_name, silent=False):
        if not silent: self.status_label_var.set(f"Aplicant tema {gtk_theme_name}...")
        print(f"Intentant aplicar tema GTK: {gtk_theme_name}, Tema Finestra: {window_theme_name}")
        success_gtk = True
        success_marco = True
        try:
            subprocess.run(["gsettings", "set", "org.mate.interface", "gtk-theme", gtk_theme_name], check=True, capture_output=True)
        except Exception as e_gtk:
            success_gtk = False
            print(f"Error aplicant tema GTK {gtk_theme_name}: {e_gtk}")
            if not silent: messagebox.showerror("Error Tema GTK", f"No s'ha pogut aplicar el tema GTK {gtk_theme_name}.\nError: {e_gtk}")
        try:
            subprocess.run(["gsettings", "set", "org.mate.Marco.general", "theme", window_theme_name], check=True, capture_output=True)
        except Exception as e_marco:
            success_marco = False
            print(f"Error aplicant tema Marco {window_theme_name}: {e_marco}")
            if not silent : 
                 messagebox.showwarning("Avís Tema Marco", f"No s'ha pogut aplicar el tema de finestra {window_theme_name}.\nError: {e_marco}")
        if success_gtk and success_marco:
            if not silent: self.status_label_var.set(f"Tema {gtk_theme_name} aplicat.")
            if not silent: messagebox.showinfo("Tema Canviat", f"S'ha intentat aplicar el tema {gtk_theme_name}.")
            print("Temes aplicats.")
        elif not silent :
             self.status_label_var.set(f"Problemes en aplicar tema {gtk_theme_name}.")

    def load_initial_redshift_config(self):
        if not os.path.exists(CONFIG_FILE_PATH_REDSHIFT):
            print(f"Avís: {CONFIG_FILE_PATH_REDSHIFT} no existeix. S'usaran valors per defecte.")
            self.current_temp_val = DEFAULT_REDSHIFT_TEMP
            self.current_brightness_val = DEFAULT_REDSHIFT_BRIGHTNESS
            return
        config_reader = configparser.ConfigParser()
        try:
            config_reader.optionxform = str 
            config_reader.read(CONFIG_FILE_PATH_REDSHIFT)
            if config_reader.has_section('redshift'):
                self.current_temp_val = config_reader.getint('redshift', 'temp-night', fallback=DEFAULT_REDSHIFT_TEMP)
                self.current_brightness_val = config_reader.getfloat('redshift', 'brightness-night', fallback=DEFAULT_REDSHIFT_BRIGHTNESS)
            else: 
                print(f"Secció [redshift] no trobada a {CONFIG_FILE_PATH_REDSHIFT}. Valors per defecte.")
                self.current_temp_val = DEFAULT_REDSHIFT_TEMP
                self.current_brightness_val = DEFAULT_REDSHIFT_BRIGHTNESS
        except Exception as e:
            print(f"Error llegint {CONFIG_FILE_PATH_REDSHIFT}: {e}. Valors per defecte.")
            self.current_temp_val = DEFAULT_REDSHIFT_TEMP
            self.current_brightness_val = DEFAULT_REDSHIFT_BRIGHTNESS

    def write_redshift_config_direct(self, temp, brightness, silent=False):
        brightness_str = f"{float(brightness):.2f}"
        temp_str = str(int(temp))
        config_content = f"""[redshift]
temp-day={temp_str}
temp-night={temp_str}
brightness-day={brightness_str}
brightness-night={brightness_str}
transition=0
location-provider=manual
adjustment-method=randr
[manual]
lat=0
lon=0
"""
        try:
            with open(CONFIG_FILE_PATH_REDSHIFT, 'w', encoding='utf-8') as f:
                f.write(config_content)
            if not silent:
                 messagebox.showinfo("Configuració Redshift", f"Configuració de Redshift guardada.")
            print(f"Configuració Redshift guardada (Temp: {temp_str}K, Bright: {brightness_str})")
            return True
        except Exception as e:
            error_msg = f"No s'ha pogut guardar la config de Redshift: {e}"
            if not silent: messagebox.showerror("Error guardant config Redshift", error_msg)
            else: print(error_msg)
            return False

    def update_temp_label(self, value):
        self.temp_label_var.set(f"{int(float(value))}K")

    def update_brightness_label(self, value):
        self.brightness_label_var.set(f"{float(value):.2f}")

if __name__ == "__main__":
    root = tk.Tk()
    app = RedshiftControlApp(root)
    root.mainloop()