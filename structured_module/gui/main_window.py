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

QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

def resource_path(relative_path):
    """ Получает путь к ресурсу, работает и для обычного запуска, и для PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


DB_PATH = os.path.join(os.path.expanduser("~"), "smart_planner.db")
CONFIG_PATH = os.path.join(os.path.expanduser("~"), "smart_planner_config.json")

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QLabel, QGraphicsOpacityEffect, QWidget
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
import json
import os
import sys


# ... ваши остальные импорты (logic, visualization) ...
# ВАЖНО: Удалите строчки "from PyQt6..." полностью!

class ToastNotification(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        # Создаем виджет поверх всех окон без рамки
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        # Создаем layout с внутренней меткой
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)
        layout.addWidget(self.label)

        # Эффект прозрачности применяем к самому виджету
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)

        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.fade_out)
        self.hide()

    def center_position(self):
        """Центрирует уведомление в ВЕРХНЕЙ части главного окна"""
        if self.parent():
            parent_geo = self.parent().geometry()
            main_center_x = parent_geo.x() + (parent_geo.width() - self.width()) // 2
            top_y = parent_geo.y() + 80
            self.move(main_center_x, top_y)

    def show_message(self, text, bg_color, is_dark, msec=3000):
        self.label.setText(text)
        text_color = "#ffffff" if is_dark else "#1e1e2e"

        # Стилизуем внутреннюю метку
        self.label.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: {text_color};
                border-radius: 25px; 
                padding: 15px 40px;
                font-size: 18px;
                font-weight: bold;
                border: 2px solid rgba(255, 255, 255, 0.3);
            }}
        """)

        # Важно: сначала adjustSize для label, потом для всего виджета
        self.label.adjustSize()
        self.adjustSize()
        self.center_position()

        self.show()
        self.raise_()

        # Анимация появления
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(400)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.start()

        self.timer.start(msec)

    def fade_out(self):
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(500)
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.finished.connect(self.hide)
        self.anim.start()

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

        # 1. Добавляем StatusBar (Гипотеза №1)
        # Создаем один экземпляр тоста для всего окна
        self.toast = ToastNotification(self)

        # Статусбар можно оставить пустым или вообще убрать
        self.setStatusBar(QtWidgets.QStatusBar())
        self.statusBar().hide()

        # 2. Добавляем кнопку "Помощь" в блок настроек для перезапуска обучения
        help_btn = QtWidgets.QPushButton("?")
        help_btn.setFixedSize(30, 30)
        help_btn.setToolTip("Пройти обучение заново")
        help_btn.clicked.connect(self.run_onboarding)
        top_editor.addWidget(help_btn)  # Добавляем рядом с кнопкой настроек

        # 3. Автозапуск при первом включении
        if not os.path.exists(CONFIG_PATH):
            QtCore.QTimer.singleShot(500, self.run_onboarding)

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
        icon_size = int(14 * self.current_scale)

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
            width: {icon_size + 8}px;
            border-left:1px solid {border_color};
            border-radius:0 6px 6px 0;
            background:{btn_bg};
        }}
        QDateEdit::down-arrow {{
            image: url({arrow_svg});
            width:{icon_size}px;
            height:{icon_size}px;
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



    def moveEvent(self, event):
        super().moveEvent(event)
        if self.toast.isVisible():
            self.toast.center_position()

    # В классе SmartPlannerMainWindow измени эти методы:

    def show_status_msg(self, text, color=None, msec=3000):
        """Показывает уведомление-плашку."""
        # Цвета Catppuccin для примера (Macchiato/Mocha)
        # Зеленый (Green) для успеха по умолчанию: #a6e3a1
        # Если передан цвет, используем его.
        if color is None:
            color = "#a6e3a1"

        is_dark = self.current_theme == "dark"
        self.toast.show_message(text, color, is_dark, msec)

    def _on_save_task(self, payload):
        ok, err = validate_task(payload)

        # Единое время показа
        display_time = 3500

        if not ok:
            # Красный (Red) цвет плашки ошибки: #f38ba8
            self.show_status_msg(f"⚠ {err}", color="#f38ba8", msec=display_time)
            return

        if payload.get("id"):
            task_manager.update_task(self.conn, payload["id"], payload)
            # Зеленый (Green) цвет плашки успеха: #a6e3a1
            self.show_status_msg(f"✅ Задача обновлена", color="#a6e3a1", msec=display_time)
        else:
            new_id = task_manager.create_task(self.conn, payload)
            payload["id"] = new_id
            self.show_status_msg("✨ Задача создана", color="#a6e3a1", msec=display_time)

        self._reload_list()
        self.editor.clear_form()
        self.task_list.clearSelection()
        self.right_stack.setCurrentIndex(0)

    def _on_delete_task(self, task_id):
        if not task_id: return

        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("Удалить")
        msg.setText("Удалить задачу?")
        btn_yes = msg.addButton("Да", QtWidgets.QMessageBox.YesRole)
        msg.addButton("Нет", QtWidgets.QMessageBox.NoRole)
        msg.exec_()

        if msg.clickedButton() == btn_yes:
            task_manager.delete_task(self.conn, task_id)
            self.editor.clear_form()
            self.task_list.clearSelection()
            self._reload_list()
            self.show_status_msg("🗑 Задача удалена", color="#fab387")  # Оранжевый

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

    def run_onboarding(self):
        """ Полностью интерактивный тур с заполнением первой задачи """

        def reset_all_onboarding_styles():
            """ Возвращает стандартный вид всем подсвеченным элементам """
            self.editor.btnNew.setStyleSheet("")
            self.editor.goal_input.setStyleSheet("")
            self.editor.s_input.setStyleSheet("")
            self.editor.m_input.setStyleSheet("")
            self.editor.a_input.setStyleSheet("")
            self.editor.r_input.setStyleSheet("")
            self.editor.start_date.setStyleSheet("")
            self.editor.end_date.setStyleSheet("")
            self.editor.btnSave.setStyleSheet("")
            self.editor.btnSwitch.setStyleSheet("")
            self.task_list.setEnabled(True)

        def highlight_widget(widget, color="#f9e2af"):
            """Красиво подсвечивает виджет с учетом темы"""
            is_dark = self.current_theme == "dark"

            if is_dark:
                bg = "#2a2a44"
                text_color = "#e0e0f0"
            else:
                bg = "#ffffff"
                text_color = "#2c3e50"

            widget.setStyleSheet(f"""
                border: 3px solid {color};
                background-color: {bg};
                color: {text_color};
                font-weight: bold;
                padding: 6px;
                border-radius: 8px;
            """)

        def custom_msg(title, text, is_final=False):
            msg = QtWidgets.QMessageBox(self)
            msg.setWindowTitle(title)
            msg.setText(text)

            next_btn = msg.addButton("Далее", QtWidgets.QMessageBox.AcceptRole)
            exit_btn = msg.addButton("Выйти из обучения", QtWidgets.QMessageBox.RejectRole)

            if is_final:
                next_btn.setText("Посмотреть диаграмму")

            msg.exec_()

            if msg.clickedButton() == exit_btn:
                return False
            return True

        # Блокируем список задач на время обучения
        self.task_list.setEnabled(False)

        # Переключаемся на редактор, если вдруг на диаграмме
        self.right_stack.setCurrentIndex(0)

        try:
            # Шаг 1: Приветствие
            if not custom_msg("🎓 Добро пожаловать в SMART-Planner!",
                              "Привет! Я помогу тебе создать твою первую цель.\n\n"
                              "Мы вместе пройдем через все этапы планирования\n"
                              "по методике SMART.\n\n"
                              "Готов начать?"):
                return

            # Шаг 2: Очистка формы
            highlight_widget(self.editor.btnNew, "#f9e2af")
            if not custom_msg("Шаг 1: Создание новой цели",
                              "Нажми на кнопку 'Новая задача' (подсвечена желтым).\n\n"
                              "Это очистит форму для создания новой записи."):
                return

            # Имитируем нажатие
            self.editor.clear_form()
            self.editor.btnNew.setStyleSheet("")

            QtCore.QTimer.singleShot(300, lambda: None)

            # Шаг 3: Название цели
            highlight_widget(self.editor.goal_input, "#89dceb")
            self.editor.goal_input.setFocus()

            if not custom_msg("Шаг 2: Название цели",
                              "Давай создадим учебную цель!\n\n"
                              "Я заполню поле 'Название цели' примером:\n"
                              "'Подготовка к экзамену по физике'\n\n"
                              "В реальной работе ты будешь вводить свои цели."):
                return

            # Заполняем название
            self.editor.goal_input.setText("Подготовка к экзамену по физике")
            self.editor.goal_input.setStyleSheet("")

            # Шаг 4: SMART - Specific (Конкретность)
            highlight_widget(self.editor.s_input, "#f5c2e7")
            if not custom_msg("Шаг 3: S - Specific (Конкретность)",
                              "SMART начинается с буквы S — Specific.\n\n"
                              "Опиши КОНКРЕТНО, что ты будешь делать.\n\n"
                              "Пример: 'Изучить 5 глав учебника, решить 20 задач'"):
                return

            self.editor.s_input.setText("Изучить главы 1-5 учебника Перышкина, решить 20 задач из задачника")
            self.editor.s_input.setStyleSheet("")

            # Шаг 5: SMART - Measurable (Измеримость)
            highlight_widget(self.editor.m_input, "#fab387")
            if not custom_msg("Шаг 4: M - Measurable (Измеримость)",
                              "M — Measurable. Как поймешь, что цель достигнута?\n\n"
                              "Должны быть четкие критерии успеха!\n\n"
                              "Пример: 'Решу все задачи без ошибок, сдам пробный тест на 80+'"):
                return

            self.editor.m_input.setText("Решу все 20 задач, сдам пробный тест на оценку не ниже 80%")
            self.editor.m_input.setStyleSheet("")

            # Шаг 6: SMART - Achievable (Достижимость)
            highlight_widget(self.editor.a_input, "#a6e3a1")
            if not custom_msg("Шаг 5: A - Achievable (Достижимость)",
                              "A — Achievable. Реально ли это выполнить?\n\n"
                              "Есть ли у тебя ресурсы: время, материалы, знания?\n\n"
                              "Пример: 'Есть учебник, 2 часа в день, помощь репетитора'"):
                return

            self.editor.a_input.setText("Есть учебник, задачник, доступ к онлайн-урокам, могу уделять 2 часа в день")
            self.editor.a_input.setStyleSheet("")

            # Шаг 7: SMART - Relevant (Актуальность)
            highlight_widget(self.editor.r_input, "#cba6f7")
            if not custom_msg("Шаг 6: R - Relevant (Актуальность)",
                              "R — Relevant. Почему это важно СЕЙЧАС?\n\n"
                              "Как эта цель связана с твоими планами?\n\n"
                              "Пример: 'Нужно для поступления, экзамен через 2 недели'"):
                return

            self.editor.r_input.setText("Экзамен влияет на итоговую оценку и поступление в ВУЗ")
            self.editor.r_input.setStyleSheet("")

            # Шаг 8: SMART - Time-bound (Сроки)
            highlight_widget(self.editor.end_date, "#f38ba8")
            if not custom_msg("Шаг 7: T - Time-bound (Ограниченность во времени)",
                              "T — Time-bound. Последняя буква SMART!\n\n"
                              "Установи ДЕДЛАЙН. Без срока цель — просто мечта.\n\n"
                              "Я установлю дату через 14 дней от сегодня."):
                return

            # Устанавливаем даты
            from datetime import datetime, timedelta
            today = datetime.now()
            start_date = today
            end_date = today + timedelta(days=14)

            self.editor.start_date.setDate(QtCore.QDate(start_date.year, start_date.month, start_date.day))
            self.editor.end_date.setDate(QtCore.QDate(end_date.year, end_date.month, end_date.day))
            self.editor.end_date.setStyleSheet("")
            self.editor.start_date.setStyleSheet("")

            # Шаг 9: Сохранение
            highlight_widget(self.editor.btnSave, "#a6e3a1")
            if not custom_msg("Шаг 8: Сохранение цели",
                              "Отлично! Все поля SMART заполнены.\n\n"
                              "Теперь нажми 'Сохранить', чтобы\n"
                              "зафиксировать цель в базе данных."):
                return

            # Имитируем сохранение
            self.editor.btnSave.click()
            self.editor.btnSave.setStyleSheet("")

            QtCore.QTimer.singleShot(400, lambda: None)

            # Шаг 10: Переход к диаграмме
            highlight_widget(self.editor.btnSwitch, "#89b4fa")
            if not custom_msg("Шаг 9: Визуализация на диаграмме Ганта",
                              "Цель создана! 🎉\n\n"
                              "Теперь посмотрим, как она выглядит\n"
                              "на диаграмме Ганта.\n\n"
                              "Нажми кнопку для перехода к диаграмме!",
                              is_final=True):
                return

            self.editor.btnSwitch.setStyleSheet("")
            self.editor.btnSwitch.click()

            # Финальные подсказки с задержкой
            QtCore.QTimer.singleShot(800, lambda: self._show_timeline_help())

        except Exception as e:
            print(f"Ошибка в onboarding: {e}")
            import traceback
            traceback.print_exc()
        finally:
            reset_all_onboarding_styles()

    def _show_timeline_help(self):
        """Показывает подсказки по работе с диаграммой"""

        help_text = """<b>Твоя первая цель на диаграмме Ганта!</b><br><br>

    <b>🔍 Управление масштабом:</b><br>
    - Используй кнопки <b>+</b> и <b>–</b> для изменения масштаба<br>
    - Доступные режимы: 1 день, 7 дней, 14 дней, 30 дней<br>
    - <span style='color: #f38ba8;'><b>⚠ Красная линия "СЕГОДНЯ" видна только в режиме "1 день"!</b></span><br><br>

    <b>💡 Полезные функции:</b><br>
    - Наводи курсор на полоску задачи — увидишь подробности<br>
    - Кликни на полоску — откроется редактор этой цели<br>
    - Используй колесико мыши для прокрутки<br><br>

    <b>Попробуй сменить масштаб на "1 день", чтобы увидеть красную линию!</b>"""

        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("🎯 Как работать с диаграммой")
        msg.setTextFormat(QtCore.Qt.RichText)
        msg.setText(help_text)
        msg.addButton("Понятно!", QtWidgets.QMessageBox.AcceptRole)
        msg.exec_()