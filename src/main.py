from tkinter import *

import logging

from src.View import ContouringWorkspace

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def main():
    root = Tk()
    ContouringWorkspace(root)
    #root.wm_minsize(3000, 1500)
    # root.maxsize(3000, 1500)
    # root.resizable(0, 0)
    root.mainloop()


if __name__ == "__main__":
    main()
