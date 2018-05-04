import hashlib
import logging
import os
import threading
import time
from tkinter import *

import cv2
import numpy as np
from PIL import Image, ImageTk

from src.ImageProcessing.contouring import cnt_from_img, save_contour, save_image

logger = logging.getLogger(__name__)


# a subclass of Canvas for dealing with resizing of windows
class ResizingImageCanvas(Canvas):
    def __init__(self, parent=None, image=None, dicom_handler=None, **kwargs):
        Canvas.__init__(self, **kwargs)
        self.parent = parent

        self.bind("<Key>", self.keydispatch)
        self.bind("<Configure>", self.on_resize)

        self.bind("<Button-1>", self.point)
        self.bind("<Button-3>", self.graph)
        self.bind("<Button-2>", self.toggle)
        # self.bind('<B1-Motion>', self.motion)
        self.configure(cursor="crosshair red")
        self.configure()

        self.dm = dicom_handler

        self.height = self.winfo_reqheight()
        self.width = self.winfo_reqwidth()

        self.user_points = []
        self.spline = 0
        self.new_point = False
        self.user_line_tag = "usr_line"
        self.user_point_tag = "usr_point"

        self.contour_line_tag = "cnt_line"
        self.contour_point_tag = "cnt_point"

        self.image_path = ""
        self.image_folder = ""
        self.image_names = []
        self.image_idx = 0
        self.image = None

        self.cnt_img = None

        self.thresh_val = 70

        self.ready = False

        self.contours = None
        self.curr_contour = 0
        self.cnt_points = []
        self.contour_image = None
        self.contour_photo = None

        self.photo = None

        self.set_image(image)

    def set_dm(self, dm):
        if dm is not None:
            logger.info("Got new DICOMManager")
            self.dm = dm

    def keydispatch(self, event):
        logger.debug("User pressed: \'{}\'".format(event.keysym))
        if event.keysym == 'Right':
            self.update_contour_idx(1)
        if event.keysym == 'Left':
            self.update_contour_idx(-1)
        if event.keysym == 'Down':
            self.export_contour(self.curr_contour)
        if event.keysym == 'a':
            logger.info("Current image: {}".format(self.image_idx))
            self.update_image_idx(-1)
        if event.keysym == 'd':
            logger.info("Current image: {}".format(self.image_idx))
            self.update_image_idx(1)
        if event.keysym == 'x':
            self.clear_points()
        if event.keysym == 'c':
            self.recontour()
        if event.keysym == 'equal' or event.keysym == 'plus':
            self.update_thresh(1)
        if event.keysym == 'minus':
            self.update_thresh(-1)

    def update_image_idx(self, direction):
        self.clear_points()
        self.curr_contour = -1
        self.image_idx += direction
        # Use images if we don't have DicomManager
        if self.dm is None:
            path = os.path.join(self.image_folder, self.image_names[self.image_idx])
            self.image_idx %= len(self.image_names)
            self.open_image(path)
        else:
            img_arr = self.dm.get_image_array(self.image_idx)
            img = Image.fromarray(img_arr)
            self.image_idx %= self.dm.get_num_images()
            self.set_image(img)

        self.parent.update_slice_label(self.image_idx)

    def update_contour_idx(self, direction):
        logger.debug("Current contour: {}".format(self.curr_contour))
        valid_contour = 0 <= self.curr_contour + direction < len(self.contours) - 1
        if valid_contour:
            self.curr_contour += direction
            self.draw_contour(self.curr_contour)

    def open_image(self, path):
        self.focus()
        self.image_path = path
        new_image = Image.open(self.image_path)
        self.set_image(new_image)

    def set_image(self, image):
        if image is not None:
            self.image = image
            # self.image = self.image.resize((self.width, self.height), Image.ANTIALIAS)
            self.photo = ImageTk.PhotoImage(self.image)
            self.width = self.photo.width()
            self.height = self.photo.height()

            thread = threading.Thread(target=self.update_contours, args=())
            thread.start()

            self.create_image(0, 0, anchor=NW, image=self.photo)
        else:
            self.create_image(0, 0, anchor=NW)

        self.config(width=self.width, height=self.height)
        self.parent.config(width=self.width, height=self.height)

    def set_photo(self, new_photo):
        self.width = new_photo.width
        self.config(width=self.width, height=self.height)

    def update_thresh(self, delta_thresh):
        self.thresh_val += delta_thresh
        self.parent.update_thresh_label(self.thresh_val)
        self.update_contours()

    def callback(self, event):
        self.focus_set()
        logger.debug("click at ({}, {})".format(event.x, event.y))

    def on_resize(self, event):
        pass
        # # determine the ratio of old width/height to new width/height
        # self.width = event.width
        # self.height = event.height
        # if self.image is not None:
        #     self.open_image(self.image_path)
        #     self.set_image(self.image)
        # # resize the canvas
        # self.config(width=self.width, height=self.height)

    def set_folder(self, folder):
        self.image_folder = folder
        self.image_names = os.listdir(folder)
        for name in self.image_names:
            if os.path.isdir(os.path.join(folder, name)):
                self.image_names.remove(name)

        self.image_names.sort()
        self.open_image(os.path.join(self.image_folder, self.image_names[self.image_idx]))

    def update_contours(self):
        self.ready = False
        self.configure(cursor="clock")

        self.contours = []
        self.curr_contour = 0
        self.contours = cnt_from_img(self.image, self.thresh_val)
        logger.debug("Got {} contours".format(len(self.contours)))

        self.ready = True
        self.configure(cursor="crosshair red")

    def recontour(self):
        point_list = self.get_point_list(self.user_points)
        point_list_len = len(point_list)
        im = None
        for i in range(point_list_len):
            j = i + 1
            logger.debug("i: {}, j: {}, point_list_len: {}".format(i, j, point_list_len))
            if j <= point_list_len - 1:
                logger.debug("Drawing points {} and {}".format(point_list[i], point_list[j]))
                im = np.array(self.image.convert('RGB'))

                line_args = {'thickness': 2, 'color': 255, 'lineType': cv2.LINE_AA}
                im = cv2.line(im, point_list[i], point_list[j], line_args)
                # plt.figure(figsize=(20, 20))
                # plt.imshow(im)
                # plt.show()
        self.image = Image.fromarray(im)
        self.update_contours()

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
            kwargs = {'tags': self.contour_line_tag, 'width': 2, 'fill': "red",
                      'joinstyle': "round", 'capstyle': "round"}
            self.itemconfigure(self.contour_line_tag, smooth=1)
            self.create_line(self.cnt_points, kwargs)
        else:
            self.contours_not_ready()

    def export_contour(self, cnt_idx):
        # Save the contour to an image by itself
        path_segs = self.image_path.split("/")
        file_name = path_segs[-1]

        file_name_split = file_name.split(".")
        file_ext = file_name_split[-1]
        file_name_wo_ext = file_name_split[0]
        # Used to just add contour index but that doesn't work because recontouring could lead to saving a different contour at the same index
        # so now we hash the current time instead
        # file_name_wo_ext += "-{}".format(self.curr_contour)

        time_hash = hashlib.sha1()
        time_hash.update(str(time.time()).encode('utf-8'))
        file_name_wo_ext += "-{}".format(time_hash.hexdigest()[:10])

        new_path = "/".join(path_segs[:-1])
        new_path += "/saved_contours/"
        try:
            os.mkdir(new_path)
        except OSError:
            # directory already exists
            pass
        im_save_path = new_path + file_name_wo_ext
        thread = threading.Thread(target=save_contour,
                                  args=(self.contours[cnt_idx], self.width, self.height, im_save_path))
        thread.start()

        # Save a background image for more processing
        bkg_save_path = new_path + file_name_split[0] + "-bkg"
        thread = threading.Thread(target=save_image, args=(self.image, bkg_save_path))
        thread.start()

        scaling_factor = self.dm.get_scaling_factor()

        contour_string_path = new_path + file_name_wo_ext + '-{}-{}-{}.txt'.format(scaling_factor, self.curr_contour,
                                                                                   self.thresh_val)
        file = open(contour_string_path, 'w')
        np.set_printoptions(threshold=np.nan)
        file.write(np.array2string(self.contours[cnt_idx], separator=','))
        file.close()

    @staticmethod
    def contours_not_ready():
        filewin = Toplevel()
        label = Label(filewin, text="Contours not ready")
        label.pack()

    def point(self, event):
        self.focus_set()
        self.new_point = True
        self.create_oval(event.x, event.y, event.x + 1, event.y + 1, outline="red", fill="red", tag=self.user_point_tag)
        # point = (event.x, event.y)
        # logger.debug("Closest point to {} is {}".format(point, self.closet_point(point, self.cnt_points)))
        self.user_points.append(event.x)
        self.user_points.append(event.y)

    def closet_point(self, point, points):
        points = np.asarray(self.get_point_list(points))
        dist = np.sum((points - point) ** 2, axis=1)
        return points[np.argmin(dist)]

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

    def get_point_list(self, point_list):
        x_list = point_list[0::2]
        y_list = point_list[1::2]
        point_list = list(zip(x_list, y_list))
        return point_list
