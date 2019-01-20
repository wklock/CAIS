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


class ResizingImageCanvas(Canvas):
    """
    Customized Canvas that can handle dynamic image resizing and displays for slice contours.
    """

    def __init__(self, parent=None, image=None, dicom_manager=None, **kwargs):
        """
        Initializer
        :param parent: The parent to this tk Element
        :param image: The image to load
        :param dicom_manager: The DicomManager instance to assign to this class
        :param kwargs: Keyword arguments to pass to parent
        """
        Canvas.__init__(self, **kwargs)
        self.parent = parent
        self.dm = dicom_manager
        self.logger = logging.getLogger(__name__)

        # Configure key and mouse bindings
        self.bind("<Key>", self.keydispatch)
        self.bind("<Configure>", self.on_resize)
        self.bind("<Button-1>", self.create_point)
        self.bind("<Button-3>", self.plot_points)
        self.bind("<Button-2>", self.toggle_smoothing)
        self.configure(cursor="crosshair red")
        self.configure()

        # Configure window size
        self.height = self.winfo_reqheight()
        self.width = self.winfo_reqwidth()

        # Configure contour parameters
        self.user_points = []
        self.spline = 0
        self.new_point = False
        self.user_line_tag = "usr_line"
        self.user_point_tag = "usr_point"
        self.contour_line_tag = "cnt_line"
        self.contour_point_tag = "cnt_point"
        self.contours = None
        self.curr_contour = 0
        self.cnt_points = []
        self.contour_image = None
        self.contour_photo = None

        # Configure image parameters
        self.image_path = ""
        self.image_folder = ""
        self.image_names = []
        self.image_idx = 0
        self.image = None
        self.photo = None

        # Configure ROI parameters
        self.roi = None
        self.roi_set = False

        self.cnt_img = None

        self.thresh_val = 70

        self.ready = False

        self.set_image(image)

    def set_dm(self, dm):
        if dm is not None:
            self.logger.info("Got new DICOMManager")
            self.dm = dm

    def keydispatch(self, event):
        """
        Receives key events and chooses the appropriate action.
        :param event: The key event to process
        """
        self.logger.debug("User pressed: '{}'".format(event.keysym))
        if event.keysym == "Right":
            self.update_contour_idx(1)
        if event.keysym == "Left":
            self.update_contour_idx(-1)
        if event.keysym == "Down":
            self.export_contour(self.curr_contour)
        if event.keysym == "a":
            self.logger.info("Current image: {}".format(self.image_idx))
            self.update_image_idx(-1)
        if event.keysym == "d":
            self.logger.info("Current image: {}".format(self.image_idx))
            self.update_image_idx(1)
        if event.keysym == "x":
            self.clear_points()
        if event.keysym == "c":
            self.apply_corrections()
        if event.keysym == "equal" or event.keysym == "plus":
            self.update_thresh(1)
        if event.keysym == "minus":
            self.update_thresh(-1)
        if event.keysym == "r":
            self.activate_roi()

    def activate_roi(self):
        """
        Activates the region of interest that the user selected.
        """
        img_arr = self.dm.get_image_array(self.image_idx)
        self.roi = cv2.selectROI(
            cv2.cvtColor(np.asarray(img_arr, np.uint8), cv2.COLOR_GRAY2BGR), False
        )
        self.extract_roi(img_arr)

    def extract_roi(self, img_arr):
        """
        Extracts the ROI from the provided image array and sets it as this canvas's image.
        :param img_arr: An OpenCV image array
        """
        r = self.roi
        (x, y, w, h) = r
        if not x == y == w == h == 0:
            self.roi_set = True
            im_crop = img_arr[
                int(r[1]) : int(r[1] + r[3]), int(r[0]) : int(r[0] + r[2])
            ]
            img = Image.fromarray(im_crop)
            self.image_idx %= self.dm.get_num_images()
            self.set_image(img)

    def update_image_idx(self, direction):
        """
        Updates the image index when a user switches image.
        :param direction: An integer representing whether or not we're moving forward or backward
        """
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
            if self.roi_set:
                self.extract_roi(img_arr)
            else:
                img = Image.fromarray(img_arr)
                self.image_idx %= self.dm.get_num_images()
                self.set_image(img)

        self.parent.update_slice_label(self.image_idx)

    def update_contour_idx(self, direction):
        """
        Updates the visible contour on user input.
        :param direction: An integer representing whether or not we're incrementing or decrementing
        """
        self.logger.debug("Current contour: {}".format(self.curr_contour))
        valid_contour = 0 <= self.curr_contour + direction < len(self.contours) - 1
        if valid_contour:
            self.curr_contour += direction
            self.draw_contour(self.curr_contour)

    def open_image(self, path):
        """
        Opens the image at the provided path for display.
        :param path: The path to the image.
        """
        self.focus()
        self.image_path = path
        new_image = Image.open(self.image_path)
        self.set_image(new_image)

    def set_image(self, image):
        """
        Sets up a PhotoImage from the provided PIL image so the Canvas can display.
        :param image: An Image
        """
        if image is not None:
            self.image = image
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

    def update_thresh(self, delta_thresh):
        """
        Update the current contouring threshold.
        :param delta_thresh: Amount and direction to change the contour by.
        """
        self.thresh_val += delta_thresh
        self.parent.update_thresh_label(self.thresh_val)
        self.update_contours()

    def set_folder(self, folder):
        """
        Updates the folder the the Canvas reads Images from.
        :param folder: A path to the folder
        """
        self.image_folder = folder
        self.image_names = os.listdir(folder)
        for name in self.image_names:
            if os.path.isdir(os.path.join(folder, name)):
                self.image_names.remove(name)

        self.image_names.sort()
        self.open_image(
            os.path.join(self.image_folder, self.image_names[self.image_idx])
        )

    def update_contours(self):
        """
        Updates the computed contours for the current Image.
        """
        self.ready = False
        self.configure(cursor="clock")

        self.contours = []
        self.curr_contour = 0
        self.contours = cnt_from_img(self.image, self.thresh_val)
        self.logger.debug("Got {} contours".format(len(self.contours)))

        self.ready = True
        self.configure(cursor="crosshair red")

    def apply_corrections(self):
        """
        Updates the image given the user's inputted corrections and updates the contours.
        """
        point_list = self.get_point_list(self.user_points)
        point_list_len = len(point_list)
        im = None
        for i in range(point_list_len):
            j = i + 1
            self.logger.debug(
                "i: {}, j: {}, point_list_len: {}".format(i, j, point_list_len)
            )
            if j <= point_list_len - 1:
                self.logger.debug(
                    "Drawing points {} and {}".format(point_list[i], point_list[j])
                )
                im = np.array(self.image.convert("RGB"))

                im = cv2.line(
                    im,
                    point_list[i],
                    point_list[j],
                    thickness=2,
                    color=(255, 255, 255),
                    lineType=cv2.LINE_AA,
                )
                self.image = Image.fromarray(im)
        self.update_contours()

    def draw_contour(self, cnt_idx):
        """
        Overlays the contour at cnt_idx over the currently displayed Image.
        :param cnt_idx: The contour to draw
        """
        if self.ready:
            self.delete(self.contour_point_tag)
            self.delete(self.contour_line_tag)
            self.cnt_points.clear()

            for point in self.contours[cnt_idx]:
                point_x = point[0][0]
                point_y = point[0][1]
                self.cnt_points.append(point_x)
                self.cnt_points.append(point_y)
            kwargs = {
                "tags": self.contour_line_tag,
                "width": 2,
                "fill": "red",
                "joinstyle": "round",
                "capstyle": "round",
            }
            self.itemconfigure(self.contour_line_tag, smooth=1)
            self.create_line(self.cnt_points, kwargs)
        else:
            self.contours_not_ready()

    def export_contour(self, cnt_idx):
        """
        Exports the current contour profile to file.
        :param cnt_idx: The contour to write
        """
        if self.dm:
            new_path = self.dm.get_output_path()
        else:
            # Save the contour to an image by itself
            path_segs = self.image_path.split("/")
            new_path = "/".join(path_segs[:-1])
            new_path += "/saved_contours/"

        time_hash = hashlib.sha1()
        time_hash.update(str(time.time()).encode("utf-8"))
        file_name_hash = "{}".format(time_hash.hexdigest()[:10])

        scaling_factor = self.dm.get_scaling_factor()

        contour_img_path = os.path.join(
            new_path,
            "{}-{}-{}-{}-{}".format(
                file_name_hash,
                scaling_factor,
                self.image_idx,
                self.curr_contour,
                self.thresh_val,
            ),
        )

        contour_string_path = os.path.join(
            new_path,
            "{}-{}-{}-{}-{}.txt".format(
                file_name_hash,
                scaling_factor,
                self.image_idx,
                self.curr_contour,
                self.thresh_val,
            ),
        )

        try:
            os.mkdir(new_path)
        except OSError:
            # directory already exists
            pass

        thread = threading.Thread(
            target=save_contour,
            args=(self.contours[cnt_idx], self.width, self.height, contour_img_path),
        )
        thread.start()

        # Save a background image for more processing
        bkg_save_path = contour_img_path + "-bkg"
        thread = threading.Thread(target=save_image, args=(self.image, bkg_save_path))
        thread.start()

        file = open(contour_string_path, "w")
        np.set_printoptions(threshold=np.nan)
        file.write(np.array2string(self.contours[cnt_idx], separator=","))
        file.close()

    @staticmethod
    def contours_not_ready():
        """
        Indicator to show the user that the contours aren't computed yet.
        """
        filewin = Toplevel()
        label = Label(filewin, text="Contours not ready")
        label.pack()

    def create_point(self, event):
        """
        Displays and stores the point from the user's mouse click event.
        :param event: The click event for the user's action
        """
        self.focus_set()
        self.new_point = True
        self.create_oval(
            event.x,
            event.y,
            event.x + 1,
            event.y + 1,
            outline="red",
            fill="red",
            tag=self.user_point_tag,
        )
        self.user_points.append(event.x)
        self.user_points.append(event.y)

    def plot_points(self):
        """
        Plots the connections between the points that the user selected.
        """
        if self.new_point and len(self.user_points) > 2:
            self.delete(self.user_line_tag)
            self.spline = 0
            self.create_line(
                self.user_points,
                tags=self.user_line_tag,
                width=2,
                fill="red",
                joinstyle="round",
                capstyle="round",
            )

        self.new_point = False

    def toggle_smoothing(self):
        """
        Toggles between smooth and connect the dot plots for the connections between points.
        :return:
        """
        if self.spline == 0:
            self.itemconfigure(self.user_line_tag, smooth=1)
            self.spline = 1
        elif self.spline == 1:
            self.itemconfigure(self.user_line_tag, smooth=0)
            self.spline = 0

    def clear_points(self):
        """
        Clears the points that the user selected.
        """
        self.user_points.clear()
        self.delete(self.user_point_tag)
        self.delete(self.user_line_tag)

    def get_point_list(self, point_list):
        """
        Zips the lists of x and y coordinates.
        :param point_list: The list of points that the user input
        :return: A list of tuples representing x/y pairs
        """
        x_list = point_list[0::2]
        y_list = point_list[1::2]
        point_list = list(zip(x_list, y_list))
        return point_list
