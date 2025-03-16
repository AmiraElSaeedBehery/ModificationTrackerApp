import tkinter as tk
from tkinter import filedialog, ttk
import threading
import time
import os

COLORS = {
    "background": "#2c3e50",  
    "frame_bg": "#34495E",    
    "text": "#E0E0E0",        
    "entry_bg": "#455A64",    
    "entry_fg": "#FFFFFF",    
    "button_blue": "#1976D2",  
    "button_green": "#2E7D32", 
    "button_red": "#C62828",   
    "progress_bg": "#424242",  
    "progress_fg": "#66BB6A"  
}

class ModificationTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("IFC Modification Tracker")
        self.root.geometry("750x450")
        self.root.configure(bg=COLORS["background"])

        self.old_ifc_path = tk.StringVar()
        self.new_ifc_path = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.output_folder.set(os.getcwd())

        self.create_styles()
        self.create_widgets()

    def create_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Blue.TButton", font=("Segoe UI", 10), padding=6, background=COLORS["button_blue"], foreground="white")
        style.configure("Green.TButton", font=("Segoe UI", 12, "bold"), padding=10, background=COLORS["button_green"], foreground="white")
        style.configure("Red.TButton", font=("Segoe UI", 12, "bold"), padding=10, background=COLORS["button_red"], foreground="white")
        style.configure("TProgressbar", troughcolor=COLORS["progress_bg"], background=COLORS["progress_fg"])

    def create_widgets(self):
        """Create UI layout with proper alignment and button positioning."""
        file_frame = tk.Frame(self.root, bg=COLORS["frame_bg"], padx=10, pady=10)
        file_frame.pack(fill="x", padx=15, pady=10)
        ttk.Label(file_frame, text="📁 File Selection", background=COLORS["frame_bg"], foreground=COLORS["text"]).pack(anchor="w")
        self.create_file_selection(file_frame)
        results_frame = tk.Frame(self.root, bg=COLORS["frame_bg"], padx=10, pady=10)
        results_frame.pack(fill="both", expand=True, padx=15, pady=10)
        ttk.Label(results_frame, text="📊 Results", background=COLORS["frame_bg"], foreground=COLORS["text"]).pack(anchor="w")
        self.create_results_section(results_frame)
        self.progress = ttk.Progressbar(self.root, orient="horizontal", mode="determinate", length=300)
        self.progress.pack(fill="x", padx=15, pady=5)
        button_frame = tk.Frame(self.root, bg=COLORS["background"])
        button_frame.pack(fill="x", padx=15, pady=5)
        run_btn = ttk.Button(button_frame, text="🔍 Run Analysis", style="Green.TButton", command=self.run_analysis)
        run_btn.pack(side="left", padx=5, pady=5, ipadx=20, ipady=10, expand=True)
        close_btn = ttk.Button(button_frame, text="❌ Close", style="Red.TButton", command=self.root.destroy)
        close_btn.pack(side="right", padx=5, pady=5, ipadx=20, ipady=10, expand=True)

    def create_file_selection(self, parent):
        labels = ["Old IFC File:", "New IFC File:", "Output Folder:"]
        commands = [self.browse_old_ifc, self.browse_new_ifc, self.browse_output_folder]
        text_vars = [self.old_ifc_path, self.new_ifc_path, self.output_folder]

        for i in range(3):
            row_frame = tk.Frame(parent, bg=COLORS["frame_bg"])
            row_frame.pack(fill="x", padx=5, pady=5)
            ttk.Label(row_frame, text=labels[i], width=12, anchor="w", background=COLORS["frame_bg"], foreground=COLORS["text"]).pack(side="left", padx=5)
            ttk.Entry(row_frame, textvariable=text_vars[i], width=60).pack(side="left", padx=5, fill="x", expand=True)
            ttk.Button(row_frame, text="Browse...", style="Blue.TButton", command=commands[i], width=10).pack(side="left", padx=5)

    def create_results_section(self, parent):
        self.results_text = tk.Text(parent, height=5, state="disabled", wrap="word", bg=COLORS["entry_bg"], fg=COLORS["text"])
        self.results_text.pack(fill="both", expand=True, padx=5, pady=5)

    def browse_old_ifc(self):
        filename = filedialog.askopenfilename(filetypes=[("IFC Files", "*.ifc")])
        if filename:
            self.old_ifc_path.set(filename)

    def browse_new_ifc(self):
        filename = filedialog.askopenfilename(filetypes=[("IFC Files", "*.ifc")])
        if filename:
            self.new_ifc_path.set(filename)

    def browse_output_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder.set(folder)

    def log_message(self, message):
        self.results_text.config(state="normal")
        self.results_text.insert(tk.END, message + "\n")
        self.results_text.see(tk.END)
        self.results_text.config(state="disabled")
        self.root.update_idletasks()

    def run_analysis(self):
        self.progress["value"] = 0
        self.progress["maximum"] = 100
        threading.Thread(target=self.perform_analysis, daemon=True).start()

    def perform_analysis(self):
        for i in range(1, 101, 10):
            time.sleep(0.3)
            self.progress["value"] = i
            self.root.update_idletasks()
        self.log_message("✅ Analysis completed successfully!")

if __name__ == "__main__":
    root = tk.Tk()
    app = ModificationTrackerApp(root)
    root.mainloop()