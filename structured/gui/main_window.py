# gui/main_window.py
from PyQt5 import QtWidgets, QtCore, QtGui
from gui.task_list_widget import TaskListWidget
from gui.task_editor import TaskEditorWidget
from visualization.timeline_render import TimelineRenderer
from visualization.animator_controller import AnimatorController
from logic.task_manager import TaskManager
from logic.validator import validate_task

class SmartPlannerMainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SMART-Planner")
        self.resize(1100, 720)

        # масштаб (дней на деление)
        self.zoom_modes = [1, 7, 14, 30]
        self.zoom_index = 2  # 14 по умолчанию

        # === Данные ===
        self.tm = TaskManager(db_file="smart_planner.db")
        self.tm.ensure_schema()

        # === UI ===
        main = QtWidgets.QWidget()
        self.setCentralWidget(main)
        layout = QtWidgets.QHBoxLayout(main)

        # Список задач слева
        self.task_list = TaskListWidget()
        layout.addWidget(self.task_list, 1)

        # Справа стек: редактор / диаграмма
        self.right_stack = QtWidgets.QStackedWidget()
        layout.addWidget(self.right_stack, 3)

        # Редактор
        self.editor = TaskEditorWidget()
        self.right_stack.addWidget(self.editor)

        # Диаграмма
        timeline = QtWidgets.QWidget()
        tl = QtWidgets.QVBoxLayout(timeline)
        top = QtWidgets.QHBoxLayout()
        back_btn = QtWidgets.QPushButton("Вернуться к задачам")
        back_btn.clicked.connect(self.toggle_view)
        top.addWidget(back_btn)
        top.addStretch(1)

        self.zoom_label = QtWidgets.QLabel("Масштаб: 14 дней/деление")
        z_minus = QtWidgets.QPushButton("–")
        z_plus = QtWidgets.QPushButton("+")
        z_minus.setToolTip("Увеличить шаг (отдалить)")
        z_plus.setToolTip("Уменьшить шаг (приблизить)")
        z_minus.clicked.connect(lambda: self.change_zoom(-1))
        z_plus.clicked.connect(lambda: self.change_zoom(+1))
        top.addWidget(self.zoom_label)
        top.addWidget(z_minus)
        top.addWidget(z_plus)
        tl.addLayout(top)

        self.scene = QtWidgets.QGraphicsScene()
        self.view = QtWidgets.QGraphicsView(self.scene)
        self.view.setRenderHint(QtGui.QPainter.Antialiasing)
        self.view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        tl.addWidget(self.view)
        self.right_stack.addWidget(timeline)

        # Рендерер диаграммы и «аниматор» масштаба (заготовка)
        self.renderer = TimelineRenderer()
        self.anim = AnimatorController()

        # Подключения сигналов
        self.task_list.itemSelected.connect(self._on_task_selected)
        self.editor.sigSave.connect(self._on_save_task)
        self.editor.sigDelete.connect(self._on_delete_task)
        self.editor.sigNew.connect(self._on_new_task)
        self.scene.selectionChanged.connect(self._on_scene_selection_changed)

        self._apply_styles()
        self._reload_list()
        self.right_stack.setCurrentIndex(0)

        # Кнопка в редакторе «переключить на диаграмму»
        self.editor.btnSwitch.clicked.connect(self.toggle_view)

    # ===== GUI helpers =====
    def _apply_styles(self):
        self.setStyleSheet("""
        QMainWindow,QWidget{background:#1e1e2e;color:#cdd6f4;font-family:'Segoe UI';font-size:10pt;}
        QListWidget{background:#181825;border:1px solid #313244;border-radius:10px;padding:8px;margin:5px;}
        QListWidget::item{padding:8px;margin:3px;border-radius:6px;background:#313244;}
        QListWidget::item:selected{background:#89b4fa;color:#1e1e2e;font-weight:bold;}
        QLineEdit,QTextEdit,QDateEdit{background:#313244;border:2px solid #45475a;border-radius:10px;padding:8px;color:#cdd6f4;}
        QPushButton{background:#313244;color:#cdd6f4;border:2px solid #45475a;border-radius:10px;padding:8px 12px;font-weight:bold;}
        QPushButton:hover{background:#45475a;border:2px solid #89b4fa;}
        QGraphicsView{background:#181825;border:1px solid #313244;border-radius:10px;}
        """)

    def _reload_list(self):
        tasks = self.tm.fetch_all_min()
        self.task_list.load(tasks)

    def _load_task_into_editor(self, task_id):
        task = self.tm.fetch_one(task_id)
        if task:
            self.editor.set_task(task)

    # ===== Сигналы слева/редактор =====
    def _on_task_selected(self, task_id):
        self._load_task_into_editor(task_id)
        self.right_stack.setCurrentIndex(0)

    def _on_save_task(self, payload):
        ok, err = validate_task(payload)
        if not ok:
            QtWidgets.QMessageBox.warning(self, "Ошибка", err)
            return

        # Сохраняем задачу
        if payload.get("id"):
            self.tm.update_task(payload["id"], payload)
        else:
            new_id = self.tm.create_task(payload)
            payload["id"] = new_id

        # Обновляем список
        self._reload_list()

        # Сообщение пользователю
        QtWidgets.QMessageBox.information(self, "Сохранено", "Задача успешно сохранена.")

        # Очищаем форму и сбрасываем id (готово к созданию новой задачи)
        self.editor.clear_form()
        self.right_stack.setCurrentIndex(0)

    def _on_delete_task(self, task_id):
        if not task_id:
            return
        if QtWidgets.QMessageBox.question(
            self, "Удалить", "Удалить задачу?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        ) == QtWidgets.QMessageBox.Yes:
            self.tm.delete_task(task_id)
            self.editor.clear_form()
            self._reload_list()

    def _on_new_task(self):
        self.editor.clear_form()

    # ===== Диаграмма =====
    def toggle_view(self):
        if self.right_stack.currentIndex() == 0:
            self.draw_diagram()
            self.right_stack.setCurrentIndex(1)
        else:
            self.right_stack.setCurrentIndex(0)

    def change_zoom(self, delta):
        new_index = self.zoom_index + delta
        if 0 <= new_index < len(self.zoom_modes):
            # (опционально) плавность через AnimatorController
            self.zoom_index = self.anim.apply_zoom_index(self.zoom_index, new_index)
            val = self.zoom_modes[self.zoom_index]
            unit = "день" if val == 1 else "дней"
            self.zoom_label.setText(f"Масштаб: {val} {unit}/деление")
            self.draw_diagram()

    def draw_diagram(self):
        self.scene.clear()
        tasks = self.tm.fetch_all_full()
        if not tasks:
            t = self.scene.addText("Нет задач с корректными датами")
            t.setDefaultTextColor(QtGui.QColor("#cdd6f4"))
            t.setPos(20, 20)
            self.scene.setSceneRect(0, 0, 600, 200)
            return

        zoom_days = self.zoom_modes[self.zoom_index]
        viewport_w = max(1, self.view.viewport().width())
        self.renderer.draw(self.scene, tasks, zoom_days, viewport_w)

    def _on_scene_selection_changed(self):
        items = self.scene.selectedItems()
        if not items:
            return
        tid = items[0].data(0)
        if tid:
            self._load_task_into_editor(tid)
            self.right_stack.setCurrentIndex(0)
