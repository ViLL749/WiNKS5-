# gui/task_editor.py
from PyQt5 import QtWidgets, QtCore

class TaskEditorWidget(QtWidgets.QWidget):
    sigSave = QtCore.pyqtSignal(dict)
    sigDelete = QtCore.pyqtSignal(int)
    sigNew = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        vbox = QtWidgets.QVBoxLayout(self)

        self.btnSwitch = QtWidgets.QPushButton("Переключить на диаграмму")
        vbox.addWidget(self.btnSwitch)

        self.goal_input = QtWidgets.QLineEdit()
        self.goal_input.setPlaceholderText("Название цели")
        vbox.addWidget(self.goal_input)

        grid = QtWidgets.QGridLayout()
        self.s_input = QtWidgets.QTextEdit(); self.s_input.setPlaceholderText("S — Specific")
        self.m_input = QtWidgets.QTextEdit(); self.m_input.setPlaceholderText("M — Measurable")
        self.a_input = QtWidgets.QTextEdit(); self.a_input.setPlaceholderText("A — Achievable")
        self.r_input = QtWidgets.QTextEdit(); self.r_input.setPlaceholderText("R — Relevant")

        grid.addWidget(QtWidgets.QLabel("S"), 0, 0); grid.addWidget(self.s_input, 0, 1)
        grid.addWidget(QtWidgets.QLabel("M"), 1, 0); grid.addWidget(self.m_input, 1, 1)
        grid.addWidget(QtWidgets.QLabel("A"), 2, 0); grid.addWidget(self.a_input, 2, 1)
        grid.addWidget(QtWidgets.QLabel("R"), 3, 0); grid.addWidget(self.r_input, 3, 1)
        grid.setColumnStretch(1, 1)
        vbox.addLayout(grid)

        dates = QtWidgets.QHBoxLayout()
        self.start_date = QtWidgets.QDateEdit(calendarPopup=True)
        self.end_date = QtWidgets.QDateEdit(calendarPopup=True)
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        self.start_date.setDate(QtCore.QDate.currentDate())
        self.end_date.setDate(QtCore.QDate.currentDate())
        dates.addWidget(QtWidgets.QLabel("Начало:")); dates.addWidget(self.start_date)
        dates.addSpacing(10)
        dates.addWidget(QtWidgets.QLabel("Окончание:")); dates.addWidget(self.end_date)
        vbox.addLayout(dates)

        row_btns = QtWidgets.QHBoxLayout()
        self.btnSave = QtWidgets.QPushButton("Сохранить")
        self.btnDel = QtWidgets.QPushButton("Удалить")
        self.btnNew = QtWidgets.QPushButton("Новая задача")
        row_btns.addWidget(self.btnSave); row_btns.addWidget(self.btnDel); row_btns.addWidget(self.btnNew)
        vbox.addLayout(row_btns)

        self._current_id = None

        self.btnSave.clicked.connect(self._emit_save)
        self.btnDel.clicked.connect(lambda: self.sigDelete.emit(self._current_id) if self._current_id else None)
        self.btnNew.clicked.connect(self._emit_new)

    def _emit_save(self):
        payload = dict(
            id=self._current_id,
            title=self.goal_input.text().strip(),
            s_text=self.s_input.toPlainText().strip(),
            m_text=self.m_input.toPlainText().strip(),
            a_text=self.a_input.toPlainText().strip(),
            r_text=self.r_input.toPlainText().strip(),
            start_date=self.start_date.date().toString("yyyy-MM-dd"),
            end_date=self.end_date.date().toString("yyyy-MM-dd"),
        )
        self.sigSave.emit(payload)

    def _emit_new(self):
        self.clear_form()
        self.sigNew.emit()

    def set_task(self, task_row):
        # task_row — словарь из TaskManager.fetch_one()
        self._current_id = task_row["id"]
        self.goal_input.setText(task_row["title"] or "")
        self.s_input.setText(task_row["s_text"] or "")
        self.m_input.setText(task_row["m_text"] or "")
        self.a_input.setText(task_row["a_text"] or "")
        self.r_input.setText(task_row["r_text"] or "")
        if task_row["start_date"]:
            self.start_date.setDate(QtCore.QDate.fromString(task_row["start_date"], "yyyy-MM-dd"))
        if task_row["end_date"]:
            self.end_date.setDate(QtCore.QDate.fromString(task_row["end_date"], "yyyy-MM-dd"))

    def clear_form(self):
        self._current_id = None
        self.goal_input.clear()
        for w in (self.s_input, self.m_input, self.a_input, self.r_input):
            w.clear()
        d = QtCore.QDate.currentDate()
        self.start_date.setDate(d)
        self.end_date.setDate(d)
        self.goal_input.setFocus()
