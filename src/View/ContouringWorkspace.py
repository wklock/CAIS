import logging
from glob import glob
from tkinter import (
    N,
    S,
    E,
    W,
    ttk,
    GROOVE,
    font,
    Label,
    DISABLED,
    NORMAL,
    filedialog,
    Menu,
)
from tkinter.ttk import Frame

from src.DicomProcessing.DicomManager import DicomManager
from src.View.ResizingImageCanvas import ResizingImageCanvas


class ContouringWorkspace(Frame):
    """
    The base workspace for CAIS. Holds a ResizingImageCanvas and some helper labels for the threshold value and
    slice index.
    """

    def __init__(self, parent, **kwargs):
        """
        Workspace initializer
        :param parent: The parent to this element
        :param kwargs: Misc. keyword arguments
        """
        super().__init__(**kwargs)
        self.logger = logging.getLogger(__name__)
        self.image_canvas = ResizingImageCanvas(
            parent=self, image=None, highlightthickness=0
        )

        self.image_canvas.grid(column=0, row=0, sticky=(N, S, E, W))
        control_frame = ttk.Frame(parent, borderwidth=2, relief=GROOVE)
        control_frame.grid(column=0, row=1, sticky=(N, S, E, W))

        info_frame = ttk.Frame(parent)
        info_frame.grid(column=1, row=0, sticky=(N, S, E, W))

        slice_font = font.Font(family="Helvetica", size=24, weight=font.BOLD)

        self.slice_label = Label(info_frame, text="0", state=DISABLED, font=slice_font)
        self.slice_label.grid(column=0, row=0)
        self.thresh_label = Label(info_frame, text="0", state=DISABLED, font=slice_font)
        self.thresh_label.grid(column=0, row=2)

        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        self.image_canvas.columnconfigure(1, weight=3)
        self.image_canvas.rowconfigure(1, weight=1)
        info_frame.columnconfigure(2, weight=1)
        info_frame.rowconfigure(2, weight=1)
        menubar = self.init_menu(parent)
        parent.config(menu=menubar)

    def update_canvas_image(self, path):
        """
        Opens the data at path in the ResizingImageCanvas
        :param path: The path for the data
        """
        self.image_canvas.open_image(path)
        self.image_canvas.focus_set()

    def update_image_folder(self, folder):
        """
        Reconfigures the image folder for the ResizingImageCanvas
        :param folder: The folder that the user selected
        """
        self.image_canvas.set_folder(folder)
        self.slice_label.config(state=NORMAL, foreground="red")
        self.image_canvas.focus_set()

    def update_slice_label(self, slice_idx):
        self.slice_label.config(text=str(slice_idx))

    def update_thresh_label(self, thresh_val):
        self.thresh_label.config(text=str(thresh_val))

    def on_open_file(self):
        """
        Called when the user opens a file from the File menu
        """
        ftypes = [("Bitmap Image", "*.bmp")]
        dlg = filedialog.Open(None, filetypes=ftypes)
        file_loader = dlg.show()
        if file_loader != "":
            self.logger.debug("User chose: {}".format(file_loader))
            if len(file_loader) == 0:
                return
            self.update_canvas_image(file_loader)

    def on_open_folder(self):
        """
        Called when the user opens a folder from the File menu
        """
        folder = filedialog.askdirectory()
        if folder != "":
            self.logger.debug("User chose: {}".format(folder))
            if len(folder) == 0:
                return

            g = glob(folder + "/*.dcm")
            if len(g) > 0:
                dm = DicomManager(folder)
                self.image_canvas.set_dm(dm)
                self.image_canvas.focus_set()

            else:
                self.update_image_folder(folder)

    def init_menu(self, root):
        """
        Initialize the file menu for opening files/folders
        :param root: The root of the menu element
        :return: The initialized Menu element
        """
        menubar = Menu(root)
        filemenu = Menu(menubar, tearoff=0)

        filemenu.add_command(label="Open file", command=self.on_open_file)
        filemenu.add_command(label="Open folder", command=self.on_open_folder)

        filemenu.add_separator()

        filemenu.add_command(label="Exit", command=root.quit)
        menubar.add_cascade(label="File", menu=filemenu)
        editmenu = Menu(menubar, tearoff=0)

        editmenu.add_separator()

        helpmenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=helpmenu)

        return menubar
