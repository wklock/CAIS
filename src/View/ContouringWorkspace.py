import logging
from glob import glob
from tkinter import N, S, E, W, ttk, GROOVE, Button, font, Label, DISABLED, Listbox, END, NORMAL, Toplevel, filedialog, \
    Menu
from tkinter.ttk import Frame

from src.DicomProcessing.DicomManager import DicomManager
from src.View.ResizingImageCanvas import ResizingImageCanvas


logger = logging.getLogger(__name__)


class ContouringWorkspace(Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(**kwargs)

        #canvas_frame = ttk.Frame(parent)
        #canvas_frame.grid(column=0, row=0, sticky=(N, S, E, W))
        self.image_canvas = ResizingImageCanvas(parent=self, image=None, highlightthickness=0)
        #self.image_canvas.pack(fill=BOTH, expand=YES)
        self.image_canvas.grid(column=0, row=0, sticky=(N,S,E,W))
        #self.frame = ttk.Frame(canvas_frame, borderwidth=5, relief="sunken", width=200, height=100)
        #self.frame.grid(column=0, row=0, columnspan=2, rowspan=2, sticky=(N, W))
        control_frame = ttk.Frame(parent, borderwidth=2, relief=GROOVE)
        control_frame.grid(column=0, row=1, sticky=(N, S, E, W))
        self.bind("<Configure>", self.on_resize)

        b = Button(control_frame, text="OK", command=self.donothing)
        b.grid(column=1, row=0)

        info_frame = ttk.Frame(parent)
        info_frame.grid(column=1, row=0, sticky=(N, S, E, W))

        slice_font = font.Font(family='Helvetica', size=24, weight=font.BOLD)

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
        # tag all of the drawn widgets
        menubar = self.init_menu(parent)
        parent.config(menu=menubar)

    def update_canvas_image(self, path):
        self.image_canvas.open_image(path)
        self.image_canvas.focus_set()

    def update_image_folder(self, folder):
        self.image_canvas.set_folder(folder)
        self.slice_label.config(state=NORMAL, foreground="red")
        self.image_canvas.focus_set()

    def update_slice_label(self, slice_idx):
        self.slice_label.config(text=str(slice_idx))

    def update_thresh_label(self, thresh_val):
        self.thresh_label.config(text=str(thresh_val))

    def on_resize(self):
        pass

    def donothing(self):
        filewin = Toplevel()
        button = Label(filewin, text="Do nothing button")
        button.pack()

    def on_open_file(self):
        ftypes = [('Bitmap Image', '*.bmp')]
        dlg = filedialog.Open(None, filetypes=ftypes)
        fl = dlg.show()
        if fl != '':
            logger.debug('User chose: {}'. format(fl))
            self.update_canvas_image(fl)
            # text = self.readFile(fl)
            # self.txt.insert(END, text)

    def on_open_folder(self):
        folder = filedialog.askdirectory()
        if folder != '':
            logger.debug('User chose: {}'.format(folder))
            g = glob(folder + '/*.dcm')
            if len(g) > 0:
                dm = DicomManager(folder)
                self.image_canvas.set_dm(dm)
                self.image_canvas.focus_set()

            else:
                self.update_image_folder(folder)

    def init_menu(self, root):
        menubar = Menu(root)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="New", command=self.donothing)
        filemenu.add_command(label="Open file", command=self.on_open_file)
        filemenu.add_command(label="Open folder", command=self.on_open_folder)
        filemenu.add_command(label="Save", command=self.donothing)
        filemenu.add_command(label="Save as...", command=self.donothing)
        filemenu.add_command(label="Close", command=self.donothing)

        filemenu.add_separator()

        filemenu.add_command(label="Exit", command=root.quit)
        menubar.add_cascade(label="File", menu=filemenu)
        editmenu = Menu(menubar, tearoff=0)
        editmenu.add_command(label="Undo", command=self.donothing)

        editmenu.add_separator()

        helpmenu = Menu(menubar, tearoff=0)
        helpmenu.add_command(label="Help Index", command=self.donothing)
        helpmenu.add_command(label="About...", command=self.donothing)
        menubar.add_cascade(label="Help", menu=helpmenu)

        return menubar