import tkinter as tk
from tkinter import filedialog, messagebox, font, PhotoImage
import json
import os
from appdirs import user_config_dir # Import user_config_dir

# ---------------------------------------------------
# INSTALL APPDIRS OR ELSE THIS PROGRAM WILL NOT WORK
# ---------------------------------------------------

# Define application details for appdirs
APP_NAME = "ArkEditor"
APP_AUTHOR = "Ark360" 

# Construct the config file path using user_config_dir
config_dir = user_config_dir(APP_NAME, APP_AUTHOR)
os.makedirs(config_dir, exist_ok=True) # Ensure the directory exists
CONFIG_FILE = os.path.join(config_dir, "config.json")

# Load and save config functions
def load_config():
    try:
        with open(CONFIG_FILE, "r") as file:
            config = json.load(file)
            if "dark_mode" not in config:
                config["dark_mode"] = False
            return config
    except FileNotFoundError:
        # Default configuration if file doesn't exist
        return {"save_hotkey": "<Control-s>", "exit_hotkey": "<Control-q>", "emoji_hotkey": "<Control-i>",
                "font": "Arial", "font_size": 12, "dark_mode": False}
    except Exception as e:
        messagebox.showerror("Error loading config", f"Could not load configuration: {e}\nUsing default settings.")
        return {"save_hotkey": "<Control-s>", "exit_hotkey": "<Control-q>", "emoji_hotkey": "<Control-i>",
                "font": "Arial", "font_size": 12, "dark_mode": False}


def save_config():
    try:
        with open(CONFIG_FILE, "w") as file:
            json.dump(config, file, indent=4) # Added indent for readability
    except Exception as e:
        messagebox.showerror("Error saving config", f"Could not save configuration: {e}")


def toggle_dark_mode():
    config["dark_mode"] = not config["dark_mode"]
    apply_theme()
    save_config()


def apply_theme():
    if config.get("dark_mode", False):
        root.configure(bg="#2E2E2E")
        text_area.configure(bg="#1E1E1E", fg="#FFFFFF", insertbackground="white")
    else:
        root.configure(bg="lightgray")
        text_area.configure(bg="white", fg="black", insertbackground="black")


def on_close():
    if text_area.edit_modified():
        if messagebox.askyesno("Unsaved Work", "You have unsaved changes. Do you want to save before exiting?"):
            if not save_file():  # If save_file returns false, the user canceled the save and should not exit.
                return
    save_config()
    root.destroy()

def show_about():
    about_window = tk.Toplevel(root)
    about_window.title("About Arc Editor")
    about_window.geometry("300x200")

    try:
        # Note: PhotoImage requires a file path; ensure 'icon.png' is accessible
        # Consider packaging this with your application or placing it in the config_dir
        icon_image = PhotoImage(file="icon.png")
        icon_label = tk.Label(about_window, image=icon_image)
        icon_label.image = icon_image  # Keep reference
        icon_label.pack()
    except Exception as e:
        print("Error loading image:", e)
        icon_label = tk.Label(about_window, text="📄", font=("Arial", 50))
        icon_label.pack()

    message_label = tk.Label(about_window,
                             text="Arc Editor\nA simple text editor that uses .arc files\nCreated in Python using Tkinter",
                             justify="center")
    message_label.pack()


def apply_hotkeys():
    # Unbind previous hotkeys to prevent multiple bindings if apply_hotkeys is called multiple times
    root.unbind_all(config.get("save_hotkey", "<Control-s>"))
    root.unbind_all(config.get("exit_hotkey", "<Control-q>"))
    root.unbind_all(config.get("emoji_hotkey", "<Control-i>"))

    root.bind(config["save_hotkey"], lambda event: save_file())
    root.bind(config["exit_hotkey"], lambda event: on_close())
    root.bind(config["emoji_hotkey"], lambda event: open_emoji_window())
    root.bind("<Control-minus>", decrease_font_size)
    root.bind("<Control-plus>", increase_font_size)
    root.bind("<Control-equal>", increase_font_size)


def increase_font_size(event=None):
    config["font_size"] += 1
    text_area.configure(font=(config["font"], config["font_size"]))
    save_config()


def decrease_font_size(event=None):
    if config["font_size"] > 6:
        config["font_size"] -= 1
        text_area.configure(font=(config["font"], config["font_size"]))
        save_config()


def open_file():
    global current_file
    file_path = filedialog.askopenfilename(filetypes=[("Arc Files", "*.arc")])
    if file_path:
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                text_area.delete(1.0, tk.END)
                text_area.insert(tk.END, file.read())
            current_file = file_path
            root.title(f"{file_path} - Arc Editor")
            text_area.edit_modified(False) # File is just loaded, so no modifications yet
        except UnicodeDecodeError:  # Try cp1252 as a fallback
            try:
                with open(file_path, "r", encoding="cp1252") as file:
                    text_area.delete(1.0, tk.END)
                    text_area.insert(tk.END, file.read())
                current_file = file_path
                root.title(f"{file_path} - Arc Editor")
                text_area.edit_modified(False)
                messagebox.showwarning("Encoding Warning", "The file was opened using cp1252 encoding. Some characters might not display correctly. It is recommended to save the file as UTF-8.")
            except UnicodeDecodeError as e:
                messagebox.showerror("Encoding Error", f"The file could not be opened.  Tried UTF-8 and cp1252. Unknown encoding.")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred while opening: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while opening: {e}")


def save_file():
    global current_file
    if current_file:
        try:
            with open(current_file, "w", encoding="utf-8") as file:
                file.write(text_area.get(1.0, tk.END))
            text_area.edit_modified(False)  # Reset the modified flag *immediately* after the save
            return True
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while saving: {e}")
            return False
    else:
        return save_file_as()

def save_file_as():
    global current_file
    file_path = filedialog.asksaveasfilename(defaultextension=".arc", filetypes=[("Arc Files", "*.arc")])
    if file_path:
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(text_area.get(1.0, tk.END))
            current_file = file_path
            root.title(f"{file_path} - Arc Editor")
            text_area.edit_modified(False)  # Reset the modified flag *immediately* after the save
            return True
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while saving: {e}")
            return False
    return False

def open_emoji_window():
    """Opens a window for emoji selection."""
    emoji_window = tk.Toplevel(root)
    emoji_window.title("Emoji Picker")
    emoji_window.geometry("400x300")  # Set initial window size

    # Use a Canvas for better layout control (optional but recommended)
    emoji_canvas = tk.Canvas(emoji_window)
    emoji_canvas.pack(fill=tk.BOTH, expand=True)

    emojis = ["😀", "😂", "😍", "👍", "❤️", "😊", "😎", "🤩", "🤔", "😴", "🥳", "🤯", "😇", "😈", "💩"] #More Emojis

    button_size = 40  # Set button size
    columns = 5 #Number of columns

    for i, emoji in enumerate(emojis):
        row = i // columns
        col = i % columns
        x_pos = col * button_size + 5 # adds padding
        y_pos = row * button_size + 5

        emoji_button = tk.Button(emoji_canvas, text=emoji, font=("Arial", 20), command=lambda e=emoji: insert_emoji(e)) # Increased font size
        emoji_button.place(x=x_pos, y=y_pos, width=button_size - 10, height=button_size - 10) #Uses place to allow for better control of the grid


def insert_emoji(emoji):
    text_area.insert(tk.INSERT, emoji) #inserts emoji at the current cursor position


def open_preferences():
    global save_hotkey_entry, exit_hotkey_entry, emoji_hotkey_entry, font_var

    preferences_window = tk.Toplevel(root)
    preferences_window.title("Preferences")
    preferences_window.geometry("400x250")

    tk.Label(preferences_window, text="Save Hotkey:").pack()
    save_hotkey_entry = tk.Entry(preferences_window)
    save_hotkey_entry.insert(0, config["save_hotkey"])
    save_hotkey_entry.pack()

    tk.Label(preferences_window, text="Exit Hotkey:").pack()
    exit_hotkey_entry = tk.Entry(preferences_window)
    exit_hotkey_entry.insert(0, config["exit_hotkey"])
    exit_hotkey_entry.pack()

    tk.Label(preferences_window, text="Emoji Picker Hotkey:").pack()
    emoji_hotkey_entry = tk.Entry(preferences_window)
    emoji_hotkey_entry.insert(0, config["emoji_hotkey"])
    emoji_hotkey_entry.pack()

    tk.Label(preferences_window, text="Font:").pack()
    font_var = tk.StringVar(value=config["font"])
    font_dropdown = tk.OptionMenu(preferences_window, font_var, *font.families(), command=lambda _: change_font())
    font_dropdown.pack()

    tk.Button(preferences_window, text="Apply", command=update_hotkeys).pack(pady=10)


def change_font():
    config["font"] = font_var.get()
    text_area.configure(font=(config["font"], config["font_size"]))
    save_config()


def update_hotkeys():
    config["save_hotkey"] = save_hotkey_entry.get()
    config["exit_hotkey"] = exit_hotkey_entry.get()
    config["emoji_hotkey"] = emoji_hotkey_entry.get()
    apply_hotkeys()
    save_config()


root = tk.Tk()
root.title("Untitled - Arc Editor")
root.geometry("600x400")
root.protocol("WM_DELETE_WINDOW", on_close)

config = load_config()
current_file = None
# The 'is_saved' flag is effectively managed by text_area.edit_modified()
# and the save_file/save_file_as functions. It can be removed or used for other purposes
# but is not strictly necessary for the core save logic as currently implemented.
# is_saved = True # This line can be removed as it's not being actively used or updated.

menu_bar = tk.Menu(root)
file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Open", command=open_file)
file_menu.add_command(label="Save", command=save_file)
file_menu.add_command(label="Save As", command=save_file_as)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=on_close)
menu_bar.add_cascade(label="File", menu=file_menu)

preferences_menu = tk.Menu(menu_bar, tearoff=0)
preferences_menu.add_command(label="Preferences", command=open_preferences)
preferences_menu.add_command(label="Toggle Dark Mode", command=toggle_dark_mode)
menu_bar.add_cascade(label="Preferences", menu=preferences_menu)

about_menu = tk.Menu(menu_bar, tearoff=0)
about_menu.add_command(label="About", command=show_about)
menu_bar.add_cascade(label="About", menu=about_menu)

root.config(menu=menu_bar)

text_area = tk.Text(root, wrap="word", undo=True, font=(config["font"], config["font_size"]))
text_area.pack(expand=True, fill="both")
apply_hotkeys()
apply_theme()
root.mainloop()
