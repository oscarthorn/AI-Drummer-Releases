"""
This module handles preprocessing of information used by fuzzy_filters and fuzzy_computation
"""
import time

from typing import Dict, Any

from math import inf

from Fuzzy.settings import time_bar


class InformationProcessor:

    persistent: Dict[str, float or None]
    variables: Dict[str, Any]

    def __init__(self):

        # Single calculation values
        self.persistent_calculated = False
        self.persistent = {'Start Time': None,
                           'Time Per Bar': None}

        # Drum state
        self.drum_state = {'History Mode': 0,
                           'History Intensity': 0,
                           'History_Complexity': 0,
                           'History Pattern': 11,
                           'History Mute Kick': 0,
                           'History Mute Snare': 0}

        # Initialize variables for preprocess
        self.velocity_queue = []
        self.velocity_queue_clear = False
        self.full_range_density = DensityRepresentation(range(0, 127))
        self.low_range_density = DensityRepresentation(range(0, 61), complexity_slots=8)
        self.high_range_density = DensityRepresentation(range(60, 128), complexity_slots=8)
        self.time_of_last_note = -inf
        self.time_since_last_note = inf
        self.pedal = False
        self.manual_end = False
        self.time_of_pedal = -inf
        self.time_since_pedal = inf
        self.shift = ShiftRepresentation()
        self.time_in_song = 0
        self.abs_time_in_song = 0

        # Initialize variables for postprocessing
        self.time_kick_muted = inf
        self.time_ks_muted = inf
        self.changed_pattern = -inf

    def preprocess(self, msg):
        """
        Input: A midi message
        Effect: Updates feature list
        Output: Nothing
        """
        # Set values that are calculated once
        # Start time
        if not self.persistent_calculated:
            if msg is not None and (msg.type == 'note_on' or (msg.type == 'control_change' and msg.control == 66 and msg.value >= 64)):
                self.persistent['Start Time'] = time.time()
                self.persistent['Time Per Bar'] = time_bar
                self.persistent_calculated = True
                # For the purposes of starting pedal 66 is considered a note
                self.time_of_last_note = time.time()
                self.time_since_last_note = 0

        # Extract features
        # Velocity
        if msg is not None and msg.type == 'note_on' and msg.velocity != 0:
            if self.velocity_queue_clear:
                self.velocity_queue.clear()
                self.velocity_queue_clear = False
            self.velocity_queue.append(msg.velocity)

        # Density
        # Full range density
        self.full_range_density.set(msg, self.persistent['Start Time'])
        # Low range density
        self.low_range_density.set(msg, self.persistent['Start Time'])
        # High range density
        self.high_range_density.set(msg, self.persistent['Start Time'])

        # Time since note
        if msg is not None and msg.type == 'note_on':
            self.time_of_last_note = time.time()
            self.time_since_last_note = 0
        else:
            self.time_since_last_note = time.time() - self.time_of_last_note

        # Pedal
        if msg is not None and msg.type == 'control_change' and msg.control == 64:
            if 64 <= msg.value <= 127:
                self.pedal = True
                self.time_of_pedal = time.time()
            else:
                self.pedal = False

        # Time since pedal down
        self.time_since_pedal = time.time() - self.time_of_pedal

        # Shift
        if msg is not None and msg.type == 'note_on' and msg.velocity != 0:
            self.shift.set(msg)

        # Time in song, resets per 32 bars
        if self.persistent['Start Time'] is not None:
            self.time_in_song = (time.time() - self.persistent['Start Time']) % (32 * self.persistent['Time Per Bar'])
            self.abs_time_in_song = time.time() - self.persistent['Start Time']

        # Set manual ending
        if msg is not None and msg.type == 'control_change' and msg.control == 66 and msg.value >= 64 and self.persistent_calculated:
            if time.time() > self.persistent['Start Time'] + 3:
                self.manual_end = True

    def get_features(self, current_time):
        """
        Input: Nothing
        Output: The features at this delta t
        """

        features = dict()

        # Velocity
        features['Velocity'] = min(127, sum(self.velocity_queue))
        self.velocity_queue_clear = True

        # Density
        features['Full range density'] = self.full_range_density.get()
        features['Low range density'] = self.low_range_density.get()
        features['High range density'] = self.high_range_density.get()

        # Time since note
        features['Time since note'] = self.time_since_last_note

        # Pedal
        features['Pedal'] = self.pedal
        features['End pedal'] = self.manual_end

        # Time since pedal
        features['Time since pedal'] = self.time_since_pedal

        # Shift
        features['Current second velocity'], features['Previous second velocity'] = self.shift.get()

        # Time in song (periodic)
        features['Time in song'] = self.time_in_song

        # Absolute time in song
        features['Absolute Time in song'] = self.abs_time_in_song

        # Time in bar
        features['Time In Bar'] = self.time_in_song % time_bar

        # Time since muting
        features['Time Since Kick Muted'] = current_time - self.time_kick_muted
        features['Time Since Kick&Snare Muted'] = current_time - self.time_ks_muted

        # Drum state
        features.update(self.drum_state)

        # Return feature dict
        return features

    def postprocess(self, instructions: dict, current_time):

        # Postprocess and save pattern
        # Set pattern to 12 (no change) if there has been no change to reduce sending of unnecessary midi messages
        if instructions['Pattern'] == self.drum_state['History Pattern']:
            instructions['Pattern'] = 12
        # Set pattern to 12 if the pattern was just changed, handles a edge case
        else:
            if instructions['Pattern'] in [0,1,2,3,4,5,6,7,8,10]:
                if self.changed_pattern > current_time - 0.025:
                    instructions['Pattern'] = 12
                else:
                    self.changed_pattern = current_time
        # Save pattern
        pattern = instructions['Pattern']
        if pattern != 12 and pattern != 9 and pattern != 13 and pattern != 14:
            self.drum_state['History Pattern'] = instructions['Pattern']

        # Save time of muting
        if 'Mute_Kick' not in instructions: instructions['Mute_Kick'] = -1
        if 'Mute_Snare' not in instructions: instructions['Mute_Snare'] = -1
        if instructions['Mute_Kick'] == 1 and self.drum_state['History Mute Kick'] == 0:
            self.time_kick_muted = current_time
        if instructions['Mute_Snare'] == 1 and instructions['Mute_Kick'] == 1 and (
                (self.drum_state['History Mute Kick'] == 0 or self.drum_state['History Mute Kick'] == 1)
                and self.drum_state['History Mute Snare'] == 0):
            self.time_ks_muted = current_time

        # Save which parts of the kit are muted
        if instructions['Mute_Kick'] != -1:
            self.drum_state['History Mute Kick'] = instructions['Mute_Kick']
        if instructions['Mute_Snare'] != -1:
            self.drum_state['History Mute Snare'] = instructions['Mute_Snare']

        # Save intensity
        self.drum_state['History Intensity'] = instructions['Intensity']

        # Save complexity
        self.drum_state['History_Complexity'] = instructions['Complexity']

        # Save mode and then delete it from instructions
        self.drum_state['History Mode'] = instructions['Mode']
        del instructions['Mode']


class DensityRepresentation:

    def __init__(self, note_range: range, complexity_slots=16):
        self.array = [0] * complexity_slots
        self.lock = -1
        self.time_per_bar = time_bar
        self.range = note_range
        self.complexity_slots = complexity_slots

    def set(self, msg, start_time):
        if start_time is not None:
            offset = time.time() - start_time
            offset = offset % self.time_per_bar
            position = int(offset * (self.complexity_slots / self.time_per_bar))

            # If a note was played
            if msg is not None and msg.type == 'note_on' and msg.note in self.range:
                self.array[position] = 1
                self.lock = position

            # If a note was not played and the slot is not locked
            elif self.lock != position:
                self.array[position] = 0
                self.lock = -1

    def get(self):
        slots_full = sum(self.array)
        density = (slots_full / self.complexity_slots) * 127.0
        return density

class ShiftRepresentation:
    """
    Used to calculate sudden shifts in velocity
    """
    def __init__(self, window=3):
        self.window = window
        self.array = []

    def set(self, msg):

        current_time = time.time()
        self.array.insert(0, (msg.velocity, current_time))
        self.array = [x for x in self.array if current_time - x[1] < self.window]

    def get(self):

        current_time = time.time()
        current_second = [x[0] for x in self.array if current_time - x[1] <= self.window / 2]
        if len(current_second) != 0:
            current_second_avg = sum(current_second) / len(current_second)
        else:
            current_second_avg = 0

        previous_second = [x[0] for x in self.array if current_time - x[1] > self.window / 2]
        if len(previous_second) != 0:
            previous_second_avg = sum(previous_second) / len(previous_second)
        else:
            previous_second_avg = 0

        return current_second_avg, previous_second_avg


