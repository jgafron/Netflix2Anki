import tkinter as tk
from tkinter import Text, messagebox, filedialog, ttk, Scrollbar
from PIL import Image, ImageTk, ImageGrab
from sentence_miner.ui.keyboards import VirtualKeyboard
import pytesseract
import keyboard
import requests
import soundcard as sc
import soundfile as sf
import numpy as np
import os
import sys
import configparser
from sentence_miner.utils.config import LANGUAGE_MAP
from .settings_window import SettingsWindow
from sentence_miner.ocr.ocr_engine import run_ocr
from sentence_miner.utils.snipping_tool import SnippingTool
from sentence_miner.anki.anki_connector import AnkiConnector
from sentence_miner.api.openai_client import OpenAIClient
from sentence_miner.audio.audio_manager import AudioManager


class OCRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("N2A Sentence Miner")
        if getattr(sys, 'frozen', False):
            application_path = sys._MEIPASS
        else:
            application_path = os.path.dirname(os.path.abspath(__file__))
        
        # Path for accessing the icon file
        icon_path = os.path.join(application_path, 'icon.ico')
        self.root.iconbitmap(icon_path)
        self.root.geometry("1024x768")

        self.keyboard_visible = False
        self.config = configparser.ConfigParser()
        self.config.read('settings.ini')
        if not self.config.has_section('Settings'):
            self.config.add_section('Settings')
        
        self.anki_connector = AnkiConnector()
        self.api_key = self.config.get('Settings', 'api_key', fallback='')
        self.ocr_language = self.config.get('Settings', 'ocr_language', fallback='eng')
        self.openai_prompt = self.config.get('Settings', 'openai_prompt', fallback=self.get_default_prompt())
        self.user_openai_prompt = self.config.get('Settings', 'user_openai_prompt', fallback=self.get_default_user_prompt())

        self.openai_client = OpenAIClient(self.api_key)  # Initialize OpenAIClient

        # Populate installed and uninstalled languages
        self.installed_languages, self.uninstalled_languages = self.get_tesseract_languages()

        self.top_frame = tk.Frame(root)
        self.top_frame.pack(side=tk.TOP, fill=tk.X)

        self.upload_btn = tk.Button(self.top_frame, text="Upload Image", command=self.upload_image)
        self.upload_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.paste_btn = tk.Button(self.top_frame, text="Paste Image from Clipboard", command=self.paste_image)
        self.paste_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.extract_btn = tk.Button(self.top_frame, text="Extract Text", command=self.extract_text, state=tk.DISABLED)
        self.extract_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.snip_btn = tk.Button(self.top_frame, text="Snipping Mode", command=self.snipping_mode)
        self.snip_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.settings_btn = tk.Button(self.top_frame, text="Settings", command=self.open_settings)
        self.settings_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.keyboard_btn = tk.Button(self.top_frame, text="Keyboard", command=self.open_keyboard)
        self.keyboard_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.append_text_var = tk.BooleanVar(value=False)
        self.append_text_checkbox = tk.Checkbutton(self.top_frame, text="Add Image Text to Current Extracted Text", variable=self.append_text_var)
        self.append_text_checkbox.pack(side=tk.LEFT, padx=5, pady=5)

        self.frame = tk.Frame(root)
        self.frame.pack(expand=True, fill=tk.BOTH)

        self.audio_frame = tk.Frame(self.frame)
        self.audio_frame.grid(row=1, column=0, columnspan=4, pady=5)

        self.record_btn = tk.Button(self.audio_frame, text="Record Audio", command=self.record_audio)
        self.record_btn.grid(row=0, column=0, padx=5, pady=5)

        self.stop_record_btn = tk.Button(self.audio_frame, text="Stop Recording", command=self.stop_recording, state=tk.DISABLED)
        self.stop_record_btn.grid(row=0, column=1, padx=5, pady=5)

        self.playback_btn = tk.Button(self.audio_frame, text="Playback Audio", command=self.playback_audio, state=tk.DISABLED)
        self.playback_btn.grid(row=0, column=2, padx=5, pady=5)

        self.timer_label = tk.Label(self.audio_frame, text="00:00 / 00:00")
        self.timer_label.grid(row=0, column=3, padx=5, pady=5)

        self.deck_label = tk.Label(self.frame, text="Deck for Response Window:")
        self.deck_label.grid(row=2, column=0, padx=5, pady=5, sticky="W")

        self.deck_combobox_response = ttk.Combobox(self.frame, state="readonly")
        self.deck_combobox_response.grid(row=2, column=1, padx=5, pady=5, sticky="W")

        self.default_deck_label = tk.Label(self.frame, text="Default Deck for Individual Words:")
        self.default_deck_label.grid(row=3, column=0, padx=5, pady=5, sticky="W")

        self.deck_combobox_default = ttk.Combobox(self.frame, state="readonly")
        self.deck_combobox_default.grid(row=3, column=1, padx=5, pady=5, sticky="W")

        self.send_api_btn = tk.Button(self.frame, text="Send Text to API", command=self.send_text_to_api, state=tk.DISABLED)
        self.send_api_btn.grid(row=4, column=0, padx=5, pady=5)

        self.image_label = tk.Label(self.frame)
        self.image_label.grid(row=5, column=0, columnspan=2, padx=5, pady=5)

        self.text_frame = tk.Frame(self.frame)
        self.text_frame.grid(row=6, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        self.text_scroll = Scrollbar(self.text_frame)
        self.text_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.text_box = Text(self.text_frame, height=10, width=80, wrap=tk.WORD, undo=True, autoseparators=True, maxundo=-1,yscrollcommand=self.text_scroll.set, font=("Times New Roman", 12))
        self.text_box.bind("<Control-z>", lambda e: self.text_box.edit_undo())
        self.text_box.bind("<Control-y>", lambda e: self.text_box.edit_redo())
        self.text_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.text_scroll.config(command=self.text_box.yview)

        self.card_side_var = tk.StringVar(value="front")
        self.front_radio = tk.Radiobutton(self.frame, text="Extracted Text on Front", variable=self.card_side_var, value="front")
        self.back_radio = tk.Radiobutton(self.frame, text="Extracted Text on Back", variable=self.card_side_var, value="back")
        self.front_radio.grid(row=7, column=0, padx=5, pady=5, sticky="W")
        self.back_radio.grid(row=7, column=1, padx=5, pady=5, sticky="W")

        self.message_label = tk.Label(self.frame, text="", fg="green")
        self.message_label.grid(row=8, column=0, columnspan=2, padx=5, pady=5)

        self.frame.grid_rowconfigure(6, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)

        self.setup_hotkey()
        self.refresh_decks()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.font_size = self.config.getint('Settings', 'font_size', fallback=12)
        self.text_box.config(font=("Times New Roman", self.font_size))
        self.recording = False
        self.samplerate = 48000
        self.output_file_name = os.path.join(os.path.expanduser("~"), "Desktop", "out.wav")
        self.mic = None
        self.data = []
        self.audio_recorded = False
        self.audio_manager = AudioManager(self.output_file_name, self)

    def setup_hotkey(self):
        def start_snipping_mode():
            self.root.after(0, self.snipping_mode)

        keyboard.add_hotkey('shift+s', start_snipping_mode)

    def update_text_box_font_size(self, new_size):
        self.font_size = new_size
        self.text_box.config(font=("Times New Roman", self.font_size))
        
        # Save the new font size in the configuration
        self.config.set('Settings', 'font_size', str(new_size))
        with open('settings.ini', 'w') as configfile:
            self.config.write(configfile)

    def on_closing(self):
        self.root.destroy()

    def open_settings(self):
        SettingsWindow(self.root, self.config, self)  # Pass root and app instance
    
    def get_language_name_from_code(self, code):
        return LANGUAGE_MAP.get(code, code)

    def get_language_code_from_name(self, name):
        return {v: k for k, v in LANGUAGE_MAP.items()}.get(name, name)
    
    def get_tesseract_languages(self):
        installed_langs = pytesseract.get_languages(config='')
        installed_langs_full = [self.get_language_name_from_code(lang) for lang in installed_langs]
        uninstalled_langs_full = [name for code, name in LANGUAGE_MAP.items() if code not in installed_langs]
        return installed_langs_full, uninstalled_langs_full

    def upload_image(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.image = Image.open(file_path)
            self.image.thumbnail((400, 400))
            self.photo = ImageTk.PhotoImage(self.image)
            self.image_label.config(image=self.photo)
            self.extract_btn.config(state=tk.NORMAL)

    def paste_image(self, path=None):
        try:
            if path:
                self.image = Image.open(path)
            else:
                image = ImageGrab.grabclipboard()
                if isinstance(image, Image.Image):
                    self.image = image
                else:
                    messagebox.showerror("Error", "No image found in clipboard.")
                    return

            self.image.thumbnail((400, 400))
            self.photo = ImageTk.PhotoImage(self.image)
            self.image_label.config(image=self.photo)
            self.extract_btn.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to paste image from clipboard: {e}")

    def open_keyboard(self):
        if hasattr(self, 'keyboard_visible') and self.keyboard_visible:
            self.keyboard_frame.destroy()
            self.keyboard_visible = False
        else:
            current_language = LANGUAGE_MAP.get(self.ocr_language, 'English')
            self.keyboard_frame = tk.Frame(self.frame)
            self.keyboard_frame.grid(row=7, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
            keyboard_app = VirtualKeyboard(self.keyboard_frame, self.text_box, current_language)
            
            self.keyboard_visible = True
    
    def extract_text(self):
        if hasattr(self, 'image'):
            try:
                # Save the image to a temporary file
                image_path = os.path.join(os.path.expanduser("~"), "Desktop", "temp_image.png")
                self.image.save(image_path)

                # Pass the image path to run_ocr
                text = run_ocr(image_path, self.ocr_language)

                if self.append_text_var.get():
                    current_text = self.text_box.get(1.0, tk.END).strip()
                    new_text = current_text + "\n" + text if current_text else text
                else:
                    new_text = text

                self.text_box.delete(1.0, tk.END)
                self.text_box.insert(tk.END, new_text)
                self.send_api_btn.config(state=tk.NORMAL)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to extract text: {e}")

    def query_openai(self, prompt_text):
        return self.openai_client.query_openai(
            prompt_text,
            self.ocr_language,
            self.openai_prompt,
            self.user_openai_prompt
        )
    
    def send_text_to_api(self):
        self.api_text = self.text_box.get("1.0", tk.END).strip()
        if self.api_text:
            try:
                openai_response = self.query_openai(self.api_text)
                self.show_response_window(self.api_text, openai_response)
            except Exception as e:
                print(f"Failed to query OpenAI API: {e}")
                messagebox.showerror("Error", f"Failed to query OpenAI API: {e}")

    def show_response_window(self, front_text, response_text):
        response_window = tk.Toplevel(self.root)
        response_window.title("OpenAI API Response")
        response_window.geometry("600x600")
        response_window.attributes('-topmost', 'true')

        response_frame = tk.Frame(response_window)
        response_frame.pack(expand=True, fill=tk.BOTH)

        response_scroll = Scrollbar(response_frame)
        response_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.response_text_box = Text(response_frame, wrap=tk.WORD, undo=True, autoseparators=True, maxundo=-1, yscrollcommand=response_scroll.set, font=("Times New Roman", 12))
        self.response_text_box.bind("<Control-z>", lambda e: self.response_text_box.edit_undo())
        self.response_text_box.bind("<Control-y>", lambda e: self.response_text_box.edit_redo())

        self.response_text_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        response_scroll.config(command=self.response_text_box.yview)

        self.response_text_box.insert(tk.END, response_text)

        self.include_audio_var = tk.BooleanVar()
        self.include_audio_checkbox = tk.Checkbutton(response_window, text="Include Audio with Card", variable=self.include_audio_var)
        self.include_audio_checkbox.pack(pady=10)

        self.audio_side_var = tk.StringVar(value="back")
        self.audio_front_radio = tk.Radiobutton(response_window, text="Audio on Front", variable=self.audio_side_var, value="front")
        self.audio_back_radio = tk.Radiobutton(response_window, text="Audio on Back", variable=self.audio_side_var, value="back")
        self.audio_front_radio.pack()
        self.audio_back_radio.pack()

        if not self.audio_recorded:
            self.include_audio_checkbox.config(state=tk.DISABLED)
            self.audio_front_radio.config(state=tk.DISABLED)
            self.audio_back_radio.config(state=tk.DISABLED)
        add_to_anki_btn = tk.Button(response_window, text="Add to Anki", command=lambda: self.add_to_anki_from_response(response_window, front_text))
        add_to_anki_btn.pack(pady=10)

        individual_words_frame = tk.Frame(response_window)
        individual_words_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        deck_label = tk.Label(individual_words_frame, text="Select Deck:")
        deck_label.grid(row=0, column=0, padx=5, pady=5, sticky="W")

        self.deck_combobox_individual = ttk.Combobox(individual_words_frame, state="readonly")
        self.deck_combobox_individual.grid(row=0, column=1, padx=5, pady=5, sticky="W")
        decks = self.get_decks()
        self.deck_combobox_individual['values'] = decks

        default_deck = self.deck_combobox_default.get()
        self.deck_combobox_individual.set(default_deck)

        self.card_side_var_individual = tk.StringVar(value="front")
        front_radio = tk.Radiobutton(individual_words_frame, text="Highlighted Text on Front", variable=self.card_side_var_individual, value="front")
        back_radio = tk.Radiobutton(individual_words_frame, text="Highlighted Text on Back", variable=self.card_side_var_individual, value="back")
        front_radio.grid(row=1, column=0, padx=5, pady=5, sticky="W")
        back_radio.grid(row=1, column=1, padx=5, pady=5, sticky="W")

        load_btn = tk.Button(individual_words_frame, text="Load", command=self.load_individual_word)
        load_btn.grid(row=2, column=0, padx=5, pady=5, sticky="W")

        finish_btn = tk.Button(individual_words_frame, text="Finish", command=lambda: self.finish_individual_word(response_window))
        finish_btn.grid(row=2, column=1, padx=5, pady=5, sticky="W")

        self.card_preview_label = tk.Label(individual_words_frame, text="Card Preview:")
        self.card_preview_label.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="W")

        self.card_preview_frame = tk.Frame(individual_words_frame)
        self.card_preview_frame.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="W")

        front_label = tk.Label(self.card_preview_frame, text="Front:")
        front_label.pack(side=tk.LEFT, padx=5, pady=5)
        self.card_preview_text_front = Text(self.card_preview_frame, height=10, width=30, wrap=tk.WORD, font=("Times New Roman", 12))
        self.card_preview_text_front.pack(side=tk.LEFT, padx=5, pady=5)

        back_label = tk.Label(self.card_preview_frame, text="Back:")
        back_label.pack(side=tk.LEFT, padx=5, pady=5)
        self.card_preview_text_back = Text(self.card_preview_frame, height=10, width=30, wrap=tk.WORD, font=("Times New Roman", 12))
        self.card_preview_text_back.pack(side=tk.LEFT, padx=5, pady=5)

        self.card_preview_text_front.insert(tk.END, front_text)
        self.card_preview_text_back.insert(tk.END, response_text)

        self.update_card_preview()

    def add_to_anki_from_response(self, response_window, front_text):
        deck_name = self.deck_combobox_response.get().split(" (")[0]
        if not deck_name:
            self.message_label.config(text="Please select a deck for the response window.", fg="red")
            return

        response_text = self.response_text_box.get("1.0", tk.END).strip()
        if not front_text or not response_text:
            messagebox.showerror("Error", "Note is empty. Please provide both front and back text.")
            return

        audio_data = None
        if self.include_audio_var.get() and self.audio_recorded:
            audio_data = {
                "path": self.output_file_name,
                "filename": os.path.basename(self.output_file_name),
                "fields": self.audio_side_var.get().capitalize()
            }

        success, message = self.anki_connector.add_note_to_deck(deck_name, front_text, response_text, audio_data)
        self.message_label.config(text=message, fg="green" if success else "red")
        if success:
            response_window.destroy()

    def load_individual_word(self):
        deck_name = self.deck_combobox_individual.get().split(" (")[0]
        if not deck_name:
            self.message_label.config(text="Please select a deck.", fg="red")
            return

        highlighted_text = self.get_selected_text()
        if not highlighted_text:
            self.message_label.config(text="Please highlight text to load.", fg="red")
            return

        # Choose the correct preview box (front or back)
        target = (self.card_preview_text_front
                if self.card_side_var_individual.get() == "front"
                else self.card_preview_text_back)

        # Add a space if there’s already text inside
        if target.index("end-1c") != "1.0":
            target.insert(tk.END, " ")

        # Insert the highlighted text directly into the preview box
        target.insert(tk.END, highlighted_text)

        # Remember which deck this card belongs to
        self.deck_name_individual = deck_name

    def finish_individual_word(self, response_window):
        self.front_text = self.card_preview_text_front.get("1.0", tk.END).strip()
        self.back_text = self.card_preview_text_back.get("1.0", tk.END).strip()

        if not self.front_text or not self.back_text:
            messagebox.showerror("Error", "Note is empty. Please provide both front and back text.")
            return

        note = {
            "deckName": self.deck_name_individual,
            "modelName": "Basic",
            "fields": {
                "Front": self.front_text,
                "Back": self.back_text
            },
            "tags": []
        }

        anki_connect_url = 'http://localhost:8765'
        payload = {
            "action": "addNote",
            "version": 6,
            "params": {
                "note": note
            }
        }

        try:
            response = requests.post(anki_connect_url, json=payload)
            if response.status_code == 200:
                result = response.json()
                if 'error' in result and result['error'] is None:
                    self.card_preview_label.config(text=f"Card Added to Deck: {self.deck_name_individual}")
                    self.front_text = ""
                    self.back_text = ""
                    self.update_card_preview()
                else:
                    self.message_label.config(text=f"Failed to add card: {result['error']}", fg="red")
            else:
                self.message_label.config(text="Failed to connect to AnkiConnect.", fg="red")
        except requests.exceptions.RequestException as e:
            self.message_label.config(text=f"Failed to connect to AnkiConnect: {e}", fg="red")

    def update_card_preview(self):
        self.card_preview_text_front.delete(1.0, tk.END)
        self.card_preview_text_back.delete(1.0, tk.END)
        self.card_preview_text_front.insert(tk.END, getattr(self, 'front_text', ''))
        self.card_preview_text_back.insert(tk.END, getattr(self, 'back_text', ''))

    def get_selected_text(self):
        try:
            selected_text = self.response_text_box.selection_get()
            return selected_text.strip()
        except:
            return None

    def snipping_mode(self, event=None):
        SnippingTool(self.root, self.snipping_done)

    def snipping_done(self, path):
        if path:
            self.paste_image(path)
            self.extract_text()
        else:
            self.message_label.config(text="No image was snipped.", fg="red")

    def refresh_decks(self):
        try:
            decks = self.anki_connector.get_decks()
            deck_names_with_counts = []
            for deck_name in decks:
                count = self.anki_connector.get_deck_card_count(deck_name)
                deck_names_with_counts.append(f"{deck_name} ({count} cards)")
            self.deck_combobox_response['values'] = deck_names_with_counts
            self.deck_combobox_default['values'] = deck_names_with_counts
        except requests.exceptions.ConnectionError:
            self.message_label.config(text="Failed to connect to AnkiConnect. Ensure Anki is running and AnkiConnect is installed.", fg="red")

    def get_decks(self):
        anki_connect_url = 'http://localhost:8765'
        payload = {
            "action": "deckNamesAndIds",
            "version": 6
        }
        try:
            response = requests.post(anki_connect_url, json=payload)
            if response.status_code == 200:
                result = response.json()
                if 'error' in result and result['error'] is None:
                    return list(result['result'].keys())
                else:
                    print("Error fetching decks:", result['error'])
            else:
                print("Failed to connect to AnkiConnect.")
        except requests.exceptions.RequestException as e:
            print(f"Failed to connect to AnkiConnect: {e}")
        return {}

    def get_deck_card_count(self, deck_name):
        anki_connect_url = 'http://localhost:8765'
        payload = {
            "action": "findCards",
            "version": 6,
            "params": {
                "query": f"deck:{deck_name}"
            }
        }
        try:
            response = requests.post(anki_connect_url, json=payload)
            if response.status_code == 200:
                result = response.json()
                if 'error' in result and result['error'] is None:
                    return len(result['result'])
                else:
                    print(f"Error fetching card count for deck {deck_name}:", result['error'])
            else:
                print(f"Failed to connect to AnkiConnect for deck {deck_name}.")
        except requests.exceptions.RequestException as e:
            print(f"Failed to connect to AnkiConnect: {e}")
        return 0
    
    def record_audio(self):
        self.audio_manager.record_audio(self.record_btn, self.stop_record_btn, self.playback_btn, self.timer_label)

    def stop_recording(self):
        self.audio_manager.stop_recording(self.record_btn, self.stop_record_btn, self.playback_btn, self.timer_label)

    def playback_audio(self):
        self.audio_manager.playback_audio(self.timer_label)

    def update_api_key(self, new_key):
        self.api_key = new_key
    
    def update_ocr_language(self, new_language):
        self.ocr_language = new_language
        # Update the OpenAI prompt with the new language
        language_name = LANGUAGE_MAP.get(new_language, 'unknown')
        default_prompt = f'You are a helpful assistant. Your task is to translate {language_name} text into English and provide a word-by-word breakdown including tones and definitions.'
        self.update_openai_prompt(default_prompt)

    def update_openai_prompt(self, new_prompt):
        self.openai_prompt = new_prompt

    def update_user_openai_prompt(self, new_user_prompt):
        self.user_openai_prompt = new_user_prompt

    def get_default_prompt(self):
        language_name = LANGUAGE_MAP.get(self.ocr_language, 'unknown')
        return f'You are a helpful assistant. Your task is to translate {language_name} text into English and provide a word-by-word breakdown including tones and definitions.'

    def get_default_user_prompt(self):
        return 'Translate the following into English, then break it down word for word. Include tone marks in the phonetics and provide the English definition of each word. The response should be formatted as:\n\nRephrased in English: "<Translation>"\nBreaking it down:\n<word> (<phonetic>): <definition>\n\n{prompt_text}'
