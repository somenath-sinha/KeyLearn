# game_engine.py
import time
import random
import json
from config import *

class GameEngine:
    def __init__(self):
        # Persistent Settings
        self.mode = MODES[-1]
        self.octaves = 5
        self.buffer = '200ms'
        self.lowest_c = None
        
        # Game State
        self.learning_lowest_c = False
        self.target_note_idx = None
        self.action_timer = None
        self.first_hit_time = None
        self.first_hit_response_time = None
        self.reaction_intervals = []
        self.hit_history = []
        self.octaves_played = set()
        
        # Level-Specific Trackers
        self.l3_pending_time = None
        self.l3_pending_octave = None
        self.l3_pending_velocity = None
        self.l4_sequence = []
        self.l4_progress = 0
        
        self.load_settings()

    def load_settings(self):
        try:
            with open('user_settings.json', 'r') as f:
                settings = json.load(f)
                self.mode = settings.get('mode', MODES[-1])
                self.octaves = int(settings.get('octaves', 5))
                self.buffer = settings.get('buffer', '200ms')
                self.lowest_c = settings.get('lowest_c', None)
        except (FileNotFoundError, json.JSONDecodeError, ValueError):
            pass

    def save_settings(self):
        settings = {
            'mode': self.mode,
            'octaves': str(self.octaves),
            'buffer': self.buffer,
            'lowest_c': self.lowest_c
        }
        with open('user_settings.json', 'w') as f:
            json.dump(settings, f)

    def get_target_max(self):
        if self.mode == 'Level 3: Bilateral Chords':
            return max(1, self.octaves - 1)
        elif self.mode == 'Level 4: Diatonic Run':
            return 1 
        return self.octaves

    def get_accuracy(self):
        total = len(self.hit_history)
        if total == 0: return "--"
        correct = sum(1 for h in self.hit_history if h['type'] == 'correct')
        return f"{(correct / total) * 100:.1f}%"
        
    def get_avg_interval(self):
        if not self.reaction_intervals: return "--"
        return f"{sum(self.reaction_intervals) / len(self.reaction_intervals):.2f}s"

    def force_recalibrate(self):
        self.lowest_c = None
        self.save_settings()

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

    def next_note(self, toggles):
        self.action_timer = time.time()
        self.first_hit_time = None
        self.first_hit_response_time = None
        self.reaction_intervals.clear()
        self.hit_history.clear()
        self.octaves_played.clear()
        
        prev_note = self.target_note_idx
        result = {'calibrate': False, 'note_text': '', 'inst1': '', 'inst2': ''}

        if self.mode == 'Level 4: Diatonic Run':
            if self.lowest_c is None:
                self.learning_lowest_c = True
                result['calibrate'] = True
                result['note_text'] = "Calibrate"
                result['inst1'] = "Play your leftmost C key "
                result['inst2'] = "(Lowest Octave)"
                return result
                
            min_midi = self.lowest_c
            max_midi = self.lowest_c + (self.octaves * 12)
            midpoint = self.lowest_c + (self.octaves * 12) / 2
            
            min_allowed = min_midi + 12 
            max_allowed = max_midi - 12 
            if max_allowed < min_allowed:
                min_allowed = min_midi
                max_allowed = max_midi
            
            while True:
                start_midi = random.randint(min_allowed, max_allowed)
                idx = start_midi % 12
                if idx not in WHITE_NOTE_INDICES or idx == prev_note: continue

                up = start_midi >= midpoint
                seq = self._generate_diatonic(start_midi, up)
                
                if all(min_midi <= n <= max_midi for n in seq):
                    self.target_note_idx = idx
                    self.l4_sequence = seq
                    start_octave = (start_midi // 12) - 2 
                    hand = "Right Hand" if up else "Left Hand"
                    result['inst1'] = f"{hand} | "
                    result['inst2'] = f"Octave {start_octave}"
                    break
            self.l4_progress = 0
            result['note_text'] = NOTES[self.target_note_idx]

        elif self.mode == 'Level 3: Bilateral Chords':
            while True:
                nxt = random.randint(0, 11)
                if nxt != prev_note: break
            self.target_note_idx = nxt
            self.l3_pending_time = None
            result['note_text'] = NOTES[self.target_note_idx]
            result['inst1'] = "Both Hands | "
            result['inst2'] = "Simultaneously"

        elif self.mode == 'Level 2: Strict Finger':
            while True:
                nxt = random.randint(0, 11)
                if nxt != prev_note: break
            self.target_note_idx = nxt
            result['note_text'] = NOTES[self.target_note_idx]
            result['inst1'] = f"{random.choice(HANDS)} | "
            result['inst2'] = f"{random.choice(FINGERS)}"

        elif self.mode == 'Level 1: Free Hunt':
            while True:
                nxt = random.randint(0, 11)
                if nxt != prev_note: break
            self.target_note_idx = nxt
            result['note_text'] = NOTES[self.target_note_idx]
            result['inst1'] = "Any Hand | "
            result['inst2'] = "Any Finger"

        else: # Unlocked Mode
            while True:
                nxt = random.randint(0, 11)
                if nxt != prev_note: break
            self.target_note_idx = nxt
            result['note_text'] = NOTES[self.target_note_idx]
            
            p1, p2 = "", ""
            if toggles['hand']: p1 = f"{random.choice(HANDS)} | "
            if toggles['finger']: p2 = f"{random.choice(FINGERS)}"
            
            if not p1 and not p2:
                p1 = "Any Hand | Any Finger"
            
            result['inst1'] = p1
            result['inst2'] = p2
            
        return result

    def _record_correct(self, velocity, response_time, sync_time=None):
        self.hit_history.append({'type': 'correct', 'velocity': velocity, 'response_time': response_time, 'sync_time': sync_time})

    def _record_wrong(self, velocity, response_time):
        self.hit_history.append({'type': 'wrong', 'velocity': velocity, 'response_time': response_time})

    def process_midi_msg(self, msg):
        resp = {'status': 'none', 'error_msg': '', 'octave': (msg.note // 12) - 2}
        
        if self.learning_lowest_c:
            if msg.note % 12 == 0:
                self.lowest_c = msg.note
                self.save_settings()
                self.learning_lowest_c = False
                resp['status'] = 'calibrated'
            else:
                resp['status'] = 'wrong'
                resp['error_msg'] = "Press a C key to calibrate."
            return resp

        if self.target_note_idx is None: return resp
        target_max = self.get_target_max()
        if len(self.octaves_played) >= target_max: return resp

        note_idx = msg.note % 12
        octave = resp['octave']
        current_time = time.time()
        response_time = current_time - self.action_timer

        if self.mode == 'Level 3: Bilateral Chords':
            self._handle_level_3(msg, note_idx, octave, current_time, response_time, target_max, resp)
        elif self.mode == 'Level 4: Diatonic Run':
            self._handle_level_4(msg, note_idx, octave, current_time, response_time, target_max, resp)
        else:
            self._handle_standard(msg, note_idx, octave, current_time, response_time, target_max, resp)

        return resp

    def _handle_standard(self, msg, note_idx, octave, current_time, response_time, target_max, resp):
        if note_idx == self.target_note_idx:
            self.action_timer = current_time
            if self.first_hit_time is None:
                self.first_hit_time = current_time
                self.first_hit_response_time = response_time
            else:
                self.reaction_intervals.append(response_time)

            self._record_correct(msg.velocity, response_time)
            self.octaves_played.add(octave)
            
            if len(self.octaves_played) >= target_max:
                resp['status'] = 'done'
            else:
                resp['status'] = 'correct'
        else:
            self._record_wrong(msg.velocity, response_time)
            resp['status'] = 'wrong'
            resp['error_msg'] = f"Played {NOTES[note_idx]}{octave}, expected {NOTES[self.target_note_idx]}"

    def _handle_level_3(self, msg, note_idx, octave, current_time, response_time, target_max, resp):
        buffer_limit = BUFFER_TIMES[self.buffer]

        if note_idx == self.target_note_idx:
            if self.l3_pending_time is None:
                self.l3_pending_time = current_time
                self.l3_pending_octave = octave
                self.l3_pending_velocity = msg.velocity
                resp['status'] = 'correct' 
            else:
                sync_delta = current_time - self.l3_pending_time
                if sync_delta <= buffer_limit and octave != self.l3_pending_octave:
                    self.action_timer = current_time
                    # Pass both velocities as a tuple instead of averaging
                    self._record_correct((self.l3_pending_velocity, msg.velocity), response_time, sync_delta)
                    
                    self.octaves_played.add(min(octave, self.l3_pending_octave))
                    self.l3_pending_time = None 
                    
                    if len(self.octaves_played) >= target_max:
                        resp['status'] = 'done'
                    else:
                        resp['status'] = 'correct'
                else:
                    self._record_wrong(msg.velocity, response_time)
                    resp['status'] = 'wrong'
                    if octave == self.l3_pending_octave:
                        resp['error_msg'] = f"Played {NOTES[note_idx]}{octave} twice, expected separate octave"
                    else:
                        resp['error_msg'] = f"Missed sync window ({sync_delta*1000:.0f}ms)"
                    self.l3_pending_time = current_time
                    self.l3_pending_octave = octave
        else:
            self._record_wrong(msg.velocity, response_time)
            resp['status'] = 'wrong'
            resp['error_msg'] = f"Played {NOTES[note_idx]}{octave}, expected {NOTES[self.target_note_idx]}"

    def _handle_level_4(self, msg, note_idx, octave, current_time, response_time, target_max, resp):
        expected_midi = self.l4_sequence[self.l4_progress]
        expected_name = NOTES[expected_midi % 12]
        expected_oct = (expected_midi // 12) - 2
        
        if msg.note == expected_midi:
            self.action_timer = current_time
            if self.first_hit_time is None:
                self.first_hit_time = current_time
                self.first_hit_response_time = response_time
            
            self._record_correct(msg.velocity, response_time)
            self.l4_progress += 1

            if self.l4_progress >= 9:
                self.octaves_played.add(len(self.octaves_played)) 
                self.l4_progress = 0 
                if len(self.octaves_played) >= target_max:
                    resp['status'] = 'done'
                else:
                    resp['status'] = 'correct'
            else:
                resp['status'] = 'correct'
        else:
            self._record_wrong(msg.velocity, response_time)
            resp['status'] = 'wrong'
            resp['error_msg'] = f"Played {NOTES[note_idx]}{octave}, expected {expected_name}{expected_oct}"