import sys
import os
import logging
import time

from math import isclose
from datetime import timedelta, datetime

def main(rec_dir):
    if not os.path.exists(rec_dir):
        msg = 'outpath %s does not exist'%rec_dir
        logging.error(msg)
        raise IOError()

    task = RecTask(rec_dir=rec_dir,
                   duration=15,
                   max_hours=0.1)
    task.start_recording()

class RecTask(object):
    def __init__(self, rec_dir=None, duration=60*60, max_hours=24*3):
        self.rec_dir = rec_dir
        self.global_start = datetime.now()
        self.duration = timedelta(seconds=duration)
        self.max_hours = max_hours # default 3 days
        self.global_end = self.global_start+timedelta(hours=self.max_hours)
        self.recording_hours = (7,22)

    def __str__(self):
        return 'dir: %s\nstarted at: %s'%(str(self.recdir),
                                          str(self.global_start))

    def start_recording(self):
        self.set_recordings()
        self.record()
        msg = 'task finished successfully'
        logging.info(msg)

    def set_recordings(self):
        self.recording_dates = []
        i=0
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
                    print('here')
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
                          ' unexpected.\nstart hour: %i'%start.hour
                    logging.warning(msg)
                end = start + self.duration
                self.recording_dates.append((start,end))
            start += self.duration
            end = start + self.duration

    def record(self):
        closeness_duration = 5
        if closeness_duration > self.duration.total_seconds():
            msg = 'duration too short %i'%self.duration
            logging.error(msg)
            raise ValueError(msg)

        for start, end in self.recording_dates:
            reference_now = datetime.now()
            if self.dt_isclose(reference_now, start, 5):
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
        fps = 4
        width = 640
        height = 360
        msg = 'taking the footage between %s and %s'%(str(start),
                                                      str(end))
        logging.info(msg)
        cmd = ['raspivid','-o', filepath,
                          '-h', str(height),
                          '-w', str(width),
                          '-t', str(duration),
                          '-fps', str(fps)]
        print(' '.join(cmd))
        time.sleep((end-start).total_seconds())

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
    main(rec_dir)
