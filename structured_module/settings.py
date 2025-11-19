# structured_module/settings.py

# Масштабы таймлайна (количество дней на одно деление)
TIMELINE_ZOOM_MODES = [1, 7, 14, 30]
DEFAULT_ZOOM_INDEX = 2

# Цветовая схема
COLORS = {
    "background": "#1e1e2e",
    "text": "#cdd6f4",
    "widget_bg": "#181825",
    "list_bg": "#313244",
    "highlight": "#89b4fa",
    "timeline_bar": (70, 130, 180),
    "timeline_bar_border": "#89b4fa",
    "axis_line": "#585b70",
    "axis_tick": "#89b4fa",
    "axis_label": "#bac2de",
}

# Отступы и размеры
PADDING = {
    "left": 40,
    "right": 40,
    "task_spacing": 60,
    "task_bar_height": 35,
}
