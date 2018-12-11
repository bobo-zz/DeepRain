import numpy as np
import matplotlib.pyplot as plt


# returns date as String YYYYMMDDHHMM and rainfall as float32
def get_data(line, dateIndex=1, rainfallIndex=3):
    a = line.split(";")
    return (a[dateIndex], np.float32(a[rainfallIndex]))


# change representation of String from .txt file
def convert_date_pretty(date):
    return "{}.{}.{} {}:{}".format(date[6:8], date[4:6], date[0:4], date[8:10], date[10:12])


# generate some statistics about selected DWD .txt File
def gen_statistic(path, bins=300, show=False):
    assert PATH.__contains__("02712") # check ID is Valid!
    rainsum_month = np.zeros(12, dtype=np.float32)
    rainsum_reference = np.array([100,20,50,35,50,50,40,40,45,28,0,0])
    all_data = []
    sum = 0
    n_rain = 0
    max_value = 0
    date = "NEVER"
    # open file
    fp = open(path, "r")
    headers = fp.readline()
    for line in fp:
        datum, value = get_data(line)
        all_data.append(value)
        sum += value
        if value > 0.0:
            n_rain += 1
            month = int(datum[4:6])-1
            rainsum_month[month] += value
            if value > max_value:
                max_value = value
                date = datum
        if value > 2.50:
            print(convert_date_pretty(datum), value)

    fp.close()
    if show:
        plt.hist(all_data, bins=bins, log=True)
        plt.show()
    np_data = np.array(all_data, dtype=np.float32)
    print("Ausgewertetes File :", path)
    # ToDo: 0.99 Quantil?
    print("maximalwert:                              {:1.2f} erreicht am {}".format(max_value, date))
    print("Regen/gesamt:                             {:1.2f}%".format(int(n_rain * 100 / np_data.size)))
    print("gesamt Regenmenge:                        {:1.2f}".format(np_data.sum()))
    print("Durchschnittliche regenmenge:             {:1.2f}".format(np_data.sum() / np_data.size))
    print("Durchschnittliche Regenmenge (bei Regen): {:1.2f}".format(np_data.sum() / n_rain))
    print("Monat\tReferenz\tmessung\tdiff")
    for i in range(12):
        rel_err = -1
        if rainsum_reference[i]>0:
            rel_err = abs((rainsum_reference[i]-rainsum_month[i])/rainsum_reference[i])
        print("{}:\t{}\t{:1.2f}\t{:1.2f}".format(i, rainsum_reference[i], rainsum_month[i], rel_err))
    return

if __name__ == '__main__':
    # Path to local copy
    PATH = "produkt_ein_min_rr_20180101_20181125_02712"
    gen_statistic(PATH + ".txt")  # resultat zwei werte > 2.50
