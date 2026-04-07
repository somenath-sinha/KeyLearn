# Changelog

## [v2.3.4] - Mac App Packaging Hotfix

### Fixed
* **Settings Persistence in Packaged App:** Updated the `user_settings.json` save/load logic to use the user's root home directory (`~/.midi_hunter_settings.json`). This prevents macOS security from crashing the application when it attempts to write settings into its own read-only `.app` bundle after being compiled with PyInstaller.

## [v2.3.3] - UI Clutter Hotfix

### Fixed
* **Response Graph Axis Clutter:** Fixed a visual bug on the Response Time graph where forcing a custom text formatter onto every single minor logarithmic tick (e.g., 0.1s, 0.2s, 0.3s) caused massive text overlapping on the Y-axis. The graph now uses a targeted `FixedLocator` to strictly label only the most readable intervals (0.1s, 0.5s, 1s, 2s, 5s, etc.) while keeping the textless minor tick marks for visual guidance.

## [v2.3.2] - Level 3 Analytics Fix

### Fixed
* **Bilateral Velocity Tooltips:** Resolved an issue where Level 3 (Bilateral Chords) averaged the velocity of both keystrokes or left them ambiguously labeled. The engine now dynamically assigns the lower-octave note to the Left Hand and the higher-octave note to the Right Hand. These are plotted as two entirely separate data series, allowing the interactive tooltips to explicitly read "L Vel" and "R Vel" when hovering over the respective dots.

## [v2.3.1] - UI Reset & Analytics Hotfixes

### Fixed
* **Live Feedback Reset:** Fixed a UI bug where the "Current Octave" display would persist its value from the previous round. It now correctly resets to "--" upon pressing the spacebar to generate a new target note.
* **Bilateral Velocity Tracking (Level 3):** Resolved an issue where Level 3 (Bilateral Chords) averaged the velocity of both keystrokes into a single data point. The velocity graph now accurately plots both individual hand velocities simultaneously for a single chord strike (showing two vertical dots), while the underlying line graph smartly tracks the moving average between them to maintain visual flow.


## [v2.3.0] - The Architecture Refactor & UI Polish

### Added
* **Live Mode Display:** Added a persistent, boldly styled label to the top-left header of the application. This ensures the user always knows exactly which Game Level/Mode is currently active without having to open the settings menu.

### Changed
* **Logic Extraction:** Resolved Single Responsibility Principle violations in `main.py` by extracting all state management, settings persistence, keyboard calibration, and game loop logic into a new, dedicated `game_engine.py` module.
* **UI Simplification:** `main.py` now functions exclusively as a pure View/Controller layer. It handles drawing the Tkinter interface, capturing keystrokes/MIDI events, and routing them to the `GameEngine`, drastically reducing file size and improving maintainability for future expansions.

## [v2.2.0] - Keyboard Calibration & Logic Refinements

### Added
* **Live Octave Display:** Added an always-visible UI element that tracks and displays the current physical octave the user's hand is operating in based on their latest keystroke.
* **Explicit Error Logging:** Introduced a dynamic error readout text box. When a user fluffs a note, the UI now explicitly diagnoses the mistake (e.g., "Played D4, expected G"), immediately clearing the message upon a successful strike.
* **Keyboard Calibration (Level 4):** Introduced a one-time "Lowest C" calibration step for Level 4. On first load, the app asks the user to press their leftmost C key to learn the exact physical bounds of their specific keyboard. This is saved to `user_settings.json`.
* **Dynamic Hand Assignment (Level 4):** The app now uses the calibrated keyboard bounds to intelligently determine which hand to use for the Diatonic Run. Notes in the lower half of the keyboard enforce the Left Hand (running downwards), while notes in the upper half enforce the Right Hand (running upwards), ensuring the 9-note sequences never fall off the physical edge of the keys.
* **Recalibration Setting:** Added a "Recalibrate Lowest C" button inside the Settings menu so users can reset their keyboard bounds if they switch hardware.

### Changed
* **Octave Offset Correction:** Adjusted the global MIDI-to-Octave mathematical formula from `(msg.note // 12) - 1` to `(msg.note // 12) - 2`. This aligns the application with the Yamaha MIDI standard (where Middle C is C3 rather than C4), correcting the reported "3rd octave detected as 4th" bug.
* **Level 4 Target Constraints:** A Diatonic Run (Level 4) now only requires a single successful 9-note run (Target = 1) to complete the objective, ignoring the global target octaves setting.
* **Instruction UI Highlighting:** The specific actionable instruction (e.g., the exact finger, or the target octave) is now dynamically isolated and highlighted in the UI's green Accent Colour for significantly faster visual parsing during high-speed play.
* **Octave Targeting (Level 4):** Level 4 instructions now explicitly ask for an "Octave X" rather than a "Finger", utilizing the newly corrected octave formula.

### Fixed
* **Level 3 Octave Scaling Logic:** Explicitly enforced the (Target Octaves - 1) rule for Bilateral Chords, ensuring the objective correctly aligns with simultaneous dual-octave strikes, and hard-locked the minimum selectable octaves to 2 when this mode is active.

## [v2.1.0] - Enhanced Learning Modes & UI Refinements

### Added
* **Rules Explanation Box:** Added a dynamic text box to the Settings menu that updates to explicitly explain the physical rules and win-conditions of the currently selected level.
* **Instruction Highlighting:** Extracted the core instruction modifier (e.g., the specific finger or octave) into a distinct UI element, highlighted in the app's accent colour for rapid visual parsing during gameplay.
* **Bilateral Sync Tracking (Level 3):** Added a new data layer to calculate the exact millisecond differential between the left and right hand strikes. Plotted as an overlapping yellow bar within the response graph, with precise values added to the hover tooltips.

### Changed
* **Level 3 Target Scaling:** Reduced the target requirement by 1 (Target Octaves - 1) since two octaves are hit simultaneously. The `1 Octave` target setting is now dynamically disabled for this level.
* **Level 4 Anchoring & Sequencing:** Hand selection and sequence direction (up/down) are now determined dynamically based on a randomly selected starting octave relative to Middle C (MIDI 60). This ensures 9-note sequences never run off the physical edge of the user's keyboard. The app now explicitly asks for an "Octave" rather than a "Finger", and 1 full 9-note run equals 1 target point.
* **Mode Hierarchy:** Reordered the application hierarchy to push "Unlocked Mode" to the absolute bottom of the list, cementing the structured levels as the primary intended use-case.

### Fixed
* **Anti-Repetition Logic:** Enforced a global rule preventing the exact same note target from being generated twice in a row across all game modes to prevent stagnant gameplay.


## [v2.0.0] - The Curriculum & Architecture Update

### Added
* **Persistent Configuration:** Introduced automated local saving via `user_settings.json`. The application now silently saves and reloads the user's preferred Game Mode, Target Octaves, and Chord Timing Buffer between sessions.
* **Game Modes Engine:** Replaced the infinite sandbox with a structured, selectable curriculum (Level 1: Free Hunt, Level 2: Strict Finger, Level 3: Bilateral Chords, Level 4: Diatonic Run, Unlocked Mode).
* **Dual Embedded Graphs:** Integrated Matplotlib directly into the Tkinter UI to provide real-time, interactive analytics without opening external windows.
* **Velocity & Response Time Tracking:** Plotted as sequential scatter and logarithmic bar charts with custom, human-readable time ticks.
* **Interactive Tooltips:** Added dynamically updating hover annotations to both graphs to reveal exact velocity integers and precise response times.
* **Accuracy Metric:** Added a real-time percentage tracker mapping correct hits against total keystrokes.
* **Collapsible Analytics:** Added independent "ON/OFF" toggles for both the Velocity and Response Time graphs.
* **Audio & Visual Feedback:** Fluffs and missed notes immediately trigger a red flash on the target text and simultaneously play the native macOS `Basso.aiff` low-thud alert.
* **Auto-Connect:** Implemented functionality to automatically detect and bind to the first available MIDI input device upon application launch.

### Changed
* **Modular Refactor:** Completely restructured the monolithic script into a scalable four-module architecture (`main.py`, `config.py`, `midi_engine.py`, `plot_engine.py`).
* **Dark Mode Enforcement:** Overhauled the Tkinter rendering engine using the `clam` theme to completely resolve macOS dark mode conflicts.
* **Spacebar Binding:** Bound the application's core "next note" progression directly to the Spacebar, enabling entirely hands-free operation across the keyboard. 
* **Dynamic Interface:** The UI now intelligently locks or unlocks the "Hand" and "Finger" UI toggles based on the strictness of the currently selected Game Mode.
* **Window Management:** Disabled the maximize button to prevent macOS from hijacking the window into full-screen mode.
* **Centralised Settings:** Created a dedicated "⚙ Settings" popup window to consolidate UI controls.
* **Penalty Visualisation:** Incorrect notes are now plotted on the response graph as accumulating red bars without resetting the underlying interval stopwatch.


## [v1.4.0]

### Added
* **Response Time Tooltips:** Implemented interactive hover annotations on the response time bar chart to display exact intervals dynamically formatted in seconds (s) or milliseconds (ms).

### Changed
* **Window Management:** Disabled the maximize button to prevent the application from entering full-screen mode on macOS, locking the UI layout proportions.
* **Action Timer Logic & Visual Error Tracking:** Modified the core timing loop so that incorrect notes no longer reset the interval timer, whilst restoring incorrect hits to the response time graph. 

### Fixed
* **Hover Annotations Sync:** Fixed an issue where tooltips for velocity and response time stopped appearing after the first note was played. 
* **Log Scale Granularity:** Enhanced the response time graph's y-axis by injecting a custom `FixedLocator`, ensuring visible gradations explicitly between the 1s and 2s intervals.
* **Logarithmic Formatter Override:** Resolved a persistent rendering bug where Matplotlib reverted the response time y-axis to scientific notation (e.g., 10^0).


## [v1.3.0]

### Added
* **Target Octaves Selection:** Introduced a dropdown menu (now housed within the Settings window) to set the target number of octaves to hunt.
* **Completion Logic:** The script now halts MIDI hit registration and displays a "Done!" state once the target number of unique octaves has been played.
* **Response Time Graph:** Added a secondary, logarithmic bar chart beneath the velocity graph to plot the isolated response time between consecutive note strikes.
* **Hover Annotations:** Implemented interactive tooltips on the velocity graph to dynamically display exact MIDI velocity values on hover.
* **Visual Error Feedback:** Added a visual cue for missed notes, rapidly flashing the target note text red.
* **Accuracy Metric:** Introduced a real-time accuracy percentage tracker within the stats panel.
* **Individual Graph Visibility Toggles:** Added separate "Velocity: ON/OFF" and "Response: ON/OFF" toggles to independently collapse and hide each analytics graph.

### Changed
* **Settings Consolidation:** Renamed the "MIDI Devices" button to "⚙ Settings" and migrated the Octave Target selection dropdown into this popup.
* **Target Octave Limit:** Reduced the maximum selectable target octaves from 9 to 7, aligning strictly with the physical limits of an 88-key keyboard.
* **Response Time Formatting:** Replaced standard scientific notation (e.g., $3 \times 10^0$) on the response time y-axis with a custom, human-readable time formatter applied to both major and minor ticks.
* **UI Styling:** Overhauled the Combobox rendering style to enforce dark-mode compliance.

### Fixed
* **Spacebar Focus Hijacking:** Resolved an event-bubbling issue where pressing the spacebar activated the last-clicked UI button instead of generating a note.


## [v1.2.1]

### Fixed
* **Toggle State Sync:** Resolved an underlying bug where the "Show Incorrect Notes" toggle failed to render missed notes on the graph. 
* **Graph Styling Persistence:** Fixed a visual glitch where the embedded Matplotlib graph would lose its dark mode styling (background and spines) upon redrawing.


## [v1.2.0]

### Added
* **MIDI Device Management:** Introduced a dedicated "Devices" button in the primary interface header, launching a secondary window for explicit MIDI connection management.
* **Auto-Connect:** Implemented functionality to automatically detect and connect to the first available MIDI input device upon application launch.
* **Advanced Tracking:** Introduced an "Average Interval" metric to calculate and display the running average time taken to strike subsequent octaves.
* **Key Binding:** Bound the application's core "next note" generation function to the Spacebar.

### Changed
* **UI Overhaul (Toggles):** Replaced native macOS checkboxes with custom, flat toggle buttons displaying explicit "ON/OFF" states.
* **Layout Adjustments:** Relocated the "Hand" and "Finger" toggle buttons to a horizontal alignment beneath the main header. 

### Fixed
* **Graph Styling:** Explicitly defined text colours for the Matplotlib graph's axes, title, and tick marks to ensure complete visibility.


## [v1.1.0]

### Added
* **Audio Feedback:** Wired in native macOS audio (`afplay /System/Library/Sounds/Basso.aiff`) to play a low-pitched thud when an incorrect key is struck.
* **Error Tracking:** Added a tickbox toggle to display fluffed notes on the timeline as red crosses, maintaining chronological position between successful hits.

### Changed
* **Embedded Canvas:** Migrated Matplotlib to the `FigureCanvasTkAgg` backend, rendering the graph directly as a standard UI element.
* **Live Sequential Plotting:** Updated logic to use a `hit_history` list, tracking the chronological sequence of hits on the x-axis and velocity on the y-axis.


## [v1.0.0]

### Added
* **Initial Release:** Basic application structure featuring core MIDI note detection, tracking, and the primary "Note Hunter" game loop.