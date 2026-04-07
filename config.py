# config.py

NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
WHITE_NOTE_INDICES = [0, 2, 4, 5, 7, 9, 11] # C, D, E, F, G, A, B

HANDS = ['Left Hand', 'Right Hand']
FINGERS = ['1 (Thumb)', '2 (Index)', '3 (Middle)', '4 (Ring)', '5 (Pinky)']

MODES = [
    'Level 1: Free Hunt',
    'Level 2: Strict Finger',
    'Level 3: Bilateral Chords',
    'Level 4: Diatonic Run',
    'Unlocked Mode'
]

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
TOGGLE_OFF = '#3E4451'
TOGGLE_ON = '#61AFEF'
TOOLTIP_BG = '#1E2227'