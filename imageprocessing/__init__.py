import cv2


def bulk_crop(img, num):
    # Load the image
    im = cv2.imread(img)
    # Crop the 4096x2160 image to
    im = im[210:710, 1798:2298]
    # Convert to greyscale
    imgray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    output_name = 'data/BP02_midsag/crop/cr_%i.bmp' % num
    cv2.imwrite(output_name, imgray)

#
# image_path = 'data/BP02_midsag/BMP/'
#
# p = ThreadPool(8)
# images = [(image_path + 'BMP%05d.bmp' % i, i) for i in range(30, 119)]
# start = time.time()
# r = p.starmap(cnt_from_img, images)
# end = time.time()
# print(end-start)