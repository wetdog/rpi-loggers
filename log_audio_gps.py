import pyaudio
import wave
import time
import subprocess
import serial
import datetime
import logging
import os

# set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
file_hander = logging.FileHandler('run_logs.txt')
formatter =logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s')
file_hander.setFormatter(formatter)
logger.addHandler(file_hander)


# create folder

date = datetime.datetime.now()
logs_folder = '/home/pi/logs/' + datetime.datetime.strftime(date,'%Y%m%d') + '/'
if not(os.path.exists(logs_folder)):
    os.makedirs(logs_folder)


## Parameters
CHUNK = 4096
FORMAT = pyaudio.paInt16
CHANNELS = 1 # mono
RATE = 44100
GAIN = 0
DURATION = 1800 # seconds

# set gain
subprocess.run(['amixer','-c','1','sset','Mic',str(GAIN)+'%'])


## callback function
def callback(in_data, frame_count, time_info, status):
    #write data to wav file
    wf.writeframes(in_data)

    # read gps data
    byte = ser.read(ser.in_waiting)
    if len(byte) > 2:
        gf.write(byte)
    
    #data_array.append(in_data)
    return (in_data, pyaudio.paContinue)


# forever cycle

while True:

    try:
        now = datetime.datetime.now()
        FILENAME = datetime.datetime.strftime(now,'%Y%m%d_%H%M%S') + '.wav'
        FILENAME_GPS = datetime.datetime.strftime(now,'%Y%m%d_%H%M%S') + '_gps.txt'
        logger.info(f'Start Measure of {DURATION} seconds and gain {GAIN}')

        ## instatiate pyaudio
        p = pyaudio.PyAudio()

        ### create wav file
        wf = wave.open(os.path.join(logs_folder, FILENAME), 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)

        # create gps file
        gf = open(os.path.join(logs_folder, FILENAME_GPS), 'wb')

        # connect to serial of gps
        ser = serial.Serial('/dev/ttyAMA0', 9600, timeout=1)
        time.sleep(0.5)
        # send gps config msg
        ser.write(b'\xB5\x62\x06\x08\x06\x00\xC8\x00\x01\x00\x01\x00\xDE\x6A')
        time.sleep(0.5)

        #### open stream
        stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
                stream_callback=callback)

        # start the stream (4)
        stream.start_stream()   #start recording
        # wait for stream to finish (5)
        for _ in range(DURATION*10):  #The waiting time is 5 seconds.
            if stream.is_active():
                time.sleep(0.1)   #Sleep, does not affect the recording

        # stop stream (6)
        stream.stop_stream()   #Until run this sentence to terminate the recording
        stream.close()
        # close files
        wf.close()
        gf.close()
        # close serial
        ser.close()
        # close PyAudio (7)
        p.terminate()
        logger.info(FILENAME + ' File stored')
        logger.info(FILENAME_GPS + ' File stored')
    
    except Exception as Argument:
        logger.info("Error occured while recording",exc_info=True)
        time.sleep(1)



