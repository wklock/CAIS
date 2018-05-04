import os
import numpy as np
import re
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import axes3d
import cv2


# Dicom image was 192x320
# BMP image was 4096x2160
# X Scaling factor = 4096/192 = 21.33333333
# Y Scaling factor = 2160/320 = 6.75


def text_files_from_folder(folder_path):
    files = os.listdir(folder_path)
    # Get a list of only the text files corresponding to the contour arrays
    contour_filenames = []
    for f in files:
        if f[-4:-1] == '.tx':
            contour_filenames.append(f)
    contour_filenames.sort()
    return contour_filenames


def contours_from_files(folder_path, contour_filenames):
    global file
    regexp = r'\[([0-9]+), ([0-9]+)\]'
    slice_num_reg = r'BMP0+(\d+)'
    # the voxel resolution is 0.8mm
    slice_width = 0.8
    #
    contour_arrs = []
    for file in contour_filenames:
        slice_num = int(re.findall(slice_num_reg, file)[0])
        z = slice_num * slice_width
        # print(z)
        full_path = os.path.join(folder_path, file)
        with open(full_path, 'r') as contour_file:
            file_arr = np.fromregex(contour_file, regexp, dtype=[('num1', np.float64), ('num2', np.float64)])

        arr = np.zeros((len(file_arr), 3))
        for idx, pair in enumerate(file_arr):
            arr[idx][0] = pair[0]
            arr[idx][2] = pair[1]
            arr[idx][1] = z
        contour_arrs.append(arr)
    return contour_arrs


def plot_from_contours(contour_arrs):
    fig = plt.figure(figsize=(10, 10))
    ax = plt.axes(projection='3d')
    X, Y, Z = axes3d.get_test_data(0.05)
    for arr in contour_arrs:
        ax.scatter(arr[:, 0], arr[:, 1], arr[:, 2], marker=',')
    plt.show()


def obj_from_contour(contour, name):
    with open(name, 'w') as obj_file:
        vertex_idx = 0
        obj_file.write('o ' + name + '\n')
        for (x, y, z) in contour:
            obj_file.write("v %.5f %.5f %.5f\n" % (x, y, z))
            vertex_idx += 1

        polyline = 'l '
        for i in range(1, vertex_idx):
            polyline += '{} '.format(i)
        polyline += '\n'
        obj_file.write(polyline)


folder_path = "../../data/BP02/BMP/saved_contours/"
filenames = text_files_from_folder(folder_path)
contours = contours_from_files(folder_path, filenames)

x_scaling_factor = 863 / 192
y_scaling_factor = 1461 / 320
pix_dimension = .8  # mm^2
scaled_contours = dict()
for (idx, c) in enumerate(contours):
    scaled_contour = []
    slice_num = int(c[0][1] / .8)
    if not slice_num in scaled_contours.keys():
        scaled_contours[slice_num] = []

    for point in c:
        pix_x = point[0] - 963
        pix_y = point[2]
        scaled_x = pix_x / x_scaling_factor
        scaled_y = pix_y / y_scaling_factor
        scaled_contour.append([[scaled_x, scaled_y]])
    # must be 32bit int or unsigned float
    scaled_contours[slice_num].append((np.asarray(scaled_contour, np.float32)))


# Return true if rect1 is within rect2
def rect_within(rect1, rect2):
    x1, y1, width1, height1 = rect1
    x2, y2, width2, height2 = rect2
    is_within = (x2 + width2) < (x1 + width1) and x2 > x1 and y2 > y1 and (y2 + height2) < (y1 + height1)
    if is_within:
        return True
    else:
        return False


center_x = 102
left_areas = []
right_areas = []
cx_list = []
cy_list = []
for key in scaled_contours.keys():
    left_rects = []
    right_rects = []
    right_area = 0
    left_area = 0
    has_left = False
    has_right = False
    for contour in scaled_contours[key]:
        M = cv2.moments(contour)
        cx = int(M['m10'] / M['m00'])
        cy = int(M['m01'] / M['m00'])
        x, y, width, height = cv2.boundingRect(contour)
        #cx = x + width / 2
        #cy = y + height / 2
        cx_list.append(cx)
        cy_list.append(cy)
        print(cx, center_x)

        curr_area = cv2.contourArea(contour)
        if cx < center_x:
            print("left")
            if has_left:
                if rect_within((x, y, width, height), left_rects[-1]):
                    left_area -= curr_area
                else:
                    left_area += curr_area
            has_left = True
            left_rects.append((x, y, width, height))
        else:
            print("right")
            if has_right:
                if rect_within((x, y, width, height), right_rects[-1]):
                    right_area -= curr_area
                else:
                    right_area += curr_area
            has_right = True
            right_rects.append((x, y, width, height))

    left_areas.append(left_area)
    right_areas.append(right_area)

plt.plot(left_areas)
plt.show()

plt.plot(right_areas)
plt.show()

plt.scatter(cx_list, cy_list)
plt.show()
# opencv contours are stored with double braces, so we have to unpack into x and y values
# [[[x y]], [[x y]]]
# plt.scatter(scaled_contours[94][0][:, 0][:, 0], scaled_contours[94][0][:, 0][:, 1])

# plt.show()
# for (idx, c) in enumerate(contours):
#     name = os.path.join(folder_path, 'contours/contour-{}.obj'.format(idx))
#     obj_from_contour(c, name)
#
