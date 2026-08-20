import ctypes
import tkinter as tk
import pytesseract
from sentence_miner.ui.main_window import OCRApp
import time

# Set DPI awareness
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception as e:
    print(f"Failed to set DPI awareness: {e}")

class SettingsWindow:
    def __init__(self, master, config, app):
        self.master = master
        self.app = app
        self.top = tk.Toplevel(master)
        self.top.title("Settings")
        self.top.geometry("400x500")
        self.config = config
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.top, text="Settings", font=("Helvetica", 16)).pack(pady=10)

        tk.Label(self.top, text="OCR Language:").pack(pady=5)
        self.language_var = tk.StringVar(value=LANGUAGE_MAP.get(self.config.get('Settings', 'ocr_language', fallback='eng'), 'English'))
        self.language_dropdown = ttk.Combobox(self.top, textvariable=self.language_var, state='readonly')

        installed_languages, uninstalled_languages = self.app.get_tesseract_languages()

        dropdown_values = ["*** Installed Languages: ***"] + installed_languages + ["*** Uninstalled Languages: ***"] + uninstalled_languages

        self.language_dropdown['values'] = dropdown_values
        self.language_dropdown.pack(pady=5)

        # Bind the dropdown selection event to update the prompt
        self.language_dropdown.bind("<<ComboboxSelected>>", self.on_language_selected)

        tk.Label(self.top, text="OpenAI Prompt:").pack(pady=5)
        self.prompt_var = tk.StringVar(value=self.config.get('Settings', 'openai_prompt', fallback=self.app.get_default_prompt()))

        self.prompt_frame = tk.Frame(self.top)
        self.prompt_frame.pack(pady=5)
        self.prompt_entry = Text(self.prompt_frame, width=40, height=5, wrap=tk.WORD)
        self.prompt_entry.insert(tk.END, self.prompt_var.get())
        self.prompt_entry.pack(fill=tk.BOTH, expand=True)
        self.prompt_entry.bind("<KeyRelease>", self.adjust_textbox_height)

        tk.Label(self.top, text="User OpenAI Prompt:").pack(pady=5)
        self.user_prompt_var = tk.StringVar(value=self.config.get('Settings', 'user_openai_prompt', fallback=self.app.get_default_user_prompt()))

        self.user_prompt_frame = tk.Frame(self.top)
        self.user_prompt_frame.pack(pady=5)
        self.user_prompt_entry = Text(self.user_prompt_frame, width=40, height=5, wrap=tk.WORD)
        self.user_prompt_entry.insert(tk.END, self.user_prompt_var.get())
        self.user_prompt_entry.pack(fill=tk.BOTH, expand=True)
        self.user_prompt_entry.bind("<KeyRelease>", self.adjust_textbox_height)

        tk.Label(self.top, text="API Key:").pack(pady=5)
        self.api_key_var = tk.StringVar(value=self.config.get('Settings', 'api_key', fallback=''))
        tk.Entry(self.top, textvariable=self.api_key_var, show="*").pack(pady=5)  # Hide API key input
        
        tk.Label(self.top, text="Extracted Text Font Size:").pack(pady=2)
        
        self.font_size_var = tk.IntVar(value=self.config.getint('Settings', 'font_size', fallback=12))
        self.font_size_slider = tk.Scale(self.top, from_=8, to=36, orient=tk.HORIZONTAL, variable=self.font_size_var)
        self.font_size_slider.pack(pady=5)
        
        self.font_size_slider.bind("<Motion>", self.on_font_size_change)
        self.font_size_slider.bind("<ButtonRelease-1>", self.on_font_size_change)

        tk.Button(self.top, text="Save", command=self.save_settings).pack(pady=20)
        tk.Button(self.top, text="Cancel", command=self.top.destroy).pack(pady=5)
        tk.Button(self.top, text="Return to Defaults", command=self.return_to_defaults).pack(pady=5)


    def on_font_size_change(self, event):
        new_font_size = self.font_size_var.get()
        self.app.update_text_box_font_size(new_font_size)

    def validate_selection(self, event):
        selected_value = self.language_dropdown.get()

        if selected_value.startswith("***") or selected_value in self.app.uninstalled_languages:
            messagebox.showerror("Invalid Selection", "Please select a valid installed language.")
            self.language_dropdown.set("")  # Clear the invalid selection

    def adjust_textbox_height(self, event=None):
        text_box = event.widget
        text_box.update_idletasks()
        num_lines = int(text_box.index('end-1c').split('.')[0])
        if num_lines > 5:
            text_box.config(height=num_lines)

    def on_language_selected(self, event):
        selected_language = self.language_dropdown.get()

        # Prevent selecting headers
        if selected_language in self.app.installed_languages:
            language_code = self.app.get_language_code_from_name(selected_language)
            default_prompt = f'You are a helpful assistant. Your task is to translate {selected_language} text into English and provide a word-by-word breakdown including tones and definitions.'
            self.prompt_var.set(default_prompt)
            self.prompt_entry.delete(1.0, tk.END)
            self.prompt_entry.insert(tk.END, default_prompt)
            self.app.update_openai_prompt(default_prompt)
        else:
            # Prevent updating prompt if an invalid selection is made
            self.language_dropdown.set("")
            messagebox.showerror("Invalid Selection", "Please select a valid installed language.")

        # Update the prompt dynamically with the selected language
        default_prompt = f'You are a helpful assistant. Your task is to translate {selected_language} text into English and provide a word-by-word breakdown including tones and definitions.'
        self.prompt_var.set(default_prompt)
        self.prompt_entry.delete(1.0, tk.END)
        self.prompt_entry.insert(tk.END, default_prompt)
        self.app.update_openai_prompt(default_prompt)

    def save_settings(self):
        selected_language = self.language_dropdown.get()
        if selected_language in ["Installed Languages:", "Uninstalled Languages:"] or selected_language not in self.language_dropdown['values']:
            messagebox.showerror("Error", "Please select a valid OCR language.")
            return

        language_code = list(LANGUAGE_MAP.keys())[list(LANGUAGE_MAP.values()).index(selected_language)]

        self.config.set('Settings', 'ocr_language', language_code)
        self.config.set('Settings', 'api_key', self.api_key_var.get())
        self.config.set('Settings', 'openai_prompt', self.prompt_entry.get(1.0, tk.END).strip())
        self.config.set('Settings', 'user_openai_prompt', self.user_prompt_entry.get(1.0, tk.END).strip())
        with open('settings.ini', 'w') as configfile:
            self.config.write(configfile)
        self.app.update_api_key(self.api_key_var.get())  # Update the API key in the main application
        self.app.update_ocr_language(language_code)  # Update the OCR language in the main application
        self.app.update_openai_prompt(self.prompt_entry.get(1.0, tk.END).strip())  # Update the OpenAI prompt in the main application
        self.app.update_user_openai_prompt(self.user_prompt_entry.get(1.0, tk.END).strip())  # Update the User OpenAI prompt in the main application
        self.top.destroy()

    def return_to_defaults(self):
        default_prompt = self.app.get_default_prompt()
        default_user_prompt = self.app.get_default_user_prompt()
        self.prompt_var.set(default_prompt)
        self.user_prompt_var.set(default_user_prompt)
        self.prompt_entry.delete(1.0, tk.END)
        self.prompt_entry.insert(tk.END, default_prompt)
        self.user_prompt_entry.delete(1.0, tk.END)
        self.user_prompt_entry.insert(tk.END, default_user_prompt)


if __name__ == "__main__":
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    root = tk.Tk()
    app = OCRApp(root)
    root.mainloop()
