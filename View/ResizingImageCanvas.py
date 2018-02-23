from tkinter import *
from tkinter import ttk
import os
import cv2
import numpy as np
from PIL import Image, ImageTk
import threading
from imageprocessing.contouring import cnt_from_img, img_with_contour, save_contour


# a subclass of Canvas for dealing with resizing of windows
class ResizingImageCanvas(Canvas):
    def __init__(self, parent, image=None, **kwargs):
        Canvas.__init__(self, parent, **kwargs)
        self.bind("<Key>", self.keydispatch)
        self.bind("<Button-1>", self.callback)
        self.bind("<Configure>", self.on_resize)

        self.height = self.winfo_reqheight()
        self.width = self.winfo_reqwidth()

        self.image_path = ""
        self.image_folder = ""
        self.image_names = []
        self.image_idx = 0
        self.image = None

        self.ready = False

        self.contours = None
        self.curr_contour = 0
        self.contour_image = None
        self.contour_photo = None

        self.photo = None

        self.set_image(image)

    def open_image(self, path):
        self.image_path = path
        new_image = Image.open(self.image_path)
        self.set_image(new_image)

    def draw_next_contour(self):
        if self.curr_contour != len(self.contours) - 1:
            self.curr_contour += 1
            self.curr_contour = 0
            self.draw_contour(self.curr_contour)

    def draw_last_contour(self):
        if self.curr_contour != 0:
            self.curr_contour -= 1
            self.curr_contour = 0
            self.draw_contour(self.curr_contour)

    def keydispatch(self, event):
        print("pressed", event.keysym)
        if event.keysym == 'Right':
            self.draw_next_contour()
        if event.keysym == 'Left':
            self.draw_last_contour()
        if event.keysym == 'Down':
            self.export_contour(self.curr_contour)
        if event.keysym == 'a':
            self.last_image()
        if event.keysym == 'd':
            self.next_image()

    def next_image(self):
        self.image_idx += 1
        self.image_idx %= len(self.image_names)
        path = os.path.join(self.image_folder, self.image_names[self.image_idx])
        self.open_image(path)

    def last_image(self):
        self.image_idx -= 1
        self.image_idx %= len(self.image_names)
        path = os.path.join(self.image_folder, self.image_names[self.image_idx])
        self.open_image(path)

    def callback(self, event):
        self.focus_set()
        print("clicked at ({}, {})".format(event.x, event.y))

    def on_resize(self, event):
        # determine the ratio of old width/height to new width/height
        self.width = event.width
        self.height = event.height
        if self.image is not None:
            self.open_image(self.image_path)
            self.set_image(self.image)
        # resize the canvas
        self.config(width=self.width, height=self.height)

    def set_image(self, image):
        if image is not None:
            self.image = image
            self.image = self.image.resize((self.width, self.height), Image.ANTIALIAS)
            self.photo = ImageTk.PhotoImage(self.image)
            self.width = self.photo.width()
            self.height = self.photo.height()

            thread = threading.Thread(target=self.update_contours, args=())
            thread.start()

            self.create_image(0, 0, anchor=NW, image=self.photo)
        else:
            self.create_image(0, 0, anchor=NW)

        self.config(width=self.width, height=self.height)

    def set_folder(self, folder):
        self.image_folder = folder
        self.image_names = os.listdir(folder)
        for name in self.image_names:
            if os.path.isdir(os.path.join(folder, name)):
                self.image_names.remove(name)

        self.image_names.sort()
        self.open_image(os.path.join(self.image_folder, self.image_names[self.image_idx]))

    def set_photo(self, new_photo):
        self.width = new_photo.widht
        self.config(width=self.width, height=self.height)

    def update_contours(self):
        self.ready = False
        self.contours = []
        self.curr_contour = 0
        self.contours = cnt_from_img(self.image)
        self.ready = True

    def draw_contour(self, cnt_idx):
        if self.ready:
            cnt_image = img_with_contour(np.asarray(self.image), self.contours[cnt_idx])
            #print(np.shape(cnt_image))
            cv2_im = cv2.cvtColor(cnt_image, cv2.COLOR_BGR2RGB)
            p_image = Image.fromarray(cv2_im)
            #self.image.paste(p_image, (0, 0), p_image)
            #self.set_image(p_image)
            self.photo = ImageTk.PhotoImage(p_image)
            self.create_image(0, 0, anchor=NW, image=self.photo)
        else:
            self.contours_not_ready()

    def export_contour(self, cnt_idx):
        path_segs = self.image_path.split("/")
        file_name = path_segs[-1]

        file_name_split = file_name.split(".")
        file_ext = file_name_split[-1]
        file_name_wo_ext = file_name_split[0]
        file_name_wo_ext += "-{}".format(self.curr_contour)

        new_path = "/".join(path_segs[:-1])
        new_path += "/saved_contours/"
        try:
            os.mkdir(new_path)
        except OSError:
            # directory already exists
            pass
        im_save_path = new_path + file_name_wo_ext
        thread = threading.Thread(target=save_contour, args=(self.contours[cnt_idx], self.width, self.height, im_save_path))
        thread.start()

    @staticmethod
    def contours_not_ready():
        filewin = Toplevel()
        label = Label(filewin, text="Contours not ready")
        label.pack()
