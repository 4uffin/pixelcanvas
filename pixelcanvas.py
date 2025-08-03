import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import json
import os
from concurrent.futures import ThreadPoolExecutor
from collections import deque

# Note: The 'requests' and 'BytesIO' imports have been removed as they are no longer
# needed for loading online images.

# --- Configuration ---
CANVAS_SIZE = 400
CELL_SIZE = 20
COLS = CANVAS_SIZE // CELL_SIZE
ROWS = CANVAS_SIZE // CELL_SIZE
COLOR_PALETTE = ["#000000", "#FFFFFF", "#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF"]

class PixelCanvas:
    """
    A simple pixel art canvas application built with Tkinter and PIL.

    This application provides a grid-based drawing interface with a variety of
    tools, including a standard pixel brush, an eraser, and a flood-fill tool.
    Users can select from a predefined color palette or use custom images from
    local files as brushes. The application also supports saving and loading
    projects as JSON files and exporting the final artwork as a PNG image.

    Features:
    - Customizable canvas size and cell size.
    - Multiple drawing modes: color, image, erase, and fill.
    - Save/Load functionality for project files (JSON format).
    - Exporting the canvas as a high-quality PNG image.
    - Toggleable grid lines for precision drawing.
    - Keyboard shortcut support (e.g., 'G' to toggle grid, 'Esc' to close).
    """

    def __init__(self, root):
        """
        Initializes the main application window and its components.
        
        Args:
            root (tk.Tk): The root Tkinter window.
        """
        self.root = root
        self.root.title("Pixel Canvas Game")
        self.root.resizable(False, False) # Prevent window resizing
        self.root.protocol("WM_DELETE_WINDOW", self.close_app)

        # --- Application State Variables ---
        self.current_mode = "color"  # "color", "image", "erase", or "fill"
        self.current_color = "#000000"
        self.current_image_info = None  # Stores image info: {'type': 'url'/'local', 'val': path/url}
        self.show_grid = True
        self.cell_size = CELL_SIZE
        
        # grid_data stores the content of each cell.
        # Format: {'mode': 'color'/'image_url'/'image_local', 'val': hex_color/url/path}
        self.grid_data = [[{'mode': 'color', 'val': '#ffffff'} for _ in range(COLS)] for _ in range(ROWS)]
        
        # Caches to prevent garbage collection and repeated loading.
        self.cell_images = {}
        self.color_swatch_images = {}
        # Presets and loading queues for online images have been removed.
        self.executor = ThreadPoolExecutor(max_workers=4)

        # --- UI Setup and Initialization ---
        self.setup_ui()
        self.redraw_canvas()
        self.update_status("Welcome! Press 'G' to toggle the grid.")
        self.select_color(self.current_color)

    def setup_ui(self):
        """
        Configures and places all UI elements, including frames, buttons,
        the canvas, and the status bar.
        """
        main_frame = tk.Frame(self.root, padx=10, pady=10)
        main_frame.pack()

        # Toolbar Frame for tools and file operations
        toolbar = tk.Frame(main_frame)
        toolbar.pack(pady=(0, 10))

        # Tool selection controls
        tools_frame = tk.LabelFrame(toolbar, text="Tools")
        tools_frame.pack(side=tk.LEFT, padx=(0, 10), pady=5)
        
        # "Pick Pixel" Menubutton for colors and images
        menu_button = tk.Menubutton(tools_frame, text="Pick Pixel", relief=tk.RAISED)
        menu_button.pack(side=tk.LEFT, padx=5)
        self.pick_pixel_menu = tk.Menu(menu_button, tearoff=0)
        menu_button.config(menu=self.pick_pixel_menu)
        
        # Colors submenu
        color_menu = tk.Menu(self.pick_pixel_menu, tearoff=0)
        self.pick_pixel_menu.add_cascade(label="Colors", menu=color_menu)
        for color in COLOR_PALETTE:
            swatch = tk.PhotoImage(width=16, height=16)
            swatch.put(color, to=(0, 0, 16, 16))
            self.color_swatch_images[color] = swatch
            color_menu.add_command(image=swatch, compound="left", command=lambda c=color: self.select_color(c))

        # Custom Images submenu
        custom_menu = tk.Menu(self.pick_pixel_menu, tearoff=0)
        self.pick_pixel_menu.add_cascade(label="Custom Images", menu=custom_menu)
        
        # The preset images and their loading logic have been removed.
        custom_menu.add_command(label="Load Custom Image...", command=self.load_image_brush)

        # Other tool buttons
        eraser_button = tk.Button(tools_frame, text="Eraser", command=self.select_eraser)
        eraser_button.pack(side=tk.LEFT, padx=5)
        fill_button = tk.Button(tools_frame, text="Fill", command=self.select_fill_tool)
        fill_button.pack(side=tk.LEFT, padx=5)
        
        # File operations frame
        file_frame = tk.LabelFrame(toolbar, text="File Operations")
        file_frame.pack(side=tk.LEFT, padx=10, pady=5)
        save_button = tk.Button(file_frame, text="Save", command=self.save_canvas)
        save_button.pack(side=tk.LEFT, padx=5)
        load_button = tk.Button(file_frame, text="Load", command=self.load_canvas)
        load_button.pack(side=tk.LEFT, padx=5)
        export_button = tk.Button(file_frame, text="Export as Image", command=self.export_as_image)
        export_button.pack(side=tk.LEFT, padx=5)

        # Canvas Controls Frame
        canvas_controls_frame = tk.LabelFrame(toolbar, text="Canvas")
        canvas_controls_frame.pack(side=tk.LEFT, padx=10, pady=5)
        clear_button = tk.Button(canvas_controls_frame, text="Clear", command=self.clear_canvas)
        clear_button.pack(side=tk.LEFT, padx=5)

        # Main drawing canvas
        self.canvas = tk.Canvas(main_frame, width=CANVAS_SIZE, height=CANVAS_SIZE, bg="#ffffff", cursor="cross")
        self.canvas.pack()
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        
        # Status Bar for user feedback
        self.status_label = tk.Label(self.root, text="", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
        self.root.bind("<Key>", self.toggle_grid)
        self.root.bind("<Escape>", lambda event: self.close_app())

    def redraw_canvas(self):
        """
        Clears the canvas and redraws all cells based on the current state
        of `self.grid_data`. Also draws grid lines if `self.show_grid` is True.
        """
        self.canvas.delete("all")
        for row in range(ROWS):
            for col in range(COLS):
                x = col * self.cell_size
                y = row * self.cell_size
                cell = self.grid_data[row][col]
                
                if cell['mode'] == "color":
                    self.canvas.create_rectangle(x, y, x + self.cell_size, y + self.cell_size,
                                                 fill=cell['val'], outline="")
                elif cell['mode'] == "image_local":
                    image_key = (cell['mode'], cell['val'])
                    if image_key in self.cell_images:
                        self.canvas.create_image(x, y, anchor='nw', image=self.cell_images[image_key])
                    else:
                        # Draw a placeholder while image is loading
                        self.canvas.create_rectangle(x, y, x + self.cell_size, y + self.cell_size, fill="#e0e0e0", outline="")
        if self.show_grid:
            for x in range(0, CANVAS_SIZE + 1, self.cell_size):
                self.canvas.create_line(x, 0, x, CANVAS_SIZE, fill="#ddd")
            for y in range(0, CANVAS_SIZE + 1, self.cell_size):
                self.canvas.create_line(0, y, CANVAS_SIZE, y, fill="#ddd")

    def handle_canvas_event(self, event):
        """
        Processes a mouse event on the canvas to determine which cell to modify.
        Dispatches to either `fill_area` or `draw_pixel`.
        
        Args:
            event (tk.Event): The mouse event object.
        """
        col = event.x // self.cell_size
        row = event.y // self.cell_size

        if 0 <= col < COLS and 0 <= row < ROWS:
            if self.current_mode == "fill":
                self.fill_area(row, col)
            else:
                self.draw_pixel(row, col)

    def draw_pixel(self, row, col):
        """
        Draws a single pixel at the specified grid coordinates using the
        current brush mode and value.
        
        Args:
            row (int): The row index of the cell.
            col (int): The column index of the cell.
        """
        if self.current_mode == "color":
            self.grid_data[row][col] = {'mode': 'color', 'val': self.current_color}
        elif self.current_mode == "image" and self.current_image_info:
            self.grid_data[row][col] = {'mode': self.current_image_info['type'], 'val': self.current_image_info['val']}
        elif self.current_mode == "erase":
            self.grid_data[row][col] = {'mode': 'color', 'val': '#ffffff'}
        
        self.redraw_canvas()

    def fill_area(self, start_row, start_col):
        """
        Performs a flood-fill algorithm starting from a given cell.
        It replaces all contiguous cells of the same type as the starting cell
        with the current brush content. This is implemented using a breadth-first
        search (BFS) with a deque for optimal performance.
        
        Args:
            start_row (int): The starting row index for the fill.
            start_col (int): The starting column index for the fill.
        """
        target_cell = self.grid_data[start_row][start_col]
        
        if self.current_mode == "color":
            new_content = {'mode': 'color', 'val': self.current_color}
        elif self.current_mode == "image" and self.current_image_info:
            new_content = {'mode': self.current_image_info['type'], 'val': self.current_image_info['val']}
        elif self.current_mode == "erase":
            new_content = {'mode': 'color', 'val': '#ffffff'}
        else:
            self.update_status("Error: Select a brush (color/image) before using the fill tool.")
            return

        # Avoid filling with the same content as the target cell.
        if target_cell == new_content:
            return

        q = deque([(start_row, start_col)])
        self.grid_data[start_row][start_col] = new_content
        
        while q:
            row, col = q.popleft()
            
            # Check the four neighboring cells (up, down, left, right)
            for d_row, d_col in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                n_row, n_col = row + d_row, col + d_col

                if 0 <= n_row < ROWS and 0 <= n_col < COLS and self.grid_data[n_row][n_col] == target_cell:
                    self.grid_data[n_row][n_col] = new_content
                    q.append((n_row, n_col))

        self.redraw_canvas()
        self.update_status("Fill operation complete!")

    def on_mouse_down(self, event):
        """
        Handles the mouse button press event. If the fill tool is not selected,
        it binds the `handle_canvas_event` to the `<B1-Motion>` event for
        continuous drawing.
        """
        if self.current_mode != "fill":
            self.handle_canvas_event(event)
            self.canvas.bind("<B1-Motion>", self.handle_canvas_event)
        else:
            self.handle_canvas_event(event)

    def on_mouse_up(self, event):
        """Unbinds the continuous drawing motion event when the mouse button is released."""
        self.canvas.unbind("<B1-Motion>")

    def toggle_grid(self, event):
        """
        Toggles the visibility of the grid lines on the canvas when the 'g'
        key is pressed.
        
        Args:
            event (tk.Event): The key press event object.
        """
        if event.char.lower() == 'g':
            self.show_grid = not self.show_grid
            self.redraw_canvas()
            self.update_status("Grid lines are now " + ("visible" if self.show_grid else "hidden") + ". Press 'G' to toggle again.")

    def clear_canvas(self):
        """
        Resets the entire canvas to a blank state (all white cells) after
        a confirmation dialog.
        """
        if messagebox.askyesno("Clear Canvas", "Are you sure you want to clear the entire canvas? This cannot be undone."):
            self.grid_data = [[{'mode': 'color', 'val': '#ffffff'} for _ in range(COLS)] for _ in range(ROWS)]
            self.redraw_canvas()
            self.update_status("Canvas cleared.")

    def select_color(self, color):
        """
        Sets the current drawing mode to "color" and updates the selected color.
        
        Args:
            color (str): The hex string of the color to be used.
        """
        self.current_mode = "color"
        self.current_color = color
        self.current_image_info = None
        self.update_status(f"Tool: Pixel, Color: {color}")

    def select_eraser(self):
        """Sets the current drawing mode to "erase" (drawing with a white color)."""
        self.current_mode = "erase"
        self.current_color = "#ffffff"
        self.current_image_info = None
        self.update_status("Tool: Eraser")
    
    def select_fill_tool(self):
        """Sets the current drawing mode to "fill"."""
        self.current_mode = "fill"
        self.update_status("Tool: Fill. Click on an area to fill it.")

    def load_image_brush(self):
        """
        Opens a file dialog for the user to select a local image file.
        The selected image is resized and set as the current brush.
        """
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif")])
        if not file_path:
            return
        
        try:
            img = Image.open(file_path).resize((self.cell_size, self.cell_size), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.current_mode = "image"
            self.current_image_info = {'type': 'image_local', 'val': file_path}
            self.cell_images[('image_local', file_path)] = photo
            self.update_status(f"Tool: Image, File: {os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not load image:\n{e}")

    # The following methods related to online presets have been removed.
    # load_preset_thumbnail, add_thumbnail_to_menu, load_preset_image_brush, update_brush

    def save_canvas(self):
        """Saves the current grid data to a JSON file chosen by the user."""
        file_path = filedialog.asksaveasfilename(defaultextension=".json",
                                                 filetypes=[("JSON files", "*.json")])
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(self.grid_data, f)
                self.update_status(f"Canvas saved to {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save canvas:\n{e}")

    def load_canvas(self, file_path=None):
        """
        Loads grid data from a JSON file. It validates the file's format and
        dimensions before loading and preloads any images referenced in the data.
        """
        if not file_path:
            file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    new_grid_data = json.load(f)
                    if len(new_grid_data) != ROWS or any(len(row) != COLS for row in new_grid_data):
                         raise ValueError("Invalid file format. Grid dimensions do not match.")
                    
                    self.grid_data = new_grid_data
                    self.cell_images.clear()
                    
                    for row in range(ROWS):
                        for col in range(COLS):
                            cell = self.grid_data[row][col]
                            if cell['mode'] == 'image_local' and ('image_local', cell['val']) not in self.cell_images:
                                self.preload_image_from_local(cell['val'])
                    self.redraw_canvas()
                    self.update_status(f"Canvas loaded from {os.path.basename(file_path)}")
            except (IOError, json.JSONDecodeError) as e:
                messagebox.showerror("Error", f"Failed to load canvas. Invalid file or format:\n{e}")
                self.update_status("Failed to load canvas.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load canvas:\n{e}")
                self.update_status("Failed to load canvas.")

    # The `preload_image_from_url`, `cache_and_redraw`, and `handle_preload_error` methods have been removed.
    # The `preload_image_from_local` method is kept and will handle local images.

    def preload_image_from_local(self, file_path):
        """Loads a single image from a local path and caches it."""
        try:
            img = Image.open(file_path).resize((self.cell_size, self.cell_size), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.cell_images[('image_local', file_path)] = photo
            self.redraw_canvas()
        except Exception:
            # Fallback to an empty cell on error
            for r, row in enumerate(self.grid_data):
                for c, cell in enumerate(row):
                    if cell['mode'] == 'image_local' and cell['val'] == file_path:
                        self.grid_data[r][c] = {'mode': 'color', 'val': '#ffffff'}
            self.redraw_canvas()

    def export_as_image(self):
        """
        Exports the current canvas content as a single PNG image file
        to a location chosen by the user.
        """
        file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                 filetypes=[("PNG files", "*.png")])
        if file_path:
            try:
                img = Image.new('RGB', (CANVAS_SIZE, CANVAS_SIZE), 'white')
                draw = ImageDraw.Draw(img)

                for row in range(ROWS):
                    for col in range(COLS):
                        x1 = col * self.cell_size
                        y1 = row * self.cell_size
                        x2 = x1 + self.cell_size
                        y2 = y1 + self.cell_size
                        cell = self.grid_data[row][col]

                        if cell['mode'] == "color":
                            draw.rectangle([x1, y1, x2, y2], fill=cell['val'])
                        elif cell['mode'] == "image_local":
                            image_key = (cell['mode'], cell['val'])
                            if image_key in self.cell_images:
                                cell_img = self.cell_images[image_key]
                                cell_pil_img = ImageTk.getimage(cell_img)
                                img.paste(cell_pil_img, (x1, y1))
                            else:
                                draw.rectangle([x1, y1, x2, y2], fill="#e0e0e0")

                img.save(file_path)
                self.update_status(f"Canvas exported to {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export canvas as image:\n{e}")

    def update_status(self, message):
        """Updates the status bar with the given message."""
        self.status_label.config(text=message)

    def close_app(self):
        """
        Properly shuts down the thread pool and closes the application.
        This is bound to the window close event to ensure a clean exit.
        """
        self.executor.shutdown(wait=False)
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = PixelCanvas(root)
    root.mainloop()
