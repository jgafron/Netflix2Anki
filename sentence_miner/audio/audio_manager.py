import soundcard as sc
import soundfile as sf
import threading
import numpy as np
import os
import time
import tkinter as tk
from tkinter import messagebox
from concurrent.futures import ThreadPoolExecutor

class AudioManager:
    def __init__(self, output_file_name, ocr_app, samplerate=48000):
        self.output_file_name = output_file_name
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.ocr_app = ocr_app  # Store the reference to OCRApp
        self.samplerate = samplerate  # Default sample rate or overridden by the user
        self.mic = None  # Placeholder for microphone input (if applicable)
        self.data = []  # List to store audio chunks
        self.recording = False  # Flag to track recording status
        self.audio_recorded = False  # Tracks if audio has been recorded
        self.audio_playing = False
        self.playback_thread = None
        self.stop_playback_event = threading.Event()

    def record_audio(self, record_btn, stop_record_btn, playback_btn, timer_label):
        record_btn.config(state=tk.DISABLED)
        stop_record_btn.config(state=tk.NORMAL)
        playback_btn.config(state=tk.DISABLED)
        timer_label.config(text="00:00 / 00:00")

        def update_timer():
            start_time = time.time()
            while self.recording:
                elapsed_time = time.time() - start_time
                minutes, seconds = divmod(int(elapsed_time), 60)
                timer_label.config(text=f"{minutes:02}:{seconds:02} / 00:00")
                timer_label.update_idletasks()
                time.sleep(0.1)

        self.recording = True
        self.data = []
        self.mic = sc.get_microphone(id=str(sc.default_speaker().name), include_loopback=True)

        def record():
            with self.mic.recorder(samplerate=self.samplerate) as mic:
                while self.recording:
                    chunk = mic.record(numframes=self.samplerate // 10)  # Record in chunks
                    self.data.append(chunk)

        self.record_thread = threading.Thread(target=record)
        self.record_thread.start()
        threading.Thread(target=update_timer).start()

    def stop_recording(self, record_btn, stop_record_btn, playback_btn, timer_label):
        self.recording = False
        self.record_thread.join()  # Wait for the recording thread to finish
        self.data = np.concatenate(self.data, axis=0)  # Combine all chunks into one array
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(self.output_file_name), exist_ok=True)
            # Write the data to a file
            sf.write(file=self.output_file_name, data=self.data, samplerate=self.samplerate)
            record_btn.config(state=tk.NORMAL)
            stop_record_btn.config(state=tk.DISABLED)
            playback_btn.config(state=tk.NORMAL)

            # Update audio recorded status
            self.ocr_app.audio_recorded = True
    
            # Update the timer label with the total duration of the recording
            total_minutes, total_seconds = divmod(self.data.shape[0] // self.samplerate, 60)
            timer_label.config(text=f"00:00 / {total_minutes:02}:{total_seconds:02}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error saving recording: {e}")

    def playback_audio(self, timer_label):
        try:
            # Stop current playback if it's still running
            if self.playback_thread and self.playback_thread.is_alive():
                self.stop_playback_event.set()
                self.playback_thread.join()
                self.stop_playback_event.clear()
                print("Stopping current playback...")

            # Read audio data
            data, samplerate = sf.read(self.output_file_name)
            self.executor.submit(self.playback_audio, data, samplerate)
            total_duration = len(data) / samplerate

            def update_playback_timer():
                start_time = time.time()
                while not self.stop_playback_event.is_set():
                    elapsed_time = time.time() - start_time
                    if elapsed_time >= total_duration:
                        break
                    minutes, seconds = divmod(int(elapsed_time), 60)
                    timer_label.config(text=f"{minutes:02}:{seconds:02} / {int(total_duration // 60):02}:{int(total_duration % 60):02}")
                    timer_label.update_idletasks()
                    time.sleep(0.1)

            self.playback_thread = threading.Thread(target=lambda: self.play_audio(data, samplerate))
            self.playback_thread.start()

            threading.Thread(target=update_playback_timer).start()

        except Exception as e:
            messagebox.showerror("Error", f"Playback failed: {e}")

    def play_audio(self, data, samplerate):
        with sc.default_speaker().player(samplerate=samplerate) as sp:
            sp.play(data)