import logging
import os
from glob import glob

import SimpleITK as SimpleITK
import cv2
import numpy as np
import pydicom as dicom
from pydicom.errors import InvalidDicomError


class DicomManager:
    """
    Class for managing the DICOM data
    """

    def __init__(self, data_path=None, scaling_factor=4):
        """
        DicomManager constructor
        :param data_path: path to precomputed .npy or raw DICOM files
        :param scaling_factor: integer for scaling how many pixels per point in DICOM image
        """

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(10)
        if data_path:
            self.output_path = os.path.join(data_path, "saved_dicom_imgs")
        else:
            raise RuntimeError("DicomManager requires a valid path for construction.")
        self.scaling_factor = scaling_factor
        self.imgs = np.zeros((0, 0))
        self.init_from_folder(data_path)

    def init_from_folder(self, data_path):
        """
        Load images from the data at data_path.
        :param data_path: The path to load the data from
        """
        self.logger.info("Initializing from path: {}".format(data_path))
        try:
            self.imgs = np.load(os.path.join(self.output_path, "output.npy"))
        except (FileNotFoundError, IOError):
            self.logger.info(
                "Could not find stored images in data_path, reading in DICOM"
            )
            g = glob(data_path + "/*.dcm")
            if len(g) == 0:
                raise RuntimeError("Could not find any DICOM data")

            self.logger.info("Found {} DICOM images".format(len(g)))
            scan_data = self.load_scan(data_path)
            self.imgs = self.get_pixels(scan_data)
            self.resize_imgs()
            self.save_data()

    def load_scan(self, data_path):
        """
        Loads DICOM data from data_path
        :param data_path: The path to the DICOM data
        :return: A list of the slices within the DICOM data set
        """
        slices = []
        for s in os.listdir(data_path):
            try:
                slices.append(dicom.read_file(data_path + "/" + s))
            except InvalidDicomError:
                self.logger.warning("Could not load {}".format(s))
            except IsADirectoryError:
                self.logger.info("Skipping directory {}".format(s))

        slices.sort(key=lambda x: int(x.InstanceNumber))
        try:
            slice_thickness = np.abs(
                slices[0].ImagePositionPatient[2] - slices[1].ImagePositionPatient[2]
            )
        except:
            slice_thickness = np.abs(slices[0].SliceLocation - slices[1].SliceLocation)

        for s in slices:
            s.SliceThickness = slice_thickness

        return slices

    @staticmethod
    def get_pixels(scans):
        """
        Returns pixel values from a set of DICOM slices
        :param scans: A list of DICOM slices
        :return: An array of the images, rotated to give the coronal plane
        """
        images = np.stack([s.pixel_array for s in scans])

        # Convert to int16 (from sometimes int16),
        # should be possible as values should always be low enough (<32k)

        # rotate image to get different slice
        img_rot = np.rot90(images, k=3, axes=(0, 2))
        return np.array(img_rot, dtype=np.uint16)

    def resize_imgs(self):
        """
        Resizes and smooths the images in this DicomManager
        """
        img_list = []
        for idx, s in enumerate(self.imgs):
            dst = cv2.resize(
                s,
                dsize=None,
                fx=self.scaling_factor,
                fy=self.scaling_factor,
                interpolation=cv2.INTER_NEAREST,
            )

            img = SimpleITK.GetImageFromArray(dst)

            img_smooth = SimpleITK.CurvatureFlow(
                image1=img, timeStep=0.05, numberOfIterations=20
            )
            s = SimpleITK.GetArrayFromImage(img_smooth)

            img_list.append(s)
        self.imgs = np.asarray(img_list)

    def save_data(self):
        """
        Saves the preprocessed images within this DicomManager
        """
        if not os.path.exists(self.output_path):
            os.mkdir(self.output_path)
        np.save(os.path.join(self.output_path, "output.npy"), self.imgs)

    def get_image_array(self, idx):
        """
        Returns the image at idx
        :param idx: The index of the requested index
        :return: The image at idx, or None if idx is invalid
        """
        valid_idx = idx < len(self.imgs)
        valid_imgs = self.imgs is not None
        if valid_idx and valid_imgs:
            return self.imgs[idx]

        return None

    def get_num_images(self):
        """
        Gets the number of images in this DicomManager
        :return: The number of images in this DicomManager
        """
        num_imgs = np.shape(self.imgs)[-1]
        return num_imgs

    def get_scaling_factor(self):
        """
        Getter for the scale factor
        :return: The scale factor for this DicomManager
        """
        return self.scaling_factor

    def get_output_path(self):
        """
        Getter for the output path
        :return: The output path for this DicomManager
        """
        return self.output_path
