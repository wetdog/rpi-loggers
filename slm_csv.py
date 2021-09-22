# coding: utf-8

### Filtros de Octavas y tercios con pyfilterbank segun IEC 61260


import numpy as np
from pyfilterbank.octbank import FractionalOctaveFilterbank
from pyfilterbank.splweighting import a_weighting_coeffs_design
from pyfilterbank.octbank import frequencies_fractional_octaves
import pyaudio
from datetime import datetime
from scipy.signal import lfilter
import time
import subprocess
import os
import logging

# set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
file_hander = logging.FileHandler('run_logs.txt')
formatter =logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s')
file_hander.setFormatter(formatter)
logger.addHandler(file_hander)


# create folder 
date = datetime.now()
folder = '/home/pi/logs/' + datetime.strftime(date,'%Y%m%d') + '/'
if not(os.path.exists(folder)):
    os.makedirs(folder)
    logger.info(str(folder) + ' Created')


# audio parameters
CHANNELS = 1
fs = 44100
CHUNK_SIZE = 11025
RATE = fs
C=0.9
GAIN = 35
DURATION = 1800

# set gain
subprocess.run(['amixer','-c','1','sset','Mic',str(GAIN)+'%'])

################################# 
# processing functions

def spl(signal):
    p_ref = 0.000002
    return 20*np.log10((np.sqrt(np.mean(np.power(signal,2))))/p_ref)

def db_level(signal, C):
    p_ref = 0.000002
    #level = 10*np.log10(np.nansum((pa/po)**2)/T) + C
    level = 20*np.log10((np.sqrt(np.mean(np.power(signal,2))))/p_ref) + C
    return level

def leq(levels):
    e_sum = (np.sum(np.power(10, np.multiply(0.1, levels))))/len(levels)
    eq_level = 10*np.log10(e_sum)
    return eq_level

def callback(in_data, frame_count, time_info, status):
    
    audio_data = np.frombuffer(in_data, dtype=np.float32)
    y = lfilter(b, a, audio_data)
    y_octaves, states = third_oct.filter(audio_data)
    
    f.write(datetime.strftime(datetime.now(),'%Y%m%d_%H:%M:%S.%f') + ',')
    for i, y_oct in enumerate(y_octaves.T):
        oct_level = db_level(y_oct, C)
        f.write('{0:.2f},'.format(oct_level))

    La = db_level(y, C)
    L = db_level(audio_data, C)
    f.write('{0:.2f},'.format(La))
    f.write('{0:.2f}'.format(L))
    f.write('\n')

    return (in_data, pyaudio.paContinue)

##################################

# third octave filterbank
third_oct = FractionalOctaveFilterbank(
    sample_rate=fs,
    order=4,
    nth_oct=3.0,
    norm_freq=1000.0,
    start_band=-10,
    end_band=9,
    edge_correction_percent=0.01,
    filterfun='cffi')

# A-weight filter
b, a = a_weighting_coeffs_design(fs)
freqs, foo = frequencies_fractional_octaves(-10,9,1000,3)

################################

# Continuous measurement

while True:
    try:
        logger.info(f'Start Measure of {DURATION} seconds and gain {GAIN}')

        # New csv file
        now = datetime.now()
        FILENAME_CSV = datetime.strftime(now,'%Y%m%d_%H%M%S') + '.csv'
        f = open(os.path.join(folder, FILENAME_CSV), 'a')

        # write header
        f.write('Time,')
        for freq in freqs:
            f.write('{0:.0f}Hz,'.format(freq))
        f.write('LA,')
        f.write('LZ,\n')
        p = pyaudio.PyAudio()

        stream = p.open(format=pyaudio.paFloat32,
                        channels=CHANNELS,
                        rate=RATE,
                        frames_per_buffer=CHUNK_SIZE,
                        input=True,
                        output=False,
                        stream_callback=callback)

        # start the stream (4)
        stream.start_stream()   #start recording
        # wait for stream to finish (5)
        for _ in range(DURATION*10):  #The waiting time is DURATION seconds.
            if stream.is_active():
                time.sleep(0.1)   #Sleep, does not affect the recording

        # Close Stream and file
        stream.stop_stream()
        stream.close()
        p.terminate()
        f.close()
        logger.info(f'{FILENAME_CSV} file stored')
        
        # wait one second and restart
        time.sleep(1)

    except Exception as Argument:
        logger.info("Error occured while recording",exc_info=True)



