# main.py
import tkinter as tk
from tkinter import ttk, messagebox
import random
import time
import os
import json

from config import *
from midi_engine import MidiEngine
from plot_engine import PlotEngine

class MidiGameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MIDI Note Hunter Pro")
        
        # Explicitly set the size BEFORE locking the window to prevent truncation
        self.root.geometry("650x950") 
        self.root.configure(bg=BG_COLOUR)
        self.root.resizable(False, False)
        
        self._configure_styles()

        self.main_frame = ttk.Frame(self.root, padding="20 20 20 20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.current_mode_var = tk.StringVar()
        self.octave_target_var = tk.StringVar()
        self.buffer_var = tk.StringVar()
        self.lowest_c = None
        self.learning_lowest_c = False
        
        self.load_settings()

        self.target_note_idx = None
        self.start_time = None
        self.first_hit_time = None
        self.action_timer = None 
        self.reaction_intervals = []
        self.hit_history = [] 
        self.octaves_played = set()
        
        self.l3_pending_time = None
        self.l3_pending_octave = None
        self.l3_pending_velocity = None
        self.l4_sequence = []
        self.l4_progress = 0
        
        self.toggles = {
            'hand': False,
            'finger': False,
            'wrong_notes': False,
            'show_vel_graph': True,
            'show_resp_graph': True
        }

        self.midi = MidiEngine()
        self.setup_ui()
        self.update_toggle_states()
        
        self.root.bind('<space>', self.handle_spacebar)
        
        ports = self.midi.get_ports()
        if ports:
            self.connect_midi(ports[0])

        self.poll_queue()

    def load_settings(self):
        try:
            with open('user_settings.json', 'r') as f:
                settings = json.load(f)
                self.current_mode_var.set(settings.get('mode', MODES[-1]))
                self.octave_target_var.set(settings.get('octaves', '5'))
                self.buffer_var.set(settings.get('buffer', '200ms'))
                self.lowest_c = settings.get('lowest_c', None)
        except (FileNotFoundError, json.JSONDecodeError):
            self.current_mode_var.set(MODES[-1])
            self.octave_target_var.set("5")
            self.buffer_var.set("200ms")

    def save_settings(self):
        settings = {
            'mode': self.current_mode_var.get(),
            'octaves': self.octave_target_var.get(),
            'buffer': self.buffer_var.get(),
            'lowest_c': self.lowest_c
        }
        with open('user_settings.json', 'w') as f:
            json.dump(settings, f)

    def _configure_styles(self):
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
            style.map('TCombobox', fieldbackground=[('readonly', BG_COLOUR)], selectbackground=[('readonly', BG_COLOUR)], selectforeground=[('readonly', TEXT_COLOUR)])

    def setup_ui(self):
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        self.settings_btn = ttk.Button(header_frame, text="⚙ Settings", command=self.open_settings_window, takefocus=False)
        self.settings_btn.pack(side=tk.RIGHT)

        toggles_frame = ttk.Frame(self.main_frame)
        toggles_frame.pack(fill=tk.X, pady=(0, 10))
        self.hand_btn = ttk.Button(toggles_frame, text="Hand: OFF", takefocus=False)
        self.hand_btn.config(command=lambda: self.toggle_state('hand', self.hand_btn, "Hand"))
        self.hand_btn.pack(side=tk.LEFT, padx=(0, 10))
        self.finger_btn = ttk.Button(toggles_frame, text="Finger: OFF", takefocus=False)
        self.finger_btn.config(command=lambda: self.toggle_state('finger', self.finger_btn, "Finger"))
        self.finger_btn.pack(side=tk.LEFT)

        self.note_label = tk.Label(self.main_frame, text="Ready?", font=("Helvetica", 54, "bold"), bg=BG_COLOUR, fg=TEXT_COLOUR)
        self.note_label.pack(pady=10)
        
        self.inst_frame = ttk.Frame(self.main_frame)
        self.inst_frame.pack(pady=(5, 0))
        self.inst_part1 = ttk.Label(self.inst_frame, text="Press Spacebar to start", font=("Helvetica", 16))
        self.inst_part1.pack(side=tk.LEFT)
        self.inst_part2 = ttk.Label(self.inst_frame, text="", font=("Helvetica", 16, "bold"), foreground=ACCENT_COLOUR)
        self.inst_part2.pack(side=tk.LEFT)

        # --- New Live Feedback Section ---
        self.live_feedback_frame = ttk.Frame(self.main_frame)
        self.live_feedback_frame.pack(pady=(5, 5))
        
        self.current_octave_disp = ttk.Label(self.live_feedback_frame, text="Current Octave: --", font=("Helvetica", 14))
        self.current_octave_disp.pack(side=tk.LEFT, padx=(0, 15))
        
        self.error_msg_disp = ttk.Label(self.live_feedback_frame, text="", font=("Helvetica", 14, "bold"), foreground=ERROR_COLOUR)
        self.error_msg_disp.pack(side=tk.LEFT)

        stats_frame = ttk.Frame(self.main_frame)
        stats_frame.pack(fill=tk.X, pady=10)
        self.time_label = ttk.Label(stats_frame, text="1st Hit: --", font=("Helvetica", 12))
        self.time_label.pack(side=tk.LEFT, expand=True)
        self.avg_time_label = ttk.Label(stats_frame, text="Avg Interval: --", font=("Helvetica", 12))
        self.avg_time_label.pack(side=tk.LEFT, expand=True)
        self.acc_label = ttk.Label(stats_frame, text="Accuracy: --", font=("Helvetica", 12))
        self.acc_label.pack(side=tk.LEFT, expand=True)
        self.octave_label = ttk.Label(stats_frame, text=f"Progress: 0 / {self._get_target_max()}", font=("Helvetica", 12))
        self.octave_label.pack(side=tk.RIGHT, expand=True)

        self.next_btn = ttk.Button(self.main_frame, text="Give me a Note! (Spacebar)", command=self.next_note, takefocus=False)
        self.next_btn.pack(fill=tk.X, pady=(10, 20))

        graph_ctrl_frame = ttk.Frame(self.main_frame)
        graph_ctrl_frame.pack(fill=tk.X, pady=(0, 10))
        self.wrong_notes_btn = ttk.Button(graph_ctrl_frame, text="Show Incorrect Notes: OFF", takefocus=False)
        self.wrong_notes_btn.config(command=lambda: self.toggle_state('wrong_notes', self.wrong_notes_btn, "Show Incorrect Notes", self.trigger_plot_update))
        self.wrong_notes_btn.pack(side=tk.LEFT)

        self.resp_graphs_btn = ttk.Button(graph_ctrl_frame, text="Response: ON", style='Toggle.TButton', takefocus=False)
        self.resp_graphs_btn.config(command=lambda: self.toggle_graph_visibility('show_resp_graph', self.resp_graphs_btn, "Response", self.graph_container_resp))
        self.resp_graphs_btn.pack(side=tk.RIGHT, padx=(10, 0))
        self.vel_graphs_btn = ttk.Button(graph_ctrl_frame, text="Velocity: ON", style='Toggle.TButton', takefocus=False)
        self.vel_graphs_btn.config(command=lambda: self.toggle_graph_visibility('show_vel_graph', self.vel_graphs_btn, "Velocity", self.graph_container_vel))
        self.vel_graphs_btn.pack(side=tk.RIGHT)

        self.graph_container_vel = ttk.Frame(self.main_frame)
        self.graph_container_vel.pack(fill=tk.BOTH, expand=True)
        self.graph_container_resp = ttk.Frame(self.main_frame)
        self.graph_container_resp.pack(fill=tk.BOTH, expand=True)

        self.plotter = PlotEngine(self.graph_container_vel, self.graph_container_resp)
        self.trigger_plot_update()

    def update_toggle_states(self):
        if self.current_mode_var.get() == 'Unlocked Mode':
            self.hand_btn.config(state=tk.NORMAL)
            self.finger_btn.config(state=tk.NORMAL)
        else:
            self.hand_btn.config(state=tk.DISABLED)
            self.finger_btn.config(state=tk.DISABLED)

    def _get_target_max(self):
        base_octaves = int(self.octave_target_var.get())
        mode = self.current_mode_var.get()
        if mode == 'Level 3: Bilateral Chords':
            return max(1, base_octaves - 1)
        elif mode == 'Level 4: Diatonic Run':
            return 1 
        return base_octaves

    def handle_spacebar(self, event):
        self.next_note()
        return "break"

    def toggle_state(self, key, btn, base_text, callback=None):
        self.toggles[key] = not self.toggles[key]
        state = "ON" if self.toggles[key] else "OFF"
        btn.config(text=f"{base_text}: {state}", style='Toggle.TButton' if self.toggles[key] else 'TButton')
        if callback: callback()

    def toggle_graph_visibility(self, toggle_key, btn, label, container):
        self.toggles[toggle_key] = not self.toggles[toggle_key]
        if self.toggles[toggle_key]:
            btn.config(text=f"{label}: ON", style='Toggle.TButton')
            container.pack(fill=tk.BOTH, expand=True)
        else:
            btn.config(text=f"{label}: OFF", style='TButton')
            container.pack_forget()

    def trigger_plot_update(self):
        self.plotter.update_plots(self.hit_history, self.toggles['wrong_notes'])

    def open_settings_window(self):
        set_win = tk.Toplevel(self.root)
        set_win.title("Settings")
        set_win.geometry("450x420")
        set_win.configure(bg=BG_COLOUR)
        
        frame = ttk.Frame(set_win, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Game Mode:", font=("Helvetica", 12)).pack(anchor=tk.W)
        mode_dropdown = ttk.Combobox(frame, textvariable=self.current_mode_var, state="readonly", takefocus=False)
        mode_dropdown['values'] = MODES
        mode_dropdown.pack(fill=tk.X, pady=(0, 5))

        rules_label = tk.Label(frame, text="", bg=BG_COLOUR, fg=TEXT_COLOUR, wraplength=400, justify=tk.LEFT)
        rules_label.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(frame, text="Target Actions (Octaves/Runs):", font=("Helvetica", 12)).pack(anchor=tk.W)
        oct_dropdown = ttk.Combobox(frame, textvariable=self.octave_target_var, state="readonly", takefocus=False)
        oct_dropdown.pack(fill=tk.X, pady=(0, 10))

        def update_rules(event=None):
            mode = self.current_mode_var.get()
            rules_label.config(text=LEVEL_RULES.get(mode, ""))
            if mode == 'Level 3: Bilateral Chords':
                oct_dropdown['values'] = [str(i) for i in range(2, 8)]
                if self.octave_target_var.get() == "1":
                    self.octave_target_var.set("2")
            else:
                oct_dropdown['values'] = [str(i) for i in range(1, 8)]
        
        mode_dropdown.bind('<<ComboboxSelected>>', update_rules)
        update_rules()

        ttk.Label(frame, text="Level 3 Chord Timing Buffer:", font=("Helvetica", 12)).pack(anchor=tk.W)
        buffer_dropdown = ttk.Combobox(frame, textvariable=self.buffer_var, state="readonly", takefocus=False)
        buffer_dropdown['values'] = list(BUFFER_TIMES.keys())
        buffer_dropdown.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(frame, text="MIDI Input Device:", font=("Helvetica", 12)).pack(anchor=tk.W)
        port_var = tk.StringVar()
        midi_dropdown = ttk.Combobox(frame, textvariable=port_var, state="readonly", takefocus=False)
        midi_dropdown['values'] = self.midi.get_ports()
        midi_dropdown.pack(fill=tk.X, pady=(0, 10))
        
        if midi_dropdown['values']:
            current = self.midi.port.name if self.midi.port else ""
            if current in midi_dropdown['values']: midi_dropdown.set(current)
            else: midi_dropdown.current(0)

        def force_recalibrate():
            self.lowest_c = None
            self.save_settings()
            set_win.destroy()
            if self.current_mode_var.get() == 'Level 4: Diatonic Run':
                self.next_note()

        ttk.Button(frame, text="Recalibrate Lowest C (Level 4)", command=force_recalibrate, takefocus=False).pack(fill=tk.X, pady=(0, 15))

        def apply_and_close():
            self.connect_midi(port_var.get())
            self.save_settings()
            self.update_toggle_states()
            self.octave_label.config(text=f"Progress: {len(self.octaves_played)} / {self._get_target_max()}")
            set_win.destroy()

        ttk.Button(frame, text="Save & Close", command=apply_and_close, takefocus=False).pack(fill=tk.X)

    def connect_midi(self, port_name):
        try:
            self.midi.connect(port_name)
        except Exception as e:
            messagebox.showerror("MIDI Error", f"Could not connect to {port_name}.\n{e}")

    def poll_queue(self):
        for msg in self.midi.get_messages():
            self.process_midi_msg(msg)
        self.root.after(50, self.poll_queue)

    def flash_error(self):
        if self.note_label.cget("text") != "Done!":
            self.note_label.config(fg=ERROR_COLOUR)
            self.root.after(250, lambda: self.note_label.config(fg=TEXT_COLOUR) if len(self.octaves_played) < self._get_target_max() else None)

    def calculate_accuracy(self):
        total = len(self.hit_history)
        if total == 0: return "--"
        correct = sum(1 for h in self.hit_history if h['type'] == 'correct')
        return f"{(correct / total) * 100:.1f}%"

    def process_midi_msg(self, msg):
        if self.learning_lowest_c:
            if msg.note % 12 == 0:
                self.lowest_c = msg.note
                self.save_settings()
                self.learning_lowest_c = False
                original_text = self.note_label.cget("text")
                self.note_label.config(text="Calibrated!", fg=ACCENT_COLOUR)
                self.root.after(1000, self.next_note) 
            else:
                self.flash_error()
                os.system("afplay /System/Library/Sounds/Basso.aiff &")
            return

        if self.target_note_idx is None: return
        target_max = self._get_target_max()
        if len(self.octaves_played) >= target_max: return 

        note_idx = msg.note % 12
        octave = (msg.note // 12) - 2 
        
        # Live Feedback Display
        self.current_octave_disp.config(text=f"Current Octave: {octave}")
        
        current_time = time.time()
        response_time = current_time - self.action_timer
        mode = self.current_mode_var.get()

        if mode == 'Level 3: Bilateral Chords':
            self._handle_level_3(msg, note_idx, octave, current_time, response_time, target_max)
        elif mode == 'Level 4: Diatonic Run':
            self._handle_level_4(msg, note_idx, octave, current_time, response_time, target_max)
        else:
            self._handle_standard(msg, note_idx, octave, current_time, response_time, target_max)

        self.acc_label.config(text=f"Accuracy: {self.calculate_accuracy()}")
        self.trigger_plot_update()

    def _handle_standard(self, msg, note_idx, octave, current_time, response_time, target_max):
        if note_idx == self.target_note_idx:
            self.action_timer = current_time
            self.error_msg_disp.config(text="") # Clear errors on success
            
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
            self.octave_label.config(text=f"Progress: {len(self.octaves_played)} / {target_max}")
            
            if len(self.octaves_played) >= target_max:
                self.note_label.config(text="Done!", fg=ACCENT_COLOUR)
                self.inst_part1.config(text="Press Spacebar for next note")
                self.inst_part2.config(text="")
        else:
            self.hit_history.append({'type': 'wrong', 'velocity': msg.velocity, 'response_time': response_time})
            self.error_msg_disp.config(text=f"Played {NOTES[note_idx]}{octave}, expected {NOTES[self.target_note_idx]}")
            self.flash_error()
            os.system("afplay /System/Library/Sounds/Basso.aiff &")

    def _handle_level_3(self, msg, note_idx, octave, current_time, response_time, target_max):
        buffer_limit = BUFFER_TIMES[self.buffer_var.get()]

        if note_idx == self.target_note_idx:
            if self.l3_pending_time is None:
                self.l3_pending_time = current_time
                self.l3_pending_octave = octave
                self.l3_pending_velocity = msg.velocity
                self.error_msg_disp.config(text="")
            else:
                sync_delta = current_time - self.l3_pending_time
                if sync_delta <= buffer_limit and octave != self.l3_pending_octave:
                    self.action_timer = current_time
                    self.error_msg_disp.config(text="")
                    avg_vel = (self.l3_pending_velocity + msg.velocity) / 2
                    self.hit_history.append({'type': 'correct', 'velocity': avg_vel, 'response_time': response_time, 'sync_time': sync_delta})
                    
                    self.octaves_played.add(min(octave, self.l3_pending_octave))
                    self.l3_pending_time = None 
                    
                    if len(self.octaves_played) >= target_max:
                        self.note_label.config(text="Done!", fg=ACCENT_COLOUR)
                        self.inst_part1.config(text="Press Spacebar for next note")
                        self.inst_part2.config(text="")
                else:
                    self.hit_history.append({'type': 'wrong', 'velocity': msg.velocity, 'response_time': response_time})
                    
                    if octave == self.l3_pending_octave:
                        self.error_msg_disp.config(text=f"Played {NOTES[note_idx]}{octave} twice, expected separate octave")
                    else:
                        self.error_msg_disp.config(text=f"Missed sync window ({sync_delta*1000:.0f}ms)")
                        
                    self.flash_error()
                    os.system("afplay /System/Library/Sounds/Basso.aiff &")
                    self.l3_pending_time = current_time
                    self.l3_pending_octave = octave

            self.octave_label.config(text=f"Progress: {len(self.octaves_played)} / {target_max}")
        else:
            self.hit_history.append({'type': 'wrong', 'velocity': msg.velocity, 'response_time': response_time})
            self.error_msg_disp.config(text=f"Played {NOTES[note_idx]}{octave}, expected {NOTES[self.target_note_idx]}")
            self.flash_error()
            os.system("afplay /System/Library/Sounds/Basso.aiff &")

    def _handle_level_4(self, msg, note_idx, octave, current_time, response_time, target_max):
        expected_midi = self.l4_sequence[self.l4_progress]
        expected_name = NOTES[expected_midi % 12]
        expected_oct = (expected_midi // 12) - 2
        
        if msg.note == expected_midi:
            self.action_timer = current_time
            self.error_msg_disp.config(text="")
            
            if self.first_hit_time is None:
                self.first_hit_time = current_time
                self.time_label.config(text=f"1st Hit: {response_time:.2f}s")
                self.note_label.config(fg=ACCENT_COLOUR)
            
            self.hit_history.append({'type': 'correct', 'velocity': msg.velocity, 'response_time': response_time})
            self.l4_progress += 1

            if self.l4_progress >= 9:
                self.octaves_played.add(len(self.octaves_played)) 
                self.l4_progress = 0 
                if len(self.octaves_played) >= target_max:
                    self.note_label.config(text="Done!", fg=ACCENT_COLOUR)
                    self.inst_part1.config(text="Press Spacebar for next note")
                    self.inst_part2.config(text="")
            
            self.octave_label.config(text=f"Progress: {len(self.octaves_played)} / {target_max}")
        else:
            self.hit_history.append({'type': 'wrong', 'velocity': msg.velocity, 'response_time': response_time})
            self.error_msg_disp.config(text=f"Played {NOTES[note_idx]}{octave}, expected {expected_name}{expected_oct}")
            self.flash_error()
            os.system("afplay /System/Library/Sounds/Basso.aiff &")

    def _generate_diatonic(self, start_midi, up=True):
        seq = [start_midi]
        curr = start_midi
        for _ in range(4):
            curr += 1 if up else -1
            while (curr % 12) not in WHITE_NOTE_INDICES:
                curr += 1 if up else -1
            seq.append(curr)
        for i in range(3, -1, -1):
            seq.append(seq[i])
        return seq

    def next_note(self):
        mode = self.current_mode_var.get()
        self.start_time = time.time()
        self.action_timer = self.start_time
        self.first_hit_time = None
        self.reaction_intervals = []
        self.hit_history = []
        self.octaves_played = set()
        
        self.time_label.config(text="1st Hit: --")
        self.avg_time_label.config(text="Avg Interval: --")
        self.acc_label.config(text="Accuracy: --")
        self.octave_label.config(text=f"Progress: 0 / {self._get_target_max()}")
        self.error_msg_disp.config(text="") # Clear errors on round start

        prev_note = self.target_note_idx

        if mode == 'Level 4: Diatonic Run':
            if self.lowest_c is None:
                self.learning_lowest_c = True
                self.note_label.config(text="Calibrate", fg=TEXT_COLOUR)
                self.inst_part1.config(text="Play your leftmost C key ")
                self.inst_part2.config(text="(Lowest Octave)")
                return
                
            octaves = int(self.octave_target_var.get())
            min_midi = self.lowest_c
            max_midi = self.lowest_c + (octaves * 12)
            midpoint = self.lowest_c + (octaves * 12) / 2
            
            min_allowed = min_midi + 12 
            max_allowed = max_midi - 12 
            if max_allowed < min_allowed:
                min_allowed = min_midi
                max_allowed = max_midi
            
            while True:
                start_midi = random.randint(min_allowed, max_allowed)
                idx = start_midi % 12
                if idx not in WHITE_NOTE_INDICES: continue
                if idx == prev_note: continue

                up = start_midi >= midpoint
                seq = self._generate_diatonic(start_midi, up)
                
                if all(min_midi <= n <= max_midi for n in seq):
                    self.target_note_idx = idx
                    self.l4_sequence = seq
                    start_octave = (start_midi // 12) - 2 
                    hand = "Right Hand" if up else "Left Hand"
                    self.inst_part1.config(text=f"{hand} | ")
                    self.inst_part2.config(text=f"Octave {start_octave}")
                    break
            self.l4_progress = 0
            self.note_label.config(text=NOTES[self.target_note_idx], fg=TEXT_COLOUR)

        elif mode == 'Level 3: Bilateral Chords':
            while True:
                nxt = random.randint(0, 11)
                if nxt != prev_note: break
            self.target_note_idx = nxt
            self.note_label.config(text=NOTES[self.target_note_idx], fg=TEXT_COLOUR)
            self.l3_pending_time = None
            self.inst_part1.config(text="Both Hands | ")
            self.inst_part2.config(text="Simultaneously")

        elif mode == 'Level 2: Strict Finger':
            while True:
                nxt = random.randint(0, 11)
                if nxt != prev_note: break
            self.target_note_idx = nxt
            self.note_label.config(text=NOTES[self.target_note_idx], fg=TEXT_COLOUR)
            self.inst_part1.config(text=f"{random.choice(HANDS)} | ")
            self.inst_part2.config(text=f"{random.choice(FINGERS)}")

        elif mode == 'Level 1: Free Hunt':
            while True:
                nxt = random.randint(0, 11)
                if nxt != prev_note: break
            self.target_note_idx = nxt
            self.note_label.config(text=NOTES[self.target_note_idx], fg=TEXT_COLOUR)
            self.inst_part1.config(text="Any Hand | ")
            self.inst_part2.config(text="Any Finger")

        else: # Unlocked Mode
            while True:
                nxt = random.randint(0, 11)
                if nxt != prev_note: break
            self.target_note_idx = nxt
            self.note_label.config(text=NOTES[self.target_note_idx], fg=TEXT_COLOUR)
            
            p1, p2 = "", ""
            if self.toggles['hand']: p1 = f"{random.choice(HANDS)} | "
            if self.toggles['finger']: p2 = f"{random.choice(FINGERS)}"
            
            if not p1 and not p2:
                p1 = "Any Hand | Any Finger"
            
            self.inst_part1.config(text=p1)
            self.inst_part2.config(text=p2)
        
        self.trigger_plot_update()

if __name__ == "__main__":
    root = tk.Tk()
    app = MidiGameApp(root)
    root.mainloop()