import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os

from megadetector.detection.run_detector_batch import load_and_run_detector_batch, write_results_to_file
from megadetector.postprocessing.postprocess_batch_results import PostProcessingOptions
from ipyfilechooser import FileChooser
from tkinter import Tk
from tkinter.filedialog import askdirectory
import threading 
import os
from contextlib import redirect_stdout, redirect_stderr
import cv2
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
def draw_detections(detection_data, output_dir, confidence_threshold=0.5):
    """
    Draw red bounding boxes on images for detections above threshold
    
    Args:
        detection_data: List of detection dictionaries
        confidence_threshold: Minimum confidence to draw box
        output_dir: Directory to save output images
    """
    categories = {
        "1" : "animal",
        "2" : "person",
        "3" : "vehicle",
    }

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    for item in detection_data:
        file_path = item['file']
        detections = item['detections']
        
        # Load the image
        img = cv2.imread(file_path)
        if img is None:
            print(f"Could not load image: {file_path}")
            continue
            
        height, width = img.shape[:2]
        
        # Draw bounding boxes for detections above threshold
        for detection in detections:
            conf = detection['conf']
            if conf >= confidence_threshold:
                bbox = detection['bbox']
                category = detection['category']
                
                # Convert normalized coordinates to pixel coordinates
                # bbox format: [x_left, y_top, width, height] (normalized)
                x_left, y_top, box_width, box_height = bbox
                
                x1 = int(x_left * width)
                y1 = int(y_top * height)
                x2 = int((x_left + box_width) * width)
                y2 = int((y_top + box_height) * height)
                
                # Draw red rectangle
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 3)
                
                # Add confidence and category label
                label = f"{categories[category]} {conf:.3f}"
                
                # Calculate text size to position it properly
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 2
                thickness = 2
                (text_width, text_height), baseline = cv2.getTextSize(label, font, font_scale, thickness)
                
                # Position text above the bounding box, but ensure it's within image bounds
                text_x = x1
                text_y = y1 - 10
                
                # If text would be cut off at the top, put it inside the box
                if text_y - text_height < 0:
                    text_y = y1 + text_height + 10
                
                # Ensure text doesn't go beyond image width
                if text_x + text_width > width:
                    text_x = width - text_width
                
                # Draw text background for better visibility
                cv2.rectangle(img, 
                             (text_x - 2, text_y - text_height - 2), 
                             (text_x + text_width + 2, text_y + baseline + 2), 
                             (0, 0, 0), -1)  # Black background
                
                # Draw the text in white for better contrast
                cv2.putText(img, label, (text_x, text_y), 
                           font, font_scale, (255, 255, 255), thickness)
        
        # Save the image with bounding boxes
        filename = Path(file_path).name
        output_path = os.path.join(output_dir, filename)
        
        cv2.imwrite(output_path, img)
        print(f"Saved: {output_path}")



class StreamingTextRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        
    def write(self, string):
        # Use after() to safely update GUI from any thread
        self.text_widget.after(0, self._update_text, string)
        
    def _update_text(self, string):
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)  # Auto-scroll
        self.text_widget.update_idletasks()  # Force immediate update
        
    def flush(self):
        pass  # Required for file-like object

class DetectionInterface:
    def __init__(self, root):
        self.root = root
        self.root.title("MegaDetector Batch Processing")
        self.root.geometry("500x600")
        
        # Variables
        self.slider_var = tk.DoubleVar(value=0.5)
        self.input_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        
        self.results = None


        self.create_widgets()
        
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.rowconfigure(9, weight=1)
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Slider section
        ttk.Label(main_frame, text="Threshold (0-1):").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # Slider
        self.slider = ttk.Scale(
            main_frame, 
            from_=0, 
            to=1, 
            orient=tk.HORIZONTAL, 
            variable=self.slider_var,
            command=self.on_slider_change
        )
        self.slider.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Manual input for slider value
        ttk.Label(main_frame, text="Threshold:").grid(row=2, column=0, sticky=tk.W, pady=(10, 5))
        self.manual_entry = ttk.Entry(main_frame, width=10)
        self.manual_entry.grid(row=2, column=1, sticky=tk.W, pady=(10, 5))
        self.manual_entry.bind('<Return>', self.on_manual_input)
        self.manual_entry.bind('<FocusOut>', self.on_manual_input)
        
        # Update manual entry with initial slider value
        self.manual_entry.insert(0, str(self.slider_var.get()))
        
        ttk.Separator(main_frame, orient='horizontal').grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=20)
        
        ttk.Label(main_frame, text="Input Directory:").grid(row=4, column=0, sticky=tk.W, pady=(0, 5))
        
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        input_frame.columnconfigure(0, weight=1)
        
        self.input_entry = ttk.Entry(input_frame, textvariable=self.input_dir, state='readonly')
        self.input_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(input_frame, text="Browse...", command=self.select_input_dir).grid(row=0, column=1)
        
        ttk.Label(main_frame, text="Output Directory:").grid(row=6, column=0, sticky=tk.W, pady=(0, 5))
        
        output_frame = ttk.Frame(main_frame)
        output_frame.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        output_frame.columnconfigure(0, weight=1)
        
        self.output_entry = ttk.Entry(output_frame, textvariable=self.output_dir, state='readonly')
        self.output_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(output_frame, text="Browse...", command=self.select_output_dir).grid(row=0, column=1)
         
        # Status/info section
        ttk.Separator(main_frame, orient='horizontal').grid(row=8, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=20)
        self.output_text = scrolledtext.ScrolledText(main_frame, height=10, wrap=tk.WORD)
        self.output_text.bind("<Key>", lambda e: "break")  # Disable text editing
        self.output_text.grid(row=9, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))


        self.run_detection = ttk.Button(main_frame, text="Run Detection", command=self.run_detection)
        self.run_detection.grid(row=15, column=0, columnspan=2, pady=(10, 0))

    def on_slider_change(self, value):
        """Update manual entry when slider changes"""
        self.manual_entry.delete(0, tk.END)
        self.manual_entry.insert(0, f"{float(value):.3f}")
        
    def on_manual_input(self, event=None):
        """Update slider when manual input changes"""
        try:
            value = float(self.manual_entry.get())
            if 0 <= value <= 1:
                self.slider_var.set(value)
            else:
                messagebox.showerror("Invalid Input", "Value must be between 0 and 1")
                self.manual_entry.delete(0, tk.END)
                self.manual_entry.insert(0, f"{self.slider_var.get():.3f}")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number")
            self.manual_entry.delete(0, tk.END)
            self.manual_entry.insert(0, f"{self.slider_var.get():.3f}")
            
    def select_input_dir(self):
        """Open directory picker for input directory"""
        directory = filedialog.askdirectory(title="Select Input Directory")
        if directory:
            self.input_dir.set(directory)
            # Auto-generate output directory suggestion
            self.generate_output_dir(directory)
            
    def select_output_dir(self):
        """Open directory picker for output directory"""
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_dir.set(directory)
            
    def generate_output_dir(self, input_path):
        """Generate default output directory path"""
        if input_path:
            parent_dir = os.path.dirname(input_path)
            base_name = os.path.basename(input_path)
            output_path = os.path.join(parent_dir, base_name + "_detections")
            self.output_dir.set(output_path)
    
    def disable_inputs(self):
        """Disable all input fields"""
        self.slider.config(state='disabled')
        self.manual_entry.config(state='disabled')
        self.input_entry.config(state='disabled')
        self.output_entry.config(state='disabled')
        self.run_detection.config(state='disabled')
        self.root.update_idletasks()  # Ensure GUI updates immediately
    def enable_inputs(self):
        """Enable all input fields"""
        self.slider.config(state='normal')
        self.manual_entry.config(state='normal')
        self.input_entry.config(state='normal')
        self.output_entry.config(state='normal')
        self.run_detection.config(state='normal')
        self.root.update_idletasks()

    def run_detection(self):
        input_path = self.input_dir.get()
        output_path = self.output_dir.get()

        def divide_list(lst, n):
            if n > len(lst):
                n = len(lst)
            k, m = divmod(len(lst), n)
            return [lst[i*k + min(i, m):(i+1)*k + min(i+1, m)] for i in range(n)]


        def _run_detection():
            
            redirector = StreamingTextRedirector(self.output_text)
            with redirect_stdout(redirector), redirect_stderr(redirector):
                self.disable_inputs()
                self.results = load_and_run_detector_batch(
                    model_file="MDV5A",
                    image_file_names=input_path,
                    checkpoint_path=os.path.join(output_path, "checkpoint.chkpt"),
                    checkpoint_frequency=1000,
                )
                cores = os.cpu_count() or 1
                split_results = divide_list(self.results, cores)
                confidence = self.slider_var.get()
                with ThreadPoolExecutor(max_workers=cores) as executor:
                    futures = [executor.submit(draw_detections, i, output_path, confidence) for i in split_results]
                    _ = [future.result() for future in futures]
                write_results_to_file(
                    self.results,
                    output_file=os.path.join(output_path, "detections.json"),

                )
                self.enable_inputs()
        thread = threading.Thread(target=_run_detection)
        thread.daemon = True
        thread.start()


    def get_current_values(self):
        """Get current values from the interface"""
        return {
            'threshold': self.slider_var.get(),
            'input_dir': self.input_dir.get(),
            'output_dir': self.output_dir.get()
        }


root = tk.Tk()
app = DetectionInterface(root)

root.mainloop()