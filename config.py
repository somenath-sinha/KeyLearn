# config.py

NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
WHITE_NOTE_INDICES = [0, 2, 4, 5, 7, 9, 11]

HANDS = ['Left Hand', 'Right Hand']
FINGERS = ['1 (Thumb)', '2 (Index)', '3 (Middle)', '4 (Ring)', '5 (Pinky)']

MODES = [
    'Level 1: Free Hunt',
    'Level 2: Strict Finger',
    'Level 3: Bilateral Chords',
    'Level 4: Diatonic Run',
    'Unlocked Mode'
]

LEVEL_RULES = {
    'Level 1: Free Hunt': "Think of the note and hit it across the keyboard using any finger. Builds spatial awareness.",
    'Level 2: Strict Finger': "Hit the note using the specific assigned finger across the keyboard. Builds digit coordination.",
    'Level 3: Bilateral Chords': "Hit the note with both hands simultaneously in different octaves. Target count is reduced by 1.",
    'Level 4: Diatonic Run': "Play a 9-note consecutive run (1-2-3-4-5-4-3-2-1) starting from the given note and octave.",
    'Unlocked Mode': "Free practice mode. Manually toggle hand and finger constraints as you see fit."
}

BUFFER_TIMES = {
    '50ms': 0.05,
    '100ms': 0.1,
    '200ms': 0.2,
    '500ms': 0.5,
    '1s': 1.0,
    '2s': 2.0,
    '3s': 3.0,
    '4s': 4.0
}

# Dark Theme Colours
BG_COLOUR = '#282C34'
TEXT_COLOUR = '#ABB2BF'
ACCENT_COLOUR = '#98C379' 
ERROR_COLOUR = '#E06C75'
SYNC_COLOUR = '#E5C07B'  
TOGGLE_OFF = '#3E4451'
TOGGLE_ON = '#61AFEF'
TOOLTIP_BG = '#1E2227'