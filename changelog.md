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