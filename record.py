import sys
import os
import logging
import time

from datetime import timedelta, datetime
from subprocess import call, Popen, PIPE

def main(rec_dir):
    if not os.path.exists(rec_dir):
        msg = 'outpath %s does not exist'%rec_dir
        logging.error(msg)
        raise IOError()

    task = RecTask(rec_dir=rec_dir,
                   duration=20*60,
                   max_hours=3*24)
    task.start_recording()

class RecTask(object):
    def __init__(self, rec_dir=None, duration=60*60, max_hours=3*24):
        self.rec_dir = rec_dir
        self.global_start = datetime.now()
        self.duration = timedelta(seconds=duration)
        self.max_hours = max_hours # default 3 days
        self.global_end = self.global_start+timedelta(hours=self.max_hours)
        self.recording_hours = (8,21)

    def __str__(self):
        return 'dir: %s\nstarted at: %s'%(str(self.recdir),
                                          str(self.global_start))

    def start_recording(self):
        self.set_recordings()
        self.discover_ip()
        msg = 'connected to the network with the ip %s'%self.ip
        logging.info(msg)
        self.record()
        msg = 'task finished successfully'
        logging.info(msg)

    def set_recordings(self):
        self.recording_dates = []
        i = 0
        start = self.global_start
        end = self.global_start + self.duration
        while end < self.global_end:
            if start.hour >= self.recording_hours[0] and\
               end.hour < self.recording_hours[1]:
                self.recording_dates.append((start,end))
            else:
                # start time is out of the desired recording hours
                if start.hour < self.recording_hours[0]:
                    # we are in the same day
                    start = start.replace(hour=self.recording_hours[0],
                                          minute=0,
                                          second=0,
                                          microsecond=0)
                elif start.hour >= self.recording_hours[1]:
                    # we need to switch to the next day
                    start = start.replace(hour=self.recording_hours[0],
                                          minute=0,
                                          second=0,
                                          microsecond=0)
                    start += timedelta(days=1)
                else:
                    msg = 'recording hours skipping logic is somewhere'\
                          ' unexpected.\n'\
                          'start hour: %i'%start.hour
                    logging.warning(msg)
                end = start + self.duration
                self.recording_dates.append((start,end))
            start += self.duration
            end = start + self.duration

    def discover_ip(self):
        cmd = ['hostname', '--all-ip-addresses']
        process = Popen(['hostname','--all-ip-addresses'],
                        stdout=PIPE,
                        stderr=PIPE)
        stdout, stderr = process.communicate()
        self.ip = ''
        if stderr:
            msg = 'ip not found with error %s'
            logging.warning(msg%stderr.decode())
            self.ip = ''
        else:
            self.ip = stdout.decode().strip()

    def record(self):
        closeness_duration = 60
        if closeness_duration > self.duration.total_seconds():
            msg = 'duration too short %i'%self.duration
            logging.error(msg)
            raise ValueError(msg)

        for start, end in self.recording_dates:
            reference_now = datetime.now()
            self.discover_ip()
            if self.ip:
                msg = 'continuing recording, still connected to %s'%self.ip
            else:
                msg = 'continuing offline, no ip found'
            logging.info(msg)

            if self.dt_isclose(reference_now, start, closeness_duration):
                start = datetime.now()
                self.take_footage(start, end)
            else:
                if start < reference_now:
                    # behind schedule
                    if end > reference_now:
                        # but there is still footage to be taken
                        start = datetime.now()
                    else:
                        msg = "more time has passed than expected, "\
                              "don't know what to do.\n"\
                              "now:%s vs (start,end):(%s,%s)"%(str(reference_now),
                                                               str(start),
                                                               str(end))
                        logging.error(msg)
                        raise ValueError(msg)
                else:
                    difference = (start - datetime.now()).total_seconds()
                    msg = "I am in the future, i will wait until then.\n"\
                          "now:%s vs (start,end):(%s,%s)\n"\
                          "sleeping for %i seconds."%(str(reference_now),
                                                      str(start),
                                                      str(end),
                                                      difference)
                    logging.info(msg)
                    time.sleep(difference)
                    self.take_footage(start, end)

    @staticmethod
    def dt_isclose(dt1, dt2, dif_seconds):
        td = dt1-dt2
        if abs(td.total_seconds()) <= dif_seconds:
            return True
        return False

    def take_footage(self, start, end):
        filename = '-'.join((start.strftime('%Y%m%d_%H%M%S'),
                             end.strftime('%Y%m%d_%H%M%S')))+'.h264'
        filepath = os.path.join(self.rec_dir, filename)
        duration = int((end-start).total_seconds()*1000)
        fps = 8
        width = 800
        height = 600
        roi = '0.1,0.35,0.65,0.65'
        msg = 'taking the footage between %s and %s'%(str(start),
                                                      str(end))
        logging.info(msg)
        cmd = ['raspivid','-o', filepath,
                          '-h', str(height),
                          '-w', str(width),
                          '-t', str(duration),
                          '-roi', roi,
                          '-fps', str(fps)]
        print(' '.join(cmd))
        call(cmd) 

if __name__ == "__main__":
    file_path = os.path.dirname(os.path.realpath(__file__))
    print(file_path)
    rec_dir = 'recordings'
    rec_path = os.path.abspath(os.path.join(file_path, rec_dir))
    log_file = 'record.log'
    logging.basicConfig(filename=os.path.join(rec_path,log_file),
                        format="%(asctime)s-%(levelname)s: %(message)s",
                        level=logging.INFO,
                        filemode='a')
    time.sleep(30)
    main(rec_path)
