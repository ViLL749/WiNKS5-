# gui/task_list_widget.py
from PyQt5 import QtWidgets, QtCore

class TaskListWidget(QtWidgets.QListWidget):
    itemSelected = QtCore.pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.itemClicked.connect(self._on_click)

    def load(self, rows):
        self.clear()
        if not rows:
            self.addItem("(Нет задач)")
            self.setEnabled(False)
            return
        self.setEnabled(True)
        for r in rows:
            it = QtWidgets.QListWidgetItem(r["title"] or f"Задача {r['id']}")
            it.setData(QtCore.Qt.UserRole, r["id"])
            self.addItem(it)

    def _on_click(self, item):
        if item.text() == "(Нет задач)":
            return
        tid = item.data(QtCore.Qt.UserRole)
        if tid:
            self.itemSelected.emit(tid)
