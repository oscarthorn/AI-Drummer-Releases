"""
This module defines the interface between the midi instrument or file and the AI
"""

import mido
import time
from mido.midifiles.meta import MetaMessage
import mido.midifiles

DEFAULT_TICKS_PER_BEAT = 480

class PlaybackInputInterface(mido.MidiFile):

    def __init__(self, filename=None, file=None,
                 type=1, ticks_per_beat=DEFAULT_TICKS_PER_BEAT,
                 charset='latin1',
                 debug=False,
                 clip=False
                 ):
        super().__init__(filename, file, type, ticks_per_beat, charset, debug, clip)
        self.playback_time = None

    def play(self, meta_messages=False):
        """Play back all tracks.
        Overrides the default behaviour of mido midifiles play to account for processing delays
        """

        if not self.playback_time:
                self.playback_time = time.time()

        for msg in self:
            self.playback_time += msg.time
            while(time.time() < self.playback_time):
                yield None

            if isinstance(msg, MetaMessage) and not meta_messages:
                continue
            else:
                yield msg
        self.playback_time = None



class LiveInputInterface():

    def __init__(self, port):
        self.port = mido.open_input(port)

    def play(self, meta_messages=False):
        """Returns the first waiting message or none if no messages are waiting"""

        msg = self.port.poll()

        if isinstance(msg, MetaMessage) and not meta_messages:
            return self.play(meta_messages)
        else:
            return msg
