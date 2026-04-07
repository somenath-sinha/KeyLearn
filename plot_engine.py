# plot_engine.py
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import MaxNLocator, FuncFormatter, FixedLocator, NullFormatter
from config import *

class PlotEngine:
    def __init__(self, vel_container, resp_container):
        self.fig_vel = Figure(figsize=(5, 2.75), dpi=100)
        self.fig_vel.patch.set_facecolor(BG_COLOUR)
        self.ax_vel = self.fig_vel.add_subplot(111)
        self.canvas_vel = FigureCanvasTkAgg(self.fig_vel, master=vel_container)
        self.canvas_vel.get_tk_widget().pack(fill="both", expand=True)

        self.fig_resp = Figure(figsize=(5, 2.75), dpi=100)
        self.fig_resp.patch.set_facecolor(BG_COLOUR)
        self.ax_resp = self.fig_resp.add_subplot(111)
        self.canvas_resp = FigureCanvasTkAgg(self.fig_resp, master=resp_container)
        self.canvas_resp.get_tk_widget().pack(fill="both", expand=True)

        # Separate Scatter Series
        self.sc_single = None
        self.sc_L = None
        self.sc_R = None
        self.sc_wrong = None
        
        self.bars = []
        self.bars_sync = []
        self.bar_data = []

        self.annot_vel = self.ax_vel.annotate("", xy=(0,0), xytext=(10,10), textcoords="offset points",
                                     bbox=dict(boxstyle="round", fc=TOOLTIP_BG, ec=TEXT_COLOUR, alpha=0.9), color=TEXT_COLOUR, zorder=10)
        self.annot_vel.set_visible(False)
        self.canvas_vel.mpl_connect("motion_notify_event", self.on_hover_vel)

        self.annot_resp = self.ax_resp.annotate("", xy=(0,0), xytext=(0,10), textcoords="offset points",
                                     bbox=dict(boxstyle="round", fc=TOOLTIP_BG, ec=TEXT_COLOUR, alpha=0.9), color=TEXT_COLOUR, zorder=10, ha='center')
        self.annot_resp.set_visible(False)
        self.canvas_resp.mpl_connect("motion_notify_event", self.on_hover_resp)

    def format_time_ticks(self, x, pos):
        if x >= 60: return f"{int(x//60)}m"
        elif x > 0: return f"{x:g}s"
        return "0s"

    def apply_styling(self):
        self.ax_vel.set_facecolor('#1E2227') 
        self.ax_vel.spines['top'].set_visible(False)
        self.ax_vel.spines['right'].set_visible(False)
        self.ax_vel.spines['bottom'].set_color(TEXT_COLOUR)
        self.ax_vel.spines['left'].set_color(TEXT_COLOUR)
        self.ax_vel.tick_params(colors=TEXT_COLOUR, which='both') 
        self.ax_vel.xaxis.set_major_locator(MaxNLocator(integer=True))
        self.ax_vel.set_title("Velocity Tracking", pad=10, color=TEXT_COLOUR)
        self.ax_vel.set_ylim(0, 130)
        self.ax_vel.set_ylabel("Velocity", color=TEXT_COLOUR)
        
        self.ax_resp.set_facecolor('#1E2227') 
        self.ax_resp.spines['top'].set_visible(False)
        self.ax_resp.spines['right'].set_visible(False)
        self.ax_resp.spines['bottom'].set_color(TEXT_COLOUR)
        self.ax_resp.spines['left'].set_color(TEXT_COLOUR)
        self.ax_resp.tick_params(colors=TEXT_COLOUR, which='both') 
        self.ax_resp.xaxis.set_major_locator(MaxNLocator(integer=True))
        self.ax_resp.set_title("Response Time Interval (Log Scale)", pad=10, color=TEXT_COLOUR)
        self.ax_resp.set_ylabel("Time", color=TEXT_COLOUR)
        self.ax_resp.set_xlabel("Hit Sequence", color=TEXT_COLOUR)
        
        self.ax_resp.set_yscale('log')
        formatter = FuncFormatter(self.format_time_ticks)
        
        # Explicitly define which ticks get text labels to prevent overlapping
        labeled_ticks = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
        self.ax_resp.yaxis.set_major_locator(FixedLocator(labeled_ticks))
        self.ax_resp.yaxis.set_major_formatter(formatter)
        
        # Keep granular ticks for visual scale guidance, but mute their text
        custom_minor_ticks = [
            0.2, 0.3, 0.4, 0.6, 0.7, 0.8, 0.9,
            1.5, 3.0, 4.0, 15.0, 20.0, 40.0, 50.0
        ]
        self.ax_resp.yaxis.set_minor_locator(FixedLocator(custom_minor_ticks))
        self.ax_resp.yaxis.set_minor_formatter(NullFormatter())

    def update_plots(self, hit_history, show_wrong):
        self.ax_vel.clear()
        self.ax_resp.clear()
        
        x_single, y_single = [], []
        x_L, y_L = [], []
        x_R, y_R = [], []
        x_line, y_line = [], []
        x_wrong, y_wrong = [], []
        
        x_all, y_response, bar_colors = [], [], []
        self.bar_data = []
        
        for i, hit in enumerate(hit_history):
            hit_index = i + 1
            if hit['type'] == 'correct':
                if isinstance(hit['velocity'], (list, tuple)):
                    x_L.append(hit_index)
                    y_L.append(hit['velocity'][0])
                    x_R.append(hit_index)
                    y_R.append(hit['velocity'][1])
                    
                    x_line.append(hit_index)
                    y_line.append(sum(hit['velocity']) / 2) 
                else:
                    x_single.append(hit_index)
                    y_single.append(hit['velocity'])
                    x_line.append(hit_index)
                    y_line.append(hit['velocity'])
                
                x_all.append(hit_index)
                y_response.append(hit['response_time'])
                bar_colors.append(ACCENT_COLOUR)
                self.bar_data.append({'x': hit_index, 'resp': hit['response_time'], 'sync': hit.get('sync_time')})
                
            elif hit['type'] == 'wrong' and show_wrong:
                x_wrong.append(hit_index)
                y_wrong.append(hit['velocity'])
                x_all.append(hit_index)
                y_response.append(hit['response_time'])
                bar_colors.append(ERROR_COLOUR)
                self.bar_data.append({'x': hit_index, 'resp': hit['response_time'], 'sync': None})
                
        self.sc_single = None
        self.sc_L = None
        self.sc_R = None
        self.sc_wrong = None
        self.bars = []
        self.bars_sync = []
        
        if x_line:
            self.ax_vel.plot(x_line, y_line, color=ACCENT_COLOUR, alpha=0.4, zorder=1)
            
        if x_single:
            self.sc_single = self.ax_vel.scatter(x_single, y_single, color=ACCENT_COLOUR, s=50, zorder=2, label="Target Note")
            
        if x_L:
            self.sc_L = self.ax_vel.scatter(x_L, y_L, color=ACCENT_COLOUR, s=50, zorder=2)
            
        if x_R:
            self.sc_R = self.ax_vel.scatter(x_R, y_R, color=ACCENT_COLOUR, s=50, zorder=2)
            
        if x_wrong:
            self.sc_wrong = self.ax_vel.scatter(x_wrong, y_wrong, color=ERROR_COLOUR, s=50, marker='x', zorder=3, label="Missed Note")
            
        if x_single or x_wrong or x_L:
            handles, labels = self.ax_vel.get_legend_handles_labels()
            by_label = dict(zip(labels, handles))
            self.ax_vel.legend(by_label.values(), by_label.keys(), loc="lower right", facecolor=BG_COLOUR, edgecolor=TEXT_COLOUR, labelcolor=TEXT_COLOUR)
            
        if x_all:
            self.bars = self.ax_resp.bar(x_all, y_response, color=bar_colors, alpha=0.8, width=0.5)
            
            x_sync, y_sync = [], []
            for d in self.bar_data:
                if d['sync']:
                    x_sync.append(d['x'])
                    y_sync.append(d['sync'])
            if x_sync:
                self.bars_sync = self.ax_resp.bar(x_sync, y_sync, color=SYNC_COLOUR, alpha=1.0, width=0.2)

        self.apply_styling() 

        self.annot_vel = self.ax_vel.annotate("", xy=(0,0), xytext=(10,10), textcoords="offset points",
                                     bbox=dict(boxstyle="round", fc=TOOLTIP_BG, ec=TEXT_COLOUR, alpha=0.9), color=TEXT_COLOUR, zorder=10)
        self.annot_vel.set_visible(False)

        self.annot_resp = self.ax_resp.annotate("", xy=(0,0), xytext=(0,10), textcoords="offset points",
                                     bbox=dict(boxstyle="round", fc=TOOLTIP_BG, ec=TEXT_COLOUR, alpha=0.9), color=TEXT_COLOUR, zorder=10, ha='center')
        self.annot_resp.set_visible(False)

        self.canvas_vel.draw()
        self.canvas_resp.draw()

    def on_hover_vel(self, event):
        vis = self.annot_vel.get_visible()
        if event.inaxes == self.ax_vel:
            found = False
            
            if self.sc_L:
                cont, ind = self.sc_L.contains(event)
                if cont:
                    pos = self.sc_L.get_offsets()[ind["ind"][0]]
                    self.annot_vel.xy = pos
                    self.annot_vel.set_text(f"L Vel: {int(pos[1])}")
                    self.annot_vel.set_visible(True)
                    self.canvas_vel.draw_idle()
                    found = True
                    
            if not found and self.sc_R:
                cont, ind = self.sc_R.contains(event)
                if cont:
                    pos = self.sc_R.get_offsets()[ind["ind"][0]]
                    self.annot_vel.xy = pos
                    self.annot_vel.set_text(f"R Vel: {int(pos[1])}")
                    self.annot_vel.set_visible(True)
                    self.canvas_vel.draw_idle()
                    found = True
                    
            if not found and self.sc_single:
                cont, ind = self.sc_single.contains(event)
                if cont:
                    pos = self.sc_single.get_offsets()[ind["ind"][0]]
                    self.annot_vel.xy = pos
                    self.annot_vel.set_text(f"Vel: {int(pos[1])}")
                    self.annot_vel.set_visible(True)
                    self.canvas_vel.draw_idle()
                    found = True
                    
            if not found and self.sc_wrong:
                cont, ind = self.sc_wrong.contains(event)
                if cont:
                    pos = self.sc_wrong.get_offsets()[ind["ind"][0]]
                    self.annot_vel.xy = pos
                    self.annot_vel.set_text(f"Vel: {int(pos[1])}")
                    self.annot_vel.set_visible(True)
                    self.canvas_vel.draw_idle()
                    found = True

            if not found and vis:
                self.annot_vel.set_visible(False)
                self.canvas_vel.draw_idle()

    def on_hover_resp(self, event):
        vis = self.annot_resp.get_visible()
        if event.inaxes == self.ax_resp:
            hovered = False
            for bar in self.bars:
                cont, _ = bar.contains(event)
                if cont:
                    x_val = bar.get_x() + bar.get_width() / 2
                    bd = next((d for d in self.bar_data if abs(d['x'] - x_val) < 0.1), None)
                    if bd:
                        text = f"Resp: {bd['resp']:.2f}s"
                        if bd['sync']:
                            text += f"\nSync: {bd['sync']*1000:.0f}ms"
                        
                        height = bar.get_height()
                        self.annot_resp.xy = (x_val, height)
                        self.annot_resp.set_text(text)
                        self.annot_resp.set_visible(True)
                        self.canvas_resp.draw_idle()
                        hovered = True
                        break
            if not hovered and vis:
                self.annot_resp.set_visible(False)
                self.canvas_resp.draw_idle()
        else:
            if vis:
                self.annot_resp.set_visible(False)
                self.canvas_resp.draw_idle()