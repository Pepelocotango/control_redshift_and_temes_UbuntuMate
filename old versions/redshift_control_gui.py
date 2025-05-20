#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox
import os
import configparser # Encara l'usem per llegir la configuració inicial
import subprocess
import time

CONFIG_FILE_PATH = os.path.expanduser("~/.config/redshift.conf")
REDSHIFT_GTK_PROCESS_NAME = "redshift-gtk"
REDSHIFT_PROCESS_NAME = "redshift"

class RedshiftControlApp:
    def __init__(self, master):
        self.master = master
        master.title("Control de Redshift")
        master.geometry("350x270")

        self.current_temp_val = 4500 # Valors per defecte
        self.current_brightness_val = 0.8

        self.load_initial_config() 

        self.current_temp = tk.IntVar(value=self.current_temp_val)
        self.current_brightness = tk.DoubleVar(value=self.current_brightness_val)

        ttk.Label(master, text="Temperatura (K):").pack(pady=(10,0))
        self.temp_scale = ttk.Scale(master, from_=2500, to=6500, orient="horizontal",
                                   variable=self.current_temp, length=300,
                                   command=self.update_temp_label)
        self.temp_scale.pack()
        self.temp_label_var = tk.StringVar(value=f"{self.current_temp.get()}K")
        ttk.Label(master, textvariable=self.temp_label_var).pack()

        ttk.Label(master, text="Brillantor (0.1 - 1.0):").pack(pady=(10,0))
        self.brightness_scale = ttk.Scale(master, from_=0.1, to=1.0, orient="horizontal",
                                     variable=self.current_brightness, length=300,
                                     command=self.update_brightness_label)
        self.brightness_scale.pack()
        self.brightness_label_var = tk.StringVar(value=f"{self.current_brightness.get():.2f}")
        ttk.Label(master, textvariable=self.brightness_label_var).pack()

        self.apply_button = ttk.Button(master, text="Aplicar i (Re)iniciar Redshift", command=self.apply_and_restart_redshift)
        self.apply_button.pack(pady=15)

        self.status_label_var = tk.StringVar(value="")
        ttk.Label(master, textvariable=self.status_label_var).pack(pady=(5,0))

        self.update_temp_label(self.current_temp.get())
        self.update_brightness_label(self.current_brightness.get())
        
        self.ensure_redshift_gtk_running(is_initial_start=True)

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

    def ensure_redshift_gtk_running(self, is_initial_start=False):
        self.status_label_var.set("Comprovant estat de Redshift...")
        if not self.is_process_running(REDSHIFT_GTK_PROCESS_NAME):
            self.status_label_var.set(f"Iniciant {REDSHIFT_GTK_PROCESS_NAME}...")
            print(f"No s'ha trobat {REDSHIFT_GTK_PROCESS_NAME} en execució. S'intentarà iniciar.")
            try:
                if is_initial_start and not os.path.exists(CONFIG_FILE_PATH):
                    print(f"El fitxer de configuració no existeix. Creant un de bàsic per a l'inici de {REDSHIFT_GTK_PROCESS_NAME}.")
                    # Escriure una configuració mínima si no existeix
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
                self.status_label_var.set(f"Excepció en iniciar: {e}")
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
        # Arrodonir la brillantor a 2 decimals per evitar massa dígits
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
                 messagebox.showinfo("Configuració guardada", f"S'ha guardat la configuració a {CONFIG_FILE_PATH}")
            print(f"Configuració guardada (directament) a {CONFIG_FILE_PATH}")
            
            # Per depurar, pots veure el que s'ha escrit
            # print("--- Contingut del fitxer escrit (mètode directe) ---")
            # print(config_content)
            # print("----------------------------------------------------")
            return True
        except Exception as e:
            error_msg = f"No s'ha pogut guardar la configuració (directament):\n{e}"
            if not silent:
                messagebox.showerror("Error guardant configuració", error_msg)
            else:
                print(error_msg)
            return False

    def apply_and_restart_redshift(self):
        self.status_label_var.set("Aplicant canvis...")
        new_temp = self.current_temp.get()
        new_brightness = self.current_brightness.get() # Ja és float

        if not self.write_config_file_direct(new_temp, new_brightness):
            self.status_label_var.set("Error en guardar la configuració.")
            return

        try:
            self.status_label_var.set("Reiniciant Redshift...")
            print("Intentant tancar processos Redshift existents...")
            subprocess.run(["killall", REDSHIFT_PROCESS_NAME], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(["killall", REDSHIFT_GTK_PROCESS_NAME], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            print("Esperant 0.5 segons...")
            time.sleep(0.5) 
            
            print(f"Intentant iniciar {REDSHIFT_GTK_PROCESS_NAME}...")
            subprocess.Popen([REDSHIFT_GTK_PROCESS_NAME]) 
            time.sleep(1) 
            if self.is_process_running(REDSHIFT_GTK_PROCESS_NAME):
                self.status_label_var.set("Redshift reiniciat amb la nova configuració.")
                print(f"{REDSHIFT_GTK_PROCESS_NAME} reiniciat correctament.")
            else:
                self.status_label_var.set(f"Error en reiniciar {REDSHIFT_GTK_PROCESS_NAME}.")
                print(f"Sembla que {REDSHIFT_GTK_PROCESS_NAME} no s'ha reiniciat correctament després de l'aplicació.")
        except Exception as e_restart:
            self.status_label_var.set(f"Excepció en reiniciar: {e_restart}")
            messagebox.showerror("Error reiniciant Redshift", f"No s'ha pogut reiniciar Redshift automàticament:\n{e_restart}\nPotser has de fer-ho manualment.")

if __name__ == "__main__":
    root = tk.Tk()
    app = RedshiftControlApp(root)
    root.mainloop()