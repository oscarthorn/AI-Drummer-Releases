"""
This is the main entry point for the AiDrummer application
"""
import multiprocessing as mp
import queue
import signal
import time

import mido

from Fuzzy import Information_processing as preprocessing
from Fuzzy import fuzzy_computation as computation
from Fuzzy import fuzzy_filters as filters
from Fuzzy import input_interface
from Fuzzy import output_interface
# from Fuzzy.animation import DrummerAnimateRun
from Fuzzy.settings import delta


class AiDrummer:

    def __init__(self, mode, in_port=None, out_port=None,
                 file=None, play_instrument=None, instrument_port=None,
                 visualize=False, flags=None, custom_rules=None):

        # Choose mode
        self.mode = mode
        if mode == 'live':
            self.input = input_interface.LiveInputInterface(in_port)
        elif mode == 'playback':
            self.messages = input_interface.PlaybackInputInterface(file).play()

        # Initialize modules
        self.extractor = preprocessing.InformationProcessor()
        self.filter = filters.TemporalFilters()
        self.agent = computation.Agent(custom_rules)
        self.output = output_interface.OutputInterface(out_port)

        # Initialize piano (instrument) output or save that it should not be played
        if play_instrument == 'yes':
            self.instrument_output = mido.open_output(instrument_port)
            self.play_instrument = play_instrument
        else:
            self.play_instrument = play_instrument

        # Initialize visualization
        # if visualize is True:
        #     self.AnimatorQueue = mp.Queue(maxsize=1)
        #     proc = mp.Process(target=DrummerAnimateRun, args=(self.AnimatorQueue,))
        #     proc.start()
        #     self.visualize = visualize
        # else:
        #     self.visualize = visualize

        # Flags
        self.flags = flags


        # Ready
        print('Ready')

    def run(self):

        delta_t = delta
        # If playing live
        if self.mode == 'live':
            time_compute = 0
            while True:
                if self.flags is not None and self.flags['stop']:
                    self.output.reset()
                    break
                message = self.input.play()
                self.extractor.preprocess(message)
                if time.time() - time_compute >= delta_t:
                    features = {'Time': time.time()}
                    features.update(self.extractor.get_features(features['Time']))
                    features.update(self.filter.filter(features))
                    instructions, cache = self.agent.compute(features)
                    self.extractor.postprocess(instructions, features['Time'])
                    self.output.send_instruction(instructions)
                    time_compute = time.time()
                    # if self.visualize is True:
                    #     cache['Result'] = {}
                    #     cache['Result'].update(instructions)
                    #     cache['Info'] = {}
                    #     cache['Info'].update(features)
                    #     try:
                    #         self.AnimatorQueue.get_nowait()
                    #     except queue.Empty:
                    #         pass
                    #     try:
                    #         self.AnimatorQueue.put_nowait(cache)
                    #     except queue.Full:
                    #         pass
                if self.play_instrument == 'yes' and message is not None:
                    self.instrument_output.send(message)

        # If playing from a file
        elif self.mode == 'playback':
            time_compute = 0
            while True:
                if self.flags is not None and self.flags['stop']:
                    self.output.reset()
                    break
                message = next(self.messages, None)
                self.extractor.preprocess(message)
                if time.time() - time_compute >= delta_t:
                    features = {'Time': time.time()}
                    features.update(self.extractor.get_features(features['Time']))
                    features.update(self.filter.filter(features))
                    instructions, cache = self.agent.compute(features)
                    self.extractor.postprocess(instructions, features['Time'])
                    self.output.send_instruction(instructions)
                    time_compute = time.time()
                    # if self.visualize is True:
                    #     cache['Result'] = {}
                    #     cache['Result'].update(instructions)
                    #     cache['Info'] = {}
                    #     cache['Info'].update(features)
                    #     try:
                    #         self.AnimatorQueue.get_nowait()
                    #     except queue.Empty:
                    #         pass
                    #     try:
                    #         self.AnimatorQueue.put_nowait(cache)
                    #     except queue.Full:
                    #         pass
                if self.play_instrument == 'yes' and message is not None:
                    self.instrument_output.send(message)
