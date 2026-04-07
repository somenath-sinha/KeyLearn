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