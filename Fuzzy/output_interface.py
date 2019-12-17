import random

import mido

Intro = mido.Message('note_on', note=44, velocity=64, channel=0)
Verse = mido.Message('note_on', note=random.choice([38,40,41,43,45,47]), velocity=64, channel=0)
Bridge = mido.Message('note_on', note=random.choice([48,50,52,53,55,57,59]), velocity=64, channel=0)
Chorus1 = mido.Message('note_on', note=60, velocity=64, channel=0)
Chorus2 = mido.Message('note_on', note=62, velocity=64, channel=0)
Chorus3 = mido.Message('note_on', note=64, velocity=64, channel=0)
Chorus4 = mido.Message('note_on', note=65, velocity=64, channel=0)
Chorus5 = mido.Message('note_on', note=67, velocity=64, channel=0)
Chorus6 = mido.Message('note_on', note=69, velocity=64, channel=0)
Chorus7 = mido.Message('note_on', note=71, velocity=64, channel=0)
Fill1 = mido.Message('note_on', note=49, velocity=64, channel=0)
Fill2 = mido.Message('note_on', note=51, velocity=64, channel=0)
Fill3 = mido.Message('note_on', note=54, velocity=64, channel=0)
Fill4 = mido.Message('note_on', note=56, velocity=64, channel=0)
Fill5 = mido.Message('note_on', note=58, velocity=64, channel=0)
Outro = mido.Message('note_on', note=61, velocity=64, channel=0)
Stop = mido.Message('note_on', note=36, velocity=64, channel=0)

"""
Pattern mapping
Pattern_Output = {0: 'Intro To Chorus 1',
                      1: 'Fill To Chorus 1',
                      2: 'Fill To Chorus 2',
                      3: 'Fill To Chorus 3',
                      4: 'Fill To Chorus 4',
                      5: 'Fill To Chorus 5',
                      6: 'Fill To Chorus 6',
                      7: 'Fill To Chorus 7',
                      8: 'Chorus 1',
                      9: 'Fill 1',
                      10: 'Outro',
                      11: 'None',
                      12: 'No Change',
                      13: 'Fill 4',
                      14: 'Fill 3'}
                      
Unmute mapping
Unmute_output = {3: 'Snare'
                 2: 'Kick and Snare'
                 1: 'Kick',
                 0: 'None'}

Mute mapping         
Mute_output = {2: 'Kick and Snare'
               1: 'Kick',
               0: 'None'}
"""

Pattern_dict = {0: [Chorus1],
                1: [Chorus1, Fill4],
                2: [Chorus2, Fill4],
                3: [Chorus3, Fill4],
                4: [Chorus4, Fill4],
                5: [Chorus5, Fill4],
                6: [Chorus6, Fill4],
                7: [Chorus7, Fill4],
                8: Chorus1,
                9: Fill1,
                10: Outro,
                11: Stop,
                12: None,
                14: Fill3,
                13: Fill4,
                }

MuteKick = mido.Message('note_on', note=24, velocity=127, channel=0)
UnmuteKick = mido.Message('note_on', note=24, velocity=0, channel=0)
# MuteHihat = mido.Message('note_on', note=26, velocity=127, channel=0)
# UnmuteHihat = mido.Message('note_on', note=26, velocity=0, channel=0)
MuteSnare = mido.Message('note_on', note=25, velocity=127, channel=0)
UnmuteSnare = mido.Message('note_on', note=25, velocity=0, channel=0)


def Mute_Kick(x):
    return {0: UnmuteKick,
            1: MuteKick,
            -1: None}[x]


def Mute_Snare(x):
    return {0: UnmuteSnare,
            1: MuteSnare,
            -1: None}[x]


def Pattern(x):
    return Pattern_dict[x]


Map = {'Pattern': lambda x: Pattern(x),
       'Intensity': lambda x: mido.Message('control_change', control=0, value=int(x)),
       'Complexity': lambda x: mido.Message('control_change', control=1, value=int(x)),
       'Mute_Kick': lambda x: Mute_Kick(x),
       'Mute_Snare': lambda x: Mute_Snare(x)}

class BaseOutputInterface:

    def __init__(self, port, Map = Map):
        self.map = Map
        if port is not None:
            self.port = mido.open_output(port)
            self.reset()
        self.previous_instruction = {}

    def _send(self, msg):
        """
        Extension for the mido send function to allow sending of multiple messages in a list
        :param msg: A single msg or a list of messages.
        """
        if msg is None:
            return
        if isinstance(msg, mido.Message):
            self.port.send(msg)
        elif isinstance(msg, list):
            for message in msg:
                self.port.send(message)
        else:
            raise ValueError('Invalid type')

    def reset(self):
        raise NotImplemented

    def send_instruction(self, instruction_set):
        raise NotImplemented


class OutputInterface(BaseOutputInterface):

    def __init__(self, port, Map=Map):
        """

        :param mapping: A dict {instruction: midi message function}
        :param port:
        """
        super().__init__(None)
        self.map = Map
        self.port = mido.open_output(port)
        self.previous_instruction = {}

        self.robot = RobotOutputInterface()

        self.reset()

    def send_instruction(self, instruction_set):

        for key in instruction_set.keys():
            if not (key in self.previous_instruction.keys() and instruction_set[key] == self.previous_instruction[key]):
                msg = self.map[key](instruction_set[key])
                self._send(msg)
        
        self.previous_instruction.update(instruction_set)

        self.robot.send_instruction(instruction_set)

    def reset(self):
        self.robot.reset()
        self._send([UnmuteSnare, UnmuteKick, Stop])
        for i in range(36, 72):
            self._send(mido.Message('note_on', note=i, velocity=0, channel=0))


class RobotOutputInterface(BaseOutputInterface):

    def __init__(self, port='Pepper', Map=Map):
        """

        :param mapping: A dict {instruction: midi message function}
        :param port:
        """
        try:
            self.port = mido.open_output(port)
        except Exception as e:
            print(e)
            self.port = None
        super().__init__(None)

    def send_instruction(self, instruction_set):

        if self.port is not None:
            for key in instruction_set.keys():
                if not (key in self.previous_instruction.keys() and instruction_set[key] == self.previous_instruction[key]):
                    msg = self.map[key](instruction_set[key])
                    self._send(msg)

            self.previous_instruction.update(instruction_set)

    def reset(self):
        if self.port is not None:
            self._send(mido.Message('control_change', control=100, value=0))
