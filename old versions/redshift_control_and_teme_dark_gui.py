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
MATE_DARK_THEME_NAME = "Ambiant-MATE-Dark" # Nom del tema fosc per a MATE

class RedshiftControlApp:
    def __init__(self, master):
        self.master = master
        master.title("Control de Redshift i Tema")
        master.geometry("380x330") # Augmentem una mica l'alçada per al nou botó i status

        self.current_temp_val = 4500 # Valors per defecte
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
        self.apply_button.pack(pady=10)

        # --- Control de Tema MATE ---
        theme_frame = ttk.LabelFrame(master, text="Control de Tema MATE", padding=(10, 5))
        theme_frame.pack(padx=10, pady=5, fill="x")

        self.theme_button = ttk.Button(theme_frame, text=f"Aplicar Tema {MATE_DARK_THEME_NAME}", command=self.apply_mate_dark_theme)
        self.theme_button.pack(pady=10)
        
        # --- Etiqueta d'Estat Global ---
        self.status_label_var = tk.StringVar(value="Llest.")
        ttk.Label(master, textvariable=self.status_label_var).pack(pady=(5,5), side="bottom")

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
        except FileNotFoundError: # Si pgrep no està instal·lat
            print("Avís: La comanda 'pgrep' no s'ha trobat. No es pot comprovar si el procés s'executa.")
            return False # Assumeix que no s'executa si no podem comprovar

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
            subprocess.run(["killall", REDSHIFT_PROCESS_NAME], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(["killall", REDSHIFT_GTK_PROCESS_NAME], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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

    def apply_mate_dark_theme(self):
        self.status_label_var.set(f"Aplicant tema {MATE_DARK_THEME_NAME}...")
        print(f"Intentant aplicar el tema GTK de MATE: {MATE_DARK_THEME_NAME}")
        try:
            # Comanda per canviar el tema GTK a MATE
            # org.mate.interface per al tema de les aplicacions (controls)
            # org.mate.Marco.general per al tema del gestor de finestres (vora de les finestres)
            
            # Canviar tema GTK (controls, etc.)
            subprocess.run(["gsettings", "set", "org.mate.interface", "gtk-theme", MATE_DARK_THEME_NAME], check=True)
            
            # Canviar tema de la vora de les finestres (opcional, però sovint desitjat per a consistència)
            # Els temes de Marco sovint tenen el mateix nom o un de similar.
            # Si 'Ambiant-MATE-Dark' també és un tema de Marco, això funcionarà.
            # Si no, caldria trobar el nom correcte del tema de Marco corresponent.
            try:
                subprocess.run(["gsettings", "set", "org.mate.Marco.general", "theme", MATE_DARK_THEME_NAME], check=True)
                print(f"Tema de Marco també canviat a {MATE_DARK_THEME_NAME}.")
            except subprocess.CalledProcessError as e_marco:
                print(f"Avís: No s'ha pogut canviar el tema de Marco a {MATE_DARK_THEME_NAME}. Error: {e_marco}")
                print("Potser el tema de Marco té un nom diferent o no està disponible.")


            self.status_label_var.set(f"Tema {MATE_DARK_THEME_NAME} aplicat.")
            messagebox.showinfo("Tema Canviat", f"S'ha intentat aplicar el tema {MATE_DARK_THEME_NAME} a GTK i Marco.")

        except FileNotFoundError:
            self.status_label_var.set("Error: 'gsettings' no trobat.")
            messagebox.showerror("Error", "La comanda 'gsettings' no s'ha trobat. Assegura't que estàs en un entorn MATE i que les eines d'escriptori estan instal·lades.")
        except subprocess.CalledProcessError as e:
            self.status_label_var.set(f"Error en aplicar el tema: {e}")
            messagebox.showerror("Error", f"No s'ha pogut aplicar el tema {MATE_DARK_THEME_NAME}.\nAssegura't que el tema està instal·lat.\nError: {e}")
        except Exception as e:
            self.status_label_var.set(f"Error inesperat en aplicar tema: {e}")
            messagebox.showerror("Error", f"Un error inesperat ha ocorregut en aplicar el tema:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = RedshiftControlApp(root)
    root.mainloop()