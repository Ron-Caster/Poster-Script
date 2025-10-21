import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

# Config
BACKGROUND = "background.png"
TEXT_FILE = "poster_text.txt"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
POSITIONS_FILE = os.path.join(SCRIPT_DIR, "positions.json")
LOGO_SIZE = (250, 250)


def load_text_lines(path):
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]
    return lines


class PosterPlacer(tk.Tk):
    def __init__(self, background_path=BACKGROUND, text_file=TEXT_FILE):
        super().__init__()
        self.title("Poster Placer")
        self.geometry("1000x700")

        self.background_path = background_path
        self.text_file = text_file
        self.lines = load_text_lines(self.text_file)
        self.num_items = len(self.lines)
        self.positions = {}  # index -> (x,y)

        self.canvas = tk.Canvas(self, bg="#ddd")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.toolbar = tk.Frame(self)
        self.toolbar.pack(fill=tk.X)

        self.save_btn = tk.Button(self.toolbar, text="Save Positions", command=self.save_positions)
        self.save_btn.pack(side=tk.LEFT)

        self.load_bg_btn = tk.Button(self.toolbar, text="Load Background", command=self.load_background_dialog)
        self.load_bg_btn.pack(side=tk.LEFT)

        self.place_logo_btn = tk.Button(self.toolbar, text="Place Logo", command=self.enter_logo_mode)
        self.place_logo_btn.pack(side=tk.LEFT)

        self.clear_btn = tk.Button(self.toolbar, text="Clear Positions", command=self.clear_positions)
        self.clear_btn.pack(side=tk.LEFT)

        self.instructions = tk.Label(self.toolbar, text=f"Click to place items 1..{self.num_items}. Current: 1")
        self.instructions.pack(side=tk.LEFT, padx=10)

        self.bind('<Configure>', self.on_resize)
        self.canvas.bind('<Button-1>', self.on_click)

        self.bg_image = None
        self.bg_tk = None
        self.bg_photo_id = None

        self.current_index = 1
        self.logo_mode = False

        self.load_background(self.background_path)
        self.draw_rulers()
        self.redraw()

    def load_background_dialog(self):
        fp = filedialog.askopenfilename(title="Select background image", filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp")])
        if fp:
            self.background_path = fp
            self.load_background(fp)
            self.redraw()

    def load_background(self, path):
        if not os.path.exists(path):
            # create placeholder background
            self.bg_image = Image.new('RGBA', (1200, 800), (255, 255, 255, 255))
        else:
            self.bg_image = Image.open(path).convert('RGBA')
        self.bg_tk = ImageTk.PhotoImage(self.bg_image)

    def draw_rulers(self):
        # Rulers are drawn on canvas on redraw
        pass

    def on_resize(self, event):
        self.redraw()

    def redraw(self):
        self.canvas.delete('all')
        # Draw background centered or fitted
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w <= 1 or h <= 1:
            self.after(50, self.redraw)
            return

        # fit bg_image to canvas while preserving aspect
        bg_w, bg_h = self.bg_image.size
        scale = min(w / bg_w, h / bg_h)
        new_w = int(bg_w * scale)
        new_h = int(bg_h * scale)
        resized = self.bg_image.resize((new_w, new_h), Image.LANCZOS)
        self.bg_tk = ImageTk.PhotoImage(resized)
        self.bg_photo_id = self.canvas.create_image((w//2, h//2), image=self.bg_tk)

        # Store transform for converting clicks
        self.offset_x = (w - new_w) // 2
        self.offset_y = (h - new_h) // 2
        self.display_w = new_w
        self.display_h = new_h

        # Draw rulers
        self.draw_rulers_lines()

        # Draw existing positions
        for key, pos in self.positions.items():
            # key may be numeric string ("1","2",...) or 'logo'
            try:
                label = int(key)
            except Exception:
                label = key
            # convert stored absolute bg coordinate to display coords
            x, y = pos
            disp_x = int(x * scale) + self.offset_x
            disp_y = int(y * scale) + self.offset_y
            self.draw_marker(disp_x, disp_y, label)

        # If current index not placed yet, optionally hint
        self.instructions.config(text=f"Click to place items 1..{self.num_items}. Current: {self.current_index}")

    def draw_rulers_lines(self):
        # horizontal ruler
        for i in range(0, self.display_w, 50):
            x = self.offset_x + i
            self.canvas.create_line(x, self.offset_y, x, self.offset_y + 10, fill='#222')
            if i % 100 == 0:
                self.canvas.create_text(x+2, self.offset_y+20, text=str(i), anchor='n', font=('Arial', 8))
        # vertical ruler
        for j in range(0, self.display_h, 50):
            y = self.offset_y + j
            self.canvas.create_line(self.offset_x, y, self.offset_x + 10, y, fill='#222')
            if j % 100 == 0:
                self.canvas.create_text(self.offset_x+20, y+2, text=str(j), anchor='w', font=('Arial', 8))

    def draw_marker(self, x, y, idx):
        r = 8
        self.canvas.create_oval(x-r, y-r, x+r, y+r, fill='red')
        # If idx is 'logo' or another string, show a short label
        label = str(idx)
        if label.lower() == 'logo':
            display = 'L'
        else:
            display = label
        self.canvas.create_text(x+12, y, text=display, anchor='w', font=('Arial', 12), fill='black')

    def on_click(self, event):
        # If click outside bg area, ignore
        if event.x < self.offset_x or event.x > self.offset_x + self.display_w:
            return
        if event.y < self.offset_y or event.y > self.offset_y + self.display_h:
            return

        # convert display coords to bg image coords
        scale = self.display_w / self.bg_image.size[0]
        bg_x = int((event.x - self.offset_x) / scale)
        bg_y = int((event.y - self.offset_y) / scale)

        # If in logo placement mode, save under 'logo' key and exit logo mode
        if self.logo_mode:
            self.positions['logo'] = (bg_x, bg_y)
            self.draw_marker(event.x, event.y, 'logo')
            self.logo_mode = False
            self.instructions.config(text=f"Click to place items 1..{self.num_items}. Current: {self.current_index}")
            messagebox.showinfo("Logo placed", "Logo position saved.")
            return

        # Save position for current index (numeric items)
        if self.current_index <= self.num_items:
            self.positions[str(self.current_index)] = (bg_x, bg_y)
            self.draw_marker(event.x, event.y, self.current_index)
            self.current_index += 1
            if self.current_index > self.num_items:
                messagebox.showinfo("Done", "All items placed. Positions will be auto-saved.")
                # auto-save when complete
                try:
                    self.save_positions()
                except Exception as e:
                    messagebox.showerror('Save Error', f'Could not auto-save positions: {e}')
        else:
            messagebox.showinfo("Info", "All items already placed")

    def enter_logo_mode(self):
        self.logo_mode = True
        self.instructions.config(text="Click on the background to place the logo (will be saved under key 'logo')")

    def save_positions(self):
        data = {
            'background': self.background_path,
            'lines': self.lines,
            'positions': self.positions,
            'logo_size': LOGO_SIZE
        }
        with open(POSITIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        messagebox.showinfo('Saved', f'Positions saved to {POSITIONS_FILE}')

    def clear_positions(self):
        self.positions = {}
        self.current_index = 1
        self.redraw()


if __name__ == '__main__':
    app = PosterPlacer()
    app.mainloop()
