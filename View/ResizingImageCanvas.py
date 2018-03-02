import logging
import os
import threading
from tkinter import *

import cv2
import numpy as np
from PIL import Image, ImageTk

from imageprocessing.contouring import cnt_from_img, save_contour, save_image

logger = logging.getLogger(__name__)


# a subclass of Canvas for dealing with resizing of windows
class ResizingImageCanvas(Canvas):
    def __init__(self, parent, image=None, **kwargs):
        Canvas.__init__(self, parent, **kwargs)
        self.bind("<Key>", self.keydispatch)
        self.bind("<Configure>", self.on_resize)

        self.height = self.winfo_reqheight()
        self.width = self.winfo_reqwidth()

        self.bind("<Button-1>", self.point)
        self.bind("<Button-3>", self.graph)
        self.bind("<Button-2>", self.toggle)
        #self.bind('<B1-Motion>', self.motion)

        self.user_points = []
        self.parent = parent
        self.spline = 0
        self.new_point = False
        self.user_line_tag = "usr_line"
        self.user_point_tag = "usr_point"

        self.contour_line_tag = "cnt_line"
        self.contour_point_tag = "cnt_point"
        self.configure(cursor="crosshair red")

        self.image_path = ""
        self.image_folder = ""
        self.image_names = []
        self.image_idx = 0
        self.image = None

        self.ready = False

        self.contours = None
        self.curr_contour = 0
        self.cnt_points = []
        self.contour_image = None
        self.contour_photo = None

        self.photo = None

        self.set_image(image)

    def open_image(self, path):
        self.focus()
        self.image_path = path
        new_image = Image.open(self.image_path)
        self.set_image(new_image)

    def draw_next_contour(self):
        logger.debug("Current contour: {}".format(self.curr_contour))
        if self.curr_contour < len(self.contours) - 1:
            self.curr_contour += 1
            self.draw_contour(self.curr_contour)

    def draw_last_contour(self):
        logger.debug("Current contour: {}".format(self.curr_contour))
        if self.curr_contour > 0:
            self.curr_contour -= 1
            self.draw_contour(self.curr_contour)

    def keydispatch(self, event):
        logger.debug("User pressed: \'{}\'".format(event.keysym))
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
        if event.keysym == 'x':
            self.clear_points()
        if event.keysym == 'c':
            self.recontour()

    def next_image(self):
        self.curr_contour = -1
        self.image_idx += 1
        self.image_idx %= len(self.image_names)
        path = os.path.join(self.image_folder, self.image_names[self.image_idx])
        self.open_image(path)

    def last_image(self):
        self.curr_contour = -1
        self.image_idx -= 1
        self.image_idx %= len(self.image_names)
        path = os.path.join(self.image_folder, self.image_names[self.image_idx])
        self.open_image(path)

    def callback(self, event):
        self.focus_set()
        logger.debug("click at ({}, {})".format(event.x, event.y))

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
        self.configure(cursor="clock")
        self.contours = []
        self.curr_contour = 0
        self.contours = cnt_from_img(self.image)
        logger.debug("Got {} contours".format(len(self.contours)))
        self.ready = True
        self.configure(cursor="crosshair red")

    def draw_contour(self, cnt_idx):
        if self.ready:
            self.delete(self.contour_point_tag)
            self.delete(self.contour_line_tag)
            self.cnt_points.clear()

            for point in self.contours[cnt_idx]:
                point_x = point[0][0]
                point_y = point[0][1]
                self.cnt_points.append(point_x)
                self.cnt_points.append(point_y)
                # kwargs = {'outline': "spring green", 'fill': "spring green",  'tag': self.contour_point_tag}
                # self.create_oval(point_x, point_y, point_x + 1, point_y + 1, kwargs)

            kwargs = {'tags': self.contour_line_tag, 'width': 2, 'fill': "red",
                      'joinstyle': "round", 'capstyle': "round"}
            self.itemconfigure(self.contour_line_tag, smooth=1)
            self.create_line(self.cnt_points, kwargs)

            # cnt_image = img_with_contour(np.asarray(self.image), self.contours[cnt_idx])
            # #print(np.shape(cnt_image))
            # cv2_im = cv2.cvtColor(cnt_image, cv2.COLOR_BGR2RGB)
            # p_image = Image.fromarray(cv2_im)
            # #self.image.paste(p_image, (0, 0), p_image)
            # #self.set_image(p_image)
            # self.photo = ImageTk.PhotoImage(p_image)
            # self.create_image(0, 0, anchor=NW, image=self.photo)
        else:
            self.contours_not_ready()

    def export_contour(self, cnt_idx):
        # Save the contour to an image by itself
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

        # Save a background image for more processing
        bkg_save_path = new_path + file_name_split[0] + "-bkg"
        thread = threading.Thread(target=save_image, args=(self.image, bkg_save_path))
        thread.start()

    @staticmethod
    def contours_not_ready():
        filewin = Toplevel()
        label = Label(filewin, text="Contours not ready")
        label.pack()

    def point(self, event):
        self.focus_set()
        self.new_point = True
        self.create_oval(event.x, event.y, event.x + 1, event.y + 1, outline="red", fill="red", tag=self.user_point_tag)
        self.user_points.append(event.x)
        self.user_points.append(event.y)

    def canxy(self, event):
        print(event.x, event.y)

    def graph(self, event):
        if self.new_point and len(self.user_points) > 2:
            self.delete(self.user_line_tag)
            self.spline = 0
            self.create_line(self.user_points, tags=self.user_line_tag, width=2, fill="red", joinstyle="round",
                             capstyle="round")

        self.new_point = False

    def toggle(self, event):
        if self.spline == 0:
            self.itemconfigure(self.user_line_tag, smooth=1)
            self.spline = 1
        elif self.spline == 1:
            self.itemconfigure(self.user_line_tag, smooth=0)
            self.spline = 0

    def clear_points(self):
        self.user_points.clear()
        self.delete(self.user_point_tag)
        self.delete(self.user_line_tag)

    def motion(self, event):
        self.user_points.append(event.x)
        self.user_points.append(event.y)

    def recontour(self):
        x_list = self.user_points[0::2]
        y_list = self.user_points[1::2]
        point_list = list(zip(x_list, y_list))
        point_list_len = len(point_list)
        for i in range(point_list_len):
            j = i + 1
            logger.debug("i: {}, j: {}, point_list_len: {}".format(i, j, point_list_len))
            if j <= point_list_len - 1:
                logger.debug("Drawing points {} and {}".format(point_list[i], point_list[j]))
                im = np.array(self.image.convert('RGB'))
                im = cv2.line(im, point_list[i], point_list[j], thickness=2, color=(255, 255, 255),
                              lineType=cv2.LINE_AA)
                self.image = Image.fromarray(im)
                # plt.figure(figsize=(20, 20))
                # plt.imshow(im)
                # plt.show()

                self.update_contours()
