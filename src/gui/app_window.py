# /src/gui/app_window.py (Version Finale avec Drag and Drop)

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import threading
import time
from tkinterdnd2 import DND_FILES, TkinterDnD
from src.config.config import SOURCES_CONFIG
from src.core.pdf_processor import extract_text_from_pdf
from src.core.ai_extractor import AIExtractor
from src.core.json_writer import save_json

class AppWindow(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("Extracteur JORF & BOCC v3.1 (avec Drag & Drop)")
        self.geometry("800x650")

        self.ai_extractor = AIExtractor()
        self.file_list = []
        self.output_dir_paie = ""
        self.output_dir_ccn = ""

        self._create_widgets()

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)


        files_frame = ttk.LabelFrame(main_frame, text="1. Faites glisser vos PDF ici ou utilisez les boutons", padding="10")
        files_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.file_listbox = tk.Listbox(files_frame, selectmode=tk.SINGLE, height=10)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.file_listbox.drop_target_register(DND_FILES)
        self.file_listbox.dnd_bind('<<Drop>>', self._on_drop)
        # ------------------------------------

        file_buttons_frame = ttk.Frame(files_frame)
        file_buttons_frame.pack(side=tk.RIGHT, padx=5, fill=tk.Y)
        add_button = ttk.Button(file_buttons_frame, text="Ajouter Fichier(s)", command=self._add_files)
        add_button.pack(fill=tk.X, pady=2)
        remove_button = ttk.Button(file_buttons_frame, text="Retirer Fichier", command=self._remove_file)
        remove_button.pack(fill=tk.X, pady=2)

        options_frame = ttk.LabelFrame(main_frame, text="2. Options pour le fichier sélectionné", padding="10")
        options_frame.pack(fill=tk.X, pady=5)

        self.source_var = tk.StringVar()
        self.source_var.set(SOURCES_CONFIG['JORF']['label'])

        self.extraction_var_paie = tk.BooleanVar()
        self.extraction_var_ccn = tk.BooleanVar()

        ttk.Label(options_frame, text="Source :").grid(row=0, column=0, sticky=tk.W, padx=5)
        source_labels = [config['label'] for config in SOURCES_CONFIG.values() if config.get('label')]
        self.source_menu = ttk.OptionMenu(options_frame, self.source_var, self.source_var.get(), *source_labels, command=self._on_source_change)
        self.source_menu.grid(row=0, column=1, sticky=tk.W)

        self.cb_paie = ttk.Checkbutton(options_frame, text="Actualités Paie", variable=self.extraction_var_paie, command=self._on_option_change)
        self.cb_paie.grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=5)
        self.cb_ccn = ttk.Checkbutton(options_frame, text="Actualités CCN", variable=self.extraction_var_ccn, command=self._on_option_change)
        self.cb_ccn.grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5)

        self.file_listbox.bind('<<ListboxSelect>>', self._on_file_select)

        output_frame = ttk.LabelFrame(main_frame, text="3. Dossiers de sauvegarde", padding="10")
        output_frame.pack(fill=tk.X, pady=5)
        output_frame.columnconfigure(1, weight=1)
        ttk.Button(output_frame, text="Dossier pour JSON Paie...", command=self._select_output_paie).grid(row=0, column=0, padx=5, pady=2)
        self.output_label_paie = ttk.Label(output_frame, text="Non défini", anchor="w", wraplength=500)
        self.output_label_paie.grid(row=0, column=1, sticky="ew")
        ttk.Button(output_frame, text="Dossier pour JSON CCN...", command=self._select_output_ccn).grid(row=1, column=0, padx=5, pady=2)
        self.output_label_ccn = ttk.Label(output_frame, text="Non défini", anchor="w", wraplength=500)
        self.output_label_ccn.grid(row=1, column=1, sticky="ew")

        self.run_button = ttk.Button(main_frame, text="Lancer l'extraction", command=self._start_extraction_thread)
        self.run_button.pack(pady=10, fill=tk.X, ipady=5)
        self.progress_bar = ttk.Progressbar(main_frame, orient='horizontal', mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=5)
        self.status_label = ttk.Label(main_frame, text="Prêt. Faites glisser des fichiers PDF ou cliquez sur 'Ajouter'.")
        self.status_label.pack(anchor=tk.W, fill=tk.X)

        self._update_ui_for_selection()

    def _on_drop(self, event):

        try:

            files_str = self.tk.splitlist(event.data)
            pdf_files = [f for f in files_str if f.lower().endswith('.pdf')]

            if pdf_files:
                self._add_files_from_paths(pdf_files)
            else:
                messagebox.showwarning("Fichiers non valides", "Veuillez ne déposer que des fichiers PDF.")
        except Exception as e:
            messagebox.showerror("Erreur de Dépôt", f"Une erreur est survenue lors du glisser-déposer : {e}")

    def _add_files(self):
        """Ouvre une boîte de dialogue pour ajouter des fichiers."""
        files = filedialog.askopenfilenames(
            title="Sélectionner un ou plusieurs PDF",
            filetypes=[("Fichiers PDF", "*.pdf")]
        )
        if files:
            self._add_files_from_paths(list(files))

    def _add_files_from_paths(self, file_paths):
        """Fonction centralisée pour ajouter des fichiers à partir d'une liste de chemins."""
        source_label = self.source_var.get()
        source_key = next((key for key, conf in SOURCES_CONFIG.items() if conf['label'] == source_label), 'JORF')

        added_count = 0
        for f_path in file_paths:
            if not any(item['path'] == f_path for item in self.file_list):
                allowed_types = SOURCES_CONFIG[source_key]['types']
                self.file_list.append({
                    'path': f_path,
                    'source': source_key,
                    'paie': 'paie' in allowed_types,
                    'ccn': 'ccn' in allowed_types
                })
                added_count += 1

        if added_count > 0:
            self._update_listbox()

            self.file_listbox.selection_clear(0, tk.END)
            self.file_listbox.selection_set(len(self.file_list) - 1)
            self._on_file_select(None)

    def _remove_file(self):
        selected_indices = self.file_listbox.curselection()
        if not selected_indices: return
        for i in sorted(selected_indices, reverse=True):
            del self.file_list[i]
        self._update_listbox()
        self._update_ui_for_selection()

    def _update_listbox(self):
        current_selection = self.file_listbox.curselection()
        self.file_listbox.delete(0, tk.END)
        for item in self.file_list:
            filename = os.path.basename(item['path'])
            options = []
            if item.get('paie'): options.append("Paie")
            if item.get('ccn'): options.append("CCN")
            display_text = f"{filename} ({item['source']}) -> [{', '.join(options)}]"
            self.file_listbox.insert(tk.END, display_text)
        if current_selection and current_selection[0] < self.file_listbox.size():
            self.file_listbox.selection_set(current_selection[0])
        elif self.file_listbox.size() > 0:
            self.file_listbox.selection_set(0)
            self._on_file_select(None)

    def _on_file_select(self, event):
        self._update_ui_for_selection()

    def _update_ui_for_selection(self):
        selected_indices = self.file_listbox.curselection()
        if not selected_indices:
            self.source_menu.config(state=tk.DISABLED)
            self.cb_paie.config(state=tk.DISABLED)
            self.cb_ccn.config(state=tk.DISABLED)
            return

        self.source_menu.config(state=tk.NORMAL)
        index = selected_indices[0]
        file_data = self.file_list[index]

        source_key = file_data.get('source', 'JORF')
        source_label = SOURCES_CONFIG[source_key]['label']
        self.source_var.set(source_label)

        self._update_checkboxes_state(source_key)

        self.extraction_var_paie.set(file_data.get('paie', False))
        self.extraction_var_ccn.set(file_data.get('ccn', False))


    def _on_source_change(self, *args):
        selected_indices = self.file_listbox.curselection()
        if not selected_indices: return
        index = selected_indices[0]

        new_source_label = self.source_var.get()
        new_source_key = next((key for key, conf in SOURCES_CONFIG.items() if conf['label'] == new_source_label), None)

        if new_source_key and self.file_list[index]['source'] != new_source_key:
            self.file_list[index]['source'] = new_source_key
            allowed_types = SOURCES_CONFIG[new_source_key]['types']

            self.file_list[index]['paie'] = 'paie' in allowed_types
            self.file_list[index]['ccn'] = 'ccn' in allowed_types

            self._update_listbox()
            self.file_listbox.selection_set(index)
            self._update_ui_for_selection()

    def _update_checkboxes_state(self, source_key):
        allowed_types = SOURCES_CONFIG[source_key]['types']
        self.cb_paie.config(state=tk.NORMAL if 'paie' in allowed_types else tk.DISABLED)
        self.cb_ccn.config(state=tk.NORMAL if 'ccn' in allowed_types else tk.DISABLED)

    def _on_option_change(self):
        selected_indices = self.file_listbox.curselection()
        if not selected_indices: return
        index = selected_indices[0]

        self.file_list[index]['paie'] = self.extraction_var_paie.get()
        self.file_list[index]['ccn'] = self.extraction_var_ccn.get()

        self._update_listbox()
        self.file_listbox.selection_set(index)

    def _select_output_paie(self):
        self.output_dir_paie = filedialog.askdirectory(title="Dossier de sortie pour les extractions PAIE")
        if self.output_dir_paie:
            self.output_label_paie.config(text=self.output_dir_paie)

    def _select_output_ccn(self):
        self.output_dir_ccn = filedialog.askdirectory(title="Dossier de sortie pour les extractions CCN")
        if self.output_dir_ccn:
            self.output_label_ccn.config(text=self.output_dir_ccn)

    def _start_extraction_thread(self):
        tasks_to_run = [f for f in self.file_list if f.get('paie') or f.get('ccn')]
        if not tasks_to_run:
            messagebox.showerror("Erreur", "Aucun fichier avec un type d'extraction n'a été configuré.")
            return
        if any(f.get('paie') for f in tasks_to_run) and not self.output_dir_paie:
            messagebox.showerror("Erreur", "Veuillez sélectionner un dossier de sauvegarde pour les fichiers Paie.")
            return
        if any(f.get('ccn') for f in tasks_to_run) and not self.output_dir_ccn:
            messagebox.showerror("Erreur", "Veuillez sélectionner un dossier de sauvegarde pour les fichiers CCN.")
            return

        self.run_button.config(state=tk.DISABLED)
        total_api_calls = sum(1 for t in tasks_to_run if t.get('paie')) + sum(1 for t in tasks_to_run if t.get('ccn'))
        self.progress_bar['maximum'] = total_api_calls
        self.progress_bar['value'] = 0

        thread = threading.Thread(target=self._run_extraction, args=(tasks_to_run,))
        thread.start()

    def _run_extraction(self, tasks):

        for task in tasks:
            try:
                filename = os.path.basename(task['path'])
                self.status_label.config(text=f"Traitement de {filename}...")
                self.update_idletasks()
                pdf_text = extract_text_from_pdf(task['path'])
                if not pdf_text:
                    print(f"Avertissement : Aucun texte extrait de {filename}. Fichier ignoré.")
                    if task.get('paie'): self.progress_bar['value'] += 1
                    if task.get('ccn'): self.progress_bar['value'] += 1
                    continue

                base_filename = os.path.splitext(filename)[0]

                if task.get('paie'):
                    self.status_label.config(text=f"...Analyse Paie de {filename}...")
                    self.update_idletasks()
                    json_str = self.ai_extractor.extract(pdf_text, "paie")
                    output_path = os.path.join(self.output_dir_paie, f"{base_filename}_paie.json")
                    save_json(json_str, output_path)
                    self.progress_bar['value'] += 1
                    self.update_idletasks()


                if task.get('ccn'):
                    self.status_label.config(text=f"...Analyse CCN de {filename}...")
                    self.update_idletasks()
                    json_str = self.ai_extractor.extract(pdf_text, "ccn")
                    output_path = os.path.join(self.output_dir_ccn, f"{base_filename}_ccn.json")
                    save_json(json_str, output_path)
                    self.progress_bar['value'] += 1
                    self.update_idletasks()

            except Exception as e:
                messagebox.showerror("Erreur d'exécution", f"Une erreur est survenue lors du traitement de {os.path.basename(task['path'])}:\n{e}")
                self.status_label.config(text="Erreur ! Traitement arrêté.")
                self.run_button.config(state=tk.NORMAL)
                return

        self.status_label.config(text="Traitement terminé.")
        self.run_button.config(state=tk.NORMAL)
        messagebox.showinfo("Succès", "L'extraction de tous les fichiers est terminée.")