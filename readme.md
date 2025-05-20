# control_redshift_and_temes_UbuntuMate

Una eina amb interfície gràfica (GUI) desenvolupada en Python amb Tkinter per a l'escriptori Ubuntu MATE. Permet gestionar de forma ràpida i senzilla la configuració de Redshift (per a la temperatura i brillantor de la pantalla) i els temes de l'escriptori, facilitant la transició entre un mode "Dia" i un mode "Nit".

**Autors:** Pëp i Gemini (Model d'IA de Google)
**Llicència:** MIT License

## Característiques Principals

*   **Canvi Ràpid de Mode amb Botons Intuïtius:**
    *   ☀️ **Botó Sol (Dia):**
        *   Desactiva (tanca) Redshift completament. _(Alternativament, es podria configurar per posar Redshift en un mode neutre si es prefereix que continuï actiu)._
        *   Aplica el teu tema GTK i Marco (vora de finestres) personalitzat. Per defecte, l'script busca una carpeta anomenada `AmbiantMATE-Personal` dins de `~/.themes/`.
        *   Si el tema personalitzat no es troba, aplica el tema clar estàndard d'Ubuntu MATE (`Ambiant-MATE`).
    *   🌙 **Botó Lluna (Nit):**
        *   Activa Redshift. Utilitza la configuració de temperatura i brillantor que estigui desada actualment al fitxer `~/.config/redshift.conf`.
        *   Si Redshift no s'estava executant, l'engega (carregant la configuració existent o creant-ne una per defecte si és el primer cop).
        *   Aplica el tema fosc estàndard d'Ubuntu MATE (`Ambiant-MATE-Dark`) tant per a GTK com per a Marco.
*   **Ajustaments Detallats de Redshift:**
    *   Controls lliscants visuals per ajustar finament la **temperatura de color** (en Kelvin) i la **brillantor** (de 0.1 a 1.0) de Redshift.
    *   Botó "Aplicar Ajustaments Redshift" per **desar els valors dels controls lliscants** al fitxer `~/.config/redshift.conf`. Aquesta acció reinicia Redshift per aplicar immediatament els nous ajustaments. Aquesta és la configuració que el botó "Lluna" utilitzarà posteriorment.
    *   Botó "Sortir de Redshift" per tancar completament tots els processos de Redshift.
*   **Selecció Manual de Temes d'Escriptori:**
    *   Un menú desplegable permet seleccionar i aplicar manualment altres temes MATE. L'script detecta automàticament `Ambiant-MATE-Dark`, `Ambiant-MATE`, i el teu tema personalitzat (`AmbiantMATE-Personal` per defecte) si existeix a `~/.themes/`.
*   **Gestió Integrada de Redshift:**
    *   L'eina s'assegura que `redshift-gtk` (la interfície gràfica de Redshift amb la icona a la safata del sistema) s'inicia si no s'està executant quan l'aplicació arrenca o quan s'activa el mode Lluna.
    *   Si el fitxer de configuració `~/.config/redshift.conf` no existeix en el primer ús, se'n crea un automàticament amb valors per defecte raonables (4500K, 0.8 de brillantor) per evitar errors de Redshift.

## Compatibilitat

*   **Sistema Operatiu:** Dissenyat i provat principalment a **Ubuntu MATE**. Pot funcionar en altres distribucions Linux amb l'escriptori MATE, però no s'ha provat exhaustivament.
*   **Escriptori:** MATE Desktop Environment.
*   **Versions de Redshift:** Provat amb Redshift 1.12 (versió comuna a Ubuntu 20.04 LTS i similars).

## Dependències i Instal·lació

Abans d'executar l'script, assegura't que tens les següents dependències instal·lades al teu sistema Ubuntu MATE:

1.  **Python 3:**
    Ubuntu MATE normalment ja ve amb Python 3. Pots verificar-ho amb `python3 --version`.

2.  **Tkinter (llibreria GUI per a Python):**
    Si no la tens (poc probable), instal·la-la amb:
    ```bash
    sudo apt update
    sudo apt install python3-tk
    ```

3.  **Redshift (eina principal i interfície GTK):**
    ```bash
    sudo apt install redshift redshift-gtk
    ```

4.  **procps (conté `pgrep`):**
    Aquesta eina s'utilitza per comprovar si Redshift ja s'està executant. Normalment està instal·lada per defecte.
    ```bash
    sudo apt install procps 
    ```
    _(És probable que ja la tinguis)._

5.  **`gsettings` (eina de configuració de l'escriptori):**
    Instal·lada per defecte amb l'escriptori MATE.

## Com Fer Servir

1.  **Descarregar l'Script:**
    *   Pots clonar aquest repositori de GitHub:
        ```bash
        git clone https://github.com/EL_TEU_USUARI_GITHUB/control_redshift_and_temes_UbuntuMate.git
        cd control_redshift_and_temes_UbuntuMate/
        ```
    *   O descarregar el fitxer `.py` directament. Anomenem-lo, per exemple, `control_pantalla_mate.py`.

2.  **Configurar el Teu Tema Personalitzat (Opcional, per al Mode "Sol"):**
    L'script està configurat per defecte per buscar un tema anomenat `AmbiantMATE-Personal` dins del teu directori `~/.themes/`.
    *   **Si el teu tema personalitzat té un altre nom:**
        Obre l'script Python amb un editor de text i modifica la següent línia a la part superior:
        ```python
        THEME_SOL_PERSONALITZAT_NOM = "ElNomDeLaCarpetaDelTeuTema"
        ```
        Reemplaça `"ElNomDeLaCarpetaDelTeuTema"` pel nom exacte de la carpeta del teu tema que es troba a `~/.themes/`.
    *   **Si el tema de les vores de les finestres (Marco) del teu tema personalitzat té un nom diferent** al tema GTK, hauràs d'ajustar la lògica dins del mètode `activate_mode_sol()` per especificar el nom correcte per a Marco. Per defecte, l'script assumeix que el nom és el mateix.

3.  **Fer Executable l'Script (Recomanat):**
    Des del terminal, navega al directori on tens l'script i executa:
    ```bash
    chmod +x control_pantalla_mate.py 
    ```
    _(Reemplaça `control_pantalla_mate.py` pel nom real del teu fitxer)._

4.  **Executar l'Script:**
    *   Si l'has fet executable:
        ```bash
        ./control_pantalla_mate.py
        ```
    *   Si no:
        ```bash
        python3 control_pantalla_mate.py
        ```
    S'obrirà la finestra de l'aplicació. Utilitza els botons "Sol" i "Lluna" per a canvis ràpids, o explora els "Ajustaments Detallats" per a un control més fi.

## Com Contribuir

Les contribucions, suggerències i informes d'errors són benvinguts!
1.  Fes un "Fork" del projecte.
2.  Crea la teva branca de funcionalitat (`git checkout -b feature/NovaFuncionalitatIncreible`).
3.  Fes "Commit" dels teus canvis (`git commit -m 'Afegeix NovaFuncionalitatIncreible'`).
4.  Fes "Push" a la branca (`git push origin feature/NovaFuncionalitatIncreible`).
5.  Obre un "Pull Request".

També pots obrir un "issue" per discutir canvis o informar de problemes.

## Llicència

Aquest projecte està sota la Llicència MIT. Consulta el fitxer `LICENSE` (que hauràs de crear si vols) per a més detalls.

```text
MIT License

Copyright (c) [Any Actual] Pëp i Gemini (Model d'IA de Google)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
