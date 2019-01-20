import os
import numpy as np
import re
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import axes3d
import cv2

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
    slice_num_reg = r'(\w+)-(\d+)-(\d+)-(\d+)-(\d+)'
    # the voxel resolution is 0.8mm
    slice_width = 0.8
    file_dict = {}
    contour_arrs = []
    for file in contour_filenames:
        slice_num = int(re.findall(slice_num_reg, file)[0][2])
        z = slice_num * slice_width
        if file_dict.get(slice_num) is None:
            file_dict[slice_num] = [file]
        else:
            file_dict[slice_num].append(file)
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

    for key in file_dict.keys():
        if len(file_dict[key]) == 1:
            print(key)
    print("######")
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

