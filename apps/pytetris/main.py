import sys

from PyQt6.QtWidgets import QApplication

from pytetris.main_window import MainWindow


def main() -> None:
    """Entry point for the PyTetris application."""
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
