import sys
from PyQt5 import QtWidgets, QtGui
from gui.main_window import SmartPlannerMainWindow


def main():
    app = QtWidgets.QApplication(sys.argv)

    app_font = QtGui.QFont("Arial")
    app.setFont(app_font)
    win = SmartPlannerMainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    app.setFont(QtGui.QFont("Arial"))
    w = SmartPlannerMainWindow()
    w.show()
    sys.exit(app.exec_())

