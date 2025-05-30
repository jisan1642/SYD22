import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import cv2
import numpy as np

class ImageEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Crop & Resize Editor with Extras")

        # Images
        self.original_img = None       # PIL original
        self.cv_img = None             # Current OpenCV BGR image
        self.cropped_img = None        # Cropped img (BGR)
        self.display_img = None        # PIL display image (after all ops)
        self.tk_img = None

        # Crop coords
        self.start_x = self.start_y = 0
        self.rect_id = None
        self.crop_coords = None

        # Undo/Redo stacks store copies of cv_img
        self.undo_stack = []
        self.redo_stack = []

        # Flags for optional features
        self.is_grayscale = False
        self.is_flipped = False

        self.setup_ui()
        self.setup_bindings()

    def setup_ui(self):
        # Buttons frame
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(btn_frame, text="Load Image", command=self.load_image).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Crop", command=self.crop_image).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Undo", command=self.undo).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Redo", command=self.redo).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Save Image", command=self.save_image).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Toggle Grayscale (G)", command=self.toggle_grayscale).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Flip Horizontal (F)", command=self.flip_horizontal).pack(side=tk.LEFT, padx=5)

        # Resize slider label
        self.slider_label = tk.Label(btn_frame, text="Resize: 100%")
        self.slider_label.pack(side=tk.LEFT, padx=5)

        # Resize slider (disabled initially)
        self.resize_slider = tk.Scale(btn_frame, from_=10, to=200, orient=tk.HORIZONTAL,
                                      command=self.resize_image, state=tk.DISABLED)
        self.resize_slider.set(100)
        self.resize_slider.pack(side=tk.LEFT, padx=5)

        # Main canvas for image display
        self.canvas = tk.Canvas(self.root, cursor="cross")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

        # Preview canvas for cropped/resized image
        self.preview_canvas = tk.Canvas(self.root, width=300, height=300, bg="gray")
        self.preview_canvas.pack(side=tk.RIGHT, padx=5, pady=5)

    def setup_bindings(self):
        self.root.bind("<Control-o>", lambda e: self.load_image())
        self.root.bind("<Control-s>", lambda e: self.save_image())
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-y>", lambda e: self.redo())
        self.root.bind("g", lambda e: self.toggle_grayscale())
        self.root.bind("G", lambda e: self.toggle_grayscale())
        self.root.bind("f", lambda e: self.flip_horizontal())
        self.root.bind("F", lambda e: self.flip_horizontal())

    def load_image(self):
        filetypes = [("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff"), ("All files", "*.*")]
        path = filedialog.askopenfilename(title="Select an image", filetypes=filetypes)
        if not path:
            return
        self.original_img = Image.open(path).convert("RGB")
        self.cv_img = cv2.cvtColor(np.array(self.original_img), cv2.COLOR_RGB2BGR)
        self.reset_flags()
        self.clear_undo_redo()
        self.display_image(self.original_img)

        self.crop_coords = None
        self.clear_rectangle()
        self.clear_preview()
        self.resize_slider.config(state=tk.DISABLED)
        self.resize_slider.set(100)
        self.slider_label.config(text="Resize: 100%")

    def reset_flags(self):
        self.is_grayscale = False
        self.is_flipped = False

    def clear_undo_redo(self):
        self.undo_stack.clear()
        self.redo_stack.clear()

    def display_image(self, pil_img):
        self.display_img = pil_img
        self.tk_img = ImageTk.PhotoImage(pil_img)
        self.canvas.config(width=pil_img.width, height=pil_img.height)
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)
        self.canvas.image = self.tk_img

    def on_button_press(self, event):
        if self.cv_img is None:
            return
        self.start_x, self.start_y = event.x, event.y
        self.clear_rectangle()

    def on_move_press(self, event):
        if self.cv_img is None:
            return
        cur_x, cur_y = event.x, event.y
        self.clear_rectangle()
        self.rect_id = self.canvas.create_rectangle(self.start_x, self.start_y, cur_x, cur_y, outline="red", width=2)
        self.show_preview(self.start_x, self.start_y, cur_x, cur_y)

    def on_button_release(self, event):
        if self.cv_img is None:
            return
        self.crop_coords = (self.start_x, self.start_y, event.x, event.y)

    def clear_rectangle(self):
        if self.rect_id:
            self.canvas.delete(self.rect_id)
            self.rect_id = None

    def show_preview(self, x1, y1, x2, y2):
        if self.cv_img is None:
            return
        h, w = self.cv_img.shape[:2]

        # Clamp coords inside image bounds
        x1, y1 = max(0, min(x1, w-1)), max(0, min(y1, h-1))
        x2, y2 = max(0, min(x2, w-1)), max(0, min(y2, h-1))
        xmin, xmax = sorted([x1, x2])
        ymin, ymax = sorted([y1, y2])

        if xmax - xmin < 5 or ymax - ymin < 5:
            self.clear_preview()
            return

        crop_img = self.cv_img[ymin:ymax, xmin:xmax]
        if crop_img.size == 0:
            self.clear_preview()
            return

        pil_crop = Image.fromarray(cv2.cvtColor(crop_img, cv2.COLOR_BGR2RGB))
        pil_crop.thumbnail((300, 300))
        self.preview_tk_img = ImageTk.PhotoImage(pil_crop)

        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(150, 150, image=self.preview_tk_img, anchor="center")
        self.preview_canvas.image = self.preview_tk_img

    def clear_preview(self):
        self.preview_canvas.delete("all")
        self.preview_canvas.image = None

    def crop_image(self):
        if self.cv_img is None or self.crop_coords is None:
            messagebox.showwarning("Warning", "No crop area selected!")
            return

        x1, y1, x2, y2 = self.crop_coords
        h, w = self.cv_img.shape[:2]

        x1, y1 = max(0, min(x1, w-1)), max(0, min(y1, h-1))
        x2, y2 = max(0, min(x2, w-1)), max(0, min(y2, h-1))
        xmin, xmax = sorted([x1, x2])
        ymin, ymax = sorted([y1, y2])

        if xmax - xmin < 10 or ymax - ymin < 10:
            messagebox.showwarning("Warning", "Crop area too small!")
            return

        # Push current state to undo stack
        self.push_undo()

        cropped = self.cv_img[ymin:ymax, xmin:xmax]
        self.cropped_img = cropped.copy()
        self.cv_img = cropped

        pil_img = Image.fromarray(cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB))
        self.display_image(pil_img)

        self.crop_coords = None
        self.clear_rectangle()
        self.clear_preview()

        self.resize_slider.config(state=tk.NORMAL)
        self.resize_slider.set(100)
        self.slider_label.config(text="Resize: 100%")

    def resize_image(self, val):
        if self.cropped_img is None:
            return
        scale_percent = int(val)
        self.slider_label.config(text=f"Resize: {scale_percent}%")

        width = int(self.cropped_img.shape[1] * scale_percent / 100)
        height = int(self.cropped_img.shape[0] * scale_percent / 100)

        if width < 1 or height < 1:
            return

        resized = cv2.resize(self.cropped_img, (width, height), interpolation=cv2.INTER_AREA)
        self.cv_img = resized

        pil_img = Image.fromarray(cv2.cvtColor(resized, cv2.COLOR_BGR2RGB))
        self.display_image(pil_img)

        pil_preview = pil_img.copy()
        pil_preview.thumbnail((300, 300))
        self.preview_tk_img = ImageTk.PhotoImage(pil_preview)
        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(150, 150, image=self.preview_tk_img, anchor="center")
        self.preview_canvas.image = self.preview_tk_img

    def save_image(self):
        if self.cv_img is None:
            messagebox.showwarning("Warning", "No image to save!")
            return

        file = filedialog.asksaveasfilename(defaultextension=".png",
                                            filetypes=[("PNG files", "*.png"),
                                                       ("JPEG files", "*.jpg;*.jpeg"),
                                                       ("BMP files", "*.bmp")])
        if not file:
            return

        cv2.imwrite(file, self.cv_img)
        messagebox.showinfo("Saved", f"Image saved to {file}")

    # Undo/Redo management
    def push_undo(self):
        if self.cv_img is not None:
            self.undo_stack.append(self.cv_img.copy())
            # Clear redo stack on new action
            self.redo_stack.clear()

    def undo(self):
        if not self.undo_stack:
            messagebox.showinfo("Undo", "Nothing to undo")
            return
        self.redo_stack.append(self.cv_img.copy())
        self.cv_img = self.undo_stack.pop()
        self.update_after_undo_redo()

    def redo(self):
        if not self.redo_stack:
            messagebox.showinfo("Redo", "Nothing to redo")
            return
        self.undo_stack.append(self.cv_img.copy())
        self.cv_img = self.redo_stack.pop()
        self.update_after_undo_redo()

    def update_after_undo_redo(self):
        pil_img = Image.fromarray(cv2.cvtColor(self.cv_img, cv2.COLOR_BGR2RGB))
        self.display_image(pil_img)

        # Reset cropped_img to current state for resize slider
        self.cropped_img = self.cv_img.copy()
        self.resize_slider.config(state=tk.NORMAL)
        self.resize_slider.set(100)
        self.slider_label.config(text="Resize: 100%")

        self.clear_rectangle()
        self.clear_preview()
        self.reset_flags()  # Reset grayscale/flip flags

    # Additional processing features
    def toggle_grayscale(self):
        if self.cv_img is None:
            return

        self.push_undo()
        if not self.is_grayscale:
            gray = cv2.cvtColor(self.cv_img, cv2.COLOR_BGR2GRAY)
            self.cv_img = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            self.is_grayscale = True
        else:
            # Revert to original or last non-gray
            # For simplicity, just reload last undo (if available)
            if self.undo_stack:
                self.cv_img = self.undo_stack.pop()
                self.is_grayscale = False
            else:
                self.is_grayscale = False

        pil_img = Image.fromarray(cv2.cvtColor(self.cv_img, cv2.COLOR_BGR2RGB))
        self.display_image(pil_img)
        self.cropped_img = self.cv_img.copy()
        self.resize_slider.config(state=tk.NORMAL)
        self.resize_slider.set(100)
        self.slider_label.config(text="Resize: 100%")
        self.clear_rectangle()
        self.clear_preview()

    def flip_horizontal(self):
        if self.cv_img is None:
            return

        self.push_undo()
        self.cv_img = cv2.flip(self.cv_img, 1)
        self.is_flipped = not self.is_flipped

        pil_img = Image.fromarray(cv2.cvtColor(self.cv_img, cv2.COLOR_BGR2RGB))
        self.display_image(pil_img)
        self.cropped_img = self.cv_img.copy()
        self.resize_slider.config(state=tk.NORMAL)
        self.resize_slider.set(100)
        self.slider_label.config(text="Resize: 100%")
        self.clear_rectangle()
        self.clear_preview()

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageEditorApp(root)
    root.mainloop()
