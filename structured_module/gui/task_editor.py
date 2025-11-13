from PyQt5 import QtWidgets, QtCore


class TaskEditorWidget(QtWidgets.QWidget):
    sigSave = QtCore.pyqtSignal(dict)
    sigDelete = QtCore.pyqtSignal(int)
    sigNew = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()

        vbox = QtWidgets.QVBoxLayout(self)

        # Switch button
        self.btnSwitch = QtWidgets.QPushButton("Переключить на диаграмму")
        vbox.addWidget(self.btnSwitch)

        # Goal
        self.goal_input = QtWidgets.QLineEdit()
        self.goal_input.setPlaceholderText("Название цели")
        vbox.addWidget(self.goal_input)

        # SMART поля
        grid = QtWidgets.QGridLayout()

        self.s_input = QtWidgets.QTextEdit()
        self.s_input.setPlaceholderText(
            "S — Конкретная: каких результатов нужно достичь, какие важные характеристики?"
        )

        self.m_input = QtWidgets.QTextEdit()
        self.m_input.setPlaceholderText(
            "M — Измеримая: какие количественные показатели и критерии успеха?"
        )

        self.a_input = QtWidgets.QTextEdit()
        self.a_input.setPlaceholderText(
            "A — Достижимая: какие действия, последовательность и ресурсы нужны?"
        )

        self.r_input = QtWidgets.QTextEdit()
        self.r_input.setPlaceholderText(
            "R — Актуальная и реалистичная: насколько цель важна и реально достижима?"
        )

        grid.addWidget(QtWidgets.QLabel("S"), 0, 0); grid.addWidget(self.s_input, 0, 1)
        grid.addWidget(QtWidgets.QLabel("M"), 1, 0); grid.addWidget(self.m_input, 1, 1)
        grid.addWidget(QtWidgets.QLabel("A"), 2, 0); grid.addWidget(self.a_input, 2, 1)
        grid.addWidget(QtWidgets.QLabel("R"), 3, 0); grid.addWidget(self.r_input, 3, 1)

        grid.setColumnStretch(1, 1)
        vbox.addLayout(grid)

        # Dates
        dbox = QtWidgets.QHBoxLayout()

        self.start_date = QtWidgets.QDateEdit(calendarPopup=True)
        self.end_date = QtWidgets.QDateEdit(calendarPopup=True)
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        self.end_date.setDisplayFormat("yyyy-MM-dd")

        dbox.addWidget(QtWidgets.QLabel("Начало:"))
        dbox.addWidget(self.start_date)
        dbox.addSpacing(10)
        dbox.addWidget(QtWidgets.QLabel("Окончание:"))
        dbox.addWidget(self.end_date)

        vbox.addLayout(dbox)

        # Buttons
        row = QtWidgets.QHBoxLayout()
        self.btnSave = QtWidgets.QPushButton("Сохранить")
        self.btnDel = QtWidgets.QPushButton("Удалить")
        self.btnNew = QtWidgets.QPushButton("Новая задача")

        row.addWidget(self.btnSave)
        row.addWidget(self.btnDel)
        row.addWidget(self.btnNew)
        vbox.addLayout(row)

        self._current_id = None

        self.btnSave.clicked.connect(self._emit_save)
        self.btnDel.clicked.connect(
            lambda: self.sigDelete.emit(self._current_id) if self._current_id else None
        )
        self.btnNew.clicked.connect(self._emit_new)

        # Default dates
        d = QtCore.QDate.currentDate()
        self.start_date.setDate(d)
        self.end_date.setDate(d)

    # --- internal ---

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

    # --- external API for main_window ---

    def set_task(self, row: dict):
        self._current_id = row["id"]

        self.goal_input.setText(row["title"] or "")
        self.s_input.setText(row["s_text"] or "")
        self.m_input.setText(row["m_text"] or "")
        self.a_input.setText(row["a_text"] or "")
        self.r_input.setText(row["r_text"] or "")

        if row["start_date"]:
            self.start_date.setDate(QtCore.QDate.fromString(row["start_date"], "yyyy-MM-dd"))
        if row["end_date"]:
            self.end_date.setDate(QtCore.QDate.fromString(row["end_date"], "yyyy-MM-dd"))

    def clear_form(self):
        self._current_id = None
        self.goal_input.clear()
        self.s_input.clear()
        self.m_input.clear()
        self.a_input.clear()
        self.r_input.clear()

        d = QtCore.QDate.currentDate()
        self.start_date.setDate(d)
        self.end_date.setDate(d)

        self.goal_input.setFocus()
