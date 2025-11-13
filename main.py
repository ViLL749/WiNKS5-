import sys
import sqlite3
from PyQt5 import QtWidgets, QtCore, QtGui

DB_FILE = "smart_planner.db"


class SmartPlanner(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SMART-Planner")
        self.resize(1100, 720)

        # Шаги временной шкалы: 1 / 7 / 14 / 30 дней на деление
        self.zoom_modes = [1, 7, 14, 30]
        self.zoom_index = 2  # по умолчанию 14 дней/деление
        self.current_task_id = None

        # ===== База данных =====
        self.conn = sqlite3.connect(DB_FILE)
        self.create_fresh_schema()  # создаёт таблицу, если её нет

        # ===== UI =====
        main = QtWidgets.QWidget()
        self.setCentralWidget(main)
        layout = QtWidgets.QHBoxLayout(main)

        # Список задач слева
        self.task_list = QtWidgets.QListWidget()
        self.task_list.itemClicked.connect(self.load_task_from_item)
        layout.addWidget(self.task_list, 1)

        # Справа стек: редактор / диаграмма
        self.right_stack = QtWidgets.QStackedWidget()
        layout.addWidget(self.right_stack, 3)

        # === Редактор ===
        editor = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout(editor)
        switch_btn = QtWidgets.QPushButton("Переключить на диаграмму")
        switch_btn.clicked.connect(self.toggle_view)
        vbox.addWidget(switch_btn)

        self.goal_input = QtWidgets.QLineEdit()
        self.goal_input.setPlaceholderText("Название цели")
        vbox.addWidget(self.goal_input)

        grid = QtWidgets.QGridLayout()
        self.s_input = QtWidgets.QTextEdit()
        self.s_input.setPlaceholderText("S — Specific")
        self.m_input = QtWidgets.QTextEdit()
        self.m_input.setPlaceholderText("M — Measurable")
        self.a_input = QtWidgets.QTextEdit()
        self.a_input.setPlaceholderText("A — Achievable")
        self.r_input = QtWidgets.QTextEdit()
        self.r_input.setPlaceholderText("R — Relevant")

        grid.addWidget(QtWidgets.QLabel("S"), 0, 0)
        grid.addWidget(self.s_input, 0, 1)
        grid.addWidget(QtWidgets.QLabel("M"), 1, 0)
        grid.addWidget(self.m_input, 1, 1)
        grid.addWidget(QtWidgets.QLabel("A"), 2, 0)
        grid.addWidget(self.a_input, 2, 1)
        grid.addWidget(QtWidgets.QLabel("R"), 3, 0)
        grid.addWidget(self.r_input, 3, 1)
        grid.setColumnStretch(1, 1)
        vbox.addLayout(grid)

        dates = QtWidgets.QHBoxLayout()
        self.start_date = QtWidgets.QDateEdit(calendarPopup=True)
        self.end_date = QtWidgets.QDateEdit(calendarPopup=True)
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        self.start_date.setDate(QtCore.QDate.currentDate())
        self.end_date.setDate(QtCore.QDate.currentDate())
        dates.addWidget(QtWidgets.QLabel("Начало:"))
        dates.addWidget(self.start_date)
        dates.addSpacing(10)
        dates.addWidget(QtWidgets.QLabel("Окончание:"))
        dates.addWidget(self.end_date)
        vbox.addLayout(dates)

        row_btns = QtWidgets.QHBoxLayout()
        save_btn = QtWidgets.QPushButton("Сохранить")
        del_btn = QtWidgets.QPushButton("Удалить")
        add_btn = QtWidgets.QPushButton("Новая задача")
        row_btns.addWidget(save_btn)
        row_btns.addWidget(del_btn)
        row_btns.addWidget(add_btn)
        vbox.addLayout(row_btns)

        save_btn.clicked.connect(self.save_task)
        del_btn.clicked.connect(self.delete_task)
        add_btn.clicked.connect(self.add_task)

        self.right_stack.addWidget(editor)

        # === Диаграмма ===
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
        self.scene.selectionChanged.connect(self.on_scene_selection_changed)
        self.view = QtWidgets.QGraphicsView(self.scene)
        self.view.setRenderHint(QtGui.QPainter.Antialiasing)
        self.view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        tl.addWidget(self.view)

        self.right_stack.addWidget(timeline)

        self.setup_styles()
        self.load_tasks()

    # ===== Стили =====
    def setup_styles(self):
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

    # ===== База: новая схема =====
    def create_fresh_schema(self):
        c = self.conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS tasks(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            s_text TEXT,
            m_text TEXT,
            a_text TEXT,
            r_text TEXT,
            start_date TEXT, -- yyyy-MM-dd
            end_date TEXT -- yyyy-MM-dd
        )
        """)
        self.conn.commit()

    # ===== Работа со списком =====
    def load_tasks(self):
        self.task_list.clear()
        c = self.conn.cursor()
        c.execute("SELECT id,title FROM tasks ORDER BY id ASC")
        rows = c.fetchall()
        if not rows:
            self.task_list.addItem("(Нет задач)")
            self.task_list.setEnabled(False)
            return
        self.task_list.setEnabled(True)
        for tid, title in rows:
            it = QtWidgets.QListWidgetItem(title or f"Задача {tid}")
            it.setData(QtCore.Qt.UserRole, tid)
            self.task_list.addItem(it)

    def load_task_from_item(self, item):
        if item.text() == "(Нет задач)":
            return
        tid = item.data(QtCore.Qt.UserRole)
        c = self.conn.cursor()
        c.execute("""SELECT title,s_text,m_text,a_text,r_text,start_date,end_date
                    FROM tasks WHERE id=?""", (tid,))
        row = c.fetchone()
        if not row:
            return
        self.current_task_id = tid
        title, s, m, a, r, sdate, edate = row
        self.goal_input.setText(title or "")
        self.s_input.setText(s or "")
        self.m_input.setText(m or "")
        self.a_input.setText(a or "")
        self.r_input.setText(r or "")
        if sdate:
            self.start_date.setDate(QtCore.QDate.fromString(sdate, "yyyy-MM-dd"))
        if edate:
            self.end_date.setDate(QtCore.QDate.fromString(edate, "yyyy-MM-dd"))

    # ===== CRUD =====
    def save_task(self):
        title = self.goal_input.text().strip()
        if not title:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Название цели обязательно.")
            return
        sdt = self.start_date.date()
        edt = self.end_date.date()
        if edt < sdt:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Дата окончания раньше даты начала.")
            return
        s_text = self.s_input.toPlainText().strip()
        m_text = self.m_input.toPlainText().strip()
        a_text = self.a_input.toPlainText().strip()
        r_text = self.r_input.toPlainText().strip()
        s = sdt.toString("yyyy-MM-dd")
        e = edt.toString("yyyy-MM-dd")
        c = self.conn.cursor()
        if self.current_task_id:
            c.execute("""UPDATE tasks
                        SET title=?,s_text=?,m_text=?,a_text=?,r_text=?,start_date=?,end_date=?
                        WHERE id=?""",
                      (title, s_text, m_text, a_text, r_text, s, e, self.current_task_id))
        else:
            c.execute("""INSERT INTO tasks(title,s_text,m_text,a_text,r_text,start_date,end_date)
                        VALUES(?,?,?,?,?,?,?)""",
                      (title, s_text, m_text, a_text, r_text, s, e))
            self.current_task_id = c.lastrowid
        self.conn.commit()
        self.load_tasks()

    def delete_task(self):
        if not self.current_task_id:
            return
        if QtWidgets.QMessageBox.question(
            self, "Удалить", "Удалить задачу?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        ) == QtWidgets.QMessageBox.Yes:
            c = self.conn.cursor()
            c.execute("DELETE FROM tasks WHERE id=?", (self.current_task_id,))
            self.conn.commit()
            self.current_task_id = None
            self.add_task()
            self.load_tasks()

    def add_task(self):
        self.current_task_id = None
        self.goal_input.clear()
        for w in (self.s_input, self.m_input, self.a_input, self.r_input):
            w.clear()
        d = QtCore.QDate.currentDate()
        self.start_date.setDate(d)
        self.end_date.setDate(d)
        self.goal_input.setFocus()

    # ===== Переключение вида =====
    def toggle_view(self):
        if self.right_stack.currentIndex() == 0:
            self.draw_diagram()
            self.right_stack.setCurrentIndex(1)
        else:
            self.right_stack.setCurrentIndex(0)

    # ===== Масштаб =====
    def change_zoom(self, delta):
        new_index = self.zoom_index + delta
        if 0 <= new_index < len(self.zoom_modes):
            self.zoom_index = new_index
            val = self.zoom_modes[self.zoom_index]
            unit = "день" if val == 1 else "дней"
            self.zoom_label.setText(f"Масштаб: {val} {unit}/деление")
            self.draw_diagram()

    # ===== Диаграмма =====
    def fetch_tasks(self):
        c = self.conn.cursor()
        c.execute("SELECT id,title,start_date,end_date,s_text,m_text,a_text,r_text FROM tasks")
        res = []
        for tid, title, s, e, S, M, A, R in c.fetchall():
            if not s or not e:
                continue
            sd = QtCore.QDate.fromString(s, "yyyy-MM-dd")
            ed = QtCore.QDate.fromString(e, "yyyy-MM-dd")
            if not (sd.isValid() and ed.isValid()):
                continue
            tooltip = (
                f"{title}\n"
                f"S: {S or '-'}\nM: {M or '-'}\nA: {A or '-'}\nR: {R or '-'}\n"
                f"{sd.toString('yyyy-MM-dd')} → {ed.toString('yyyy-MM-dd')}"
            )
            res.append((tid, title or f"Задача {tid}", sd, ed, tooltip))
        return res

    def on_scene_selection_changed(self):
        items = self.scene.selectedItems()
        if not items:
            return
        tid = items[0].data(0)
        if tid:
            self.right_stack.setCurrentIndex(0)
            for i in range(self.task_list.count()):
                it = self.task_list.item(i)
                if it.data(QtCore.Qt.UserRole) == tid:
                    self.task_list.setCurrentRow(i)
                    self.load_task_from_item(it)
                    break

    # ===== Вспомогательные функции для «целой» и длинной оси =====
    def _align_to_step(self, qdate: QtCore.QDate, step_days: int, ceil=False) -> QtCore.QDate:
        """Округление даты к границе шага (вниз/вверх)."""
        epoch = QtCore.QDate(2000, 1, 1)  # произвольная фиксированная эпоха
        days = epoch.daysTo(qdate)
        if ceil:
            k = (days + (step_days - 1)) // step_days
        else:
            k = days // step_days
        return epoch.addDays(k * step_days)

    def _ensure_min_span(
        self, start_d, end_d, step_days, px_per_day, min_divisions, viewport_width, left_pad, right_pad
    ):
        """
        Возвращает (axis_start_date, axis_end_date) так, чтобы:
        - количество делений >= min_divisions;
        - визуальная длина оси >= ширины вьюпорта;
        - конец выровнен к границе шага.
        """
        # Минимум по делениям
        span_days_min_div = min_divisions * step_days
        # Минимум по ширине вьюпорта
        needed_px = max(0, viewport_width - (left_pad + right_pad))
        span_days_min_view = int((needed_px / max(px_per_day, 0.001)) + 0.999)

        base_span = start_d.daysTo(end_d)
        span_days = max(base_span, span_days_min_div, span_days_min_view)

        axis_start = start_d
        axis_end = axis_start.addDays(span_days)
        axis_end = self._align_to_step(axis_end, step_days, ceil=True)
        return axis_start, axis_end

    def draw_diagram(self):
        self.scene.clear()
        tasks = self.fetch_tasks()
        if not tasks:
            t = self.scene.addText("Нет задач с корректными датами")
            t.setDefaultTextColor(QtGui.QColor("#cdd6f4"))
            t.setPos(20, 20)
            self.scene.setSceneRect(0, 0, 600, 200)
            return

        # ---- Параметры шага и масштаба ----
        step_days = self.zoom_modes[self.zoom_index]   # 1 / 7 / 14 / 30
        px_per_day = 3.6 * (30 / step_days)           # пикс/день
        left_pad, right_pad = 40, 40
        y = 20
        bar_h = 35
        spacing = 60

        # ---- Даты задач ----
        min_task_date = min(t[2] for t in tasks)
        max_task_date = max(t[3] for t in tasks).addDays(1)  # включительно

        # ---- 1) Выравниваем к «целым» границам шага ----
        axis_start_date = self._align_to_step(min_task_date, step_days, ceil=False)
        axis_end_date_raw = self._align_to_step(max_task_date, step_days, ceil=True)

        # ---- 2) Гарантируем минимальную длину оси (деления + ширина вьюпорта) ----
        viewport_w = max(1, self.view.viewport().width())
        axis_start_date, axis_end_date = self._ensure_min_span(
            axis_start_date, axis_end_date_raw, step_days, px_per_day,
            min_divisions=10,  # минимум 10 делений
            viewport_width=viewport_w, left_pad=left_pad, right_pad=right_pad
        )

        # ---- Геометрия оси ----
        total_days_boundary = axis_start_date.daysTo(axis_end_date)
        axis_start_x = left_pad
        axis_end_x = axis_start_x + total_days_boundary * px_per_day

        # ---- Блоки задач ----
        for tid, title, sd, ed, tip in tasks:
            x = axis_start_x + axis_start_date.daysTo(sd) * px_per_day
            w = max(15, sd.daysTo(ed.addDays(1)) * px_per_day)  # конец включительно
            rect = self.scene.addRect(
                QtCore.QRectF(x, y, w, bar_h),
                QtGui.QPen(QtGui.QColor("#89b4fa"), 2),
                QtGui.QBrush(QtGui.QColor(70, 130, 180))
            )
            rect.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
            rect.setData(0, tid)
            rect.setToolTip(tip)

            txt = self.scene.addText(title)
            txt.setDefaultTextColor(QtGui.QColor("#cdd6f4"))
            f = txt.font()
            f.setPointSize(9)
            f.setBold(True)
            txt.setFont(f)
            txt.setPos(x + 8, y + 6)

            dtx = self.scene.addText(f"{sd.toString('dd.MM')} → {ed.toString('dd.MM')}")
            dtx.setDefaultTextColor(QtGui.QColor("#a6adc8"))
            dtx.setFont(QtGui.QFont("Segoe UI", 8))
            dtx.setPos(x + 8, y + 22)

            y += spacing

        # ---- Ось времени ----
        axis_y = y + 15
        self.scene.addLine(
            axis_start_x, axis_y, axis_end_x, axis_y,
            QtGui.QPen(QtGui.QColor("#585b70"), 2)
        )

        # Деления и подписи
        tick_font = QtGui.QFont("Segoe UI", 10)
        fm = QtGui.QFontMetrics(tick_font)

        current = axis_start_date
        while current < axis_end_date:
            x = axis_start_x + axis_start_date.daysTo(current) * px_per_day
            self.scene.addLine(x, axis_y - 5, x, axis_y + 5, QtGui.QPen(QtGui.QColor("#89b4fa")))
            lbl = self.scene.addText(current.toString("dd.MM"))
            lbl.setFont(tick_font)
            lbl.setDefaultTextColor(QtGui.QColor("#bac2de"))
            try:
                half = fm.horizontalAdvance("00.00") / 2
            except AttributeError:
                half = fm.width("00.00") / 2
            lbl.setPos(x - half, axis_y + 8)
            current = current.addDays(step_days)

        # Последняя метка — ровно на конце оси, подпись = последний день интервала
        last_text = axis_end_date.addDays(-1).toString("dd.MM")
        try:
            last_half = fm.horizontalAdvance(last_text) / 2
        except AttributeError:
            last_half = fm.width(last_text) / 2
        last_x = axis_end_x
        self.scene.addLine(last_x, axis_y - 5, last_x, axis_y + 5, QtGui.QPen(QtGui.QColor("#89b4fa")))
        last_lbl = self.scene.addText(last_text)
        last_lbl.setFont(tick_font)
        last_lbl.setDefaultTextColor(QtGui.QColor("#bac2de"))
        last_lbl.setPos(last_x - last_half, axis_y + 8)

        # ---- Итоговые границы сцены ----
        tail_pad = last_half + 20
        scene_w = max(axis_end_x + tail_pad + right_pad, viewport_w + 1)
        self.scene.setSceneRect(0, 0, scene_w, axis_y + 60)


def main():
    app = QtWidgets.QApplication(sys.argv)
    w = SmartPlanner()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
