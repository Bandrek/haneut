"""
Mencoba memproses sinyal ECG memakai python
author : Umble
"""

import numpy as np
from scipy.signal import butter, lfilter

class ProcessECG(object):

	def butter_bandpass(lowcut, highcut, sampleRate, order = 1):
		nyq = 0.5 * sampleRate
		low = lowcut / nyq
		high = highcut / nyq
		b, a = butter(order, [low, high], btype = 'band')
		return b, a

	def butter_bandpass_filter(data, lowcut, highcut, sampleRate, order=1):
		b, a = butter_bandpass(lowcut, highcut, sampleRate, order=order)
		y = lfilter(b, a, data)
		return y