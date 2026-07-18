from __future__ import annotations

import sys
from PySide6.QtWidgets import QApplication

from astronavigator.application.application import Application
from astronavigator.gui.main_window import MainWindow


def main() -> int:
    qt_app = QApplication(sys.argv)
    application = Application()

    window = MainWindow(application)
    window.show()

    return qt_app.exec()



if __name__ == "__main__":
    raise SystemExit(main())