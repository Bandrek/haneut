import csv
import wfdb
from time import gmtime, strftime
import numpy as np
import proses
import neurokit as nk
import scipy.fftpack as fftpack
import matplotlib.pyplot as plt
from biosppy.signals import ecg
import biosppy
import json

def convert(array):
    divisor = np.divide
    subtractor = np.subtract
    multiplier = np.multiply
    powerer = np.power

    n = 10
    vcc = 3.3
    half = 0.5
    g = 1100
    denominator = powerer(2,n)

    result = np.array([])
    result = divisor(array,denominator)
    result = subtractor(result,half)
    result = multiplier(result,vcc)
    result = divisor(result,g)
    result = multiplier(result,1000)

    return result

# def adaptive_threshold(self, data, ff=0.85):
#     # y = []

#     # for i in range(0, len(data)):
#     #     y.append(0)
#     y = np.empty(len(data))

#     for i in range(0, len(data)):
#         if i == 0:
#             y[i] = 1  # ff + (1 - ff) * data[i]
#         else:
#             y[i] = ff * y[i - 1] + (1 - ff) * data[i]

#     return y

# Load raw ECG signal
# signals = np.loadtxt('ecgRaw.txt')
# rawAri = np.loadtxt('ari.txt')
# nData = np.linspace(1,len(signals),num=len(signals))
# signals = convert(signals)
# Process it and plot
# output = ecg.ecg(signals = signals, sampling_rate=100., show=True)

# # Pick csv file
# csvfile = "aritmia/106.csv"

# # Create numpy array
# ecgRaw = np.array([])

# # Store ecg column in array
# with open(csvfile, 'rb') as csvfile:
#     reader = csv.reader(csvfile)

#     for row in reader:
#         ecgRaw = np.append(ecgRaw,row[1])

# ecgRaw = ecgRaw[2:]
# ecgRaw = ecgRaw.astype(np.float)

# # time = strftime("%Y-%m-%d %H:%M:%S", gmtime())



myarray = wfdb.rdsamp('data/113')
-r 113
-a atr
-f 8:22
-p
annotation = wfdb.rdann('113', 'atr')

dataArray = np.asarray(myarray)[0]

myarray = np.array([])
for row in dataArray:
    myarray = np.append(myarray, row[0])

nData = np.linspace(1,len(myarray), num = len(myarray))

# print ecgRaw
lowcut = 0.5
highcut = 40
sampling_rate = 360
order = 2
result = []

# ps = proses.ProcessECG()

# filtered = nk.ecg_preprocess(myarray, sampling_rate = 360)
# filtered = ps.butter_bandpass_filter(myarray,lowcut,highcut,sampling_rate,order)
#filtered2 = ps.butter_bandpass_filter(rawAri,lowcut,highcut,sampling_rate,order)
# normalized = np.asarray(biosppy.signals.tools.normalize(signal=filtered,ddof=1))[0]
#normalized2 = np.asarray(biosppy.signals.tools.normalize(signal=filtered2,ddof=1))[0]
# rpeaks, = biosppy.ecg.hamilton_segmenter(signal=normalized, sampling_rate=sampling_rate)
# rpeaks, = biosppy.ecg.correct_rpeaks(signal=normalized, rpeaks=rpeaks, sampling_rate=sampling_rate,tol=0.05)

rpeaks = nk.ecg_find_peaks(myarray, sampling_rate = 360)
# print rpeaks
# rpeaks2 = list(rpeaks)

rri = np.diff(rpeaks)
rri = rri.astype(float)
rris = np.divide(rri, sampling_rate)
print rris

# my_dict = dict( n = nData ,ECG = filtered, RRI = rris )
# print my_dict

# plt.plot(filtered, color='red', alpha=0.5)
plt.plot(nData,myarray, color='blue', alpha=0.5)
# plt.plot(nData[0:248],normalized2,color='red',alpha=0.5)
# plt.plot(nData,rfft, color='red', alpha=0.5)
# plt.scatter(rpeaks)

# result.append(myarray.tolist())
# result.append(rris.tolist())

# print type(result)

# with open('Ariresults_5.json', 'w') as f:
#     json.dump(result,f)

np.savetxt("resultAgain_2.csv", np.transpose(myarray), fmt='%.3e',delimiter=",")
# pd.DataFrame.from_dict(data=my_dict, orient='index').to_csv('dict_file.csv', header=False)

plt.show()



