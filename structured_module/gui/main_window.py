from PyQt5 import QtWidgets, QtCore, QtGui
import json
import os

from PyQt5.QtGui import QIcon

# GUI widgets
from gui.task_list_widget import TaskListWidget
from gui.task_editor import TaskEditorWidget

# Logic
from logic import task_manager
from logic.validator import validate_task

# Visualization
from visualization.timeline_render import draw_timeline
from visualization.animator_controller import apply_zoom_index

from PyQt5 import QtWidgets, QtCore

from PyQt5 import QtWidgets, QtCore

from PyQt5 import QtWidgets, QtCore

import sys
import os

def resource_path(relative_path):
    """ Получает путь к ресурсу, работает и для обычного запуска, и для PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

DB_PATH = os.path.join(os.path.expanduser("~"), "smart_planner.db")
CONFIG_PATH = os.path.join(os.path.expanduser("~"), "smart_planner_config.json")


class SettingsDialog(QtWidgets.QDialog):
    scaleChanged = QtCore.pyqtSignal(float)
    themeChanged = QtCore.pyqtSignal(str)

    def __init__(self, current_scale=1.0, current_theme="dark"):
        super().__init__()
        self.setWindowTitle("Настройки")
        self.resize(320, 200)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Масштаб интерфейса
        scale_label = QtWidgets.QLabel("Масштаб интерфейса:")
        layout.addWidget(scale_label)

        self.scale_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.scale_slider.setMinimum(5)
        self.scale_slider.setMaximum(20)
        self.scale_slider.setSingleStep(1)
        self.scale_slider.setValue(int(current_scale * 10))
        self.scale_slider.valueChanged.connect(self.on_scale_change)
        layout.addWidget(self.scale_slider)

        self.scale_value_label = QtWidgets.QLabel(f"{current_scale:.1f}x")
        self.scale_value_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.scale_value_label)

        # Тема интерфейса
        theme_label = QtWidgets.QLabel("Цветовая схема:")
        layout.addWidget(theme_label)

        self.radio_dark = QtWidgets.QRadioButton("Темная")
        self.radio_light = QtWidgets.QRadioButton("Светлая")
        self.radio_dark.setChecked(current_theme == "dark")
        self.radio_light.setChecked(current_theme == "light")

        # Горизонтальный layout для переключателя
        theme_layout = QtWidgets.QHBoxLayout()
        theme_layout.setSpacing(20)
        theme_layout.addWidget(self.radio_dark)
        theme_layout.addWidget(self.radio_light)
        layout.addLayout(theme_layout)

        # Сигналы для мгновенной смены темы
        self.radio_dark.toggled.connect(lambda checked: self.on_theme_change("dark") if checked else None)
        self.radio_light.toggled.connect(lambda checked: self.on_theme_change("light") if checked else None)


        # Кнопки
        btn_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
        close_btn = btn_box.button(QtWidgets.QDialogButtonBox.Close)
        close_btn.setText("Закрыть")
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def on_scale_change(self, value):
        scale = value / 10
        self.scale_value_label.setText(f"{scale:.1f}x")
        self.scaleChanged.emit(scale)

    def on_theme_change(self, theme):
        self.themeChanged.emit(theme)


class SmartPlannerMainWindow(QtWidgets.QMainWindow):
    CONFIG_FILE = "config.json"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SMART-Planner")
        self.resize(1100, 720)

        # Таймлайн
        self.zoom_modes = [1, 7, 14, 30]
        self.zoom_index = 2

        # Подключение к БД
        self.conn = task_manager.connect(DB_PATH)
        task_manager.ensure_schema(self.conn)

        # Основной layout
        main = QtWidgets.QWidget()
        self.setCentralWidget(main)
        layout = QtWidgets.QHBoxLayout(main)

        # Левая панель со списком задач (с заголовком и шрифтом Comic Sans)
        vbox_left = QtWidgets.QVBoxLayout()
        vbox_left.setAlignment(QtCore.Qt.AlignTop)

        # Заголовок панели
        title_label = QtWidgets.QLabel("Список задач")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        vbox_left.addWidget(title_label)
        title_label.setObjectName("titleLabel")

        # Сам виджет списка задач
        self.task_list = TaskListWidget()
        vbox_left.addWidget(self.task_list)

        layout.addLayout(vbox_left, 1)

        # Правая панель
        self.right_stack = QtWidgets.QStackedWidget()
        layout.addWidget(self.right_stack, 3)

        # Редактор
        self.editor = TaskEditorWidget()
        editor_widget = QtWidgets.QWidget()
        editor_layout = QtWidgets.QVBoxLayout(editor_widget)

        top_editor = QtWidgets.QHBoxLayout()
        top_editor.addWidget(self.editor.btnSwitch)
        top_editor.addStretch(1)
        settings_btn = QtWidgets.QPushButton("Настройки")
        settings_btn.setToolTip("Открыть настройки")
        settings_btn.clicked.connect(self.open_settings)
        top_editor.addWidget(settings_btn)
        editor_layout.addLayout(top_editor)

        editor_layout.addWidget(self.editor)
        self.right_stack.addWidget(editor_widget)

        # Диаграмма
        timeline_widget = QtWidgets.QWidget()
        tl_layout = QtWidgets.QVBoxLayout(timeline_widget)

        # Кнопка вернуться к задачам
        top_timeline = QtWidgets.QHBoxLayout()
        back_btn = QtWidgets.QPushButton("Вернуться к задачам")
        back_btn.clicked.connect(self.toggle_view)
        top_timeline.addWidget(back_btn)
        top_timeline.addStretch(1)
        tl_layout.addLayout(top_timeline)

        # Масштаб и кнопки zoom
        zoom_layout = QtWidgets.QHBoxLayout()
        self.zoom_label = QtWidgets.QLabel("Масштаб: 14 дней/деление")
        z_minus = QtWidgets.QPushButton("–")
        z_plus = QtWidgets.QPushButton("+")
        z_minus.setToolTip("Увеличить шаг (отдалить)")
        z_plus.setToolTip("Уменьшить шаг (приблизить)")
        z_minus.clicked.connect(lambda: self.change_zoom(+1))  # Поменял кнопки местами
        z_plus.clicked.connect(lambda: self.change_zoom(-1))
        zoom_layout.addWidget(self.zoom_label)
        zoom_layout.addWidget(z_minus)
        zoom_layout.addWidget(z_plus)
        zoom_layout.addStretch(1)
        tl_layout.addLayout(zoom_layout)

        # Сцена и view
        self.scene = QtWidgets.QGraphicsScene()
        self.view = QtWidgets.QGraphicsView(self.scene)
        self.view.setRenderHint(QtGui.QPainter.Antialiasing)
        self.view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        tl_layout.addWidget(self.view)
        self.right_stack.addWidget(timeline_widget)

        # Сигналы
        self.task_list.itemSelected.connect(self._on_task_selected)
        self.editor.sigSave.connect(self._on_save_task)
        self.editor.sigDelete.connect(self._on_delete_task)
        self.editor.sigNew.connect(self._on_new_task)
        self.scene.selectionChanged.connect(self._on_scene_selection_changed)
        self.editor.btnSwitch.clicked.connect(self.toggle_view)

        # Загружаем config
        self.load_config()
        # Применяем тему и масштаб
        self._apply_styles()
        QtCore.QTimer.singleShot(0, self._apply_initial_scale)
        # Загружаем задачи
        self._reload_list()
        self.right_stack.setCurrentIndex(0)

    def load_config(self):
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        else:
            cfg = {"ui_scale": 1.0, "theme": "dark"}
        self.current_scale = cfg.get("ui_scale", 1.0)
        self.current_theme = cfg.get("theme", "dark")

    def save_config(self):
        cfg = {"ui_scale": self.current_scale, "theme": self.current_theme}
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=4)

    def _apply_styles(self, dark=None):
        if dark is None:
            dark = self.current_theme == "dark"

        # if dark:
        #     bg = "#1e1e2e"
        #     fg = "#cdd6f4"
        #     widget_bg = "#181825"
        #     item_bg = "#313244"
        #     item_selected_bg = "#89b4fa"
        #     item_selected_fg = "#1e1e2e"
        #     input_bg = "#313244"
        #     btn_bg = "#313244"
        #     btn_hover = "#45475a"
        #     graphics_bg = "#181825"
        #     scroll_bg = "#1e1e2e"
        #     scroll_handle = "#45475a"
        #     border_color = "#888888"
        #     arrow_svg = "calendar-range-dark.svg"
        # else:
        #     bg = "#f0f4fa"
        #     fg = "#1e2e3e"
        #     widget_bg = "#e8f0fa"
        #     item_bg = "#d0e1f7"
        #     item_selected_bg = "#3399ff"
        #     item_selected_fg = "#ffffff"
        #     input_bg = "#ffffff"
        #     btn_bg = "#d0e1f7"
        #     btn_hover = "#a0c8ff"
        #     graphics_bg = "#ffffff"
        #     scroll_bg = "#e0e5eb"
        #     scroll_handle = "#a0c8ff"
        #     border_color = "#888888"
        #     arrow_svg = "calendar-range-light.svg"

        if dark:
            bg = "#1b1b2f"  # общий фон
            fg = "#e0e0f0"  # основной текст
            widget_bg = "#1f1f36"  # фон виджетов
            item_bg = "#2a2a44"  # фон элементов списка
            item_selected_bg = "#7f9cf5"  # фон выбранного элемента
            item_selected_fg = "#1b1b2f"  # текст выбранного элемента
            input_bg = "#2a2a44"  # фон QLineEdit/QTextEdit
            btn_bg = "#2a2a44"  # фон кнопок
            btn_hover = "#5c5cd6"  # при наведении
            graphics_bg = "#1f1f36"  # фон QGraphicsView
            scroll_bg = "#1b1b2f"  # фон скроллбара
            scroll_handle = "#5c5cd6"  # бегунок скроллбара
            border_color = "#9999aa"
            arrow_svg = resource_path("calendar-range-dark.svg").replace("\\", "/")
        else:
            bg = "#f7f9fc"
            fg = "#2c3e50"
            widget_bg = "#ffffff"
            item_bg = "#e4ebf5"
            item_selected_bg = "#5dade2"
            item_selected_fg = "#ffffff"
            input_bg = "#ffffff"
            btn_bg = "#e4ebf5"
            btn_hover = "#85c1e9"
            graphics_bg = "#ffffff"
            scroll_bg = "#f0f3f7"
            scroll_handle = "#85c1e9"
            border_color = "#bbbbcc"
            arrow_svg = resource_path("calendar-range-light.svg").replace("\\", "/")

        font_size = int(10 * self.current_scale)

        style = f"""
        QMainWindow, QWidget {{
            background:{bg};
            color:{fg};
            font-size:{font_size}pt;
        }}
        QListWidget {{
            background:{widget_bg};
            border:1px solid {border_color};
            border-radius:10px;
            padding:8px;
        }}
        QListWidget::item {{
            background:{item_bg};
            padding:6px;
            margin:3px;
            border-radius:6px;
        }}
        QListWidget::item:selected {{
            background:{item_selected_bg};
            color:{item_selected_fg};
            font-weight:bold;
        }}
        QLineEdit, QTextEdit, QDateEdit {{
            background:{input_bg};
            border:1px solid {border_color};
            border-radius:6px;
            padding:4px 6px;
            color:{fg};
        }}
        QDateEdit::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width:20px;
            border-left:1px solid {border_color};
            border-radius:0 6px 6px 0;
            background:{btn_bg};
        }}
        QDateEdit::down-arrow {{
            image: url({arrow_svg});
            width:12px;
            height:12px;
        }}
        QPushButton {{
            background:{btn_bg};
            color:{fg};
            border:1px solid {border_color};
            border-radius:8px;
            padding:6px 10px;
            font-weight:bold;
        }}
        QPushButton:hover {{
            background:{btn_hover};
            border:1px solid #3399ff;
        }}
        QGraphicsView {{
            background:{graphics_bg};
            border:1px solid {border_color};
            border-radius:10px;
        }}

    QScrollBar:vertical {{
        background: {scroll_bg};
        width: 12px;
        margin: 0;
        border: none;
        border-radius: 6px;
    }}
    QScrollBar::groove:vertical {{
        background: transparent;   /* убирает нативный трек */
        margin: 0;
        border-radius: 6px;
    }}
    QScrollBar::handle:vertical {{
        background: {scroll_handle};
        min-height: 20px;
        border-radius: 6px;
        border: none;
        margin: 2px 0;
    }}
    QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical,
    QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {{
        height: 0; width: 0;        /* скрываем стрелки/кнопки */
        background: transparent;
        image: none;
        border: none;
    }}
    QScrollBar::corner {{
        background: transparent;    /* убирает квадрат в углу */
        width: 0; height: 0;
        border: none;
    }}
    
    /* Горизонтальная — аналогично */
    QScrollBar:horizontal {{
        background: {scroll_bg};
        height: 12px;
        margin: 0;
        border: none;
        border-radius: 6px;
    }}
    QScrollBar::groove:horizontal {{ background: transparent; margin: 0; border-radius: 6px; }}
    QScrollBar::handle:horizontal {{
        background: {scroll_handle};
        min-width: 20px;
        border-radius: 6px;
        border: none;
        margin: 0 2px;
    }}
    QScrollBar::sub-line:horizontal, QScrollBar::add-line:horizontal,
    QScrollBar::left-arrow:horizontal, QScrollBar::right-arrow:horizontal {{
        width: 0; height: 0;
        background: transparent;
        image: none;
        border: none;
    }}
    
    QLabel#titleLabel {{
    font-weight: bold;
    font-size: {int(14 * self.current_scale)}pt;
    }}

        """
        self.setStyleSheet(style)

    def apply_theme(self, theme: str):
        self.current_theme = theme
        self._apply_styles()
        self.draw_diagram()

    def _apply_initial_scale(self):
        self.apply_ui_scale(self.current_scale)
        self.draw_diagram()

    def apply_ui_scale(self, scale: float):
        self.current_scale = scale
        self._apply_styles()
        self.draw_diagram()

    def _reload_list(self):
        rows = task_manager.fetch_all_min(self.conn)
        self.task_list.load(rows)

    def _load_task_into_editor(self, task_id):
        task = task_manager.fetch_one(self.conn, task_id)
        if task:
            self.editor.set_task(task)

    def _on_task_selected(self, task_id):
        self._load_task_into_editor(task_id)
        self.right_stack.setCurrentIndex(0)

    def _on_save_task(self, payload):
        ok, err = validate_task(payload)
        if not ok:
            QtWidgets.QMessageBox.warning(self, "Ошибка", err)
            return
        if payload.get("id"):
            task_manager.update_task(self.conn, payload["id"], payload)
        else:
            new_id = task_manager.create_task(self.conn, payload)
            payload["id"] = new_id
        self._reload_list()
        QtWidgets.QMessageBox.information(self, "Сохранено", "Задача успешно сохранена.")
        self.editor.clear_form()
        self.right_stack.setCurrentIndex(0)

    # def _on_delete_task(self, task_id):
    #     if not task_id:
    #         return
    #     if QtWidgets.QMessageBox.question(
    #             self, "Удалить", "Удалить задачу?",
    #             QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
    #     ) == QtWidgets.QMessageBox.Yes:
    #         task_manager.delete_task(self.conn, task_id)
    #         self.editor.clear_form()
    #         self._reload_list()

    def _on_delete_task(self, task_id):
        if not task_id:
            return

        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("Удалить")
        msg.setText("Удалить задачу?")
        msg.setIcon(QtWidgets.QMessageBox.Question)

        btn_yes = msg.addButton("Да", QtWidgets.QMessageBox.YesRole)
        btn_no = msg.addButton("Нет", QtWidgets.QMessageBox.NoRole)

        msg.exec_()

        if msg.clickedButton() == btn_yes:
            task_manager.delete_task(self.conn, task_id)
            self.editor.clear_form()
            self._reload_list()

    def _on_new_task(self):
        self.editor.clear_form()
        self.task_list.clearSelection()
        self.task_list.setCurrentItem(None)

    def toggle_view(self):
        if self.right_stack.currentIndex() == 0:
            self.draw_diagram()
            self.right_stack.setCurrentIndex(1)
        else:
            self.right_stack.setCurrentIndex(0)

    def change_zoom(self, delta):
        new_index = self.zoom_index + delta
        if 0 <= new_index < len(self.zoom_modes):
            self.zoom_index = apply_zoom_index(self.zoom_index, new_index)
            val = self.zoom_modes[self.zoom_index]
            unit = "день" if val == 1 else "дней"
            self.zoom_label.setText(f"Масштаб: {val} {unit}/деление")
            self.draw_diagram()

    def draw_diagram(self):
        self.scene.clear()
        tasks = task_manager.fetch_all_full(self.conn)
        viewport_w = max(1, self.view.viewport().width())
        dark_theme = self.current_theme == "dark"
        self.draw_timeline_scaled(tasks, viewport_w, dark_theme)

    def draw_timeline_scaled(self, tasks, viewport_w, dark_theme):
        zoom_days = self.zoom_modes[self.zoom_index]
        draw_timeline(self.scene, tasks, zoom_days, viewport_w,
                      ui_scale=self.current_scale, dark_theme=dark_theme)

    def _on_scene_selection_changed(self):
        items = self.scene.selectedItems()
        if not items:
            return
        tid = items[0].data(0)
        if not tid:
            return

        # Открываем задачу и переключаемся
        self.task_list.itemSelected.emit(tid)

        # ВИЗУАЛЬНО выделяем строку в списке
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            if item and item.data(QtCore.Qt.UserRole) == tid:
                self.task_list.setCurrentItem(item)
                self.task_list.scrollToItem(item)
                return
        # Если не нашли - снимаем выделение
        self.task_list.clearSelection()

    def open_settings(self):
        dialog = SettingsDialog(current_scale=self.current_scale, current_theme=self.current_theme)
        dialog.scaleChanged.connect(self.apply_ui_scale)
        dialog.themeChanged.connect(self.apply_theme)
        dialog.exec_()
        self.save_config()
