import ifcopenshell
import ifcopenshell.util.element
import csv
import os
from collections import Counter
from datetime import datetime
import addUser
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import threading

def open_ifc_file(file_path):
    """Opens an IFC file and returns the model instance."""
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        return None
    return ifcopenshell.open(file_path)

def get_elements_by_globalid(ifc_file):
    """Returns a dictionary of IFC elements indexed by their GlobalId."""
    return {el.GlobalId: el for el in ifc_file.by_type("IfcElement")}

def get_user_who_modified(element):
    """Retrieve the user who last modified the element."""
    if element.OwnerHistory and element.OwnerHistory.LastModifiedBy:
        return element.OwnerHistory.LastModifiedBy.Name
    return "Unknown"

def get_timestamp_of_change(element):
    """Retrieve the timestamp of when the element was modified."""
    if element.OwnerHistory and element.OwnerHistory.LastModifiedDate:
        return datetime.utcfromtimestamp(element.OwnerHistory.LastModifiedDate).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    return "Unknown"

def get_added_elements(old_ifc, new_ifc):
    """Finds elements present in the new IFC file but not in the old one."""
    old_elements = set(get_elements_by_globalid(old_ifc).keys())
    new_elements = set(get_elements_by_globalid(new_ifc).keys())

    added_elements = new_elements - old_elements
    return [new_ifc.by_guid(gid) for gid in added_elements]

def get_deleted_elements(old_ifc, new_ifc):
    """Finds elements present in the old IFC file but not in the new one."""
    old_elements = set(get_elements_by_globalid(old_ifc).keys())
    new_elements = set(get_elements_by_globalid(new_ifc).keys())

    deleted_elements = old_elements - new_elements
    return [old_ifc.by_guid(gid) for gid in deleted_elements]

def get_reference_value(element):
    """Gets the 'Reference' property value from an element's property sets."""
    property_sets = ifcopenshell.util.element.get_psets(element)
    return property_sets.get("Pset_BuildingElementProxyCommon", {}).get("Reference", None)

def get_modified_elements(old_ifc, new_ifc):
    """Finds elements that exist in both files but have modified properties."""
    modified_elements = []
    old_elements = get_elements_by_globalid(old_ifc)
    new_elements = get_elements_by_globalid(new_ifc)

    common_elements = old_elements.keys() & new_elements.keys()

    for gid in common_elements:
        old_el = old_elements[gid]
        new_el = new_elements[gid]

        old_reference = get_reference_value(old_el)
        new_reference = get_reference_value(new_el)

        if old_reference != new_reference:
            modified_elements.append((new_el, old_reference, new_reference))

    return modified_elements

def save_ifc_changes_to_csv(added, deleted, modified, filename=None):
    """Saves IFC changes to a CSV file with random user tracking and timestamps."""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ifc_changes_{timestamp}.csv"

    user_changes = Counter()
    element_modifications = Counter()
    timeline_data = []

    with open(filename, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            ["GlobalId", "ChangeType", "OldReference", "NewReference", "User", "Timestamp"]
        )

        for el in added:
            user = addUser.assign_random_user()  # Assign random user
            timestamp = addUser.assign_random_timestamp()  # Assign random timestamp
            writer.writerow([el.GlobalId, "Added", "", "", user, timestamp])

            user_changes[user] += 1
            element_modifications[el.GlobalId] += 1
            timeline_data.append((timestamp, "Added"))

        for el in deleted:
            user = addUser.assign_random_user()  # Assign random user
            timestamp = addUser.assign_random_timestamp()  # Assign random timestamp
            writer.writerow([el.GlobalId, "Deleted", "", "", user, timestamp])

            user_changes[user] += 1
            element_modifications[el.GlobalId] += 1
            timeline_data.append((timestamp, "Deleted"))

        for el, old_ref, new_ref in modified:
            user = addUser.assign_random_user()  # Assign random user
            timestamp = addUser.assign_random_timestamp()  # Assign random timestamp
            writer.writerow([el.GlobalId, "Modified", old_ref, new_ref, user, timestamp])

            user_changes[user] += 1
            element_modifications[el.GlobalId] += 1
            timeline_data.append((timestamp, "Modified"))

    print(f"Change log saved as {filename}")
    save_user_change_summary(user_changes)
    save_element_modifications_summary(element_modifications)
    save_timeline_data(timeline_data)

def save_user_change_summary(user_changes, filename="user_changes_summary.csv"):
    """Saves a summary of changes per user."""
    with open(filename, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["User", "Number of Changes"])
        for user, count in user_changes.items():
            writer.writerow([user, count])

    print(f"User change summary saved as {filename}")

def save_element_modifications_summary(element_modifications, filename="element_modifications_summary.csv"):
    """Saves a summary of the most frequently modified elements."""
    with open(filename, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["GlobalId", "Modification Count"])
        for gid, count in element_modifications.most_common(10):  # Top 10 modified elements
            writer.writerow([gid, count])

    print(f"Element modifications summary saved as {filename}")

def save_timeline_data(timeline_data, filename="modification_timeline.csv"):
    """Saves a timeline of modifications."""
    with open(filename, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Change Type"])
        for timestamp, change_type in sorted(timeline_data):
            writer.writerow([timestamp, change_type])

    print(f"Timeline data saved as {filename}")

class ModificationTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("IFC Modification Tracker")
        self.root.geometry("700x450")
        self.root.configure(padx=20, pady=20)
        
        # File path variables
        self.old_ifc_path = tk.StringVar()
        self.new_ifc_path = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.output_folder.set(os.getcwd())  # Default to current directory
        
        # Create UI elements
        self.create_widgets()
        
    def create_widgets(self):
        # Create frame for file selection
        file_frame = ttk.LabelFrame(self.root, text="File Selection")
        file_frame.pack(fill="x", padx=5, pady=5)
        
        # Old Version IFC
        ttk.Label(file_frame, text="Old Version IFC:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(file_frame, textvariable=self.old_ifc_path, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(file_frame, text="Browse...", command=self.browse_old_ifc).grid(row=0, column=2, padx=5, pady=5)
        
        # New Version IFC
        ttk.Label(file_frame, text="New Version IFC:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(file_frame, textvariable=self.new_ifc_path, width=50).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(file_frame, text="Browse...", command=self.browse_new_ifc).grid(row=1, column=2, padx=5, pady=5)
        
        # Output Folder
        ttk.Label(file_frame, text="Output Folder:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(file_frame, textvariable=self.output_folder, width=50).grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(file_frame, text="Browse...", command=self.browse_output_folder).grid(row=2, column=2, padx=5, pady=5)
        
        # Results frame
        results_frame = ttk.LabelFrame(self.root, text="Results")
        results_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Results text
        self.results_text = tk.Text(results_frame, height=10, state="disabled")
        self.results_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Scrollbar for results
        scrollbar = ttk.Scrollbar(self.results_text, command=self.results_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.results_text.config(yscrollcommand=scrollbar.set)
        
        # Progress bar
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=200, mode="indeterminate")
        self.progress.pack(fill="x", padx=5, pady=5)
        
        # Button frame
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill="x", padx=5, pady=5)
        
        # Run and Close buttons
        ttk.Button(button_frame, text="Run Analysis", command=self.run_analysis).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Close", command=self.root.destroy).pack(side="right", padx=5)
    
    def browse_old_ifc(self):
        filename = filedialog.askopenfilename(
            title="Select Old Version IFC File",
            filetypes=[("IFC Files", "*.ifc"), ("All Files", "*.*")]
        )
        if filename:
            self.old_ifc_path.set(filename)
    
    def browse_new_ifc(self):
        filename = filedialog.askopenfilename(
            title="Select New Version IFC File",
            filetypes=[("IFC Files", "*.ifc"), ("All Files", "*.*")]
        )
        if filename:
            self.new_ifc_path.set(filename)
    
    def browse_output_folder(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder.set(folder)
    
    def log_message(self, message):
        self.results_text.config(state="normal")
        self.results_text.insert(tk.END, message + "\n")
        self.results_text.see(tk.END)
        self.results_text.config(state="disabled")
        self.root.update_idletasks()
    
    def run_analysis(self):
        # Validate inputs
        if not self.old_ifc_path.get() or not self.new_ifc_path.get() or not self.output_folder.get():
            messagebox.showerror("Error", "Please select all required files and folders.")
            return
        
        if not os.path.isfile(self.old_ifc_path.get()):
            messagebox.showerror("Error", "Old IFC file does not exist.")
            return
            
        if not os.path.isfile(self.new_ifc_path.get()):
            messagebox.showerror("Error", "New IFC file does not exist.")
            return
            
        if not os.path.isdir(self.output_folder.get()):
            messagebox.showerror("Error", "Output folder does not exist.")
            return
        
        # Clear results
        self.results_text.config(state="normal")
        self.results_text.delete(1.0, tk.END)
        self.results_text.config(state="disabled")
        
        # Start progress bar
        self.progress.start()
        
        # Run analysis in a separate thread to avoid UI freezing
        threading.Thread(target=self.perform_analysis, daemon=True).start()
    
    def perform_analysis(self):
        try:
            # Set working directory to output folder
            original_dir = os.getcwd()
            os.chdir(self.output_folder.get())
            
            # Open IFC files
            self.log_message("Opening IFC files...")
            old_ifc = open_ifc_file(self.old_ifc_path.get())
            new_ifc = open_ifc_file(self.new_ifc_path.get())
            
            if not old_ifc or not new_ifc:
                self.log_message("Failed to load IFC files. Check if they are valid IFC files.")
                self.progress.stop()
                return
            
            # Get elements
            self.log_message("Analyzing changes...")
            added_elements = get_added_elements(old_ifc, new_ifc)
            deleted_elements = get_deleted_elements(old_ifc, new_ifc)
            modified_elements = get_modified_elements(old_ifc, new_ifc)
            
            # Log results
            self.log_message(f"Found {len(added_elements)} added elements")
            self.log_message(f"Found {len(deleted_elements)} deleted elements")
            self.log_message(f"Found {len(modified_elements)} modified elements")
            
            # Generate timestamp for filenames
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ifc_changes_{timestamp}.csv"
            
            # Save to CSV
            self.log_message("Saving reports...")
            save_ifc_changes_to_csv(added_elements, deleted_elements, modified_elements, 
                                   filename=os.path.join(self.output_folder.get(), filename))
            
            self.log_message("Analysis completed successfully!")
            self.log_message(f"Reports saved to {self.output_folder.get()}")
            
            # Reset working directory
            os.chdir(original_dir)
        except Exception as e:
            self.log_message(f"An error occurred: {e}")
        finally:
            self.progress.stop()

def main():
    root = tk.Tk()
    app = ModificationTrackerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()