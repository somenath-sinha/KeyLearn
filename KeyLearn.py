import tkinter as tk
from tkinter import ttk, messagebox
import mido
import random
import time
import queue
import os
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import MaxNLocator, FuncFormatter, FixedLocator

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
TOOLTIP_BG = '#1E2227'

class MidiGameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MIDI Note Hunter Pro")
        self.root.configure(bg=BG_COLOUR)
        
        # Disables the macOS maximize button
        self.root.resizable(False, False)
        
        style = ttk.Style()
        if 'clam' in style.theme_names():
            style.theme_use('clam')
            style.configure('.', background=BG_COLOUR, foreground=TEXT_COLOUR)
            style.configure('TLabel', background=BG_COLOUR, foreground=TEXT_COLOUR)
            
            style.configure('TButton', background=TOGGLE_OFF, foreground=TEXT_COLOUR, borderwidth=0)
            style.map('TButton', background=[('active', '#5c6370')])
            
            style.configure('Toggle.TButton', background=TOGGLE_ON, foreground='#ffffff', font=('Helvetica', 10, 'bold'))
            style.map('Toggle.TButton', background=[('active', '#4D8BBE')])
            
            style.configure('TCombobox', fieldbackground=BG_COLOUR, background=TOGGLE_OFF, foreground=TEXT_COLOUR, bordercolor=BG_COLOUR, arrowcolor=TEXT_COLOUR)
            style.map('TCombobox', 
                      fieldbackground=[('readonly', BG_COLOUR)],
                      selectbackground=[('readonly', BG_COLOUR)],
                      selectforeground=[('readonly', TEXT_COLOUR)])

        self.main_frame = ttk.Frame(self.root, padding="20 20 20 20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.target_note_idx = None
        self.start_time = None
        self.first_hit_time = None
        self.action_timer = None 
        self.reaction_intervals = []
        self.hit_history = [] 
        self.octaves_played = set()
        self.midi_port = None
        self.msg_queue = queue.Queue()
        self.octave_target_var = tk.StringVar(value="5")
        
        self.toggles = {
            'hand': False,
            'finger': False,
            'wrong_notes': False,
            'show_vel_graph': True,
            'show_resp_graph': True
        }

        self.setup_ui()
        self.root.bind('<space>', self.handle_spacebar)
        
        available_ports = mido.get_input_names()
        if available_ports:
            self.connect_midi(available_ports[0])

        self.poll_queue()

    def handle_spacebar(self, event):
        self.next_note()
        return "break"

    def setup_ui(self):
        # --- Header Section ---
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))

        self.settings_btn = ttk.Button(header_frame, text="⚙ Settings", command=self.open_settings_window, takefocus=False)
        self.settings_btn.pack(side=tk.RIGHT)

        # --- Inline Toggles Section ---
        toggles_frame = ttk.Frame(self.main_frame)
        toggles_frame.pack(fill=tk.X, pady=(0, 10))

        self.hand_btn = ttk.Button(toggles_frame, text="Hand: OFF", takefocus=False)
        self.hand_btn.config(command=lambda: self.toggle_state('hand', self.hand_btn, "Hand"))
        self.hand_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.finger_btn = ttk.Button(toggles_frame, text="Finger: OFF", takefocus=False)
        self.finger_btn.config(command=lambda: self.toggle_state('finger', self.finger_btn, "Finger"))
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
        
        self.avg_time_label = ttk.Label(stats_frame, text="Avg Interval: --", font=("Helvetica", 12))
        self.avg_time_label.pack(side=tk.LEFT, expand=True)

        self.acc_label = ttk.Label(stats_frame, text="Accuracy: --", font=("Helvetica", 12))
        self.acc_label.pack(side=tk.LEFT, expand=True)
        
        self.octave_label = ttk.Label(stats_frame, text=f"Octaves: 0 / {self.octave_target_var.get()}", font=("Helvetica", 12))
        self.octave_label.pack(side=tk.RIGHT, expand=True)

        self.next_btn = ttk.Button(self.main_frame, text="Give me a Note! (Spacebar)", command=self.next_note, takefocus=False)
        self.next_btn.pack(fill=tk.X, pady=(10, 20))

        # --- Graph Controls ---
        graph_ctrl_frame = ttk.Frame(self.main_frame)
        graph_ctrl_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.wrong_notes_btn = ttk.Button(graph_ctrl_frame, text="Show Incorrect Notes: OFF", takefocus=False)
        self.wrong_notes_btn.config(command=lambda: self.toggle_state('wrong_notes', self.wrong_notes_btn, "Show Incorrect Notes", self.update_plots))
        self.wrong_notes_btn.pack(side=tk.LEFT)

        self.resp_graphs_btn = ttk.Button(graph_ctrl_frame, text="Response: ON", style='Toggle.TButton', takefocus=False)
        self.resp_graphs_btn.config(command=lambda: self.toggle_graph_visibility('show_resp_graph', self.resp_graphs_btn, "Response", self.graph_container_resp))
        self.resp_graphs_btn.pack(side=tk.RIGHT, padx=(10, 0))

        self.vel_graphs_btn = ttk.Button(graph_ctrl_frame, text="Velocity: ON", style='Toggle.TButton', takefocus=False)
        self.vel_graphs_btn.config(command=lambda: self.toggle_graph_visibility('show_vel_graph', self.vel_graphs_btn, "Velocity", self.graph_container_vel))
        self.vel_graphs_btn.pack(side=tk.RIGHT)

        # --- Velocity Graph Container ---
        self.graph_container_vel = ttk.Frame(self.main_frame)
        self.graph_container_vel.pack(fill=tk.BOTH, expand=True)

        self.fig_vel = Figure(figsize=(5, 2.75), dpi=100)
        self.fig_vel.patch.set_facecolor(BG_COLOUR)
        self.ax_vel = self.fig_vel.add_subplot(111)
        self.canvas_vel = FigureCanvasTkAgg(self.fig_vel, master=self.graph_container_vel)
        self.canvas_vel.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # --- Response Graph Container ---
        self.graph_container_resp = ttk.Frame(self.main_frame)
        self.graph_container_resp.pack(fill=tk.BOTH, expand=True)

        self.fig_resp = Figure(figsize=(5, 2.75), dpi=100)
        self.fig_resp.patch.set_facecolor(BG_COLOUR)
        self.ax_resp = self.fig_resp.add_subplot(111)
        self.canvas_resp = FigureCanvasTkAgg(self.fig_resp, master=self.graph_container_resp)
        self.canvas_resp.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.canvas_vel.mpl_connect("motion_notify_event", self.on_hover_vel)
        self.canvas_resp.mpl_connect("motion_notify_event", self.on_hover_resp)
        
        self.sc_correct = None
        self.sc_wrong = None
        self.bars = []
        
        self.update_plots() 

    def toggle_graph_visibility(self, toggle_key, btn, label, container):
        self.toggles[toggle_key] = not self.toggles[toggle_key]
        if self.toggles[toggle_key]:
            btn.config(text=f"{label}: ON", style='Toggle.TButton')
            container.pack(fill=tk.BOTH, expand=True)
        else:
            btn.config(text=f"{label}: OFF", style='TButton')
            container.pack_forget()

    def format_time_ticks(self, x, pos):
        if x >= 60:
            return f"{int(x//60)}m"
        elif x > 0:
            return f"{x:g}s"
        return "0s"

    def on_hover_vel(self, event):
        vis = self.annot_vel.get_visible()
        if event.inaxes == self.ax_vel:
            cont_c, ind_c = self.sc_correct.contains(event) if self.sc_correct else (False, {})
            cont_w, ind_w = self.sc_wrong.contains(event) if self.sc_wrong else (False, {})
            
            if cont_c:
                pos = self.sc_correct.get_offsets()[ind_c["ind"][0]]
                self.annot_vel.xy = pos
                self.annot_vel.set_text(f"Vel: {int(pos[1])}")
                self.annot_vel.set_visible(True)
                self.canvas_vel.draw_idle()
            elif cont_w:
                pos = self.sc_wrong.get_offsets()[ind_w["ind"][0]]
                self.annot_vel.xy = pos
                self.annot_vel.set_text(f"Vel: {int(pos[1])}")
                self.annot_vel.set_visible(True)
                self.canvas_vel.draw_idle()
            else:
                if vis:
                    self.annot_vel.set_visible(False)
                    self.canvas_vel.draw_idle()

    def on_hover_resp(self, event):
        vis = self.annot_resp.get_visible()
        if event.inaxes == self.ax_resp:
            hovered = False
            if hasattr(self, 'bars') and self.bars:
                for bar in self.bars:
                    cont, _ = bar.contains(event)
                    if cont:
                        height = bar.get_height()
                        text = f"{height:.2f}s" if height >= 1 else f"{height*1000:.0f}ms"
                        self.annot_resp.xy = (bar.get_x() + bar.get_width() / 2, height)
                        self.annot_resp.set_text(text)
                        self.annot_resp.set_visible(True)
                        self.canvas_resp.draw_idle()
                        hovered = True
                        break
            if not hovered and vis:
                self.annot_resp.set_visible(False)
                self.canvas_resp.draw_idle()
        else:
            if vis:
                self.annot_resp.set_visible(False)
                self.canvas_resp.draw_idle()

    def apply_graph_styling(self):
        # Velocity Graph Styling
        self.ax_vel.set_facecolor('#1E2227') 
        self.ax_vel.spines['top'].set_visible(False)
        self.ax_vel.spines['right'].set_visible(False)
        self.ax_vel.spines['bottom'].set_color(TEXT_COLOUR)
        self.ax_vel.spines['left'].set_color(TEXT_COLOUR)
        self.ax_vel.tick_params(colors=TEXT_COLOUR, which='both') 
        self.ax_vel.xaxis.set_major_locator(MaxNLocator(integer=True))
        self.ax_vel.set_title("Velocity Tracking", pad=10, color=TEXT_COLOUR)
        self.ax_vel.set_ylim(0, 130)
        self.ax_vel.set_ylabel("Velocity", color=TEXT_COLOUR)
        
        # Response Graph Styling
        self.ax_resp.set_facecolor('#1E2227') 
        self.ax_resp.spines['top'].set_visible(False)
        self.ax_resp.spines['right'].set_visible(False)
        self.ax_resp.spines['bottom'].set_color(TEXT_COLOUR)
        self.ax_resp.spines['left'].set_color(TEXT_COLOUR)
        self.ax_resp.tick_params(colors=TEXT_COLOUR, which='both') 
        self.ax_resp.xaxis.set_major_locator(MaxNLocator(integer=True))
        self.ax_resp.set_title("Response Time Interval (Log Scale)", pad=10, color=TEXT_COLOUR)
        self.ax_resp.set_ylabel("Time", color=TEXT_COLOUR)
        self.ax_resp.set_xlabel("Hit Sequence", color=TEXT_COLOUR)
        
        self.ax_resp.set_yscale('log')
        formatter = FuncFormatter(self.format_time_ticks)
        self.ax_resp.yaxis.set_major_formatter(formatter)
        self.ax_resp.yaxis.set_minor_formatter(formatter)
        
        custom_minor_ticks = [
            0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9,
            1.2, 1.4, 1.6, 1.8, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0, 7.0, 8.0, 9.0,
            10, 15, 20, 30, 40, 50, 60
        ]
        self.ax_resp.yaxis.set_minor_locator(FixedLocator(custom_minor_ticks))

    def toggle_state(self, key, btn, base_text, callback=None):
        self.toggles[key] = not self.toggles[key]
        state = "ON" if self.toggles[key] else "OFF"
        btn.config(text=f"{base_text}: {state}")
        
        if self.toggles[key]:
            btn.configure(style='Toggle.TButton')
        else:
            btn.configure(style='TButton')
            
        if callback:
            callback()

    def open_settings_window(self):
        set_win = tk.Toplevel(self.root)
        set_win.title("Settings")
        set_win.geometry("350x250")
        set_win.configure(bg=BG_COLOUR)
        
        frame = ttk.Frame(set_win, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Select MIDI Input:", font=("Helvetica", 12)).pack(anchor=tk.W)
        port_var = tk.StringVar()
        dropdown = ttk.Combobox(frame, textvariable=port_var, state="readonly", takefocus=False)
        try:
            dropdown['values'] = mido.get_input_names()
        except Exception:
            dropdown['values'] = []

        dropdown.pack(fill=tk.X, pady=(5, 15))
        
        if dropdown['values']:
            current = self.midi_port.name if self.midi_port else ""
            if current in dropdown['values']:
                dropdown.set(current)
            else:
                dropdown.current(0)

        ttk.Label(frame, text="Select number of octaves:", font=("Helvetica", 12)).pack(anchor=tk.W)
        oct_dropdown = ttk.Combobox(frame, textvariable=self.octave_target_var, state="readonly", takefocus=False)
        oct_dropdown['values'] = [str(i) for i in range(1, 8)] 
        oct_dropdown.pack(fill=tk.X, pady=(5, 15))

        def apply_and_close():
            self.connect_midi(port_var.get())
            self.octave_label.config(text=f"Octaves: {len(self.octaves_played)} / {self.octave_target_var.get()}")
            set_win.destroy()

        ttk.Button(frame, text="Save & Close", command=apply_and_close, takefocus=False).pack(fill=tk.X)

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
        
    def flash_error(self):
        current_text = self.note_label.cget("text")
        if current_text != "Done!":
            self.note_label.config(fg=ERROR_COLOUR)
            self.root.after(250, self.reset_colour)
            
    def reset_colour(self):
        if self.target_note_idx is not None and len(self.octaves_played) < int(self.octave_target_var.get()):
            self.note_label.config(fg=TEXT_COLOUR)

    def calculate_accuracy(self):
        total = len(self.hit_history)
        if total == 0:
            return "--"
        correct = sum(1 for h in self.hit_history if h['type'] == 'correct')
        return f"{(correct / total) * 100:.1f}%"

    def process_midi_msg(self, msg):
        if self.target_note_idx is None:
            return
            
        target_max = int(self.octave_target_var.get())
        if len(self.octaves_played) >= target_max:
            return 

        note_idx = msg.note % 12
        octave = (msg.note // 12) - 1
        current_time = time.time()
        
        # Calculates response time from the start of the note, or the last CORRECT hit
        response_time = current_time - self.action_timer

        if note_idx == self.target_note_idx:
            # ONLY reset the timer if a correct note is hit
            self.action_timer = current_time
            
            if self.first_hit_time is None:
                self.first_hit_time = current_time
                self.time_label.config(text=f"1st Hit: {response_time:.2f}s")
                self.note_label.config(fg=ACCENT_COLOUR)
            else:
                self.reaction_intervals.append(response_time)
                avg_interval = sum(self.reaction_intervals) / len(self.reaction_intervals)
                self.avg_time_label.config(text=f"Avg Interval: {avg_interval:.2f}s")

            self.hit_history.append({'type': 'correct', 'velocity': msg.velocity, 'response_time': response_time})
            self.octaves_played.add(octave)
            self.octave_label.config(text=f"Octaves: {len(self.octaves_played)} / {self.octave_target_var.get()}")
            
            if len(self.octaves_played) >= target_max:
                self.note_label.config(text="Done!", fg=ACCENT_COLOUR)
                self.instruction_label.config(text="Press Spacebar for next note")
            
        else:
            # Logs the wrong hit for velocity plotting and accuracy, and retains response time for massive red bars!
            self.hit_history.append({'type': 'wrong', 'velocity': msg.velocity, 'response_time': response_time})
            self.flash_error()
            os.system("afplay /System/Library/Sounds/Basso.aiff &")
            
        self.acc_label.config(text=f"Accuracy: {self.calculate_accuracy()}")
        self.update_plots()

    def next_note(self):
        self.target_note_idx = random.randint(0, 11)
        target_note_name = NOTES[self.target_note_idx]
        
        self.note_label.config(text=target_note_name, fg=TEXT_COLOUR)
        
        instructions = []
        if self.toggles['hand']:
            instructions.append(random.choice(HANDS))
        if self.toggles['finger']:
            instructions.append(random.choice(FINGERS))
            
        self.instruction_label.config(text=" | ".join(instructions) if instructions else "")
        
        self.start_time = time.time()
        self.action_timer = self.start_time
        self.first_hit_time = None
        self.reaction_intervals = []
        self.hit_history = []
        self.octaves_played = set()
        
        self.time_label.config(text="1st Hit: --")
        self.avg_time_label.config(text="Avg Interval: --")
        self.acc_label.config(text="Accuracy: --")
        self.octave_label.config(text=f"Octaves: 0 / {self.octave_target_var.get()}")
        
        self.update_plots()

    def update_plots(self):
        self.ax_vel.clear()
        self.ax_resp.clear()
        
        show_wrong = self.toggles['wrong_notes']
        
        x_correct, y_correct = [], []
        x_wrong, y_wrong = [], []
        
        x_all = []
        y_response = []
        bar_colors = []
        
        for i, hit in enumerate(self.hit_history):
            hit_index = i + 1
            if hit['type'] == 'correct':
                x_correct.append(hit_index)
                y_correct.append(hit['velocity'])
                
                x_all.append(hit_index)
                y_response.append(hit['response_time'])
                bar_colors.append(ACCENT_COLOUR)
                
            elif hit['type'] == 'wrong' and show_wrong:
                x_wrong.append(hit_index)
                y_wrong.append(hit['velocity'])
                
                # Restored to response graph for visual tracking
                x_all.append(hit_index)
                y_response.append(hit['response_time'])
                bar_colors.append(ERROR_COLOUR)
                
        self.sc_correct = None
        self.sc_wrong = None
        self.bars = []
        
        if x_correct:
            self.ax_vel.plot(x_correct, y_correct, color=ACCENT_COLOUR, alpha=0.4, zorder=1)
            self.sc_correct = self.ax_vel.scatter(x_correct, y_correct, color=ACCENT_COLOUR, s=50, zorder=2, label="Target Note")
            
        if x_wrong:
            self.sc_wrong = self.ax_vel.scatter(x_wrong, y_wrong, color=ERROR_COLOUR, s=50, marker='x', zorder=3, label="Missed Note")
            
        if x_correct or x_wrong:
            self.ax_vel.legend(loc="lower right", facecolor=BG_COLOUR, edgecolor=TEXT_COLOUR, labelcolor=TEXT_COLOUR)
            
        if x_all:
            self.bars = self.ax_resp.bar(x_all, y_response, color=bar_colors, alpha=0.8, width=0.5)

        self.apply_graph_styling() 

        self.annot_vel = self.ax_vel.annotate("", xy=(0,0), xytext=(10,10), textcoords="offset points",
                                     bbox=dict(boxstyle="round", fc=TOOLTIP_BG, ec=TEXT_COLOUR, alpha=0.9),
                                     color=TEXT_COLOUR, zorder=10)
        self.annot_vel.set_visible(False)

        self.annot_resp = self.ax_resp.annotate("", xy=(0,0), xytext=(0,10), textcoords="offset points",
                                     bbox=dict(boxstyle="round", fc=TOOLTIP_BG, ec=TEXT_COLOUR, alpha=0.9),
                                     color=TEXT_COLOUR, zorder=10, ha='center')
        self.annot_resp.set_visible(False)

        self.canvas_vel.draw()
        self.canvas_resp.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = MidiGameApp(root)
    root.mainloop()