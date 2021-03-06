import numpy as np
import time
import matplotlib.pyplot as plt

import preprocessing as prp

name = 'train/data/100.csv'
with open(name, 'r') as f:
	reader = csv.DictReader(f)
hasil = prp.readData(name)
timestamp = hasil.T[0]
hasilLen = len(hasil)
hasil = hasil.T[1:].T

name = "csv/cf-play.csv"
hasil2 = prp.readData(name)
timestamp2 = hasil2.T[0]
hasil2Len = len(hasil2)
hasil2 = hasil2.T[1:].T

hasil = np.vstack((hasil, hasil2[1:]))

target = np.zeros(hasilLen-1)
target = np.append(target, np.ones(hasil2Len-1))

from sklearn import svm
import time
start = time.time()
model = svm.SVC(kernel='linear')
model.fit(hasil[1:], target)
print time.time() - start

import pickle
modelkuh = {'modelkuh': model}
# Pickle
pickle.dump(modelkuh, open("modelkuh.p", "wb"))
pickle.dumps(modelkuh)

# print target
# print len(target)
