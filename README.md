# Computer Assisted Image Segmentation
An intuitive user interface for image segmentation with computer assistance via OpenCV.


Will open DICOM archives or BMP images, compute contours, and provides mechanisms for parameter tweaking, selection, and output.
Exporting a contour will produce a contour-only image, the background the contour was computed from, and a text file with the contour points.
The files follow the format: `<file hash>-<scaling factor>-<image index>-<contour index>-<threshold value>.bmp/txt`

There are some post-processing helper functions in the **src/PostProcessing**.
These can help load files back into memory for further processing (e.g. volume modeling).

## Control 

### Mouse

- Left Click: Create a new point for the bounding polygon
- Right Click: Plot the current bounding contour
- Middle Click: Toggle smoothing of the bounding contour

### Keyboard

- Right arrow: Increments displayed contour index
- Left Arrow: Decrements displayed contour index
- Down arrow: Exports the current contour to file
- D: Increments displayed image index
- A: Decrements displayed image index
- X: Clears the points for the bounding polygon
- C: Applies bounding polygon to image and recomputes contours
- +: Increments binary threshold value
- -: Decrements binary threshold value
- R: Activates region of interest mode
