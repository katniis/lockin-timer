import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(__file__))

from ui.main_window import MainWindow


def main():
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
