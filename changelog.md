# Ver 1.0.0
Basic app

## Ver 1.1.0

* The Mac Audio: Wired in os.system("afplay /System/Library/Sounds/Basso.aiff &"). When you hit the wrong key, your Mac will play its native, low-pitched "Basso" thud.

* The Embedded Canvas: Matplotlib is now using the FigureCanvasTkAgg backend, which effectively renders the graph as a standard UI element right below the buttons.

* Live Sequential Plotting: The logic now uses a hit_history list. The x-axis tracks the chronological sequence of the hits (1st hit, 2nd hit, etc.), and the y-axis shows the velocity.

* The Tickbox Toggle: You'll see a new tickbox under your finger/hand suggestions. If you switch it on, any fluffed notes will immediately appear on the timeline as red crosses, correctly maintaining their chronological position between your successful hits!

## Ver 1.2.0

### Added
* **MIDI Device Management:** Introduced a dedicated "Devices" button in the primary interface header, launching a secondary window for explicit MIDI connection management.
* **Auto-Connect:** Implemented functionality to automatically detect and connect to the first available MIDI input device upon application launch.
* **Advanced Tracking:** Introduced an "Average Interval" metric to calculate and display the running average time taken to strike subsequent octaves after the initial target note hit.
* **Key Binding:** Bound the application's core "next note" generation function to the Spacebar, enabling hands-free progression.

### Changed
* **UI Overhaul (Toggles):** Replaced native macOS checkboxes with custom, flat toggle buttons displaying explicit "ON/OFF" states to resolve underlying dark mode rendering conflicts.
* **Layout Adjustments:** Relocated the "Hand" and "Finger" toggle buttons to a horizontal alignment beneath the main header. Repositioned the "Show Incorrect Notes" toggle to sit directly above the embedded Matplotlib graph.

### Fixed
* **Graph Styling:** Explicitly defined text colours for the Matplotlib graph's axes, title, and tick marks to ensure complete visibility and contrast against the application's dark UI theme.

## [v1.2.1]

### Fixed
* **Toggle State Sync:** Resolved an underlying bug where the "Show Incorrect Notes" toggle failed to render missed notes on the graph. This was caused by Tkinter's native `tk.BooleanVar` losing reference tracking; state management has been entirely refactored to use standard Python boolean dictionaries.
* **Graph Styling Persistence:** Fixed a visual glitch where the embedded Matplotlib graph would lose its dark mode styling (background and spines) upon redrawing. Styling properties are now correctly re-injected via `apply_graph_styling()` immediately following the `ax.clear()` command.

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
* **Response Time Formatting:** Replaced standard scientific notation (e.g., $3 \times 10^0$) on the response time y-axis with a custom, human-readable time formatter applied to both major and minor ticks (e.g., 0.5s, 1s, 3s, 1m).
* **UI Styling:** Overhauled the Combobox rendering style to enforce dark-mode compliance, removing the default cream background.

### Fixed
* **Spacebar Focus Hijacking:** Resolved an event-bubbling issue where pressing the spacebar activated the last-clicked UI button instead of generating a note.

## [v1.4.0]

### Added
* **Response Time Tooltips:** Implemented interactive hover annotations on the response time bar chart to display exact intervals dynamically formatted in seconds (s) or milliseconds (ms).

### Changed
* **Window Management:** Disabled the maximize button to prevent the application from entering full-screen mode on macOS, locking the UI layout proportions.

### Fixed
* **Hover Annotations Sync:** Fixed an issue where tooltips for velocity and response time stopped appearing after the first note was played. This was resolved by re-initializing the annotation objects upon clearing and redrawing the Matplotlib axes.
* **Log Scale Granularity:** Enhanced the response time graph's y-axis by injecting a custom `FixedLocator`, ensuring visible gradations explicitly between the 1s and 2s intervals (e.g., 1.2s, 1.4s) where response times frequently cluster.
* **Logarithmic Formatter Override:** Resolved a persistent rendering bug where Matplotlib reverted the response time y-axis to scientific notation (e.g., 10^0) by enforcing the custom human-readable time formatter strictly *after* the logarithmic scale is instantiated on each redraw.
* **Action Timer Logic & Visual Error Tracking:** Modified the core timing loop so that incorrect notes no longer reset the interval timer, whilst restoring incorrect hits to the response time graph. This creates a visual "struggle stack"—fluffed notes will plot as increasingly tall red bars, culminating in an accurately measured green bar reflecting the total time taken to successfully hunt down the correct octave.


# [v2.0.0] - The Curriculum & Architecture Update

### Architecture & Persistence
* **Modular Refactor:** Completely restructured the monolithic script into a scalable four-module architecture (`main.py`, `config.py`, `midi_engine.py`, `plot_engine.py`) to separate the UI, hardware interfacing, data rendering, and state management.
* **Persistent Configuration:** Introduced automated local saving via `user_settings.json`. The application now silently saves and reloads the user's preferred Game Mode, Target Octaves, and Chord Timing Buffer between sessions.

### Structured Learning Modes
* **Game Modes Engine:** Replaced the infinite sandbox with a structured, selectable curriculum:
  * **Level 1 (Free Hunt):** Focuses on basic spatial awareness. Hand and finger constraints are explicitly disabled.
  * **Level 2 (Strict Finger):** Focuses on explicit digit targeting. The application dictates exactly which hand and finger must be used.
  * **Level 3 (Bilateral Chords):** Focuses on simultaneous execution. The user must strike the target note with both hands within a configurable time buffer (50ms to 4s).
  * **Level 4 (Diatonic Run):** Focuses on sequential dexterity. The application requests a 9-note diatonic run (1-2-3-4-5-4-3-2-1) starting from a specific white key.
  * **Unlocked Mode:** Retains the original sandbox functionality, allowing manual toggling of Hand and Finger constraints.

### Analytics & Visualizations
* **Dual Embedded Graphs:** Integrated Matplotlib directly into the Tkinter UI to provide real-time, interactive analytics without opening external windows.
* **Velocity Tracking:** Plotted as a sequential scatter graph, highlighting correct strikes (green) and missed notes (red).
* **Response Time Tracking (Log Scale):** Plotted as a sequential bar chart using a logarithmic scale to prevent massive outliers from breaking the visual hierarchy. Formatted with custom, human-readable time ticks (e.g., 0.5s, 1s, 2s).
* **Penalty Visualisation:** Incorrect notes are now plotted on the response graph as accumulating red bars without resetting the underlying interval stopwatch, creating a visual "struggle stack" until the correct note is struck.
* **Interactive Tooltips:** Added dynamically updating hover annotations to both graphs to reveal exact velocity integers and precise response times (in seconds or milliseconds).
* **Accuracy Metric:** Added a real-time percentage tracker mapping correct hits against total keystrokes.

### UI / UX Enhancements
* **Dark Mode Enforcement:** Overhauled the Tkinter rendering engine using the `clam` theme to completely resolve macOS dark mode conflicts (e.g., invisible text, cream-coloured hover states, and white comboboxes).
* **Spacebar Binding:** Bound the application's core "next note" progression directly to the Spacebar, enabling entirely hands-free operation across the keyboard. Resolved an event-bubbling issue to ensure the spacebar does not accidentally trigger focused UI buttons.
* **Dynamic Interface:** The UI now intelligently locks or unlocks the "Hand" and "Finger" UI toggles based on the strictness of the currently selected Game Mode.
* **Collapsible Analytics:** Added independent "ON/OFF" toggles for both the Velocity and Response Time graphs, allowing the user to collapse the analytics panels to save screen real estate. 
* **Audio & Visual Feedback:** Fluffs and missed notes immediately trigger a red flash on the target text and simultaneously play the native macOS `Basso.aiff` low-thud alert.
* **Window Management:** Disabled the maximize button to prevent macOS from hijacking the window into full-screen mode, preserving the intended application proportions.

### MIDI & Hardware Integration
* **Centralised Settings:** Created a dedicated "⚙ Settings" popup window to consolidate MIDI Device selection, Target Octaves (capped at a realistic 7), Game Mode selection, and Level 3 Timing Buffers.
* **Auto-Connect:** Implemented functionality to automatically detect and bind to the first available MIDI input device upon application launch.