# main.py
import tkinter as tk
from tkinter import ttk, messagebox
import os

from config import *
from midi_engine import MidiEngine
from plot_engine import PlotEngine
from game_engine import GameEngine

class MidiGameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MIDI Note Hunter Pro")
        self.root.geometry("650x950") 
        self.root.configure(bg=BG_COLOUR)
        self.root.resizable(False, False)
        
        self._configure_styles()

        self.main_frame = ttk.Frame(self.root, padding="20 20 20 20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.engine = GameEngine()
        
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
        
        # --- New Live Mode Display ---
        self.mode_disp = ttk.Label(header_frame, text=self.engine.mode, font=("Helvetica", 14, "bold"), foreground=ACCENT_COLOUR)
        self.mode_disp.pack(side=tk.LEFT)
        
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
        self.octave_label = ttk.Label(stats_frame, text=f"Progress: 0 / {self.engine.get_target_max()}", font=("Helvetica", 12))
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
        if self.engine.mode == 'Unlocked Mode':
            self.hand_btn.config(state=tk.NORMAL)
            self.finger_btn.config(state=tk.NORMAL)
        else:
            self.hand_btn.config(state=tk.DISABLED)
            self.finger_btn.config(state=tk.DISABLED)

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
        self.plotter.update_plots(self.engine.hit_history, self.toggles['wrong_notes'])

    def open_settings_window(self):
        set_win = tk.Toplevel(self.root)
        set_win.title("Settings")
        set_win.geometry("450x420")
        set_win.configure(bg=BG_COLOUR)
        
        frame = ttk.Frame(set_win, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Game Mode:", font=("Helvetica", 12)).pack(anchor=tk.W)
        mode_var = tk.StringVar(value=self.engine.mode)
        mode_dropdown = ttk.Combobox(frame, textvariable=mode_var, state="readonly", takefocus=False)
        mode_dropdown['values'] = MODES
        mode_dropdown.pack(fill=tk.X, pady=(0, 5))

        rules_label = tk.Label(frame, text="", bg=BG_COLOUR, fg=TEXT_COLOUR, wraplength=400, justify=tk.LEFT)
        rules_label.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(frame, text="Target Actions (Octaves/Runs):", font=("Helvetica", 12)).pack(anchor=tk.W)
        oct_var = tk.StringVar(value=str(self.engine.octaves))
        oct_dropdown = ttk.Combobox(frame, textvariable=oct_var, state="readonly", takefocus=False)
        oct_dropdown.pack(fill=tk.X, pady=(0, 10))

        def update_rules(event=None):
            mode = mode_var.get()
            rules_label.config(text=LEVEL_RULES.get(mode, ""))
            if mode == 'Level 3: Bilateral Chords':
                oct_dropdown['values'] = [str(i) for i in range(2, 8)]
                if oct_var.get() == "1":
                    oct_var.set("2")
            else:
                oct_dropdown['values'] = [str(i) for i in range(1, 8)]
        
        mode_dropdown.bind('<<ComboboxSelected>>', update_rules)
        update_rules()

        ttk.Label(frame, text="Level 3 Chord Timing Buffer:", font=("Helvetica", 12)).pack(anchor=tk.W)
        buffer_var = tk.StringVar(value=self.engine.buffer)
        buffer_dropdown = ttk.Combobox(frame, textvariable=buffer_var, state="readonly", takefocus=False)
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

        def do_recalibrate():
            self.engine.force_recalibrate()
            set_win.destroy()
            if self.engine.mode == 'Level 4: Diatonic Run':
                self.next_note()

        ttk.Button(frame, text="Recalibrate Lowest C (Level 4)", command=do_recalibrate, takefocus=False).pack(fill=tk.X, pady=(0, 15))

        def apply_and_close():
            self.connect_midi(port_var.get())
            self.engine.mode = mode_var.get()
            self.engine.octaves = int(oct_var.get())
            self.engine.buffer = buffer_var.get()
            self.engine.save_settings()
            
            # Update the UI components
            self.mode_disp.config(text=self.engine.mode)
            self.update_toggle_states()
            self.octave_label.config(text=f"Progress: {len(self.engine.octaves_played)} / {self.engine.get_target_max()}")
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
            self.root.after(250, lambda: self.note_label.config(fg=TEXT_COLOUR) if len(self.engine.octaves_played) < self.engine.get_target_max() else None)

    def process_midi_msg(self, msg):
        resp = self.engine.process_midi_msg(msg)
        if resp['status'] == 'none': return
        
        self.current_octave_disp.config(text=f"Current Octave: {resp['octave']}")
        
        if resp['error_msg']:
            self.error_msg_disp.config(text=resp['error_msg'])
        else:
            self.error_msg_disp.config(text="")

        if resp['status'] == 'calibrated':
            self.note_label.config(text="Calibrated!", fg=ACCENT_COLOUR)
            self.root.after(1000, self.next_note)
            return

        if resp['status'] == 'wrong':
            self.flash_error()
            os.system("afplay /System/Library/Sounds/Basso.aiff &")
        
        if resp['status'] == 'done':
            self.note_label.config(text="Done!", fg=ACCENT_COLOUR)
            self.inst_part1.config(text="Press Spacebar for next note")
            self.inst_part2.config(text="")

        if resp['status'] in ['correct', 'done']:
            if self.engine.first_hit_response_time:
                self.time_label.config(text=f"1st Hit: {self.engine.first_hit_response_time:.2f}s")
                self.note_label.config(fg=ACCENT_COLOUR)

        self.avg_time_label.config(text=f"Avg Interval: {self.engine.get_avg_interval()}")
        self.acc_label.config(text=f"Accuracy: {self.engine.get_accuracy()}")
        self.octave_label.config(text=f"Progress: {len(self.engine.octaves_played)} / {self.engine.get_target_max()}")
        self.trigger_plot_update()

    def next_note(self):
        result = self.engine.next_note(self.toggles)
        
        self.time_label.config(text="1st Hit: --")
        self.avg_time_label.config(text="Avg Interval: --")
        self.acc_label.config(text="Accuracy: --")
        self.octave_label.config(text=f"Progress: 0 / {self.engine.get_target_max()}")
        self.error_msg_disp.config(text="") 
        
        self.note_label.config(text=result['note_text'], fg=TEXT_COLOUR)
        self.inst_part1.config(text=result['inst1'])
        self.inst_part2.config(text=result['inst2'])
        
        if not result['calibrate']:
            self.trigger_plot_update()

if __name__ == "__main__":
    root = tk.Tk()
    app = MidiGameApp(root)
    root.mainloop()