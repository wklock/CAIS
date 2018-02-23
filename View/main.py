# from tkinter import *
#
#

#
# image = Image.open("data/BP02_midsag/BMP/BMP00033.bmp")
# image = image.resize((200, 100), Image.ANTIALIAS) #The (250, 250) is (height, width)
#
# photo = ImageTk.PhotoImage(image)
#
# frame = ttk.Frame(content, borderwidth=5, relief="sunken", width=200, height=100)
#
# photo_label = Label(frame, image=photo)
#
# namelbl = ttk.Label(content, text="Name")
# name = ttk.Entry(content)
#
# onevar = BooleanVar()
# twovar = BooleanVar()
# threevar = BooleanVar()
#
# onevar.set(True)
# twovar.set(False)
# threevar.set(True)
#
# one = ttk.Checkbutton(content, text="One", variable=onevar, onvalue=True)
# two = ttk.Checkbutton(content, text="Two", variable=twovar, onvalue=True)
# three = ttk.Checkbutton(content, text="Three", variable=threevar, onvalue=True)
# ok = ttk.Button(content, text="Okay")
# cancel = ttk.Button(content, text="Cancel")
#
# frame.grid(column=0, row=0, columnspan=3, rowspan=2, sticky=(N, S, E, W))
# photo_label.grid(column=0, row=0, columnspan=3, rowspan=3, sticky=(N,S,E,W))
# namelbl.grid(column=3, row=0, columnspan=2, sticky=(N, W), padx=5)
# name.grid(column=3, row=1, columnspan=2, sticky=(N, E, W), pady=5, padx=5)
# one.grid(column=0, row=3)
# two.grid(column=1, row=3)
# three.grid(column=2, row=3)
# ok.grid(column=3, row=3)
# cancel.grid(column=4, row=3)
#
# root.columnconfigure(0, weight=1)
# root.rowconfigure(0, weight=1)
# content.columnconfigure(0, weight=3)
# content.columnconfigure(1, weight=3)
# content.columnconfigure(2, weight=3)
# content.columnconfigure(3, weight=1)
# content.columnconfigure(4, weight=1)
# content.rowconfigure(1, weight=1)
#
# root.mainloop()

from tkinter import *
from tkinter.ttk import *
from tkinter import ttk, filedialog

from PIL import Image

from View.ResizingImageCanvas import ResizingImageCanvas


class ContouringWindow(Frame):
    def __init__(self, parent, **kwargs):
        Frame.__init__(self, parent, **kwargs)
        content = ttk.Frame(parent, padding=(3,3,12,12))
        content.grid(column=0, row=0, sticky=(N, S, E, W))

        self.frame = ttk.Frame(content, borderwidth=5, relief="sunken", width=200, height=100)
        self.frame.grid(column=0, row=0, columnspan=3, rowspan=2, sticky=(N, S, E, W))
        self.image = None
        self.image_canvas = ResizingImageCanvas(self.frame, image=None, width=850, height=400, highlightthickness=0)
        self.image_canvas.pack(fill=BOTH, expand=YES)

        onevar = BooleanVar()
        onevar.set(True)
        one = ttk.Checkbutton(content, text="One", variable=onevar, onvalue=True)
        one.grid(column=0, row=3)

        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=3)
        content.columnconfigure(2, weight=3)
        content.columnconfigure(3, weight=1)
        content.columnconfigure(4, weight=1)
        content.rowconfigure(1, weight=1)

        # tag all of the drawn widgets
        menubar = self.init_menu(parent)
        parent.config(menu=menubar)

    def update_canvas_image(self, path):
        self.image_canvas.open_image(path)

    def update_image_folder(self, folder):
        self.image_canvas.set_folder(folder)

    def donothing(self):
        filewin = Toplevel()
        button = Label(filewin, text="Do nothing button")
        button.pack()

    def on_open_file(self):
        ftypes = [('Bitmap Image', '*.bmp')]
        dlg = filedialog.Open(None, filetypes=ftypes)
        fl = dlg.show()

        if fl != '':
            print("User chose: {}".format(fl))
            self.update_canvas_image(fl)
            # text = self.readFile(fl)
            # self.txt.insert(END, text)

    def on_open_folder(self):
        folder = filedialog.askdirectory()

        if folder != '':
            print("User chose: {}".format(folder))
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




def main():
    root = Tk()
    ContouringWindow(root)
    root.minsize(2000, 1000)
    root.maxsize(2000, 1000)
    root.resizable(0, 0)
    root.mainloop()


if __name__ == "__main__":
    main()
