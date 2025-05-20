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

THEME_AMBIANT_MATE_DARK = "Ambiant-MATE-Dark"
THEME_PERSONALITZAT_NAME = "AmbiantMATE-Personal"
THEME_PERSONALITZAT_PATH = os.path.expanduser(f"~/.themes/{THEME_PERSONALITZAT_NAME}")


class RedshiftControlApp:
    def __init__(self, master):
        self.master = master
        master.title("Control de Redshift i Tema")
        # Augmentem una mica l'alçada per al nou botó de sortir de Redshift
        master.geometry("380x420") 

        self.current_temp_val = 4500
        self.current_brightness_val = 0.8

        self.load_initial_config() 

        self.current_temp = tk.IntVar(value=self.current_temp_val)
        self.current_brightness = tk.DoubleVar(value=self.current_brightness_val)

        # --- Controls de Redshift ---
        redshift_frame = ttk.LabelFrame(master, text="Control de Redshift", padding=(10, 5))
        redshift_frame.pack(padx=10, pady=5, fill="x")
        
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

        self.apply_button = ttk.Button(redshift_frame, text="Aplicar i (Re)iniciar Redshift", command=self.apply_and_restart_redshift)
        self.apply_button.pack(pady=(10,5)) # Ajustem una mica el padding

        # Nou botó per sortir de Redshift
        self.quit_redshift_button = ttk.Button(redshift_frame, text="Sortir de Redshift", command=self.quit_redshift)
        self.quit_redshift_button.pack(pady=(0,10))


        # --- Control de Tema MATE ---
        theme_frame = ttk.LabelFrame(master, text="Control de Tema MATE", padding=(10, 5))
        theme_frame.pack(padx=10, pady=5, fill="x")

        self.available_themes = [THEME_AMBIANT_MATE_DARK]
        if os.path.isdir(THEME_PERSONALITZAT_PATH):
            self.available_themes.append(THEME_PERSONALITZAT_NAME)
        else:
            print(f"Avís: El directori del tema personalitzat '{THEME_PERSONALITZAT_PATH}' no s'ha trobat.")
        
        self.selected_theme_var = tk.StringVar(master)
        if self.available_themes:
            self.selected_theme_var.set(self.available_themes[0]) 
        else:
            self.selected_theme_var.set("Cap tema disponible")

        ttk.Label(theme_frame, text="Selecciona un tema:").pack(pady=(5,0))
        self.theme_option_menu = ttk.OptionMenu(theme_frame, self.selected_theme_var, self.selected_theme_var.get(), *self.available_themes)
        self.theme_option_menu.pack(pady=5)
        
        self.apply_theme_button = ttk.Button(theme_frame, text="Aplicar Tema Seleccionat", command=self.apply_selected_mate_theme)
        self.apply_theme_button.pack(pady=10)
        
        # --- Etiqueta d'Estat Global ---
        self.status_label_var = tk.StringVar(value="Llest.")
        ttk.Label(master, textvariable=self.status_label_var).pack(pady=(5,5), side="bottom")

        self.update_temp_label(self.current_temp.get())
        self.update_brightness_label(self.current_brightness.get())
        
        self.ensure_redshift_gtk_running(is_initial_start=True)

    # --- Mètodes de Redshift ---
    def quit_redshift(self):
        self.status_label_var.set("Tancant Redshift...")
        print("Intentant tancar tots els processos de Redshift...")
        try:
            # -q per a killall fa que no doni error si no hi ha processos
            subprocess.run(["killall", "-q", REDSHIFT_PROCESS_NAME], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(["killall", "-q", REDSHIFT_GTK_PROCESS_NAME], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(0.5) # Donar un moment per tancar
            if not self.is_process_running(REDSHIFT_GTK_PROCESS_NAME) and not self.is_process_running(REDSHIFT_PROCESS_NAME):
                self.status_label_var.set("Redshift tancat.")
                print("Tots els processos de Redshift s'han tancat.")
                messagebox.showinfo("Redshift", "S'han tancat els processos de Redshift.")
            else:
                self.status_label_var.set("Error: Redshift encara s'està executant.")
                print("Avís: Un o més processos de Redshift encara podrien estar executant-se.")
                messagebox.showwarning("Redshift", "No s'han pogut tancar tots els processos de Redshift.")

        except Exception as e:
            self.status_label_var.set(f"Error en tancar Redshift: {e}")
            messagebox.showerror("Error", f"Un error ha ocorregut en intentar tancar Redshift:\n{e}")


    # ... (Resta de mètodes: update_temp_label, update_brightness_label, is_process_running, 
    # ensure_redshift_gtk_running, load_initial_config, write_config_file_direct, 
    # apply_and_restart_redshift, apply_selected_mate_theme són IGUALS que abans) ...
    def update_temp_label(self, value):
        self.temp_label_var.set(f"{int(float(value))}K")

    def update_brightness_label(self, value):
        self.brightness_label_var.set(f"{float(value):.2f}")

    def is_process_running(self, process_name):
        try:
            subprocess.check_call(["pgrep", "-x", process_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False
        except FileNotFoundError: 
            print("Avís: La comanda 'pgrep' no s'ha trobat. No es pot comprovar si el procés s'executa.")
            return False 

    def ensure_redshift_gtk_running(self, is_initial_start=False):
        self.status_label_var.set("Comprovant estat de Redshift...")
        if not self.is_process_running(REDSHIFT_GTK_PROCESS_NAME):
            self.status_label_var.set(f"Iniciant {REDSHIFT_GTK_PROCESS_NAME}...")
            print(f"No s'ha trobat {REDSHIFT_GTK_PROCESS_NAME} en execució. S'intentarà iniciar.")
            try:
                if is_initial_start and not os.path.exists(CONFIG_FILE_PATH):
                    print(f"El fitxer de configuració no existeix. Creant un de bàsic per a l'inici de {REDSHIFT_GTK_PROCESS_NAME}.")
                    self.write_config_file_direct(self.current_temp_val, self.current_brightness_val, silent=True)

                subprocess.Popen([REDSHIFT_GTK_PROCESS_NAME])
                time.sleep(1) 
                if self.is_process_running(REDSHIFT_GTK_PROCESS_NAME):
                    self.status_label_var.set(f"{REDSHIFT_GTK_PROCESS_NAME} iniciat.")
                    print(f"{REDSHIFT_GTK_PROCESS_NAME} iniciat correctament.")
                else:
                    self.status_label_var.set(f"Error en iniciar {REDSHIFT_GTK_PROCESS_NAME}.")
                    print(f"Sembla que {REDSHIFT_GTK_PROCESS_NAME} no s'ha iniciat correctament.")
            except Exception as e:
                self.status_label_var.set(f"Excepció en iniciar Redshift: {e}")
                messagebox.showerror("Error", f"No s'ha pogut iniciar {REDSHIFT_GTK_PROCESS_NAME}:\n{e}")
        else:
            self.status_label_var.set(f"{REDSHIFT_GTK_PROCESS_NAME} ja s'està executant.")
            print(f"{REDSHIFT_GTK_PROCESS_NAME} ja s'està executant.")

    def load_initial_config(self):
        if not os.path.exists(CONFIG_FILE_PATH):
            print(f"Avís: El fitxer {CONFIG_FILE_PATH} no existeix. S'usaran valors per defecte.")
            return

        config_reader = configparser.ConfigParser()
        try:
            config_reader.optionxform = str
            config_reader.read(CONFIG_FILE_PATH)
            if config_reader.has_section('redshift'):
                self.current_temp_val = config_reader.getint('redshift', 'temp-night', 
                                                             fallback=config_reader.getint('redshift', 'temp-day', fallback=4500))
                self.current_brightness_val = config_reader.getfloat('redshift', 'brightness-night',
                                                                   fallback=config_reader.getfloat('redshift', 'brightness-day', fallback=0.8))
        except Exception as e:
            print(f"Error llegint configuració inicial des de {CONFIG_FILE_PATH}: {e}. S'usaran valors per defecte.")

    def write_config_file_direct(self, temp, brightness, silent=False):
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
                 messagebox.showinfo("Configuració Redshift guardada", f"S'ha guardat la configuració de Redshift a {CONFIG_FILE_PATH}")
            print(f"Configuració Redshift guardada (directament) a {CONFIG_FILE_PATH}")
            return True
        except Exception as e:
            error_msg = f"No s'ha pogut guardar la configuració de Redshift (directament):\n{e}"
            if not silent: messagebox.showerror("Error guardant config Redshift", error_msg)
            else: print(error_msg)
            return False

    def apply_and_restart_redshift(self):
        self.status_label_var.set("Aplicant canvis a Redshift...")
        new_temp = self.current_temp.get()
        new_brightness = self.current_brightness.get()

        if not self.write_config_file_direct(new_temp, new_brightness):
            self.status_label_var.set("Error en guardar la config de Redshift.")
            return

        try:
            self.status_label_var.set("Reiniciant Redshift...")
            print("Intentant tancar processos Redshift existents...")
            subprocess.run(["killall", "-q", REDSHIFT_PROCESS_NAME], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(["killall", "-q", REDSHIFT_GTK_PROCESS_NAME], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(0.5) 
            print(f"Intentant iniciar {REDSHIFT_GTK_PROCESS_NAME}...")
            subprocess.Popen([REDSHIFT_GTK_PROCESS_NAME]) 
            time.sleep(1) 
            if self.is_process_running(REDSHIFT_GTK_PROCESS_NAME):
                self.status_label_var.set("Redshift reiniciat amb la nova configuració.")
                print(f"{REDSHIFT_GTK_PROCESS_NAME} reiniciat correctament.")
            else:
                self.status_label_var.set(f"Error en reiniciar {REDSHIFT_GTK_PROCESS_NAME}.")
                print(f"Sembla que {REDSHIFT_GTK_PROCESS_NAME} no s'ha reiniciat correctament.")
        except Exception as e_restart:
            self.status_label_var.set(f"Excepció en reiniciar Redshift: {e_restart}")
            messagebox.showerror("Error reiniciant Redshift", f"No s'ha pogut reiniciar Redshift automàticament:\n{e_restart}")


    def apply_selected_mate_theme(self):
        selected_theme = self.selected_theme_var.get()
        if not selected_theme or selected_theme == "Cap tema disponible":
            messagebox.showwarning("Cap Tema", "No hi ha cap tema seleccionat o disponible.")
            return

        self.status_label_var.set(f"Aplicant tema {selected_theme}...")
        print(f"Intentant aplicar el tema GTK de MATE: {selected_theme}")
        
        theme_name_for_gsettings = selected_theme 

        try:
            subprocess.run(["gsettings", "set", "org.mate.interface", "gtk-theme", theme_name_for_gsettings], check=True)
            try:
                subprocess.run(["gsettings", "set", "org.mate.Marco.general", "theme", theme_name_for_gsettings], check=True)
                print(f"Tema de Marco també canviat a {theme_name_for_gsettings}.")
            except subprocess.CalledProcessError as e_marco:
                print(f"Avís: No s'ha pogut canviar el tema de Marco a {theme_name_for_gsettings}. Error: {e_marco}")

            self.status_label_var.set(f"Tema {theme_name_for_gsettings} aplicat.")
            messagebox.showinfo("Tema Canviat", f"S'ha intentat aplicar el tema {theme_name_for_gsettings} a GTK i Marco.")

        except FileNotFoundError:
            self.status_label_var.set("Error: 'gsettings' no trobat.")
            messagebox.showerror("Error", "La comanda 'gsettings' no s'ha trobat.")
        except subprocess.CalledProcessError as e:
            self.status_label_var.set(f"Error en aplicar el tema: {e}")
            messagebox.showerror("Error", f"No s'ha pogut aplicar el tema {theme_name_for_gsettings}.\nError: {e}")
        except Exception as e:
            self.status_label_var.set(f"Error inesperat en aplicar tema: {e}")
            messagebox.showerror("Error", f"Un error inesperat ha ocorregut en aplicar el tema:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = RedshiftControlApp(root)
    root.mainloop()