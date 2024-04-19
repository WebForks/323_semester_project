import tkinter as tk
from tkinter import filedialog, scrolledtext, font
from drm_analysis import DRMAnalysis
import os
import sys
import io
import time
import threading
import SteamDRMStripper
import download_required
from goldberg_emulator_implementation import GB_Modification

BACKGROUND_COLOR = "#121212"
TEXT_COLOR = "#FFFFFF"
BUTTON_COLOR = "#32CD32"
ACTIVE_BUTTON_COLOR = "#4DFFB8"
FONT_STYLE = "Terminus"


def create_title_label(parent):
    title_font = font.Font(family=FONT_STYLE, size=20)  # Increased font size
    title_label = tk.Label(parent, text="👾 378 Semester Project 👾",
                           bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=title_font)  # Changed text
    title_label.grid(row=0, column=0, columnspan=4,
                     sticky='nsew', padx=10, pady=3)


class PrintLogger(io.StringIO):
    def __init__(self, log_area):
        super().__init__()
        self.log_area = log_area

    def write(self, text):
        self.log_area.insert(tk.END, text)
        self.log_area.yview(tk.END)


# Store the folder_path and game_name globally
folder_path = None
game_name = None
game_file_path = None
steamless_folder_path = None
goldberg_folder_path = None


def check_required_folder():
    '''Checks if the required folders are present. Downloads them if not found.'''

    global steamless_folder_path, goldberg_folder_path
    try:
        # Gets the directory of the current script
        exe_path = os.path.dirname(os.path.abspath(__file__))

        # Check for Steamless folder
        steamless_folder_path = os.path.join(
            exe_path, "Steamless.v3.1.0.3.-.by.atom0s")
        if not os.path.exists(steamless_folder_path):
            log_area.insert(
                tk.END, "Steamless folder not found. Downloading Steamless...\n")
            # Assuming download_required.py is in the same directory as this script
            download_required.download_steamless()
        else:
            log_area.insert(
                tk.END, "Steamless folder found. Skipping Steamless download...\n")

        # Check for Goldberg folder
        goldberg_folder_path = os.path.join(
            exe_path, "Goldberg_Lan_Steam_Emu_v0.2.5")
        if not os.path.exists(goldberg_folder_path):
            log_area.insert(
                tk.END, "Goldberg folder not found. Downloading Goldberg Emulator...\n")
            download_required.download_goldberg()
        else:
            log_area.insert(
                tk.END, "Goldberg folder found. Skipping Goldberg Emulator download...\n")
    except Exception as e:
        log_area.insert(tk.END, f"Error: {e}\n")


def browse_file():
    '''Opens a file dialog to select a game file. Extracts the folder path and game name.'''
    global folder_path, game_name, game_file_path
    game_file_path = filedialog.askopenfilename(
        filetypes=[("Executable files", "*.exe")])
    if game_file_path:
        # Extract the folder path and the game name from the file path
        folder_path = os.path.dirname(game_file_path)
        print("folder_path:", folder_path)
        game_name = os.path.basename(folder_path)
        print("game_name:", game_name)
        path_label.config(text=folder_path)
    else:
        path_label.config(text="No file selected")
        folder_path = None
        game_name = None


def decrypt():
    """Searches pcgamingwikifor info, unpacks() if needed, and emulates()."""

    global game_name
    if not game_name:
        log_area.insert(tk.END, "Please select a folder first.\n")
        return

    log_area.insert(tk.END, f"Analyzing {game_name}...\n")
    drm_analysis = DRMAnalysis(game_name)  # need to look at
    availability_section, denuvo_detected = drm_analysis.get_pcgamingwiki_info()
    if denuvo_detected:
        log_area.insert(tk.END, "Denuvo Anti-Tamper detected.\n")
    elif availability_section:
        analysis_result = drm_analysis.analyze_steam_availability(
            availability_section)

        # Run Steamless if game doesn't use DRM
        if "Doesn't use DRM" not in analysis_result:
            log_area.insert(tk.END, f"Unpacking {game_name}...\n")
            if steamless_folder_path:
                unpacked_file_path = SteamDRMStripper.unpack_with_steamless(
                    game_file_path, steamless_folder_path)
            else:
                log_area.insert(
                    tk.END, "Steamless folder not found. Unable to unpack.\n")

        # Emulate game NEED TO LOOK AT
        if unpacked_file_path:
            emulate(unpacked_file_path)
        else:
            emulate(game_file_path)
        log_area.insert(tk.END, analysis_result)
        print(steamless_folder_path)
        print(goldberg_folder_path)
        print(game_file_path)
        print(game_name)
        log_area.insert(tk.END, "DONE")

    else:
        log_area.insert(
            tk.END, "Availability section not found or failed to retrieve data.\n")

    log_area.yview(tk.END)


def emulate(game_exe_path):
    log_area.insert(tk.END, f"Analyzing bit version of {game_name}...\n")
    gb_analysis = GB_Modification(folder_path, game_name)
    dll_path = gb_analysis.find_game_dll()

    if dll_path is not None:
        dll_basename = os.path.basename(dll_path)

        if dll_basename == "steam_api64.dll":
            log_area.insert(tk.END, "64-bit application\n")
            log_area.insert(tk.END, f"{dll_basename} found at {dll_path}\n")
            log_area.insert(tk.END, f"Preparing to emulate {game_name}...\n")
            gb_analysis.modify_files(
                goldberg_folder_path, dll_path, game_exe_path)
            time.sleep(1)
            SteamDRMStripper.run_unpacked_file(game_exe_path)
        elif dll_basename == "steam_api.dll":
            log_area.insert(tk.END, "32-bit application\n")
            log_area.insert(tk.END, f"{dll_basename} found at {dll_path}\n")
            log_area.insert(tk.END, f"Preparing to emulate {game_name}...\n")
            gb_analysis.modify_files(
                goldberg_folder_path, dll_path, game_exe_path)
            time.sleep(1)
            SteamDRMStripper.run_unpacked_file(game_exe_path)
    else:
        log_area.insert(tk.END, "DLL file not found.\n")
        print("DLL file not found.")
    log_area.yview(tk.END)


'''  TESTING
def unpack():
    global game_name, steamless_folder_path, game_file_path
    if not game_name:
        log_area.insert(tk.END, "Please select a folder first.\n")
        return
    log_area.insert(tk.END, f"Unpacking {game_name}...\n")
    if steamless_folder_path:
        unpacked_file_path = SteamDRMStripper.unpack_with_steamless(
            game_file_path, steamless_folder_path)
    else:
        log_area.insert(
            tk.END, "Steamless folder not found. Unable to unpack.\n")
    log_area.yview(tk.END)
'''


text_font = (FONT_STYLE, 10)
app = tk.Tk()
app.title('Game Folder Selector')
app.configure(bg=BACKGROUND_COLOR)

create_title_label(app)

log_area = scrolledtext.ScrolledText(
    app, width=60, height=40, state='normal', bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=text_font)
log_area.grid(row=1, column=0, columnspan=4, sticky='nsew', padx=10, pady=10)

path_label = tk.Label(app, text="Please Select A Folder",
                      bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=text_font)
path_label.grid(row=2, column=0, columnspan=4, sticky='nsew', padx=10, pady=5)

button_frame = tk.Frame(app, bg=BACKGROUND_COLOR)
button_frame.grid(row=3, column=0, columnspan=4, sticky='ew', padx=10, pady=5)

browse_button = tk.Button(button_frame, text="Browse", command=browse_file, bg=BUTTON_COLOR,
                          fg=TEXT_COLOR, activebackground=ACTIVE_BUTTON_COLOR, activeforeground=TEXT_COLOR, font=text_font)
browse_button.grid(row=0, column=0, padx=30)

decrypt_button = tk.Button(button_frame, text="Decrypt", command=decrypt, bg=BUTTON_COLOR,
                           fg=TEXT_COLOR, activebackground=ACTIVE_BUTTON_COLOR, activeforeground=TEXT_COLOR, font=text_font)
decrypt_button.grid(row=0, column=1, padx=30)

# Testing
# unpack_button = tk.Button(button_frame, text="Unpack", command=unpack)
# unpack_button.grid(row=0, column=2, padx=5)

# goldberg_button = tk.Button(button_frame, text="Emulate", command=emulate)
# goldberg_button.grid(row=0, column=3, padx=5)

log_stream = PrintLogger(log_area)
sys.stdout = log_stream

app.grid_rowconfigure(0, weight=1)
app.grid_columnconfigure(0, weight=1)


# Change at the end of script, before mainloop

thread = threading.Thread(target=check_required_folder)
thread.start()

app.mainloop()
