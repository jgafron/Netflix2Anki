import tkinter as tk
from tkinter import Canvas
from PIL import ImageGrab
import os

class SnippingTool:
    def __init__(self, root, callback):
        self.root = root
        self.callback = callback
        self.snip_window = tk.Toplevel(root)
        self.snip_window.attributes("-fullscreen", True)
        self.snip_window.attributes("-topmost", True)
        self.snip_window.attributes("-alpha", 0.3)
        self.snip_window.configure(bg='gray')

        self.canvas = tk.Canvas(self.snip_window, cursor="cross", bg="gray")
        self.canvas.pack(fill=tk.BOTH, expand=tk.YES)

        self.snip_window.bind("<Button-1>", self.on_button_press)
        self.snip_window.bind("<B1-Motion>", self.on_mouse_drag)
        self.snip_window.bind("<ButtonRelease-1>", self.on_button_release)

        self.rect = None
        self.start_x = None
        self.start_y = None

    def on_button_press(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red')

    def on_mouse_drag(self, event):
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_button_release(self, event):
        x1 = min(self.start_x, event.x)
        y1 = min(self.start_y, event.y)
        x2 = max(self.start_x, event.x)
        y2 = max(self.start_y, event.y)

        self.snip_window.withdraw()
        self.root.after(0, self.capture, x1, y1, x2, y2)

    def capture(self, x1, y1, x2, y2):
        self.snip_window.destroy()
        img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
        img_path = os.path.join(os.path.expanduser("~"), "Desktop", "snip.png")
        img.save(img_path)
        self.callback(img_path)