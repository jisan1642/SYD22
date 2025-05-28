#!/usr/bin/env python
# coding: utf-8

# In[2]:


pip install opencv-python pillow


# In[3]:


import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import cv2
from PIL import Image, ImageTk
import numpy as np
import copy


# In[4]:


class ImageEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Editor")

        self.image_path = None
        self.original_image = None
        self.display_image = None
        self.tk_image = None
        self.cropped_image = None
        self.modified_image = None
        self.undo_stack = []

        self.start_x = self.start_y = self.end_x = self.end_y = None
        self.rect_id = None

        self.setup_ui()

    def setup_ui(self):
        # Frames
        self.canvas_frame = tk.Frame(self.root)
        self.canvas_frame.pack(side=tk.LEFT, padx=10, pady=10)

        self.control_frame = tk.Frame(self.root)
        self.control_frame.pack(side=tk.RIGHT, padx=10, pady=10)

        # Canvas
        self.canvas = tk.Canvas(self.canvas_frame, width=500, height=500, bg='gray')
        self.canvas.pack()
        self.canvas.bind("<ButtonPress-1>", self.start_crop)
        self.canvas.bind("<B1-Motion>", self.draw_crop)
        self.canvas.bind("<ButtonRelease-1>", self.end_crop)

        # Controls
        ttk.Button(self.control_frame, text="Load Image", command=self.load_image).pack(pady=5)
        ttk.Button(self.control_frame, text="Save Image", command=self.save_image).pack(pady=5)

        self.slider_label = tk.Label(self.control_frame, text="Resize:")
        self.slider = tk.Scale(self.control_frame, from_=10, to=200, orient=tk.HORIZONTAL, command=self.resize_image)
        self.slider.set(100)
        self.slider_label.pack(pady=5)
        self.slider.pack(pady=5)

        self.cropped_preview_label = tk.Label(self.control_frame, text="Cropped Image:")
        self.cropped_preview_label.pack(pady=5)
        self.cropped_canvas = tk.Canvas(self.control_frame, width=200, height=200, bg='white')
        self.cropped_canvas.pack()

    def load_image(self):
        file_path = filedialog.askopenfilename()
        if not file_path:
            return
        self.image_path = file_path
        self.original_image = cv2.imread(file_path)
        self.display_image = copy.deepcopy(self.original_image)
        self.show_image()
        self.undo_stack.clear()

    def show_image(self):
        if self.display_image is None:
            return
        bgr_image = cv2.cvtColor(self.display_image, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(bgr_image)
        img = img.resize((500, 500))
        self.tk_image = ImageTk.PhotoImage(img)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

    def start_crop(self, event):
        if self.display_image is None:
            return
        self.start_x, self.start_y = event.x, event.y

    def draw_crop(self, event):
        if self.start_x is None or self.start_y is None:
            return
        self.end_x, self.end_y = event.x, event.y
        self.canvas.delete(self.rect_id)
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.end_x, self.end_y, outline='red'
        )

    def end_crop(self, event):
        if self.display_image is None:
            return
        x0, y0 = int(self.start_x), int(self.start_y)
        x1, y1 = int(event.x), int(event.y)
        x0, x1 = sorted([x0, x1])
        y0, y1 = sorted([y0, y1])
        scale_x = self.original_image.shape[1] / 500
        scale_y = self.original_image.shape[0] / 500
        x0, x1 = int(x0 * scale_x), int(x1 * scale_x)
        y0, y1 = int(y0 * scale_y), int(y1 * scale_y)

        self.cropped_image = self.original_image[y0:y1, x0:x1]
        self.modified_image = copy.deepcopy(self.cropped_image)
        self.show_cropped_preview()
        self.undo_stack.append(copy.deepcopy(self.cropped_image))

    def resize_image(self, val):
        if self.cropped_image is None:
            return
        scale_percent = int(val)
        width = int(self.cropped_image.shape[1] * scale_percent / 100)
        height = int(self.cropped_image.shape[0] * scale_percent / 100)
        self.modified_image = cv2.resize(self.cropped_image, (width, height))
        self.show_cropped_preview()

    def show_cropped_preview(self):
        if self.modified_image is None:
            return
        bgr_image = cv2.cvtColor(self.modified_image, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(bgr_image)
        img = img.resize((200, 200))
        img_tk = ImageTk.PhotoImage(img)
        self.cropped_canvas.image = img_tk
        self.cropped_canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)

    def save_image(self):
        if self.modified_image is None:
            messagebox.showerror("Error", "No modified image to save.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                 filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg")])
        if file_path:
            cv2.imwrite(file_path, self.modified_image)
            messagebox.showinfo("Saved", "Image saved successfully.")

# Run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = ImageEditorApp(root)
    root.mainloop()


# In[ ]:




