# plot_engine.py
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import MaxNLocator, FuncFormatter, FixedLocator
from config import *

class PlotEngine:
    def __init__(self, vel_container, resp_container):
        # Velocity Graph
        self.fig_vel = Figure(figsize=(5, 2.75), dpi=100)
        self.fig_vel.patch.set_facecolor(BG_COLOUR)
        self.ax_vel = self.fig_vel.add_subplot(111)
        self.canvas_vel = FigureCanvasTkAgg(self.fig_vel, master=vel_container)
        self.canvas_vel.get_tk_widget().pack(fill="both", expand=True)

        # Response Graph
        self.fig_resp = Figure(figsize=(5, 2.75), dpi=100)
        self.fig_resp.patch.set_facecolor(BG_COLOUR)
        self.ax_resp = self.fig_resp.add_subplot(111)
        self.canvas_resp = FigureCanvasTkAgg(self.fig_resp, master=resp_container)
        self.canvas_resp.get_tk_widget().pack(fill="both", expand=True)

        # State vars for hover
        self.sc_correct = None
        self.sc_wrong = None
        self.bars = []

        # Tooltips
        self.annot_vel = self.ax_vel.annotate("", xy=(0,0), xytext=(10,10), textcoords="offset points",
                                     bbox=dict(boxstyle="round", fc=TOOLTIP_BG, ec=TEXT_COLOUR, alpha=0.9),
                                     color=TEXT_COLOUR, zorder=10)
        self.annot_vel.set_visible(False)
        self.canvas_vel.mpl_connect("motion_notify_event", self.on_hover_vel)

        self.annot_resp = self.ax_resp.annotate("", xy=(0,0), xytext=(0,10), textcoords="offset points",
                                     bbox=dict(boxstyle="round", fc=TOOLTIP_BG, ec=TEXT_COLOUR, alpha=0.9),
                                     color=TEXT_COLOUR, zorder=10, ha='center')
        self.annot_resp.set_visible(False)
        self.canvas_resp.mpl_connect("motion_notify_event", self.on_hover_resp)

    def format_time_ticks(self, x, pos):
        if x >= 60: return f"{int(x//60)}m"
        elif x > 0: return f"{x:g}s"
        return "0s"

    def apply_styling(self):
        # Velocity
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
        
        # Response
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
        self.ax_resp.yaxis.set_major_formatter(formatter)
        self.ax_resp.yaxis.set_minor_formatter(formatter)
        
        custom_minor_ticks = [
            0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9,
            1.2, 1.4, 1.6, 1.8, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0, 7.0, 8.0, 9.0,
            10, 15, 20, 30, 40, 50, 60
        ]
        self.ax_resp.yaxis.set_minor_locator(FixedLocator(custom_minor_ticks))

    def update_plots(self, hit_history, show_wrong):
        self.ax_vel.clear()
        self.ax_resp.clear()
        
        x_correct, y_correct = [], []
        x_wrong, y_wrong = [], []
        x_all, y_response, bar_colors = [], [], []
        
        for i, hit in enumerate(hit_history):
            hit_index = i + 1
            if hit['type'] == 'correct':
                x_correct.append(hit_index)
                y_correct.append(hit['velocity'])
                x_all.append(hit_index)
                y_response.append(hit['response_time'])
                bar_colors.append(ACCENT_COLOUR)
                
            elif hit['type'] == 'wrong' and show_wrong:
                x_wrong.append(hit_index)
                y_wrong.append(hit['velocity'])
                x_all.append(hit_index)
                y_response.append(hit['response_time'])
                bar_colors.append(ERROR_COLOUR)
                
        self.sc_correct = None
        self.sc_wrong = None
        self.bars = []
        
        if x_correct:
            self.ax_vel.plot(x_correct, y_correct, color=ACCENT_COLOUR, alpha=0.4, zorder=1)
            self.sc_correct = self.ax_vel.scatter(x_correct, y_correct, color=ACCENT_COLOUR, s=50, zorder=2, label="Target Note")
            
        if x_wrong:
            self.sc_wrong = self.ax_vel.scatter(x_wrong, y_wrong, color=ERROR_COLOUR, s=50, marker='x', zorder=3, label="Missed Note")
            
        if x_correct or x_wrong:
            self.ax_vel.legend(loc="lower right", facecolor=BG_COLOUR, edgecolor=TEXT_COLOUR, labelcolor=TEXT_COLOUR)
            
        if x_all:
            self.bars = self.ax_resp.bar(x_all, y_response, color=bar_colors, alpha=0.8, width=0.5)

        self.apply_styling() 

        # Re-initialize annotations after clear
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
            cont_c, ind_c = self.sc_correct.contains(event) if self.sc_correct else (False, {})
            cont_w, ind_w = self.sc_wrong.contains(event) if self.sc_wrong else (False, {})
            
            if cont_c:
                pos = self.sc_correct.get_offsets()[ind_c["ind"][0]]
                self.annot_vel.xy = pos
                self.annot_vel.set_text(f"Vel: {int(pos[1])}")
                self.annot_vel.set_visible(True)
                self.canvas_vel.draw_idle()
            elif cont_w:
                pos = self.sc_wrong.get_offsets()[ind_w["ind"][0]]
                self.annot_vel.xy = pos
                self.annot_vel.set_text(f"Vel: {int(pos[1])}")
                self.annot_vel.set_visible(True)
                self.canvas_vel.draw_idle()
            else:
                if vis:
                    self.annot_vel.set_visible(False)
                    self.canvas_vel.draw_idle()

    def on_hover_resp(self, event):
        vis = self.annot_resp.get_visible()
        if event.inaxes == self.ax_resp:
            hovered = False
            for bar in self.bars:
                cont, _ = bar.contains(event)
                if cont:
                    height = bar.get_height()
                    text = f"{height:.2f}s" if height >= 1 else f"{height*1000:.0f}ms"
                    self.annot_resp.xy = (bar.get_x() + bar.get_width() / 2, height)
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