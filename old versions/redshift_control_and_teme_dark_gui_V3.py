#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox
import os
import configparser
import subprocess
import time

CONFIG_FILE_PATH = os.path.expanduser("~/.config/redshift.conf")
REDSHIFT_GTK_PROCESS_NAME = "redshift-gtk"
REDSHIFT_PROCESS_NAME = "redshift"

THEME_LLUNA_GTK_MARCO = "Ambiant-MATE-Dark"
THEME_SOL_PERSONALITZAT_NOM = "AmbiantMATE-Personal"
THEME_SOL_PERSONALITZAT_PATH = os.path.expanduser(f"~/.themes/{THEME_SOL_PERSONALITZAT_NOM}")
THEME_SOL_DEFAULT_GTK_MARCO = "Ambiant-MATE"

# Valors de Redshift per defecte si redshift.conf no existeix
# o per als sliders si no hi ha config prèvia
DEFAULT_REDSHIFT_TEMP = 4500
DEFAULT_REDSHIFT_BRIGHTNESS = 0.8

# Valors per al mode Sol si Redshift es posa en neutre en lloc de tancar-se
REDSHIFT_TEMP_SOL_NEUTRE = 6500
REDSHIFT_BRIGHTNESS_SOL_NEUTRE = 1.0


class RedshiftControlApp:
    def __init__(self, master):
        self.master = master
        master.title("Control Ràpid de Pantalla")
        master.geometry("380x480")

        mode_frame = ttk.Frame(master, padding=(10,10))
        mode_frame.pack(pady=10, fill="x")

        self.sol_button = ttk.Button(mode_frame, text="☀️ Sol (Dia)", command=self.activate_mode_sol, width=15)
        self.sol_button.pack(side="left", padx=(0,5), expand=True, fill="x")

        self.lluna_button = ttk.Button(mode_frame, text="🌙 Lluna (Nit)", command=self.activate_mode_lluna, width=15)
        self.lluna_button.pack(side="right", padx=(5,0), expand=True, fill="x")

        details_frame = ttk.LabelFrame(master, text="Ajustaments Detallats", padding=(10, 5))
        details_frame.pack(padx=10, pady=5, fill="x", expand=True)

        redshift_frame = ttk.LabelFrame(details_frame, text="Redshift", padding=(10, 5))
        redshift_frame.pack(padx=5, pady=5, fill="x")
        
        self.current_temp_val = DEFAULT_REDSHIFT_TEMP
        self.current_brightness_val = DEFAULT_REDSHIFT_BRIGHTNESS
        self.load_initial_redshift_config() # Carrega valors actuals de .conf per als sliders

        self.current_temp = tk.IntVar(value=self.current_temp_val)
        self.current_brightness = tk.DoubleVar(value=self.current_brightness_val)

        ttk.Label(redshift_frame, text="Temperatura (K):").pack(pady=(5,0))
        self.temp_scale = ttk.Scale(redshift_frame, from_=2500, to=6500, orient="horizontal",
                                   variable=self.current_temp, length=300,
                                   command=self.update_temp_label)
        self.temp_scale.pack()
        self.temp_label_var = tk.StringVar(value=f"{self.current_temp.get()}K")
        ttk.Label(redshift_frame, textvariable=self.temp_label_var).pack()

        ttk.Label(redshift_frame, text="Brillantor (0.1 - 1.0):").pack(pady=(5,0))
        self.brightness_scale = ttk.Scale(redshift_frame, from_=0.1, to=1.0, orient="horizontal",
                                     variable=self.current_brightness, length=300,
                                     command=self.update_brightness_label)
        self.brightness_scale.pack()
        self.brightness_label_var = tk.StringVar(value=f"{self.current_brightness.get():.2f}")
        ttk.Label(redshift_frame, textvariable=self.brightness_label_var).pack()

        self.apply_redshift_button = ttk.Button(redshift_frame, text="Aplicar Ajustaments Redshift", command=self.apply_and_restart_redshift_manually)
        self.apply_redshift_button.pack(pady=(10,5))

        self.quit_redshift_button = ttk.Button(redshift_frame, text="Sortir de Redshift", command=self.quit_redshift)
        self.quit_redshift_button.pack(pady=(0,10))

        theme_frame = ttk.LabelFrame(details_frame, text="Tema Escriptori MATE", padding=(10, 5))
        theme_frame.pack(padx=5, pady=5, fill="x")

        self.available_themes_for_menu = [THEME_LLUNA_GTK_MARCO, THEME_SOL_DEFAULT_GTK_MARCO] 
        if os.path.isdir(THEME_SOL_PERSONALITZAT_PATH):
            if THEME_SOL_PERSONALITZAT_NOM not in self.available_themes_for_menu:
                self.available_themes_for_menu.append(THEME_SOL_PERSONALITZAT_NOM)
        else:
            print(f"Avís: El directori del tema personalitzat '{THEME_SOL_PERSONALITZAT_PATH}' no s'ha trobat.")
        
        self.selected_theme_var = tk.StringVar(master)
        if self.available_themes_for_menu:
            self.selected_theme_var.set(self.available_themes_for_menu[0]) 
        else:
            self.selected_theme_var.set("Cap tema disponible")

        ttk.Label(theme_frame, text="Selecciona un tema (per aplicació manual):").pack(pady=(5,0))
        if self.available_themes_for_menu :
            self.theme_option_menu = ttk.OptionMenu(theme_frame, self.selected_theme_var, self.selected_theme_var.get() , *self.available_themes_for_menu)
            self.theme_option_menu.pack(pady=5)
        
        self.apply_theme_button = ttk.Button(theme_frame, text="Aplicar Tema Seleccionat Manualment", command=self.apply_selected_mate_theme_manually)
        self.apply_theme_button.pack(pady=10)
        
        self.status_label_var = tk.StringVar(value="Llest.")
        ttk.Label(master, textvariable=self.status_label_var).pack(pady=(5,5), side="bottom")

        self.update_temp_label(self.current_temp.get())
        self.update_brightness_label(self.current_brightness.get())
        
        self.ensure_redshift_gtk_running(is_initial_start=True, silent=True)


    def is_process_running(self, process_name):
        # ... (codi igual) ...
        try:
            subprocess.check_call(["pgrep", "-x", process_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False
        except FileNotFoundError: 
            print("Avís: La comanda 'pgrep' no s'ha trobat. No es pot comprovar si el procés s'executa.")
            return False

    def activate_mode_sol(self):
        self.status_label_var.set("Activant Mode Sol...")
        print("\n--- Activant Mode Sol (Dia) ---")
        self.quit_redshift(silent=True) # Apaga Redshift
        
        gtk_theme_to_apply = THEME_SOL_DEFAULT_GTK_MARCO
        marco_theme_to_apply = THEME_SOL_DEFAULT_GTK_MARCO
        if os.path.isdir(THEME_SOL_PERSONALITZAT_PATH):
            gtk_theme_to_apply = THEME_SOL_PERSONALITZAT_NOM
            marco_theme_to_apply = THEME_SOL_PERSONALITZAT_NOM
        
        self.apply_mate_theme_direct(gtk_theme_to_apply, marco_theme_to_apply, silent=True)
        self.status_label_var.set(f"Mode Sol Activat (Tema: {gtk_theme_to_apply}, Redshift Apagat).")
        print(f"Mode Sol Activat. Tema: {gtk_theme_to_apply}.")

    def activate_mode_lluna(self):
        self.status_label_var.set("Activant Mode Lluna...")
        print("\n--- Activant Mode Lluna (Nit) ---")
        
        # 1. Assegurar que Redshift s'està executant.
        #    Si no ho està, s'iniciarà i carregarà la configuració existent de redshift.conf.
        #    Si ja s'està executant, no fem res a la seva configuració, simplement el deixem estar.
        self.ensure_redshift_gtk_running(silent=True) 

        # 2. Aplicar tema fosc
        self.apply_mate_theme_direct(THEME_LLUNA_GTK_MARCO, THEME_LLUNA_GTK_MARCO, silent=True)
        
        self.status_label_var.set(f"Mode Lluna Activat (Tema: {THEME_LLUNA_GTK_MARCO}, Redshift actiu).")
        print(f"Mode Lluna Activat. Tema: {THEME_LLUNA_GTK_MARCO}. Redshift hauria d'estar utilitzant la seva última config guardada.")

    def quit_redshift(self, silent=False):
        # ... (codi igual) ...
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
        
        # Només escriure una configuració per defecte si el fitxer NO existeix
        # i és el primer inici de l'script.
        if is_initial_start and not os.path.exists(CONFIG_FILE_PATH):
            print(f"El fitxer de configuració {CONFIG_FILE_PATH} no existeix. Creant un de bàsic amb valors per defecte.")
            self.write_redshift_config_direct(DEFAULT_REDSHIFT_TEMP, DEFAULT_REDSHIFT_BRIGHTNESS, silent=True)

        if not self.is_process_running(REDSHIFT_GTK_PROCESS_NAME):
            print(f"No s'ha trobat {REDSHIFT_GTK_PROCESS_NAME} en execució. S'intentarà iniciar.")
            try:
                # Quan s'inicia, redshift-gtk carregarà la configuració actual de CONFIG_FILE_PATH
                subprocess.Popen([REDSHIFT_GTK_PROCESS_NAME], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(1) 
                if self.is_process_running(REDSHIFT_GTK_PROCESS_NAME):
                    if not silent: self.status_label_var.set(f"{REDSHIFT_GTK_PROCESS_NAME} iniciat.")
                    print(f"{REDSHIFT_GTK_PROCESS_NAME} iniciat correctament (hauria d'haver carregat config existent).")
                else: 
                    if not silent: self.status_label_var.set(f"Error en iniciar {REDSHIFT_GTK_PROCESS_NAME}.")
                    print(f"Sembla que {REDSHIFT_GTK_PROCESS_NAME} no s'ha iniciat correctament.")
            except Exception as e:
                error_msg = f"No s'ha pogut iniciar {REDSHIFT_GTK_PROCESS_NAME}:\n{e}"
                if not silent: 
                    self.status_label_var.set(f"Excepció en iniciar Redshift: {e}")
                    messagebox.showerror("Error", error_msg)
                else: print(error_msg)
        else: # Si Redshift-gtk ja s'està executant, no fem res amb la seva configuració aquí.
             if not silent: self.status_label_var.set(f"{REDSHIFT_GTK_PROCESS_NAME} ja s'està executant.")
             print(f"{REDSHIFT_GTK_PROCESS_NAME} ja s'està executant (cap canvi de configuració aplicat per aquest mètode).")

    def restart_redshift_process(self, silent=False): # Aquest SÍ reinicia per aplicar una NOVA config
        if not silent: self.status_label_var.set("Reiniciant Redshift...")
        print("Intentant reiniciar processos Redshift (per aplicar nova config)...")
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

        # Aquest botó SÍ que escriu la configuració dels sliders
        if not self.write_redshift_config_direct(new_temp, new_brightness, silent=False): 
            self.status_label_var.set("Error en guardar la config de Redshift.")
            return
        # I després reinicia Redshift per aplicar-la
        self.restart_redshift_process(silent=False) 

    def apply_mate_theme_direct(self, gtk_theme_name, window_theme_name, silent=False):
        # ... (codi igual) ...
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
                 messagebox.showwarning("Avís Tema Marco", f"No s'ha pogut aplicar el tema de finestra {window_theme_name}.\nPotser té un nom diferent o no està disponible.\nError: {e_marco}")
        
        if success_gtk and success_marco:
            if not silent: self.status_label_var.set(f"Tema {gtk_theme_name} aplicat.")
            if not silent: messagebox.showinfo("Tema Canviat", f"S'ha intentat aplicar el tema {gtk_theme_name}.")
            print("Temes aplicats.")
        elif not silent :
             self.status_label_var.set(f"Problemes en aplicar tema {gtk_theme_name}.")


    def apply_selected_mate_theme_manually(self): 
        # ... (codi igual) ...
        selected_theme_name = self.selected_theme_var.get()
        if not selected_theme_name or selected_theme_name == "Cap tema disponible":
            messagebox.showwarning("Cap Tema", "No hi ha cap tema seleccionat o disponible.")
            return
        self.apply_mate_theme_direct(selected_theme_name, selected_theme_name, silent=False)

    def load_initial_redshift_config(self):
        # ... (codi igual) ...
        if not os.path.exists(CONFIG_FILE_PATH):
            print(f"Avís: El fitxer {CONFIG_FILE_PATH} no existeix. S'usaran valors per defecte ({DEFAULT_REDSHIFT_TEMP}K, {DEFAULT_REDSHIFT_BRIGHTNESS} brill) per als controls.")
            self.current_temp_val = DEFAULT_REDSHIFT_TEMP
            self.current_brightness_val = DEFAULT_REDSHIFT_BRIGHTNESS
            return

        config_reader = configparser.ConfigParser()
        try:
            config_reader.optionxform = str 
            config_reader.read(CONFIG_FILE_PATH)
            if config_reader.has_section('redshift'):
                self.current_temp_val = config_reader.getint('redshift', 'temp-night', 
                                                             fallback=config_reader.getint('redshift', 'temp-day', fallback=DEFAULT_REDSHIFT_TEMP))
                self.current_brightness_val = config_reader.getfloat('redshift', 'brightness-night',
                                                                   fallback=config_reader.getfloat('redshift', 'brightness-day', fallback=DEFAULT_REDSHIFT_BRIGHTNESS))
            else: # Si el fitxer existeix però no té la secció [redshift]
                print(f"La secció [redshift] no s'ha trobat a {CONFIG_FILE_PATH}. S'usaran valors per defecte per als controls.")
                self.current_temp_val = DEFAULT_REDSHIFT_TEMP
                self.current_brightness_val = DEFAULT_REDSHIFT_BRIGHTNESS

        except Exception as e:
            print(f"Error llegint configuració inicial de Redshift des de {CONFIG_FILE_PATH}: {e}. S'usaran valors per defecte.")
            self.current_temp_val = DEFAULT_REDSHIFT_TEMP
            self.current_brightness_val = DEFAULT_REDSHIFT_BRIGHTNESS


    def write_redshift_config_direct(self, temp, brightness, silent=False):
        # ... (codi igual) ...
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
            with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as f:
                f.write(config_content)
            if not silent:
                 messagebox.showinfo("Configuració Redshift", f"Configuració de Redshift guardada a {CONFIG_FILE_PATH}")
            print(f"Configuració Redshift guardada (Temp: {temp_str}K, Bright: {brightness_str})")
            return True
        except Exception as e:
            error_msg = f"No s'ha pogut guardar la config de Redshift: {e}"
            if not silent: messagebox.showerror("Error guardant config Redshift", error_msg)
            else: print(error_msg)
            return False

    def update_temp_label(self, value):
        # ... (codi igual) ...
        self.temp_label_var.set(f"{int(float(value))}K")

    def update_brightness_label(self, value):
        # ... (codi igual) ...
        self.brightness_label_var.set(f"{float(value):.2f}")


if __name__ == "__main__":
    root = tk.Tk()
    app = RedshiftControlApp(root)
    root.mainloop()