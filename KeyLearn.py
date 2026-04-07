import tkinter as tk
from tkinter import ttk, messagebox
import mido
import random
import time
import queue
import os
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
HANDS = ['Left Hand', 'Right Hand']
FINGERS = ['1 (Thumb)', '2 (Index)', '3 (Middle)', '4 (Ring)', '5 (Pinky)']

# Dark Theme Colours
BG_COLOUR = '#282C34'
TEXT_COLOUR = '#ABB2BF'
ACCENT_COLOUR = '#98C379' # A nice green for correct notes
ERROR_COLOUR = '#E06C75'  # Red for incorrect notes

class MidiGameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MIDI Note Hunter Pro")
        self.root.geometry("600x850") # Taller to fit the embedded graph
        self.root.configure(bg=BG_COLOUR)
        
        # Configure the theme for a proper dark mode look
        style = ttk.Style()
        if 'clam' in style.theme_names():
            style.theme_use('clam')
            style.configure('.', background=BG_COLOUR, foreground=TEXT_COLOUR)
            style.configure('TLabel', background=BG_COLOUR, foreground=TEXT_COLOUR)
            style.configure('TCheckbutton', background=BG_COLOUR, foreground=TEXT_COLOUR, selectcolor=BG_COLOUR)
            style.configure('TButton', background='#3E4451', foreground=TEXT_COLOUR)

        self.main_frame = ttk.Frame(self.root, padding="20 20 20 20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # State variables
        self.target_note_idx = None
        self.start_time = None
        self.first_hit_time = None
        self.hit_history = [] # Will store dicts: {'type': 'correct'/'wrong', 'velocity': int}
        self.octaves_played = set()
        self.midi_port = None
        self.msg_queue = queue.Queue()

        self.setup_ui()
        self.poll_queue()

    def setup_ui(self):
        # --- Controls Section ---
        controls_frame = ttk.Frame(self.main_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(controls_frame, text="Select MIDI Input:", font=("Helvetica", 12)).pack(anchor=tk.W)
        self.port_var = tk.StringVar()
        self.port_dropdown = ttk.Combobox(controls_frame, textvariable=self.port_var, state="readonly")
        
        try:
            self.port_dropdown['values'] = mido.get_input_names()
        except Exception as e:
            self.port_dropdown['values'] = []

        self.port_dropdown.pack(fill=tk.X, pady=(5, 10))
        self.port_dropdown.bind('<<ComboboxSelected>>', self.connect_midi)

        if not self.port_dropdown['values']:
            self.port_dropdown.set("No MIDI devices found!")
        else:
            self.port_dropdown.current(0)
            self.connect_midi()

        # Toggles
        self.use_hand_var = tk.BooleanVar(value=False)
        self.use_finger_var = tk.BooleanVar(value=False)
        self.show_wrong_var = tk.BooleanVar(value=False)
        
        ttk.Checkbutton(controls_frame, text="Suggest Hand (L/R)", variable=self.use_hand_var).pack(anchor=tk.W)
        ttk.Checkbutton(controls_frame, text="Suggest Finger (1-5)", variable=self.use_finger_var).pack(anchor=tk.W)
        ttk.Checkbutton(controls_frame, text="Show Incorrect Notes on Graph", variable=self.show_wrong_var, command=self.update_plot).pack(anchor=tk.W, pady=(10, 0))

        # --- Display Section ---
        self.note_label = tk.Label(self.main_frame, text="Ready?", font=("Helvetica", 54, "bold"), bg=BG_COLOUR, fg=TEXT_COLOUR)
        self.note_label.pack(pady=10)

        self.instruction_label = ttk.Label(self.main_frame, text="", font=("Helvetica", 16))
        self.instruction_label.pack(pady=5)

        # Stats
        stats_frame = ttk.Frame(self.main_frame)
        stats_frame.pack(fill=tk.X, pady=10)
        
        self.time_label = ttk.Label(stats_frame, text="Reaction Time: --", font=("Helvetica", 12))
        self.time_label.pack(side=tk.LEFT, expand=True)
        
        self.octave_label = ttk.Label(stats_frame, text="Octaves Found: 0", font=("Helvetica", 12))
        self.octave_label.pack(side=tk.RIGHT, expand=True)

        self.next_btn = ttk.Button(self.main_frame, text="Give me a Note!", command=self.next_note)
        self.next_btn.pack(fill=tk.X, pady=(10, 20))

        # --- Embedded Matplotlib Graph ---
        self.fig = Figure(figsize=(5, 3), dpi=100)
        self.fig.patch.set_facecolor(BG_COLOUR) # Match the Tkinter background
        
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#1E2227') # Slightly darker for the graph area
        self.ax.tick_params(colors=TEXT_COLOUR)
        self.ax.xaxis.label.set_color(TEXT_COLOUR)
        self.ax.yaxis.label.set_color(TEXT_COLOUR)
        self.ax.title.set_color(TEXT_COLOUR)
        
        # Hide the top and right spines for a cleaner look
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['bottom'].set_color(TEXT_COLOUR)
        self.ax.spines['left'].set_color(TEXT_COLOUR)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.main_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.update_plot() # Initialize empty plot

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
                self.note_label.config(fg=ACCENT_COLOUR)

            # Track correct hit
            self.hit_history.append({'type': 'correct', 'velocity': msg.velocity})
            self.octaves_played.add(octave)
            self.octave_label.config(text=f"Octaves Found: {len(self.octaves_played)}")
            
        else:
            # Track incorrect hit and play system beep
            self.hit_history.append({'type': 'wrong', 'velocity': msg.velocity})
            # Uses macOS native audio player. '&' makes it run in the background so the GUI doesn't freeze
            os.system("afplay /System/Library/Sounds/Basso.aiff &")
            
        self.update_plot()

    def next_note(self):
        self.target_note_idx = random.randint(0, 11)
        target_note_name = NOTES[self.target_note_idx]
        
        self.note_label.config(text=target_note_name, fg=TEXT_COLOUR)
        
        instructions = []
        if self.use_hand_var.get():
            instructions.append(random.choice(HANDS))
        if self.use_finger_var.get():
            instructions.append(random.choice(FINGERS))
            
        self.instruction_label.config(text=" | ".join(instructions))
        
        # Reset stats
        self.start_time = time.time()
        self.first_hit_time = None
        self.hit_history = []
        self.octaves_played = set()
        
        self.time_label.config(text="Reaction Time: --")
        self.octave_label.config(text="Octaves Found: 0")
        
        self.update_plot()

    def update_plot(self):
        self.ax.clear()
        self.ax.set_title("Live Velocity Tracking", pad=10)
        self.ax.set_ylim(0, 130)
        self.ax.set_ylabel("Velocity")
        self.ax.set_xlabel("Hit Sequence")
        
        show_wrong = self.show_wrong_var.get()
        
        x_correct = []
        y_correct = []
        x_wrong = []
        y_wrong = []
        
        # Parse history to separate correct and wrong notes by their absolute index
        for i, hit in enumerate(self.hit_history):
            hit_index = i + 1
            if hit['type'] == 'correct':
                x_correct.append(hit_index)
                y_correct.append(hit['velocity'])
            elif hit['type'] == 'wrong' and show_wrong:
                x_wrong.append(hit_index)
                y_wrong.append(hit['velocity'])
                
        # Plot correct hits (connected by a subtle line to see the trend)
        if x_correct:
            self.ax.plot(x_correct, y_correct, color=ACCENT_COLOUR, alpha=0.4, zorder=1)
            self.ax.scatter(x_correct, y_correct, color=ACCENT_COLOUR, s=50, zorder=2, label="Target Note")
            
        # Plot incorrect hits
        if x_wrong:
            self.ax.scatter(x_wrong, y_wrong, color=ERROR_COLOUR, s=50, marker='x', zorder=3, label="Missed Note")
            
        if x_correct or x_wrong:
            self.ax.legend(loc="lower right", facecolor=BG_COLOUR, edgecolor=TEXT_COLOUR, labelcolor=TEXT_COLOUR)
            
        # Force integer ticks on the X axis so it doesn't show "Hit 1.5"
        self.ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
        
        self.canvas.draw()

if __name__ == "__main__":
    # We import pyplot here just for the locator utility, but we don't use it to draw windows anymore
    import matplotlib.pyplot as plt 
    root = tk.Tk()
    app = MidiGameApp(root)
    root.mainloop()