import tkinter as tk
from tkinter import ttk, messagebox
import sympy as sp
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from dataclasses import dataclass


# core/function_parser.py content
class FunctionParser:
    def __init__(self):
        self.x = sp.symbols('x')

    def parse(self, func_text: str):
        try:
            return sp.sympify(func_text, {"x": self.x})
        except Exception as e:
            raise ValueError(f"Ошибка парсинга: {e}")

    def evaluate(self, expr, x_values):
        try:
            f = sp.lambdify(self.x, expr, 'numpy')
            return f(x_values)
        except Exception as e:
            raise ValueError(f"Ошибка вычисления функции: {e}")


# core/plot_generator.py content
@dataclass
class PlotData:
    x_values: list
    y_values: list
    func: str
    limits: tuple


class PlotGenerator:
    def __init__(self, parser):
        self.parser = parser

    def generate(self, func_text, xmin, xmax, points=1000):
        expr = self.parser.parse(func_text)
        x_vals = np.linspace(xmin, xmax, points)
        y_vals = self.parser.evaluate(expr, x_vals)
        return PlotData(x_vals, y_vals, func_text, (xmin, xmax))


# visualization/renderer.py content
# visualization/renderer.py — НОВАЯ ВЕРСИЯ
# visualization/renderer.py — ФИНАЛЬНАЯ ВЕРСИЯ (с плавностью и фиксами)
# visualization/renderer.py — ОКОНЧАТЕЛЬНАЯ ВЕРСИЯ (идеальная)
class PlotRenderer:
    """
    Оптимизированный рендер matplotlib + Tkinter:
      - Живое перемещение мышью
      - Плавный zoom колёсиком
      - Blit для линий, фон осей хранится отдельно
      - Автоподгонка под размер Tkinter виджета
    """
    def __init__(self, master):
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        self.last_plot_data = None  # новое поле для хранения последнего графика
        self.figure = Figure(figsize=(8, 6), dpi=100, facecolor="white")
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor("#fafafa")
        self.figure.subplots_adjust(left=0, right=1, top=1, bottom=0)
        self.ax.set_xmargin(0)
        self.ax.set_ymargin(0)

        self.canvas = FigureCanvasTkAgg(self.figure, master=master)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        master.bind("<Configure>", self._resize_figure)

        # настройки линии
        self.linewidth = 2.5
        self.linecolor = "#1f77b4"

        # Drag & drop
        self.dragging = False
        self.last_px = None
        self.last_py = None
        self.start_xlim = None
        self.start_ylim = None

        # фон осей
        self.axes_bg = None

        # placeholder
        self.placeholder = self.ax.text(
            0.5, 0.5, "График", fontsize=32, color="#cccccc",
            ha="center", va="center", transform=self.ax.transAxes
        )
        self.ax.axis("off")
        self.canvas.draw()

        # события
        self.canvas.mpl_connect("scroll_event", self.on_scroll)
        self.canvas.mpl_connect("button_press_event", self.on_press)
        self.canvas.mpl_connect("button_release_event", self.on_release)
        self.canvas.mpl_connect("motion_notify_event", self.on_motion)
        self.canvas.mpl_connect("draw_event", self.on_draw)

    # --- resize ---
    def _resize_figure(self, event):
        if event.widget != self.canvas.get_tk_widget().master:
            return
        w, h = event.width, event.height
        if w < 10 or h < 10:
            return
        dpi = self.figure.get_dpi()
        self.figure.set_size_inches(w / dpi, h / dpi)
        self.canvas.draw()
        self._update_axes_bg()

    def on_draw(self, event):
        self._update_axes_bg()

    # --- render ---
    def render(self, plot_data, color=None, style="-", linewidth=None):
        self.last_plot_data = plot_data
        self.ax.clear()
        self.figure.subplots_adjust(left=0, right=1, top=1, bottom=0)
        self.ax.set_xmargin(0)
        self.ax.set_ymargin(0)

        color = color or self.linecolor
        linewidth = linewidth if linewidth is not None else self.linewidth

        x_vals = plot_data.x_values
        y_vals = plot_data.y_values

        if len(x_vals) < 2 or np.all(np.isnan(y_vals)):
            raise ValueError("Функция не определена на интервале")

        if self.placeholder is not None:
            try:
                self.placeholder.remove()
            except Exception:
                pass
            self.placeholder = None

        self.ax.plot(x_vals, y_vals, color=color, linewidth=linewidth, linestyle=style, zorder=10)

        self.ax.set_xlim(x_vals[0], x_vals[-1])
        y_min, y_max = np.nanmin(y_vals), np.nanmax(y_vals)
        y_range = y_max - y_min if y_max > y_min else 1.0
        self.ax.set_ylim(y_min - 0.05 * y_range, y_max + 0.05 * y_range)

        self._setup_axes()
        self.ax.grid(True, linestyle="--", alpha=0.5, zorder=0)
        self.ax.set_xlabel("x", fontsize=13, loc="right", labelpad=10)
        self.ax.set_ylabel("y", fontsize=13, loc="top", rotation=0, labelpad=10)

        self.canvas.draw()
        self._update_axes_bg()

    # --- обновление фона осей ---
    def _update_axes_bg(self):
        # сохраняем фон всей оси, включая сетку и метки
        self.axes_bg = self.canvas.copy_from_bbox(self.ax.bbox)

    # --- настройка осей ---
    def _setup_axes(self):
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        ax = self.ax

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        if xlim[0] <= 0 <= xlim[1]:
            ax.spines['bottom'].set_position(('data', 0))
        else:
            ax.spines['bottom'].set_position(('axes', 0))
        ax.spines['bottom'].set_color('black')

        if ylim[0] <= 0 <= ylim[1]:
            ax.spines['left'].set_position(('data', 0))
        else:
            ax.spines['left'].set_position(('axes', 0))
        ax.spines['left'].set_color('black')

    # --- очистка ---
    def clear(self):
        self.ax.clear()
        self.placeholder = self.ax.text(
            0.5, 0.5, "График", fontsize=32, color="#cccccc",
            ha="center", va="center", transform=self.ax.transAxes
        )
        self.ax.axis("off")
        self.canvas.draw()
        self._update_axes_bg()

    # --- zoom ---
    def on_scroll(self, event):
        if event.inaxes != self.ax:
            return

        base_scale = 1.15
        scale = 1 / base_scale if getattr(event, "step", 0) > 0 else base_scale

        xdata = event.xdata if event.xdata is not None else sum(self.ax.get_xlim()) / 2
        ydata = event.ydata if event.ydata is not None else sum(self.ax.get_ylim()) / 2

        xlim, ylim = self.ax.get_xlim(), self.ax.get_ylim()

        new_xlim = (xdata - (xdata - xlim[0]) * scale, xdata + (xlim[1] - xdata) * scale)
        new_ylim = (ydata - (ydata - ylim[0]) * scale, ydata + (ylim[1] - ydata) * scale)

        self.ax.set_xlim(new_xlim)
        self.ax.set_ylim(new_ylim)
        self._setup_axes()
        self.canvas.draw()
        self._update_axes_bg()

    # --- drag start ---
    def on_press(self, event):
        if event.inaxes != self.ax or event.button != 1:
            return
        self.dragging = True
        self.last_px = event.x
        self.last_py = event.y
        self.start_xlim = self.ax.get_xlim()
        self.start_ylim = self.ax.get_ylim()
        if self.axes_bg is None:
            self._update_axes_bg()

    # --- drag motion ---


    def on_motion(self, event):
        if not self.dragging or event.x is None or event.y is None:
            return

        dx_pixels = event.x - self.last_px
        dy_pixels = event.y - self.last_py

        inv = self.ax.transData.inverted()
        p1 = inv.transform((0, 0))
        p2 = inv.transform((dx_pixels, dy_pixels))
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]

        new_xlim = (self.start_xlim[0] - dx, self.start_xlim[1] - dx)
        new_ylim = (self.start_ylim[0] - dy, self.start_ylim[1] - dy)
        self.ax.set_xlim(new_xlim)
        self.ax.set_ylim(new_ylim)

        # живой рендер
        if self.axes_bg is not None:
            self.canvas.restore_region(self.axes_bg)  # фон осей + сетки
            for line in self.ax.lines:
                self.ax.draw_artist(line)  # линии графиков
            for text in self.ax.texts:
                self.ax.draw_artist(text)  # подписи, placeholder
            self.canvas.blit(self.ax.bbox)  # мгновенная отрисовка
        else:
            self.canvas.draw_idle()

    # --- drag end ---
    def on_release(self, event):
        if event.button != 1:
            return
        self.dragging = False
        self.last_px = None
        self.last_py = None
        self.canvas.draw()
        self._update_axes_bg()


# gui/settings_window.py content
class SettingsWindow(tk.Toplevel):
    def __init__(self, parent, renderer):
        super().__init__(parent)
        self.renderer = renderer
        self.title("Настройки")
        self.geometry("300x150")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # сохраняем текущие настройки для сравнения
        self.prev_linewidth = renderer.linewidth
        self.prev_linecolor = renderer.linecolor

        tk.Label(self, text="Ширина линии:").pack(pady=(10, 5), anchor="w", padx=20)
        self.width_var = tk.StringVar(value=str(renderer.linewidth))
        tk.Entry(self, textvariable=self.width_var).pack(fill=tk.X, padx=20)

        tk.Label(self, text="Цвет линии rgb:").pack(pady=(5, 5), anchor="w", padx=20)
        color_value = renderer.linecolor
        if isinstance(color_value, tuple):
            color_value = f"{int(color_value[0]*255)},{int(color_value[1]*255)},{int(color_value[2]*255)}"
        self.color_var = tk.StringVar(value=color_value)
        tk.Entry(self, textvariable=self.color_var).pack(fill=tk.X, padx=20)

        tk.Button(self, text="Применить", command=self.apply).pack(pady=5)

    def apply(self):
        try:
            new_linewidth = float(self.width_var.get())
            color_str = self.color_var.get()
            if ',' in color_str:
                r, g, b = map(int, color_str.split(','))
                new_linecolor = (r / 255, g / 255, b / 255)
            else:
                new_linecolor = color_str

            # проверка на изменение
            changed = new_linewidth != self.prev_linewidth or new_linecolor != self.prev_linecolor

            self.renderer.linewidth = new_linewidth
            self.renderer.linecolor = new_linecolor

            if changed and self.renderer.last_plot_data:
                # перерисовываем график с новыми настройками
                self.renderer.render(self.renderer.last_plot_data)

            self.destroy()
        except ValueError:
            tk.messagebox.showerror("Ошибка", "Неверный формат данных")



# gui/input_panel.py content
@dataclass
class InputData:
    func: str
    xmin: float
    xmax: float
    points: int
    color: str = "blue"
    style: str = "-"
    linewidth: float = 2.0


class InputPanel(tk.Frame):
    def __init__(self, master, build_callback, clear_callback):
        super().__init__(master, height=80, bg='#f0f0f0')
        self.pack_propagate(False)

        self.build_callback = build_callback
        self.clear_callback = clear_callback

        self._create_widgets()

    def _create_widgets(self):
        pad_x = 5
        pad_y = 5

        # Вспомогательная функция для placeholder
        def add_placeholder(entry, text):
            entry.insert(0, text)
            entry.config(fg='lightgray')

            def on_focus_in(event):
                if entry.get() == text:
                    entry.delete(0, tk.END)
                    entry.config(fg='black')

            def on_focus_out(event):
                if not entry.get():
                    entry.insert(0, text)
                    entry.config(fg='lightgray')

            entry.bind("<FocusIn>", on_focus_in)
            entry.bind("<FocusOut>", on_focus_out)

        # Функция
        tk.Label(self, text="Функция", bg='#f0f0f0').grid(row=0, column=0, padx=pad_x, pady=pad_y, sticky="w")
        self.func_entry = tk.Entry(self, width=30)
        self.func_entry.grid(row=0, column=1, padx=(0, 10), sticky="w")
        add_placeholder(self.func_entry, "например: sin(x) или x**2")

        # Начало
        tk.Label(self, text="Начало:", bg='#f0f0f0').grid(row=0, column=2, padx=pad_x, pady=pad_y)
        self.xmin_entry = tk.Entry(self, width=8)
        self.xmin_entry.grid(row=0, column=3, padx=(0, 10))
        add_placeholder(self.xmin_entry, "-10")

        # Конец
        tk.Label(self, text="Конец:", bg='#f0f0f0').grid(row=0, column=4, padx=pad_x, pady=pad_y)
        self.xmax_entry = tk.Entry(self, width=8)
        self.xmax_entry.grid(row=0, column=5, padx=(0, 10))
        add_placeholder(self.xmax_entry, "10")

        # Количество точек
        tk.Label(self, text="Количество точек:", bg='#f0f0f0').grid(row=0, column=6, padx=pad_x, pady=pad_y)
        self.points_entry = tk.Entry(self, width=8)
        self.points_entry.grid(row=0, column=7, padx=(0, 10))
        add_placeholder(self.points_entry, "1000")

        # Кнопки
        buttons_frame = tk.Frame(self, bg='#f0f0f0')
        buttons_frame.grid(row=1, column=0, columnspan=8, sticky="w", pady=pad_y, padx=pad_x)

        tk.Button(buttons_frame, text="Рисовать", width=10, bg="#4CAF50", fg="white",
                  command=self.build_callback).pack(side=tk.LEFT, padx=5)
        tk.Button(buttons_frame, text="Очистить", width=10, bg="#f44336", fg="white",
                  command=self.clear_callback).pack(side=tk.LEFT, padx=5)

    def get_inputs(self):
        try:
            return InputData(
                func=self.func_entry.get().strip() or "0",
                xmin=float(self.xmin_entry.get() or "-10"),
                xmax=float(self.xmax_entry.get() or "10"),
                points=int(self.points_entry.get() or "1000"),
            )
        except ValueError as e:
            raise ValueError("Проверьте правильность введённых чисел")


# gui/main_window.py content
class MathGraphApp:
    def __init__(self, root):
        self.root = root
        root.title("MathGraph")
        root.geometry("1100x1000")
        root.minsize(1000, 950)

        self.parser = FunctionParser()
        self.generator = PlotGenerator(self.parser)

        self._create_widgets()

    def _create_widgets(self):
        # === Верхняя панель с кнопкой Настройки ===
        top_frame = tk.Frame(self.root, height=40, bg='#f0f0f0')
        top_frame.pack(fill=tk.X)
        top_frame.pack_propagate(False)

        settings_btn = tk.Button(top_frame, text="Настройки", bg='#f0f0f0', relief=tk.FLAT, command=self.open_settings)
        settings_btn.pack(side=tk.RIGHT, padx=10, pady=8)

        # === Центральная область графика ===
        self.plot_frame = tk.Frame(self.root, relief=tk.SUNKEN, bd=1, bg='white')
        self.plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.renderer = PlotRenderer(self.plot_frame)

        # === Нижняя панель ввода ===
        self.input_panel = InputPanel(self.root,
                                      build_callback=self.build_graph,
                                      clear_callback=self.clear_graph)
        self.input_panel.pack(fill=tk.X, padx=10, pady=(0, 10))

    def open_settings(self):
        SettingsWindow(self.root, self.renderer)

    def build_graph(self):
        try:
            data = self.input_panel.get_inputs()

            # Подставляем текущие настройки renderer, если пользователь не изменял цвет/ширину
            if data.linewidth == 2.0:  # default
                data.linewidth = self.renderer.linewidth
            if data.color == "blue":  # default
                if isinstance(self.renderer.linecolor, tuple):
                    # конвертируем RGB в matplotlib формат
                    r, g, b = self.renderer.linecolor
                    data.color = (r, g, b)
                else:
                    data.color = self.renderer.linecolor

            # Генерация данных
            plot_data = self.generator.generate(
                data.func, data.xmin, data.xmax, points=data.points
            )

            # Проверка на NaN или inf в y_values
            if np.any(np.isnan(plot_data.y_values)) or np.any(np.isinf(plot_data.y_values)):
                messagebox.showwarning(
                    "Внимание",
                    "Функция содержит неопределённые значения (деление на ноль или sqrt отрицательного числа). "
                    "Некоторые точки могут быть пропущены."
                )
                # Можно заменить NaN/inf на np.nan, чтобы matplotlib корректно отрисовал
                y_safe = np.where(np.isfinite(plot_data.y_values), plot_data.y_values, np.nan)
                plot_data = PlotData(plot_data.x_values, y_safe, plot_data.func, plot_data.limits)

            self.renderer.render(plot_data, data.color, data.style, data.linewidth)

        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def clear_graph(self):
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите очистить график?"):
            self.renderer.clear()

            # Очистка полей ввода и восстановление placeholder
            panel = self.input_panel
            for entry, placeholder in [
                (panel.func_entry, "например: sin(x) или x**2"),
                (panel.xmin_entry, "-10"),
                (panel.xmax_entry, "10"),
                (panel.points_entry, "1000")
            ]:
                entry.delete(0, tk.END)
                entry.insert(0, placeholder)
                entry.config(fg='lightgray')


# main.py content
if __name__ == "__main__":
    root = tk.Tk()
    app = MathGraphApp(root)
    root.mainloop()