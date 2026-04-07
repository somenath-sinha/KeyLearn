import tkinter as tk
from tkinter import ttk, messagebox
import mido
import random
import time
import queue
import os
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import MaxNLocator

NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
HANDS = ['Left Hand', 'Right Hand']
FINGERS = ['1 (Thumb)', '2 (Index)', '3 (Middle)', '4 (Ring)', '5 (Pinky)']

# Dark Theme Colours
BG_COLOUR = '#282C34'
TEXT_COLOUR = '#ABB2BF'
ACCENT_COLOUR = '#98C379' 
ERROR_COLOUR = '#E06C75'  
TOGGLE_OFF = '#3E4451'
TOGGLE_ON = '#61AFEF'

class MidiGameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MIDI Note Hunter Pro")
        self.root.geometry("600x850") 
        self.root.configure(bg=BG_COLOUR)
        
        # Configure theme to stamp out that weird cream hover colour
        style = ttk.Style()
        if 'clam' in style.theme_names():
            style.theme_use('clam')
            style.configure('.', background=BG_COLOUR, foreground=TEXT_COLOUR)
            style.configure('TLabel', background=BG_COLOUR, foreground=TEXT_COLOUR)
            
            # Standard button style
            style.configure('TButton', background=TOGGLE_OFF, foreground=TEXT_COLOUR, borderwidth=0)
            style.map('TButton', background=[('active', '#5c6370')])
            
            # Highlighted toggle button style
            style.configure('Toggle.TButton', background=TOGGLE_ON, foreground='#ffffff', font=('Helvetica', 10, 'bold'))
            style.map('Toggle.TButton', background=[('active', '#4D8BBE')])

        self.main_frame = ttk.Frame(self.root, padding="20 20 20 20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # State variables
        self.target_note_idx = None
        self.start_time = None
        self.first_hit_time = None
        self.last_hit_time = None
        self.reaction_intervals = []
        self.hit_history = [] 
        self.octaves_played = set()
        self.midi_port = None
        self.msg_queue = queue.Queue()

        self.setup_ui()
        
        # Bind the spacebar to the 'Give me a note' function
        self.root.bind('<space>', lambda event: self.next_note())
        
        # Auto-connect to the first available MIDI port in the background
        available_ports = mido.get_input_names()
        if available_ports:
            self.connect_midi(available_ports[0])

        self.poll_queue()

    def setup_ui(self):
        # --- Header Section ---
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 1. Devices Button tucked away in the top right
        self.devices_btn = ttk.Button(header_frame, text="⚙ MIDI Devices", command=self.open_devices_window)
        self.devices_btn.pack(side=tk.RIGHT)

        # --- Inline Toggles Section ---
        self.use_hand_var = tk.BooleanVar(value=False)
        self.use_finger_var = tk.BooleanVar(value=False)
        self.show_wrong_var = tk.BooleanVar(value=False)

        toggles_frame = ttk.Frame(self.main_frame)
        toggles_frame.pack(fill=tk.X, pady=(0, 10))

        self.hand_btn = ttk.Button(toggles_frame, text="Hand: OFF", command=lambda: self.toggle_btn(self.use_hand_var, self.hand_btn, "Hand"))
        self.hand_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.finger_btn = ttk.Button(toggles_frame, text="Finger: OFF", command=lambda: self.toggle_btn(self.use_finger_var, self.finger_btn, "Finger"))
        self.finger_btn.pack(side=tk.LEFT)

        # --- Display Section ---
        self.note_label = tk.Label(self.main_frame, text="Ready?", font=("Helvetica", 54, "bold"), bg=BG_COLOUR, fg=TEXT_COLOUR)
        self.note_label.pack(pady=10)

        self.instruction_label = ttk.Label(self.main_frame, text="Press Spacebar to start", font=("Helvetica", 16))
        self.instruction_label.pack(pady=5)

        # --- Stats Section ---
        stats_frame = ttk.Frame(self.main_frame)
        stats_frame.pack(fill=tk.X, pady=10)
        
        self.time_label = ttk.Label(stats_frame, text="1st Hit: --", font=("Helvetica", 12))
        self.time_label.pack(side=tk.LEFT, expand=True)
        
        # New Average Interval Label
        self.avg_time_label = ttk.Label(stats_frame, text="Avg Interval: --", font=("Helvetica", 12))
        self.avg_time_label.pack(side=tk.LEFT, expand=True)
        
        self.octave_label = ttk.Label(stats_frame, text="Octaves: 0", font=("Helvetica", 12))
        self.octave_label.pack(side=tk.RIGHT, expand=True)

        self.next_btn = ttk.Button(self.main_frame, text="Give me a Note! (Spacebar)", command=self.next_note)
        self.next_btn.pack(fill=tk.X, pady=(10, 20))

        # --- Graph Controls ---
        graph_ctrl_frame = ttk.Frame(self.main_frame)
        graph_ctrl_frame.pack(fill=tk.X)
        
        self.wrong_notes_btn = ttk.Button(graph_ctrl_frame, text="Show Incorrect Notes: OFF", command=lambda: self.toggle_btn(self.show_wrong_var, self.wrong_notes_btn, "Show Incorrect Notes", self.update_plot))
        self.wrong_notes_btn.pack(side=tk.LEFT, pady=(0, 5))

        # --- Embedded Graph ---
        self.fig = Figure(figsize=(5, 3), dpi=100)
        self.fig.patch.set_facecolor(BG_COLOUR) 
        
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#1E2227') 
        self.ax.tick_params(colors=TEXT_COLOUR)
        
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['bottom'].set_color(TEXT_COLOUR)
        self.ax.spines['left'].set_color(TEXT_COLOUR)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.main_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.update_plot() 

    def toggle_btn(self, var, btn, base_text, callback=None):
        """Custom toggle logic to mimic switch behaviour"""
        var.set(not var.get())
        state = "ON" if var.get() else "OFF"
        btn.config(text=f"{base_text}: {state}")
        
        if var.get():
            btn.configure(style='Toggle.TButton')
        else:
            btn.configure(style='TButton')
            
        if callback:
            callback()

    def open_devices_window(self):
        """Dedicated window for MIDI device selection"""
        dev_win = tk.Toplevel(self.root)
        dev_win.title("MIDI Devices")
        dev_win.geometry("300x150")
        dev_win.configure(bg=BG_COLOUR)
        
        frame = ttk.Frame(dev_win, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Select MIDI Input:", font=("Helvetica", 12)).pack(anchor=tk.W)
        
        port_var = tk.StringVar()
        dropdown = ttk.Combobox(frame, textvariable=port_var, state="readonly")
        try:
            dropdown['values'] = mido.get_input_names()
        except Exception:
            dropdown['values'] = []

        dropdown.pack(fill=tk.X, pady=(5, 15))
        
        # Pre-select current port if it exists
        if dropdown['values']:
            current = self.midi_port.name if self.midi_port else ""
            if current in dropdown['values']:
                dropdown.set(current)
            else:
                dropdown.current(0)

        def apply_and_close():
            self.connect_midi(port_var.get())
            dev_win.destroy()

        ttk.Button(frame, text="Connect", command=apply_and_close).pack(fill=tk.X)

    def connect_midi(self, port_name):
        if not port_name: return
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
        current_time = time.time()

        if note_idx == self.target_note_idx:
            # First hit logic
            if self.first_hit_time is None:
                self.first_hit_time = current_time
                self.last_hit_time = current_time
                reaction = self.first_hit_time - self.start_time
                self.time_label.config(text=f"1st Hit: {reaction:.2f}s")
                self.note_label.config(fg=ACCENT_COLOUR)
            else:
                # Interval logic for subsequent correct octaves
                interval = current_time - self.last_hit_time
                self.reaction_intervals.append(interval)
                self.last_hit_time = current_time
                
                avg_interval = sum(self.reaction_intervals) / len(self.reaction_intervals)
                self.avg_time_label.config(text=f"Avg Interval: {avg_interval:.2f}s")

            # Track correct hit
            self.hit_history.append({'type': 'correct', 'velocity': msg.velocity})
            self.octaves_played.add(octave)
            self.octave_label.config(text=f"Octaves: {len(self.octaves_played)}")
            
        else:
            # Track incorrect hit
            self.hit_history.append({'type': 'wrong', 'velocity': msg.velocity})
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
            
        self.instruction_label.config(text=" | ".join(instructions) if instructions else "")
        
        # Reset stats
        self.start_time = time.time()
        self.first_hit_time = None
        self.last_hit_time = None
        self.reaction_intervals = []
        self.hit_history = []
        self.octaves_played = set()
        
        self.time_label.config(text="1st Hit: --")
        self.avg_time_label.config(text="Avg Interval: --")
        self.octave_label.config(text="Octaves: 0")
        
        self.update_plot()

    def update_plot(self):
        self.ax.clear()
        
        # Fixed the black text issue by explicitly setting label colors here
        self.ax.set_title("Live Velocity Tracking", pad=10, color=TEXT_COLOUR)
        self.ax.set_ylim(0, 130)
        self.ax.set_ylabel("Velocity", color=TEXT_COLOUR)
        self.ax.set_xlabel("Hit Sequence", color=TEXT_COLOUR)
        self.ax.tick_params(colors=TEXT_COLOUR)
        
        show_wrong = self.show_wrong_var.get()
        
        x_correct, y_correct = [], []
        x_wrong, y_wrong = [], []
        
        for i, hit in enumerate(self.hit_history):
            hit_index = i + 1
            if hit['type'] == 'correct':
                x_correct.append(hit_index)
                y_correct.append(hit['velocity'])
            elif hit['type'] == 'wrong' and show_wrong:
                x_wrong.append(hit_index)
                y_wrong.append(hit['velocity'])
                
        if x_correct:
            self.ax.plot(x_correct, y_correct, color=ACCENT_COLOUR, alpha=0.4, zorder=1)
            self.ax.scatter(x_correct, y_correct, color=ACCENT_COLOUR, s=50, zorder=2, label="Target Note")
            
        if x_wrong:
            self.ax.scatter(x_wrong, y_wrong, color=ERROR_COLOUR, s=50, marker='x', zorder=3, label="Missed Note")
            
        if x_correct or x_wrong:
            self.ax.legend(loc="lower right", facecolor=BG_COLOUR, edgecolor=TEXT_COLOUR, labelcolor=TEXT_COLOUR)
            
        self.ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        
        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = MidiGameApp(root)
    root.mainloop()