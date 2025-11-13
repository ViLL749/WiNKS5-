from PyQt5 import QtWidgets, QtCore


class TaskListWidget(QtWidgets.QListWidget):
    itemSelected = QtCore.pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.itemClicked.connect(self._click)

    def load(self, rows):
        self.clear()

        if not rows:
            self.addItem("(Нет задач)")
            self.setEnabled(False)
            return

        self.setEnabled(True)
        for r in rows:
            title = r["title"] or f"Задача {r['id']}"
            item = QtWidgets.QListWidgetItem(title)
            item.setData(QtCore.Qt.UserRole, r["id"])
            self.addItem(item)

    def _click(self, item):
        if item.text() == "(Нет задач)":
            return
        tid = item.data(QtCore.Qt.UserRole)
        if tid:
            self.itemSelected.emit(tid)
