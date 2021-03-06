import numpy as np
import pickle
import sys

sys.path.append("../Data")
import sample_bundle

class Sample_Bundle():
    def __init__(self, subimg, resizeshape, all_samples, details=""):
        self.subimg = subimg    # Subimg selection ((Y,X), (width, height))
        self.resizeshape = resizeshape  # Tuple or int == outputshape
        self.all_samples = all_samples  # list of Tuples [(data0, label0), (data1, label1), ...]
        self.details = details  # Userinput string
        self.id = 0
        self.cleared = -1       # clear threshold

    def info(self):
        info = "Set Bundle with " + str(len(self.all_samples)) + " Samples\n"
        info += "Shapes are: input {}, output {}\n".format(self.all_samples[0][0].shape, self.all_samples[0][1].shape)
        info += "Subimg selection is: {}, resizeshape is: {}\n".format(self.subimg, self.resizeshape)
        if hasattr(self, "cleared"):
            if self.cleared > 0:
                info += "Samples are cleared, minimal max value per Sample is {}\n".format(self.cleared)
        if self.details is not "":
            info += "### Userinfostring:\n"+self.details
        return  info

    def get_next(self):
        tmp = self.all_samples[self.id]
        self.id += 1
        if len(self.all_samples) > self.id:
            self.id = 0
        return tmp

    def get_item_at(self, i):
        return self.all_samples[i]

    def get_number_samples(self):
        return len(self.all_samples)

    ## axis = position batchsize in shape, default: (x, y, n_data, batchsize)
    def get_batch(self, batchsize, random=True, axis=3):
        if random:
            indexlist = np.random.permutation(len(self.all_samples))
        else:
            indexlist = np.arange(len(self.all_samples))

        all_b_data = []
        all_b_label = []
        b_data = None
        b_label = None
        for i in range(len(self.all_samples)):
            a = self.all_samples[indexlist[i]]
            if i%batchsize == 0:
                if b_data is not None:
                    all_b_data.append(np.stack(b_data, axis=axis))
                    all_b_label.append(np.stack(b_label, axis=axis))
                b_data = []
                b_label = []
            b_data.append(a[0])
            b_label.append(a[1])
        if len(b_data) > 0:
            all_b_data.append(np.stack(b_data, axis=axis))
            all_b_label.append(np.stack(b_label, axis=axis))
        return all_b_data, all_b_label

    def get_all_data_label(self, channels_Last, flatten_output=False):
        data = []
        label = []
        for item in self.all_samples:
            data.append(item[0])
            if flatten_output:
                label.append(item[1].flatten())
            else:
                label.append(item[1])
        if channels_Last:
            return np.array(data), np.array(label)
        return np.swapaxes(np.array(data),1,3), np.swapaxes(np.array(label),1,3)

    def sample_is_moving(self, sample):
        shape = sample.shape
        for i in range(shape[0]):
            for j in range(shape[1]):
                if np.unique(sample[i][j]).size > 1:
                    return True
        return False

    def sample_is_empty(self, sample, percentage=0.25):
        assert percentage > 0.0 and percentage < 1.0
        n_pixels = sample.shape[0]*sample.shape[1]
        if len(sample.shape) > 2:
            n_pixels = n_pixels*sample.shape[2]

        number = np.count_nonzero(sample < 0)
        return number > n_pixels*percentage

    def clear_samples(self, threshold=1, ignorevalue=-1, move=False, percentage=0.25, clip=True):
        """
        :param threshold:   minimum value needed in array
        :param ignorevalue: currently unused
        :param move:        if True, at least one Pixel has to change along z-axis
        :param percentage:  maximum ammount of 'none radar data' in image
        :param clip:        if True, negative values will be clipped
        :return:            None
        """
        if not hasattr(self, 'cleared'):   #supports older versions of Objects
            print("You are using an outdatet Version of sample_bundle! this may cause to errors!")
            self.cleared = -1

        if threshold <= self.cleared:
            print("cleared already done with threshold {}".format(self.cleared))
            return
        index = 0
        while(True):
            removed=False
            a = self.all_samples[index]
            if np.max(a[0]) < threshold or self.sample_is_empty(a[0], percentage=percentage):
                del self.all_samples[index]
            else:
                if move:
                    if not self.sample_is_moving(a[0]):
                        del self.all_samples[index]
                    else:
                        index += 1
                else:
                    index +=1
            if index >= len(self.all_samples):
                break
        if clip:
            self.clip_all()
        self.cleared = threshold
        return

    def normalize(self, max_val= 0):
        if max_val == 0:   #max value raussuchen
            for i in range(len(self.all_samples)):
                a = self.all_samples[i]
                if np.max(a[0]) > max_val: #data
                    max_val = np.max(a[0])
                if np.max(a[1]) > max_val: #label
                    max_val = np.max(a[1])
            if max_val == 1:    # wenn schon 1, gibts nichts zu tun
                return

        for i in range(len(self.all_samples)):
            a = self.all_samples[i]
            normalized = (a[0]/max_val, a[1]/max_val)
            self.all_samples[i] = normalized

        return

    def clear_by_sum(self, threshold):
        index = 0
        b = []
        while(True):
            a = self.all_samples[index]
            if np.sum(a[0]) < threshold:
                del self.all_samples[index]
            else:
                index +=1
                b.append(np.sum(a[0]))
            if index >= len(self.all_samples):
                break
        return b

    def clip_all(self):
        for i in range(len(self.all_samples)):
            a = self.all_samples[i]
            clipped = (np.clip(a[0], a_min=0, a_max=None, out=None), np.clip(a[1], a_min=0, a_max=None, out=None))
            self.all_samples[i] = clipped
        return

    def save_object(self, filename):
        filename += ".sb"
        with open(filename, 'wb') as output:  # Overwrites any existing file.
            pickle.dump(self, output, pickle.HIGHEST_PROTOCOL)
        print(filename + " saved successfully")
        return


def load_Sample_Bundle(path):
    path += ".sb"
    with open(path, 'rb') as input:
        sb = pickle.load(input)
        assert isinstance(sb, sample_bundle.Sample_Bundle)
    return sb


if __name__ == '__main__':
    data = np.array([[200,200,1,0,4,200],[200,5,3,2,6,200]])
    label = np.array([[0,0,0],[0,0,0]])
    sb = Sample_Bundle((0,0), (64,64), [(data, label)], details="")
    print(sb.info())
    print(sb.all_samples[0][0])
    sb.clear_samples(threshold=7, ignorevalue=200)
    print(sb.info())
    input("NEINNEIN")


    sb = load_Sample_Bundle("einObjekt")
    print(sb.info())
    #duplicate first Sample 10 times, so 11 images are avaliable
    for i in range(10):
        sb.all_samples.append(sb.get_item_at(0))
        sb.all_samples[i+1][0][0][0]=i
    print("one sample has shape:",sb.get_item_at(0)[0].shape)
    d,l = sb.get_batch(batchsize=4)
    print("anz Batches:",len(d),"mit shape:",d[0].shape,"und label-shape:",l[0].shape)
    print(sb.subimg)
    print(sb.resizeshape)
    data, label = sb.get_all_data_label(channels_Last=True)
    print("data:",data.shape, "label",label.shape)