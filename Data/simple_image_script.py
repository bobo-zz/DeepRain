import matplotlib.pyplot as plt
import cv2
import numpy as np
import os
import glob
import re


class Data_converter():
    def __init__(self, path, max_num_samples, n_data, n_label, start_img=None, subimg_startpos=None, subimg_shape=None,
                 output_shape=None):
        assert os.path.exists(path)
        if start_img is not None:
            assert os.path.exists(start_img)
            raise NotImplementedError("Path is okay, but functionality not implemented yet!")
        assert n_data > 0 and n_label > 0
        self.path = path
        self.max_num_samples = max_num_samples
        self.n_data = n_data
        self.n_label = n_label
        if subimg_startpos is None or subimg_shape is None:
            self.subimg = None
        else:
            assert isinstance(subimg_startpos, tuple)
            assert isinstance(subimg_shape, tuple)
            self.subimg = (subimg_startpos, subimg_shape)  # z.B. ((100, 100), (200, 200))
        assert output_shape is None or isinstance(output_shape, tuple) or isinstance(output_shape, int)
        self.resize_shape = output_shape  # (60, 60)

        self.all_images = self.collect_images()
        self.create_images()

        self.id = 0  # id for .get_next()

        print("data", self.all_samples[0][0].shape, "label", self.all_samples[0][1].shape)
        return

    def get_next(self):
        tmp = self.all_images[self.id]
        self.id += 1
        if len(self.all_images > self.id):
            self.id = 0
        return tmp

    def get_item_at(self, i):
        return self.all_samples[i]

    def get_number_samples(self):
        return len(self.all_samples)

    def _info(self):
        return "DWD Radarbilder"  # ToDo: shape len usw.

    def collect_images(self):
        all_images = []
        path = self.path + "*.png"
        for image_path in glob.glob(path):
            all_images.append(image_path)
        all_images.sort()  # Sortieren
        # ToDo: pattern ersetzen durch regexp
        pattern = "raa01-rw_10000"
        while len(all_images) > 0 and pattern not in all_images[0]:
            del all_images[0]
        while len(all_images) > 0 and pattern not in all_images[-1]:
            del all_images[-1]

        all_valid_images = []
        legals = []
        first_d = None
        next_d = None
        datecomp = Date_Comperator(pre=self.path + "raa01-rw_10000-", post="-dwd---bin.gz.png")
        for i in all_images:
            first_d = next_d
            next_d = i
            if first_d is None:
                legals = [next_d]
                continue
            if datecomp.compare(first_d, next_d):
                # Datum okay:
                legals.append(next_d)
                if len(legals) == self.n_data + self.n_label:
                    all_valid_images.extend(legals)
                    next_d = None
                    legals = []
            else:
                # Datum nicht okay
                legals = [next_d]
        return all_valid_images

    def create_images(self):
        min_n = self.n_data + self.n_label
        self.all_samples = []
        while len(self.all_images) >= min_n:
            data = None
            label = None
            for i in range(self.n_data):
                current = self.all_images.pop(0)
                current = open_one_img(path=current, _subimg=self.subimg, _resize_shape=self.resize_shape,
                                       raiseError=True)
                if data is None:
                    data = np.atleast_3d(current)
                else:
                    data = np.dstack((data, current))
            for i in range(self.n_label):
                current = self.all_images.pop(0)
                current = open_one_img(path=current, _subimg=self.subimg, _resize_shape=self.resize_shape,
                                       raiseError=True)
                if label is None:
                    label = np.atleast_3d(current)
                else:
                    label = np.dstack((label, current))
            one_sample = (data, label)
            self.all_samples.append(one_sample)
            if len(self.all_samples) == self.max_num_samples:
                break

        return


class Date_Comperator():
    def __init__(self, pre, post, timediff=100):
        self.pre = pre
        self.post = post
        self.diff = timediff

    def compare(self, vFirst, vNext):
        # ToDo: 17:60 gibt es nicht, muss dann zu 1800 umgerechnet werden, überlauf geht weiter usw...
        try:
            time = vFirst.replace(self.pre, "").replace(self.post, "")
            time = int(time)
            time2 = vNext.replace(self.pre, "").replace(self.post, "")
            time2 = int(time2)
            return time == time2 - self.diff
        except:
            raise ValueError("There are problems converting img name to timestamp!")
            return False


def open_2D_img(path):
    img = cv2.imread(path)
    if img is None:
        print("Datei nicht vorhanden")
        return None
    if len(img.shape) > 2:
        print("Eingelesenes Bild hat zu hohe Dimension (wird gekürzt auf 2D)")
        img = img[:, :, 0]
    return img


def resize_img(img, shape=(65, 65)):
    # INTER_NEAREST - a nearest-neighbor interpolation
    # INTER_LINEAR - a bilinear interpolation (used by default)
    # INTER_AREA - resampling using pixel area relation. It may be a preferred method for image decimation, as it gives moire’-free results. But when the image is zoomed, it is similar to the INTER_NEAREST method.
    # INTER_CUBIC - a bicubic interpolation over 4x4 pixel neighborhood
    # INTER_LANCZOS4 - a Lanczos interpolation over 8x8 pixel neighborhood

    if shape is None:
        return img
    if isinstance(shape, int):
        shape = (shape, shape)
    assert isinstance(shape, tuple)
    res = cv2.resize(img, dsize=shape, interpolation=cv2.INTER_CUBIC)
    return res


def select_subimg(img, startpos=(0, 0), _size=None, raiseError=False):
    size = _size
    assert isinstance(startpos, tuple)
    tmp = (img.shape[0] - startpos[0], img.shape[1] - startpos[1])
    if tmp[0] < 1 or tmp[1] < 1:
        print("subimg nicht möglich!")
        if raiseError:
            raise ValueError("startposition out of range!")
        return img
    if size is None:
        size = tmp
    size = (min(size[0], tmp[0]), min(size[1], tmp[1]))
    if raiseError and not size == _size:
        raise ValueError("selected size not possible with startposition " + str(startpos))

    return img[startpos[0]:startpos[0] + size[0], startpos[1]:startpos[1] + size[1]]


# ToDo: Methode noch nicht verwendet, später in Objekt ziehen!
def list_to_set(imgList, n_input, n_output):
    x = None
    y = None

    assert (n_input + n_output <= len(imgList))

    for i in range(n_input + n_output):
        img = imgList[i][:, :, 0]
        if i < n_input:
            if x is None:
                x = np.atleast_3d(img)
            else:
                x = np.dstack((x, img))
        else:
            if y is None:
                y = np.atleast_3d(img)
            else:
                y = np.dstack((y, img))
    return (x, y)


def open_one_img(path, _subimg=None, _resize_shape=None, raiseError=False, show_result=False):
    img2D = open_2D_img(path)
    if _subimg is None:
        img2D_sub = img2D
    else:
        assert isinstance(_subimg, tuple)
        img2D_sub = select_subimg(img2D, startpos=_subimg[0], _size=_subimg[1], raiseError=raiseError)
    if _resize_shape is None:
        scaled = img2D_sub
    else:
        scaled = resize_img(img2D_sub, shape=_resize_shape)
    if show_result:
        images = [img2D, img2D_sub, scaled]
        titles = ["Original Bild", "Ausschnitt (200x200)", "Skaliert (80x80)"]
        fig = plt.figure()
        columns = 3
        rows = 1
        for i in range(len(images)):
            fig.add_subplot(rows, columns, i + 1)
            plt.imshow(images[i], vmin=0, vmax=255, cmap="gray")
            plt.title(titles[i])
        plt.show()
    return scaled


def usage():
    path = "raa01-rw_10000-0506301650-dwd---bin.gz.png"
    print("lese Bild:", path)

    # Einfaches einlesen eines Bildes:
    OriginalBild = open_one_img(path)
    # Auswählen eines Ausschnittes (zb. region 200x200 Pixel um Konstanz):
    Ausschnitt = open_one_img(path, _subimg=((100, 100), (200, 200)))
    # Skalierter output -> output-Bildgröße = 60x60
    Skaliert = open_one_img(path, _resize_shape=60)
    # alles in einem, mit show_result -> öffnet Plot, welcher die einzelnen Schritte zeigt
    Demo = open_one_img(path, _subimg=((100, 100), (200, 200)), _resize_shape=(60, 60), raiseError=True,
                        show_result=True)


if __name__ == '__main__':
    path = ".\\"
    path = "C:\\temp\\loeschen\\"
    Data_converter(path=path, max_num_samples=2, n_data=1, n_label=1, start_img=None, subimg_startpos=(100, 200),
                   subimg_shape=(100, 100), output_shape=50)
