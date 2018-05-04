import logging
import os
from glob import glob

import SimpleITK as SimpleITK
import cv2
import numpy as np
import pydicom as dicom
from pydicom.errors import *

logger = logging.getLogger(__name__)
logger.setLevel(10)


class DicomManager:
    def __init__(self, data_path):
        self.output_path = os.path.join(data_path, 'saved_dicom_imgs')

        self.scaling_factor = 4

        self.imgs = np.zeros((0, 0))

        self.init_from_folder(data_path)

    def get_image_array(self, idx):
        valid_idx = idx < len(self.imgs)
        valid_imgs = self.imgs is not None
        if valid_idx and valid_imgs:
            return self.imgs[idx]

        return None

    def save_data(self):
        if not os.path.exists(self.output_path):
            os.mkdir(self.output_path)
        np.save(os.path.join(self.output_path, 'output.npy'), self.imgs)

    def get_num_images(self):
        num_imgs = np.shape(self.imgs)[-1]
        return num_imgs

    def init_from_folder(self, data_path):
        logger.info("Initializing from path: {}".format(data_path))
        try:
            self.imgs = np.load(os.path.join(self.output_path, 'output.npy'))
        except (FileNotFoundError, IOError):
            logger.info("Could not find stored images in data_path, reading in DICOM")
            g = glob(data_path + '/*.dcm')
            logger.info("Found {} DICOM images".format(len(g)))
            scan_data = self.load_scan(data_path)
            self.imgs = self.get_pixels(scan_data)
            self.resize_imgs()
            self.save_data()

    def resize_imgs(self):
        img_list = []
        for idx, s in enumerate(self.imgs):
            dst = cv2.resize(s, dsize=None, fx=self.scaling_factor, fy=self.scaling_factor,
                             interpolation=cv2.INTER_NEAREST)

            img = SimpleITK.GetImageFromArray(dst)

            img_smooth = SimpleITK.CurvatureFlow(image1=img,
                                                 timeStep=0.05,
                                                 numberOfIterations=20)
            s = SimpleITK.GetArrayFromImage(img_smooth)

            img_list.append(s)
        self.imgs = np.asarray(img_list)

    def init_from_file(self, data_path):
        pass

    def get_scaling_factor(self):
        return self.scaling_factor

    @staticmethod
    def load_scan(data_path):
        slices = []
        for s in os.listdir(data_path):
            try:
                slices.append(dicom.read_file(data_path + '/' + s))
            except InvalidDicomError:
                logger.warning("Could not load {}".format(s))
            except IsADirectoryError:
                logger.info("Skipping directory {}".format(s))

        slices.sort(key=lambda x: int(x.InstanceNumber))
        try:
            slice_thickness = np.abs(slices[0].ImagePositionPatient[2] - slices[1].ImagePositionPatient[2])
        except:
            slice_thickness = np.abs(slices[0].SliceLocation - slices[1].SliceLocation)

        for s in slices:
            s.SliceThickness = slice_thickness

        return slices

    @staticmethod
    def get_pixels(scans):

        images = np.stack([s.pixel_array for s in scans])

        # Convert to int16 (from sometimes int16),
        # should be possible as values should always be low enough (<32k)

        # rotate image to get different slice
        img_rot = np.rot90(images, k=3, axes=(0, 2))
        return np.array(img_rot, dtype=np.uint16)
