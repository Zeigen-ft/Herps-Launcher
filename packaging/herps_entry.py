"""PyInstaller entrypoint; imports shared code without relative entrypoint imports."""
import sys
from herps_launcher.app import main

if __name__ == "__main__":
    if "--smoke-test" in sys.argv:
        import tempfile
        from pathlib import Path
        from PySide6.QtWidgets import QApplication
        from PySide6.QtTest import QTest
        from herps_launcher.app import Window, STYLE
        from herps_launcher.core import Launcher
        app = QApplication([])
        app.setStyleSheet(STYLE)
        with tempfile.TemporaryDirectory() as temporary:
            window = Window(Launcher(Path(temporary)))
            window.show()
            for i, button in enumerate(window.nav):
                QTest.mouseClick(button, __import__("PySide6.QtCore", fromlist=["Qt"]).Qt.MouseButton.LeftButton)
                app.processEvents()
                assert window.pages.currentIndex() == i, f"Page {i} did not open"
            window.close()
        print("Herps Launcher: all five native UI pages opened successfully")
        raise SystemExit(0)
    raise SystemExit(main())
