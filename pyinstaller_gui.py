"""
PyInstaller GUI Builder
Ein benutzerfreundliches GUI-Tool zum Erstellen von EXE-Dateien mit PyInstaller
"""

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import subprocess
import sys
import os
from pathlib import Path
import threading
import re


class PyInstallerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PyInstaller GUI Builder")
        self.root.geometry("900x750")
        self.root.resizable(True, True)
        
        # Variablen
        self.python_file = tk.StringVar()
        self.output_name = tk.StringVar()
        self.icon_file = tk.StringVar()
        self.additional_files = []
        
        # Checkbox Variablen
        self.onefile_var = tk.BooleanVar(value=True)
        self.clean_var = tk.BooleanVar(value=True)
        self.upx_var = tk.BooleanVar(value=False)
        self.debug_var = tk.BooleanVar(value=False)
        self.noconfirm_var = tk.BooleanVar(value=True)
        
        # ComboBox Variable für Konsole
        self.console_mode = tk.StringVar(value="Mit Konsole")
        
        # Building Flag
        self.is_building = False
        
        self.create_widgets()
        self.check_pyinstaller()
    
    def create_widgets(self):
        """Erstellt alle GUI-Elemente"""
        
        # Header
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=70)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="🔧 PyInstaller GUI Builder",
            font=("Segoe UI", 20, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(pady=15)
        
        # Hauptcontainer mit Scrollbar
        main_container = ttk.Frame(self.root)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # === DATEIAUSWAHL BEREICH ===
        file_frame = ttk.LabelFrame(main_container, text="📁 Dateiauswahl", padding=15)
        file_frame.pack(fill="x", pady=(0, 10))
        
        # Python-Datei
        ttk.Label(file_frame, text="Python-Datei (.py):").grid(row=0, column=0, sticky="w", pady=5)
        py_entry_frame = ttk.Frame(file_frame)
        py_entry_frame.grid(row=0, column=1, sticky="ew", pady=5, padx=(10, 0))
        
        ttk.Entry(py_entry_frame, textvariable=self.python_file).pack(side="left", fill="x", expand=True)
        ttk.Button(py_entry_frame, text="Durchsuchen...", command=self.browse_python_file).pack(side="left", padx=(5, 0))
        
        # Ausgabename
        ttk.Label(file_frame, text="EXE-Name (optional):").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(file_frame, textvariable=self.output_name).grid(row=1, column=1, sticky="ew", pady=5, padx=(10, 0))
        
        # Icon-Datei
        ttk.Label(file_frame, text="Icon (.ico, optional):").grid(row=2, column=0, sticky="w", pady=5)
        icon_entry_frame = ttk.Frame(file_frame)
        icon_entry_frame.grid(row=2, column=1, sticky="ew", pady=5, padx=(10, 0))
        
        ttk.Entry(icon_entry_frame, textvariable=self.icon_file).pack(side="left", fill="x", expand=True)
        ttk.Button(icon_entry_frame, text="Durchsuchen...", command=self.browse_icon_file).pack(side="left", padx=(5, 0))
        
        file_frame.columnconfigure(1, weight=1)
        
        # === OPTIONEN BEREICH ===
        options_frame = ttk.LabelFrame(main_container, text="⚙️ PyInstaller Optionen", padding=15)
        options_frame.pack(fill="x", pady=(0, 10))
        
        # Linke Spalte - Checkboxen
        left_options = ttk.Frame(options_frame)
        left_options.pack(side="left", fill="both", expand=True)
        
        ttk.Checkbutton(
            left_options,
            text="--onefile (Einzelne EXE-Datei)",
            variable=self.onefile_var
        ).pack(anchor="w", pady=3)
        
        ttk.Checkbutton(
            left_options,
            text="--clean (Temporäre Dateien löschen vor Build)",
            variable=self.clean_var
        ).pack(anchor="w", pady=3)
        
        ttk.Checkbutton(
            left_options,
            text="--upx-dir (UPX Kompression verwenden)",
            variable=self.upx_var
        ).pack(anchor="w", pady=3)
        
        # Rechte Spalte - Weitere Optionen
        right_options = ttk.Frame(options_frame)
        right_options.pack(side="left", fill="both", expand=True)
        
        ttk.Checkbutton(
            right_options,
            text="--debug (Debug-Modus aktivieren)",
            variable=self.debug_var
        ).pack(anchor="w", pady=3)
        
        ttk.Checkbutton(
            right_options,
            text="--noconfirm (Überschreiben ohne Nachfrage)",
            variable=self.noconfirm_var
        ).pack(anchor="w", pady=3)
        
        # === KONSOLEN-MODUS ===
        console_frame = ttk.LabelFrame(main_container, text="🖥️ Konsolen-Modus", padding=15)
        console_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(console_frame, text="Wähle den Ausführungs-Modus:").pack(anchor="w", pady=(0, 5))
        
        console_combo = ttk.Combobox(
            console_frame,
            textvariable=self.console_mode,
            values=["Mit Konsole", "Ohne Konsole (GUI)", "Ohne Konsole (--noconsole)"],
            state="readonly",
            width=35
        )
        console_combo.pack(anchor="w", pady=5)
        console_combo.current(0)
        
        # Info-Label
        self.console_info = ttk.Label(
            console_frame,
            text="ℹ️ Mit Konsole: Zeigt ein schwarzes Fenster (gut für Debugging)",
            foreground="blue",
            font=("Segoe UI", 9)
        )
        self.console_info.pack(anchor="w", pady=(5, 0))
        
        # Bind für Modus-Änderung
        console_combo.bind("<<ComboboxSelected>>", self.update_console_info)
        
        # === ZUSÄTZLICHE DATEIEN ===
        files_frame = ttk.LabelFrame(main_container, text="📎 Zusätzliche Dateien/Ordner", padding=15)
        files_frame.pack(fill="x", pady=(0, 10))
        
        files_button_frame = ttk.Frame(files_frame)
        files_button_frame.pack(fill="x", pady=(0, 5))
        
        ttk.Button(files_button_frame, text="+ Datei hinzufügen", command=self.add_data_file).pack(side="left", padx=5)
        ttk.Button(files_button_frame, text="+ Ordner hinzufügen", command=self.add_data_folder).pack(side="left", padx=5)
        ttk.Button(files_button_frame, text="Liste leeren", command=self.clear_data_files).pack(side="left", padx=5)
        
        # Listbox für zusätzliche Dateien
        self.files_listbox = tk.Listbox(files_frame, height=4)
        self.files_listbox.pack(fill="x", pady=5)
        
        # === COMMAND PREVIEW ===
        preview_frame = ttk.LabelFrame(main_container, text="📋 Befehl-Vorschau", padding=15)
        preview_frame.pack(fill="x", pady=(0, 10))
        
        self.command_text = tk.Text(preview_frame, height=4, wrap="word", font=("Courier", 9))
        self.command_text.pack(fill="x")
        
        ttk.Button(preview_frame, text="🔄 Befehl aktualisieren", command=self.update_command_preview).pack(pady=(5, 0))
        
        # === BUILD BUTTON ===
        build_frame = ttk.Frame(main_container)
        build_frame.pack(fill="x", pady=(0, 10))
        
        self.build_button = tk.Button(
            build_frame,
            text="🚀 EXE ERSTELLEN",
            font=("Segoe UI", 12, "bold"),
            bg="#27ae60",
            fg="white",
            activebackground="#229954",
            activeforeground="white",
            relief="raised",
            bd=3,
            height=2,
            command=self.start_build
        )
        self.build_button.pack(fill="x")
        
        # === LOG OUTPUT ===
        log_frame = ttk.LabelFrame(main_container, text="📝 Build-Log", padding=10)
        log_frame.pack(fill="both", expand=True)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=12,
            wrap="word",
            font=("Courier", 9),
            state="disabled"
        )
        self.log_text.pack(fill="both", expand=True)
        
        # Fortschrittsbalken
        self.progress = ttk.Progressbar(log_frame, mode="indeterminate")
        self.progress.pack(fill="x", pady=(5, 0))
    
    def update_console_info(self, event=None):
        """Aktualisiert die Info-Nachricht basierend auf dem gewählten Konsolen-Modus"""
        mode = self.console_mode.get()
        
        info_texts = {
            "Mit Konsole": "ℹ️ Mit Konsole: Zeigt ein schwarzes Fenster (gut für Debugging)",
            "Ohne Konsole (GUI)": "ℹ️ Ohne Konsole (--windowed): Für GUI-Programme, keine Konsole sichtbar",
            "Ohne Konsole (--noconsole)": "ℹ️ Ohne Konsole (--noconsole): Alternative Variante ohne Konsole"
        }
        
        self.console_info.config(text=info_texts.get(mode, ""))
    
    def check_pyinstaller(self):
        """Prüft ob PyInstaller installiert ist"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "show", "pyinstaller"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                self.log_message("⚠️ PyInstaller ist nicht installiert!", "warning")
                response = messagebox.askyesno(
                    "PyInstaller nicht gefunden",
                    "PyInstaller ist nicht installiert.\n\n"
                    "Möchtest du es jetzt installieren?"
                )
                if response:
                    self.install_pyinstaller()
            else:
                # Extrahiere Version
                version_match = re.search(r'Version: ([\d.]+)', result.stdout)
                version = version_match.group(1) if version_match else "unbekannt"
                self.log_message(f"✓ PyInstaller {version} ist installiert")
        except Exception as e:
            self.log_message(f"❌ Fehler beim Prüfen von PyInstaller: {e}", "error")
    
    def install_pyinstaller(self):
        """Installiert PyInstaller"""
        self.log_message("Installiere PyInstaller...")
        self.build_button.config(state="disabled")
        
        def install():
            try:
                process = subprocess.Popen(
                    [sys.executable, "-m", "pip", "install", "pyinstaller"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                
                for line in process.stdout:
                    self.root.after(0, self.log_message, line.strip())
                
                process.wait()
                
                if process.returncode == 0:
                    self.root.after(0, self.log_message, "✓ PyInstaller erfolgreich installiert!", "success")
                else:
                    self.root.after(0, self.log_message, "❌ Installation fehlgeschlagen!", "error")
                
            except Exception as e:
                self.root.after(0, self.log_message, f"❌ Fehler: {e}", "error")
            finally:
                self.root.after(0, lambda: self.build_button.config(state="normal"))
        
        thread = threading.Thread(target=install, daemon=True)
        thread.start()
    
    def browse_python_file(self):
        """Öffnet Dialog zur Auswahl der Python-Datei"""
        filename = filedialog.askopenfilename(
            title="Python-Datei auswählen",
            filetypes=[("Python Dateien", "*.py"), ("Alle Dateien", "*.*")]
        )
        if filename:
            self.python_file.set(filename)
            # Setze Standard-Namen wenn noch nicht gesetzt
            if not self.output_name.get():
                base_name = Path(filename).stem
                self.output_name.set(base_name)
            self.update_command_preview()
    
    def browse_icon_file(self):
        """Öffnet Dialog zur Auswahl der Icon-Datei"""
        filename = filedialog.askopenfilename(
            title="Icon-Datei auswählen",
            filetypes=[("Icon Dateien", "*.ico"), ("Alle Dateien", "*.*")]
        )
        if filename:
            self.icon_file.set(filename)
            self.update_command_preview()
    
    def add_data_file(self):
        """Fügt eine zusätzliche Datei hinzu"""
        filename = filedialog.askopenfilename(title="Datei hinzufügen")
        if filename:
            self.additional_files.append(("file", filename))
            self.files_listbox.insert("end", f"📄 {filename}")
            self.update_command_preview()
    
    def add_data_folder(self):
        """Fügt einen zusätzlichen Ordner hinzu"""
        foldername = filedialog.askdirectory(title="Ordner hinzufügen")
        if foldername:
            self.additional_files.append(("folder", foldername))
            self.files_listbox.insert("end", f"📁 {foldername}")
            self.update_command_preview()
    
    def clear_data_files(self):
        """Leert die Liste der zusätzlichen Dateien"""
        self.additional_files.clear()
        self.files_listbox.delete(0, "end")
        self.update_command_preview()
    
    def build_command(self):
        """Erstellt den PyInstaller-Befehl"""
        if not self.python_file.get():
            return None
        
        cmd = [sys.executable, "-m", "PyInstaller"]
        
        # Basis-Optionen
        if self.onefile_var.get():
            cmd.append("--onefile")
        
        if self.clean_var.get():
            cmd.append("--clean")
        
        if self.noconfirm_var.get():
            cmd.append("--noconfirm")
        
        if self.debug_var.get():
            cmd.append("--debug=all")
        
        # Konsolen-Modus
        mode = self.console_mode.get()
        if "Ohne Konsole (GUI)" in mode:
            cmd.append("--windowed")
        elif "Ohne Konsole (--noconsole)" in mode:
            cmd.append("--noconsole")
        
        # Ausgabename
        if self.output_name.get():
            cmd.extend(["--name", self.output_name.get()])
        
        # Icon
        if self.icon_file.get() and os.path.exists(self.icon_file.get()):
            cmd.extend(["--icon", self.icon_file.get()])
        
        # UPX
        if self.upx_var.get():
            cmd.append("--upx-dir=upx")
        
        # Zusätzliche Dateien
        for file_type, path in self.additional_files:
            if os.path.exists(path):
                if file_type == "file":
                    # Format: source;destination
                    cmd.extend(["--add-data", f"{path};."])
                else:  # folder
                    folder_name = Path(path).name
                    cmd.extend(["--add-data", f"{path};{folder_name}"])
        
        # Python-Datei (muss am Ende sein)
        cmd.append(self.python_file.get())
        
        return cmd
    
    def update_command_preview(self):
        """Aktualisiert die Befehlsvorschau"""
        cmd = self.build_command()
        
        self.command_text.config(state="normal")
        self.command_text.delete(1.0, "end")
        
        if cmd:
            # Formatiere den Befehl schön
            cmd_str = " ".join(f'"{arg}"' if " " in arg else arg for arg in cmd)
            self.command_text.insert(1.0, cmd_str)
        else:
            self.command_text.insert(1.0, "Bitte wähle zuerst eine Python-Datei aus...")
        
        self.command_text.config(state="disabled")
    
    def log_message(self, message, level="info"):
        """Fügt eine Nachricht zum Log hinzu"""
        self.log_text.config(state="normal")
        
        # Farbcodierung basierend auf Level
        if "✓" in message or "success" in level.lower():
            self.log_text.insert("end", message + "\n", "success")
        elif "❌" in message or "error" in level.lower():
            self.log_text.insert("end", message + "\n", "error")
        elif "⚠️" in message or "warning" in level.lower():
            self.log_text.insert("end", message + "\n", "warning")
        else:
            self.log_text.insert("end", message + "\n")
        
        self.log_text.see("end")
        self.log_text.config(state="disabled")
        
        # Konfiguriere Tags für Farben
        self.log_text.tag_config("success", foreground="green")
        self.log_text.tag_config("error", foreground="red")
        self.log_text.tag_config("warning", foreground="orange")
    
    def start_build(self):
        """Startet den Build-Prozess"""
        if not self.python_file.get():
            messagebox.showerror("Fehler", "Bitte wähle zuerst eine Python-Datei aus!")
            return
        
        if not os.path.exists(self.python_file.get()):
            messagebox.showerror("Fehler", "Die ausgewählte Python-Datei existiert nicht!")
            return
        
        # UI anpassen
        self.is_building = True
        self.build_button.config(state="disabled", bg="#95a5a6")
        self.progress.start()
        
        # Log leeren
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, "end")
        self.log_text.config(state="disabled")
        
        self.log_message("=" * 70)
        self.log_message("🚀 Starte PyInstaller Build-Prozess...")
        self.log_message("=" * 70)
        
        # Starte Build in separatem Thread
        thread = threading.Thread(target=self.run_build, daemon=True)
        thread.start()
    
    def run_build(self):
        """Führt den Build-Prozess aus"""
        try:
            cmd = self.build_command()
            
            self.root.after(0, self.log_message, f"\n📋 Befehl:\n{' '.join(cmd)}\n")
            self.root.after(0, self.log_message, "⏳ Build läuft, bitte warten...\n")
            
            # Führe PyInstaller aus
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # Lese Output Zeile für Zeile
            for line in process.stdout:
                line = line.strip()
                if line:
                    self.root.after(0, self.log_message, line)
            
            process.wait()
            
            # Prüfe Ergebnis
            if process.returncode == 0:
                self.root.after(0, self.log_message, "\n" + "=" * 70)
                self.root.after(0, self.log_message, "✓ Build erfolgreich abgeschlossen!", "success")
                self.root.after(0, self.log_message, "=" * 70)
                
                # Finde die EXE
                output_name = self.output_name.get() or Path(self.python_file.get()).stem
                exe_path = Path("dist") / f"{output_name}.exe"
                
                if exe_path.exists():
                    self.root.after(0, self.log_message, f"\n📦 EXE-Datei erstellt:")
                    self.root.after(0, self.log_message, f"   {exe_path.absolute()}")
                    self.root.after(0, self.log_message, f"\n💾 Größe: {exe_path.stat().st_size / (1024*1024):.2f} MB")
                    
                    self.root.after(0, lambda: messagebox.showinfo(
                        "Erfolg!",
                        f"EXE wurde erfolgreich erstellt!\n\n"
                        f"Pfad: {exe_path.absolute()}\n"
                        f"Größe: {exe_path.stat().st_size / (1024*1024):.2f} MB"
                    ))
                else:
                    self.root.after(0, self.log_message, "\n⚠️ EXE-Datei nicht im dist/-Ordner gefunden", "warning")
            
            else:
                self.root.after(0, self.log_message, "\n" + "=" * 70)
                self.root.after(0, self.log_message, "❌ Build fehlgeschlagen!", "error")
                self.root.after(0, self.log_message, "=" * 70)
                self.root.after(0, self.handle_build_errors, process.returncode)
        
        except Exception as e:
            self.root.after(0, self.log_message, f"\n❌ Fehler beim Build: {str(e)}", "error")
            self.root.after(0, lambda: messagebox.showerror("Fehler", f"Build fehlgeschlagen:\n{str(e)}"))
        
        finally:
            self.root.after(0, self.finish_build)
    
    def handle_build_errors(self, returncode):
        """Behandelt häufige Build-Fehler und gibt Lösungsvorschläge"""
        self.log_message("\n🔍 Mögliche Ursachen und Lösungen:\n")
        
        common_errors = [
            ("ModuleNotFoundError", "❌ Fehlende Module: Installiere alle benötigten Pakete mit 'pip install paketname'"),
            ("Permission denied", "❌ Zugriffsfehler: Schließe andere Programme und führe als Administrator aus"),
            ("spec file", "❌ Spec-Datei Problem: Lösche alte .spec-Dateien und versuche es erneut"),
            ("UnicodeDecodeError", "❌ Encoding Problem: Stelle sicher, dass alle Dateien UTF-8 kodiert sind"),
            ("ImportError", "❌ Import-Fehler: Verwende --hidden-import für problematische Module"),
            ("No module named", "❌ Modul nicht gefunden: Stelle sicher, dass alle Dependencies installiert sind"),
        ]
        
        self.log_message("Häufige Probleme:")
        for error_type, solution in common_errors:
            self.log_message(f"  • {solution}")
        
        self.log_message("\n💡 Tipps:")
        self.log_message("  • Aktiviere 'Debug-Modus' für detailliertere Fehlermeldungen")
        self.log_message("  • Prüfe ob alle benötigten Pakete installiert sind")
        self.log_message("  • Teste erst mit einem einfachen Python-Skript")
        self.log_message("  • Deaktiviere Antivirus temporär (kann Build blockieren)")
    
    def finish_build(self):
        """Beendet den Build-Prozess und setzt UI zurück"""
        self.is_building = False
        self.build_button.config(state="normal", bg="#27ae60")
        self.progress.stop()


def main():
    """Hauptfunktion"""
    root = tk.Tk()
    
    # Stil konfigurieren
    style = ttk.Style()
    style.theme_use('clam')
    
    app = PyInstallerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
