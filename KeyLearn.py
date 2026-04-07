import tkinter as tk
from tkinter import ttk, messagebox
import mido
import random
import time
import queue
import matplotlib.pyplot as plt

NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
HANDS = ['Left Hand', 'Right Hand']
FINGERS = ['1 (Thumb)', '2 (Index)', '3 (Middle)', '4 (Ring)', '5 (Pinky)']

class MidiGameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MIDI Note Hunter")
        self.root.geometry("400x550")
        
        # --- THE FIX FOR macOS ---
        # 1. Use the 'clam' theme which plays much nicer with macOS colours
        style = ttk.Style()
        if 'clam' in style.theme_names():
            style.theme_use('clam')
            
        # 2. Create a master frame. Attaching widgets to this stops them vanishing into the dark mode void!
        self.main_frame = ttk.Frame(self.root, padding="20 20 20 20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        # -------------------------

        # State variables
        self.target_note_idx = None
        self.start_time = None
        self.first_hit_time = None
        self.velocities = []
        self.octaves_played = set()
        self.midi_port = None
        self.msg_queue = queue.Queue()

        self.setup_ui()
        self.poll_queue()

    def setup_ui(self):
        # We now attach everything to self.main_frame instead of self.root
        
        # MIDI Device Selection
        ttk.Label(self.main_frame, text="Select MIDI Input:", font=("Helvetica", 12)).pack(anchor=tk.W)
        self.port_var = tk.StringVar()
        self.port_dropdown = ttk.Combobox(self.main_frame, textvariable=self.port_var, state="readonly")
        
        try:
            self.port_dropdown['values'] = mido.get_input_names()
        except Exception as e:
            self.port_dropdown['values'] = []
            print(f"Error finding MIDI ports: {e}")

        self.port_dropdown.pack(fill=tk.X, pady=(0, 15))
        self.port_dropdown.bind('<<ComboboxSelected>>', self.connect_midi)

        if not self.port_dropdown['values']:
            self.port_dropdown.set("No MIDI devices found!")
        else:
            self.port_dropdown.current(0)
            self.connect_midi()

        # Toggles
        self.use_hand_var = tk.BooleanVar(value=False)
        self.use_finger_var = tk.BooleanVar(value=False)
        
        ttk.Checkbutton(self.main_frame, text="Suggest Hand (L/R)", variable=self.use_hand_var).pack(anchor=tk.W)
        ttk.Checkbutton(self.main_frame, text="Suggest Finger (1-5)", variable=self.use_finger_var).pack(anchor=tk.W, pady=(0, 15))

        # Big Display
        self.note_label = ttk.Label(self.main_frame, text="Ready?", font=("Helvetica", 48, "bold"))
        self.note_label.pack(pady=20)

        self.instruction_label = ttk.Label(self.main_frame, text="", font=("Helvetica", 16))
        self.instruction_label.pack(pady=5)

        # Stats
        self.time_label = ttk.Label(self.main_frame, text="Reaction Time: --", font=("Helvetica", 12))
        self.time_label.pack(pady=5)
        
        self.octave_label = ttk.Label(self.main_frame, text="Octaves Found: 0", font=("Helvetica", 12))
        self.octave_label.pack(pady=5)

        # Buttons
        self.next_btn = ttk.Button(self.main_frame, text="Give me a Note!", command=self.next_note)
        self.next_btn.pack(fill=tk.X, pady=(20, 10))

        self.hist_btn = ttk.Button(self.main_frame, text="Show Velocity Histogram", command=self.show_histogram, state=tk.DISABLED)
        self.hist_btn.pack(fill=tk.X)
        
        # Force a visual update
        self.root.update_idletasks()

    def connect_midi(self, event=None):
        port_name = self.port_var.get()
        if self.midi_port:
            self.midi_port.close()
        try:
            self.midi_port = mido.open_input(port_name, callback=self.midi_callback)
        except Exception as e:
            messagebox.showerror("MIDI Error", f"Could not connect to {port_name}.\n{e}")

    def midi_callback(self, msg):
        if msg.type == 'note_on' and msg.velocity > 0:
            self.msg_queue.put(msg)

    def poll_queue(self):
        while not self.msg_queue.empty():
            msg = self.msg_queue.get()
            self.process_midi_msg(msg)
        self.root.after(50, self.poll_queue)

    def process_midi_msg(self, msg):
        if self.target_note_idx is None:
            return

        note_idx = msg.note % 12
        octave = (msg.note // 12) - 1

        if note_idx == self.target_note_idx:
            # First hit logic
            if self.first_hit_time is None:
                self.first_hit_time = time.time()
                reaction = self.first_hit_time - self.start_time
                self.time_label.config(text=f"Reaction Time: {reaction:.2f} seconds")
                # We use a hex colour code here as it's more reliable across themes
                self.note_label.config(foreground="#008000") 

            # Track velocity and octaves
            self.velocities.append(msg.velocity)
            self.octaves_played.add(octave)
            
            self.octave_label.config(text=f"Octaves Found: {len(self.octaves_played)}")
            
            # Enable histogram button once we have data
            if len(self.velocities) > 0:
                self.hist_btn.config(state=tk.NORMAL)

    def next_note(self):
        self.target_note_idx = random.randint(0, 11)
        target_note_name = NOTES[self.target_note_idx]
        
        # Reset colour to standard text colour for the current theme
        self.note_label.config(text=target_note_name, foreground="")
        
        instructions = []
        if self.use_hand_var.get():
            instructions.append(random.choice(HANDS))
        if self.use_finger_var.get():
            instructions.append(random.choice(FINGERS))
            
        self.instruction_label.config(text=" | ".join(instructions))
        
        # Reset stats
        self.start_time = time.time()
        self.first_hit_time = None
        self.velocities = []
        self.octaves_played = set()
        
        self.time_label.config(text="Reaction Time: --")
        self.octave_label.config(text="Octaves Found: 0")
        self.hist_btn.config(state=tk.DISABLED)

    def show_histogram(self):
        if not self.velocities:
            return
            
        plt.figure(figsize=(8, 5))
        plt.hist(self.velocities, bins=range(0, 130, 5), color='teal', edgecolor='black')
        plt.title(f"Velocity Histogram for {NOTES[self.target_note_idx]}")
        plt.xlabel("MIDI Velocity (0-127)")
        plt.ylabel("Number of Hits")
        plt.xlim(0, 127)
        plt.grid(axis='y', alpha=0.75)
        plt.show()

if __name__ == "__main__":
    root = tk.Tk()
    app = MidiGameApp(root)
    root.mainloop()