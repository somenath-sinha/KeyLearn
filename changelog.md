# Ver 1.0.0
Basic app

## Ver 1.1.0

* The Mac Audio: Wired in os.system("afplay /System/Library/Sounds/Basso.aiff &"). When you hit the wrong key, your Mac will play its native, low-pitched "Basso" thud.

* The Embedded Canvas: Matplotlib is now using the FigureCanvasTkAgg backend, which effectively renders the graph as a standard UI element right below the buttons.

* Live Sequential Plotting: The logic now uses a hit_history list. The x-axis tracks the chronological sequence of the hits (1st hit, 2nd hit, etc.), and the y-axis shows the velocity.

* The Tickbox Toggle: You'll see a new tickbox under your finger/hand suggestions. If you switch it on, any fluffed notes will immediately appear on the timeline as red crosses, correctly maintaining their chronological position between your successful hits!