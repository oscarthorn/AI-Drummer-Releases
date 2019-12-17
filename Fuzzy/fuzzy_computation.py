"""
This module is the brains of the AiDrummer project
"""

from collections import deque
from sys import float_info as f
from time import time

from math import inf
from scipy.stats import linregress

from Fuzzy import fuzzy_logic as logic
from Fuzzy.Information_processing import time_bar
from Fuzzy.settings import delta
from Fuzzy.utility import RunningLinearRegression

e = f.epsilon * 1000


class Agent:

    def __init__(self, custom_rules):
        self.mode = Mode()
        self.pattern = Pattern(custom_rules)
        self.intensity = Intensity(custom_rules)
        self.complexity = Complexity(custom_rules)
        self.drum_state = {'History Mode': 0,
                           'History Intensity': 0,
                           'History_Complexity': 0,
                           'History Pattern': 11,
                           'History Mute Kick': 0,
                           'History Mute Snare': 0}

    def compute(self, features):

        # New instruction set
        instructions = {}

        # Create a cache
        cache = dict()
        cache['Antecedents'] = {}
        cache['Consequents'] = {}

        # Computations
        # Intensity
        intensity = self.intensity(features['Average Velocity'], features['Sudden Shift'],
                                   features['Time Since Shift Up'], features['Time Since Shift Down'], features['Time since note'], cache)
        instructions.update(intensity)

        # Complexity
        complexity = self.complexity(features['Full Average Density'], features['Low Average Density'],
                                     features['High Average Density'],
                                     features['Pedal'], intensity['Intensity'], cache)
        instructions.update(complexity)

        # Mode
        mode = self.mode(features['Time since note'], features['End pedal'], cache)
        instructions.update(mode)

        # Pattern and muting
        pattern_muting = self.pattern(mode['Mode'], features['History Mode'], features['History Pattern'], intensity['Intensity'],
                                      complexity['Complexity'], features['Time in song'], features['Slow Average Velocity'],
                                      features['Hype'], features['High Average Density'], features['Time since pedal'],
                                      features['History Mute Kick'], features['History Mute Snare'], features['Low Average Density'],
                                      features['Time In Bar'], features['Time Since Kick Muted'], features['Time Since Kick&Snare Muted'],
                                      features['Time'], cache)
        instructions.update(pattern_muting)

        # Add more computations here

        # Return instructions
        return instructions, cache


class Mode:
    """
    Determines if the drums should be playing
    Input: Time since note
    Output: New mode
    """
    def __init__(self):
        # Initialize fuzzy logic
        ##############
        # Antecedent #
        ##############
        Time_since_note = logic.Antecedent('Time_since_note', (0, inf))
        Time_since_note['Short'] = logic.AntecedentTerm('Short', [(0, 1), (4, 1), (6, 0)])

        Manual_end = logic.Antecedent('Manual_end', (0, 1))
        Manual_end['True'] = logic.AntecedentTerm('True', mf=[1], type_mf='Single')

        ##############
        # Consequent #
        ##############
        Mode = logic.Consequent('Mode', (0, 127), output_type='Discrete')
        Mode['Play'] = logic.ConsequentTerm('Play', 1)
        Mode['Stop'] = logic.ConsequentTerm('Stop', 0)

        #########
        # Rules #
        #########
        Rule1 = logic.Rule(Time_since_note['Short'] & (~ Manual_end['True']), Mode['Play'])
        Rule2 = logic.Rule((~ Time_since_note['Short']) | Manual_end['True'], Mode['Stop'])

        self.control = logic.FuzzyControl([Rule1, Rule2])

    def __call__(self, Time_since_note, end_pedal, cache):

        # Compute new mode
        return self.control.compute({'Time_since_note': Time_since_note, 'Manual_end': end_pedal},
                                    use_functions=True, cache=cache)


class Pattern:
    """
    Determines which pattern the drums should play


    Pattern mapping
    Pattern_Output = {0: 'Intro-To-Chorus-1',
                          1: 'Fill-To-Chorus-1',
                          2: 'Fill-To-Chorus-2',
                          3: 'Fill-To-Chorus-3',
                          4: 'Fill-To-Chorus-4',
                          5: 'Fill-To-Chorus-5',
                          6: 'Fill-To-Chorus-6',
                          7: 'Fill-To-Chorus-7',
                          8: 'Chorus-1',
                          9: 'Fill-1',
                          10: 'Outro',
                          11: 'None',
                          12: 'No-Change',
                          13: 'Fill-4',
                          14: 'Fill-3'}

    Unmute mapping
    Unmute_output = {3: 'Snare'
                     2: 'Kick-and-Snare'
                     1: 'Kick',
                     0: 'None'}

    Mute mapping
    Mute_output = {2: 'Kick-and-Snare'
                   1: 'Kick',
                   0: 'None'}

    Mode_output = {1: 'Play',
                   0: 'Stop'}
    """
    def __init__(self, custom_rules):

        self.bar8regression = RunningLinearRegression()
        self.bar8regression.update(time(), 0)
        self.intensities3sec = deque(maxlen=int(3 / delta))
        self.intensities3sec.append([time(), 0])

        # Initialize fuzzy logic
        ##############
        # Antecedent #
        ##############
        Mode = logic.Antecedent('Mode', (0, 1))
        Mode['Play'] = logic.AntecedentTerm('Play', mf=[1], type_mf='Single')
        Mode['Stop'] = logic.AntecedentTerm('Stop', mf=[0], type_mf='Single')

        History_Mode = logic.Antecedent('History_Mode', (0, 1))
        History_Mode['Play'] = logic.AntecedentTerm('Play', mf=[1], type_mf='Single')
        History_Mode['Stop'] = logic.AntecedentTerm('Stop', mf=[0], type_mf='Single')

        History_Pattern = logic.Antecedent('History_Pattern', (0, 15))
        History_Pattern['Intro-To-Chorus-1'] = logic.AntecedentTerm('Intro-To-Chorus-1', mf=[0], type_mf='Single')
        History_Pattern['Fill-To-Chorus-1'] = logic.AntecedentTerm('Fill-To-Chorus-1', mf=[1], type_mf='Single')
        History_Pattern['Fill-To-Chorus-2'] = logic.AntecedentTerm('Fill-To-Chorus-2', mf=[2], type_mf='Single')
        History_Pattern['Fill-To-Chorus-3'] = logic.AntecedentTerm('Fill-To-Chorus-3', mf=[3], type_mf='Single')
        History_Pattern['Fill-To-Chorus-4'] = logic.AntecedentTerm('Fill-To-Chorus-4', mf=[4], type_mf='Single')
        History_Pattern['Fill-To-Chorus-5'] = logic.AntecedentTerm('Fill-To-Chorus-5', mf=[5], type_mf='Single')
        History_Pattern['Fill-To-Chorus-6'] = logic.AntecedentTerm('Fill-To-Chorus-6', mf=[6], type_mf='Single')
        History_Pattern['Fill-To-Chorus-7'] = logic.AntecedentTerm('Fill-To-Chorus-7', mf=[7], type_mf='Single')
        History_Pattern['Chorus-1'] = logic.AntecedentTerm('Chorus-1', mf=[8], type_mf='Single')
        History_Pattern['Outro'] = logic.AntecedentTerm('Outro', mf=[10], type_mf='Single')
        History_Pattern['None'] = logic.AntecedentTerm('None', mf=[11], type_mf='Single')

        History_Mute_Kick = logic.Antecedent('History_Mute_Kick', (0, 1))
        History_Mute_Kick['True'] = logic.AntecedentTerm('True', mf=[1], type_mf='Single')
        History_Mute_Kick['False'] = logic.AntecedentTerm('False', mf=[0], type_mf='Single')

        History_Mute_Snare = logic.Antecedent('History_Mute_Snare', (0, 1))
        History_Mute_Snare['True'] = logic.AntecedentTerm('True', mf=[1], type_mf='Single')
        History_Mute_Snare['False'] = logic.AntecedentTerm('False', mf=[0], type_mf='Single')

        Complexity = logic.Antecedent('Complexity', (0, 127))
        Complexity.auto_generate_terms(6, ['Low', 'Mid-Low', 'Middle', 'Mid-High', 'High', 'Max'])

        Intensity = logic.Antecedent('Intensity', (0, 127))
        Intensity.auto_generate_terms(6, ['Low', 'Mid-Low', 'Middle', 'Mid-High', 'High', 'Max'])

        # Gives the start of the bar
        Bar = logic.Antecedent('Bar', (0, inf))
        mf8 = [(7 * time_bar - e, 0), (7 * time_bar, 1), (7 * time_bar + .025, 1), (7 * time_bar + .025 + e, 0)]
        mf16 = [(15 * time_bar - e, 0), (15 * time_bar, 1), (15 * time_bar + .025, 1), (15 * time_bar + .025 + e, 0)]
        mf24 = [(23 * time_bar - e, 0), (23 * time_bar, 1), (23 * time_bar + .025, 1), (23 * time_bar + .025 + e, 0)]
        mf32 = [(31 * time_bar - e, 0), (31 * time_bar, 1), (31 * time_bar + .025, 1), (31 * time_bar + .025 + e, 0)]
        Bar['8th'] = logic.AntecedentTerm('8th', mf8)
        Bar['16th'] = logic.AntecedentTerm('16th', mf16)
        Bar['24th'] = logic.AntecedentTerm('24th', mf24)
        Bar['32th'] = logic.AntecedentTerm('32th', mf32)
        # Gives the a time during the second half of the bar
        mf4 = [(5 * time_bar - (time_bar/7) - e, 0), (5 * time_bar - (time_bar / 7), 1), (5 * time_bar - 0.1, 1), (5 * time_bar, 0)]
        mf12 = [(13 * time_bar - (time_bar / 7) - e, 0), (13 * time_bar - (time_bar / 7), 1), (13 * time_bar - 0.1, 1), (13 * time_bar, 0)]
        mf20 = [(21 * time_bar - (time_bar / 7) - e, 0), (21 * time_bar - (time_bar / 7), 1), (21 * time_bar - 0.1, 1), (21 * time_bar, 0)]
        mf28 = [(29 * time_bar - (time_bar / 7) - e, 0), (29 * time_bar - (time_bar / 7), 1), (29 * time_bar - 0.1, 1), (29 * time_bar, 0)]
        Bar['End-4th'] = logic.AntecedentTerm('End-4th', mf4)
        Bar['End-12th'] = logic.AntecedentTerm('End-12th', mf12)
        Bar['End-20th'] = logic.AntecedentTerm('End-20th', mf20)
        Bar['End-28th'] = logic.AntecedentTerm('End-28th', mf28)

        Change_Intensity = logic.Antecedent('Change_Intensity', (-inf, inf))
        Change_Intensity['Up'] = logic.AntecedentTerm('Up', mf=[(0, 0), (1, 1)])
        Change_Intensity['Down'] = logic.AntecedentTerm('Down', mf=[(-1, 1), (0, 0)])
        Change_Intensity['Same'] = logic.AntecedentTerm('Same', mf=[(-1, 0), (0, 1), (1, 0)])

        Change_Intensity_Short = logic.Antecedent('Change_Intensity_Short', (-inf, inf))
        Change_Intensity_Short['Up'] = logic.AntecedentTerm('Up', mf=[(0, 0), (3, 1)])
        Change_Intensity_Short['Down'] = logic.AntecedentTerm('Down', mf=[(-3, 1), (0, 0)])
        Change_Intensity_Short['Same'] = logic.AntecedentTerm('Same', mf=[(-3, 0), (0, 1), (3, 0)])

        Hype = logic.Antecedent('Hype', (0, 1))
        Hype['Coming'] = logic.AntecedentTerm('Coming', [(0, 0), (1, 1)])

        Time_In_Bar = logic.Antecedent('Time_In_Bar', (0, time_bar))
        last_quarter = [(time_bar - (time_bar / 4) - e, 0), (time_bar - (time_bar / 4), 1), (time_bar, 1)]
        Time_In_Bar['Last-Quarter'] = logic.AntecedentTerm('Last-Quarter', last_quarter)

        Time_Since_Kick_Muted = logic.Antecedent('Time_Since_Kick_Muted', (-inf, inf))
        Time_Since_Kick_Muted['Long'] = logic.AntecedentTerm('Long', mf=[(time_bar, 0), (4*time_bar, 1)])

        Time_Since_KS_Muted = logic.Antecedent('Time_Since_KS_Muted', (-inf, inf))
        Time_Since_KS_Muted['Very-Long'] = logic.AntecedentTerm('Very-Long', mf=[(time_bar, 0), (16*time_bar, 1)])

        High_Avg_Density = logic.Antecedent('High_Avg_Density', (0, 127))
        High_Avg_Density.auto_generate_terms(7, ['None', 'Low', 'Mid-Low', 'Middle', 'Mid-High', 'High', 'Max'])

        Low_Avg_Density = logic.Antecedent('Low_Avg_Density', (0, 127))
        Low_Avg_Density.auto_generate_terms(7, ['None', 'Low', 'Mid-Low', 'Middle', 'Mid-High', 'High', 'Max'])

        Time_Since_Pedal = logic.Antecedent('Time_Since_Pedal', (0, inf))
        Time_Since_Pedal['Very-Short'] = logic.AntecedentTerm('Very-Short', [(0, 1), (2, 0)])

        ##############
        # Consequent #
        ##############
        Pattern = logic.Consequent('Pattern', (0, 14), default_output=12,
                                   output_type='Discrete')
        Pattern['Intro-To-Chorus-1'] = logic.ConsequentTerm('Intro-To-Chorus-1', 0)
        Pattern['Fill-To-Chorus-1'] = logic.ConsequentTerm('Fill-To-Chorus-1', 1)
        Pattern['Fill-To-Chorus-2'] = logic.ConsequentTerm('Fill-To-Chorus-2', 2)
        Pattern['Fill-To-Chorus-3'] = logic.ConsequentTerm('Fill-To-Chorus-3', 3)
        Pattern['Fill-To-Chorus-4'] = logic.ConsequentTerm('Fill-To-Chorus-4', 4)
        Pattern['Fill-To-Chorus-5'] = logic.ConsequentTerm('Fill-To-Chorus-5', 5)
        Pattern['Fill-To-Chorus-6'] = logic.ConsequentTerm('Fill-To-Chorus-6', 6)
        Pattern['Fill-To-Chorus-7'] = logic.ConsequentTerm('Fill-To-Chorus-7', 7)
        Pattern['Chorus-1'] = logic.ConsequentTerm('Chorus-1', 8)
        Pattern['Fill-1'] = logic.ConsequentTerm('Fill-1', 9)
        Pattern['Outro'] = logic.ConsequentTerm('Outro', 10)
        Pattern['None'] = logic.ConsequentTerm('None', 11)
        Pattern['Fill-4'] = logic.ConsequentTerm('Fill-4', 13)
        Pattern['Fill-3'] = logic.ConsequentTerm('Fill-3', 14)

        Mute_Kick = logic.Consequent('Mute_Kick', (-1, 1), default_output=-1, output_type='Discrete')
        Mute_Kick['True'] = logic.ConsequentTerm('True', 1)
        Mute_Kick['False'] = logic.ConsequentTerm('False', 0)
        Mute_Kick['No-Change'] = logic.ConsequentTerm('No-Change', -1)

        Mute_Snare = logic.Consequent('Mute_Snare', (-1, 1), default_output=-1, output_type='Discrete')
        Mute_Snare['True'] = logic.ConsequentTerm('True', 1)
        Mute_Snare['False'] = logic.ConsequentTerm('False', 0)
        Mute_Snare['No-Change'] = logic.ConsequentTerm('No-Change', -1)

        #########
        # Rules #
        #########
        if custom_rules is None:
            # Starting and stopping
            Start1 = logic.Rule(History_Pattern['None'] & History_Mode['Stop'] & Mode['Play'], Pattern['Intro-To-Chorus-1'])
            Start2 = logic.Rule(History_Mode['Play'] & Mode['Stop'], Pattern['Outro'])
            Start3 = logic.Rule(History_Pattern['None'] & History_Mode['Stop'] & Mode['Stop'], Pattern['None'])

            # Deciding pattern
            # Antecedent set for for every 8th bar
            BarMod8 = (Bar['8th'] | Bar['16th'] | Bar['24th'] | Bar['32th'])

            # Pattern is Fill-To-Chorus-1
            Pattern1up = logic.Rule((History_Pattern['Intro-To-Chorus-1'] | History_Pattern['Fill-To-Chorus-1'] | History_Pattern['Chorus-1'])
                                    & BarMod8
                                    & (Change_Intensity['Up']
                                       | (Change_Intensity['Same'] & (Intensity['Mid-High'] | Intensity['High'] | Intensity['Max'])))
                                    , Pattern['Fill-To-Chorus-2'])

            Pattern1down = logic.Rule((History_Pattern['Intro-To-Chorus-1'] | History_Pattern['Fill-To-Chorus-1'] | History_Pattern['Chorus-1'])
                                      & BarMod8
                                      & (Change_Intensity['Down'] | (Change_Intensity['Same'] & (Intensity['Low'] | Intensity['Mid-Low'])))
                                      , Pattern['Fill-4'])

            Pattern1same = logic.Rule((History_Pattern['Intro-To-Chorus-1'] | History_Pattern['Fill-To-Chorus-1'] | History_Pattern['Chorus-1'])
                                      & BarMod8
                                      & Change_Intensity['Same']
                                      & ~(Intensity['Low'] | Intensity['Mid-High'] | Intensity['High'] | Intensity['Max'])
                                      , Pattern['Fill-4'])

            # ... Fill-To-Chorus-2
            Pattern2up = logic.Rule(History_Pattern['Fill-To-Chorus-2']
                                    & BarMod8
                                    & (Change_Intensity['Up']
                                       | (Change_Intensity['Same'] & (Intensity['Mid-High'] | Intensity['High'] | Intensity['Max'])))
                                    , Pattern['Fill-To-Chorus-3'])

            Pattern2down = logic.Rule(History_Pattern['Fill-To-Chorus-2']
                                      & BarMod8
                                      & (Change_Intensity['Down'] | (Change_Intensity['Same'] & Intensity['Low']))
                                      , Pattern['Fill-To-Chorus-1'])

            Pattern2same = logic.Rule(History_Pattern['Fill-To-Chorus-2']
                                      & BarMod8
                                      & Change_Intensity['Same']
                                      & ~(Intensity['Low'] | Intensity['Mid-High'] | Intensity['High'] | Intensity['Max'])
                                      , Pattern['Fill-4'])
            # ... Fill-to-Chorus-3
            Pattern3up = logic.Rule(History_Pattern['Fill-To-Chorus-3']
                                    & BarMod8
                                    & (Change_Intensity['Up']
                                       | (Change_Intensity['Same'] & (Intensity['Mid-High'] | Intensity['High'] | Intensity['Max'])))
                                    , Pattern['Fill-To-Chorus-4'])

            Pattern3down = logic.Rule(History_Pattern['Fill-To-Chorus-3']
                                      & BarMod8
                                      & (Change_Intensity['Down'] | (Change_Intensity['Same'] & Intensity['Low']))
                                      , Pattern['Fill-To-Chorus-2'])

            Pattern3same = logic.Rule(History_Pattern['Fill-To-Chorus-3']
                                      & BarMod8
                                      & Change_Intensity['Same']
                                      & ~(Intensity['Low'] | Intensity['Mid-High'] | Intensity['High'] | Intensity['Max'])
                                      , Pattern['Fill-4'])

            # ... Fill-to-Chorus-4
            Pattern4up = logic.Rule(History_Pattern['Fill-To-Chorus-4']
                                    & BarMod8
                                    & (Change_Intensity['Up'] | (Change_Intensity['Same'] & (Intensity['High'] | Intensity['Max'])))
                                    & ~(History_Mute_Snare['True'])
                                    , Pattern['Fill-To-Chorus-5'])

            Pattern4down = logic.Rule(History_Pattern['Fill-To-Chorus-4']
                                      & BarMod8
                                      & (Change_Intensity['Down'] | (Change_Intensity['Same'] & Intensity['Low']))
                                      , Pattern['Fill-To-Chorus-3'])
            Pattern4same = logic.Rule(History_Pattern['Fill-To-Chorus-4']
                                      & BarMod8
                                      & Change_Intensity['Same']
                                      & ~(Intensity['Low'] | Intensity['High'] | Intensity['Max'])
                                      , Pattern['Fill-4'])

            # ... Fill-to-Chorus-5
            Pattern5up = logic.Rule(History_Pattern['Fill-To-Chorus-5']
                                    & BarMod8
                                    & (Change_Intensity['Up'] | (Change_Intensity['Same'] & (Intensity['High'] | Intensity['Max'])))
                                    , Pattern['Fill-To-Chorus-6'])

            Pattern5down = logic.Rule(History_Pattern['Fill-To-Chorus-5']
                                      & BarMod8
                                      & (Change_Intensity['Down']
                                         | (Change_Intensity['Same'] & (Intensity['Low'] | Intensity['Mid-Low']))
                                         | (History_Mute_Snare['True']))
                                      , Pattern['Fill-To-Chorus-4'])

            Pattern5same = logic.Rule(History_Pattern['Fill-To-Chorus-5']
                                      & BarMod8
                                      & Change_Intensity['Same']
                                      & ~(Intensity['Low'] | Intensity['Mid-Low'] | Intensity['High'] | Intensity['Max'])
                                      , Pattern['Fill-4'])

            # ... Fill-to-Chorus-6
            Pattern6up = logic.Rule(History_Pattern['Fill-To-Chorus-6']
                                    & BarMod8
                                    & (Change_Intensity['Up'] | (Change_Intensity['Same'] & (Intensity['High'] | Intensity['Max'])))
                                    , Pattern['Fill-To-Chorus-7'])

            Pattern6down = logic.Rule(History_Pattern['Fill-To-Chorus-6']
                                      & BarMod8
                                      & (Change_Intensity['Down']
                                         | (Change_Intensity['Same'] & (Intensity['Low'] | Intensity['Mid-Low']))
                                         | (History_Mute_Snare['True']))
                                      , Pattern['Fill-To-Chorus-5'])

            Pattern6same = logic.Rule(History_Pattern['Fill-To-Chorus-6']
                                      & BarMod8 & Change_Intensity['Same']
                                      & ~(Intensity['Low'] | Intensity['Mid-Low'] | Intensity['High'] | Intensity['Max'])
                                      , Pattern['Fill-4'])

            # ... Fill-to-Chorus-7
            Pattern7up = logic.Rule(History_Pattern['Fill-To-Chorus-7']
                                    & BarMod8
                                    & (Change_Intensity['Up'] | (Change_Intensity['Same'] & (Intensity['High'] | Intensity['Max'])))
                                    , Pattern['Fill-4'])

            Pattern7down = logic.Rule(History_Pattern['Fill-To-Chorus-7']
                                      & BarMod8
                                      & (Change_Intensity['Down']
                                         | (Change_Intensity['Same'] & (Intensity['Low'] | Intensity['Mid-Low']))
                                         | (History_Mute_Snare['True']))
                                      , Pattern['Fill-To-Chorus-6'])

            Pattern7same = logic.Rule(History_Pattern['Fill-To-Chorus-7']
                                      & BarMod8
                                      & Change_Intensity['Same']
                                      & ~(Intensity['Low'] | Intensity['Mid-Low'] | Intensity['High'] | Intensity['Max'])
                                      , Pattern['Fill-4'])

            # Determine Fills
            EndBars = (Bar['End-4th'] | Bar['End-12th'] | Bar['End-20th'] | Bar['End-28th'])

            Fill = logic.Rule(EndBars & ~Mode['Stop'] & ~(Complexity['Low'] | Complexity['Mid-Low']), Pattern['Fill-1'])
            Fill2 = logic.Rule(~(History_Mute_Snare['False'] & History_Mute_Kick['False']) & EndBars & ~Mode['Stop'], Pattern['Fill-4'])

            # Determine Muting
            # If intensity is low, pedal is down and high register is played then chorus-1
            Softdrums2 = logic.Rule((History_Mute_Snare['False'] & History_Mute_Kick['False'])
                                    & Change_Intensity_Short['Down']
                                    & ~(Intensity['Max'] | Intensity['High'])
                                    & ~(High_Avg_Density['None'] | High_Avg_Density['Low']), Mute_Kick['True'])

            Softdrums3a = logic.Rule((~High_Avg_Density['None'] & ~High_Avg_Density['Max'])
                                     & Time_Since_Pedal['Very-Short']
                                     & (Intensity['Low']
                                        | Intensity['Mid-Low']
                                        | Intensity['Middle']
                                        | (Intensity['Mid-High'] & Low_Avg_Density['None']))
                                     & Change_Intensity_Short['Down']
                                     & ~(History_Mute_Snare['True'] & History_Mute_Kick['True'])
                                     & ~History_Mute_Snare['True'], Mute_Kick['True'])

            Softdrums3b = logic.Rule((~High_Avg_Density['None'] & ~High_Avg_Density['Max'])
                                     & Time_Since_Pedal['Very-Short']
                                     & (Intensity['Low']
                                        | Intensity['Mid-Low']
                                        | Intensity['Middle']
                                        | (Intensity['Mid-High'] & Low_Avg_Density['None']))
                                     & Change_Intensity_Short['Down']
                                     & ~(History_Mute_Snare['True'] & History_Mute_Kick['True'])
                                     & ~History_Mute_Snare['True'], Mute_Snare['True'])

            Softdrums4a = logic.Rule(((History_Mute_Snare['True'] & History_Mute_Kick['True']) | History_Mute_Snare['True'])
                                     & Change_Intensity_Short['Up']
                                     & ~(Intensity['Low']
                                         | Intensity['Mid-Low']
                                         | ((Intensity['Middle'] | Intensity['Mid-High']) & (Low_Avg_Density['None'] | Low_Avg_Density['Low']))
                                         | (Intensity['High'] & Low_Avg_Density['None'])), Mute_Kick['False'])

            Softdrums4b = logic.Rule(((History_Mute_Snare['True'] & History_Mute_Kick['True']) | History_Mute_Snare['True'])
                                     & Change_Intensity_Short['Up']
                                     & ~(Intensity['Low']
                                         | Intensity['Mid-Low']
                                         | ((Intensity['Middle'] | Intensity['Mid-High']) & (Low_Avg_Density['None'] | Low_Avg_Density['Low']))
                                         | (Intensity['High'] & Low_Avg_Density['None'])), Mute_Snare['False'])

            Softdrums5 = logic.Rule(Time_Since_Kick_Muted['Long']
                                    & (History_Mute_Kick['True'] & History_Mute_Snare['False'])
                                    & ~Change_Intensity_Short['Down']
                                    | (History_Mute_Kick['True'] & (Intensity['Max'] | Intensity['High'])), Mute_Kick['False'])

            Softdrums6 = logic.Rule(Time_Since_KS_Muted['Very-Long']
                                    & (History_Mute_Snare['True'] & History_Mute_Kick['True'])
                                    & Change_Intensity_Short['Up'],
                                    Mute_Kick['False'])

            # Anticipating hype
            Hype_rule = logic.Rule(Hype['Coming'] & Time_In_Bar['Last-Quarter'], Pattern['Fill-3'])

            rules = [Start1, Start2, Start3, Pattern1up, Pattern1down, Pattern2down, Pattern2up, Pattern3down,
                     Pattern3up, Pattern4down, Pattern4up, Pattern5down, Pattern5up, Pattern6down, Pattern6up,
                     Pattern7down, Pattern7up, Fill, Fill2, Hype_rule, Softdrums2, Softdrums3a, Softdrums3b,
                     Softdrums4a, Softdrums4b, Softdrums5, Softdrums6, Pattern1same, Pattern2same, Pattern3same,
                     Pattern4same, Pattern5same, Pattern6same, Pattern7same]
        else:
            assert isinstance(custom_rules, dict)
            assert isinstance(custom_rules['Pattern'], list)
            rules = []
            for rule in custom_rules['Pattern']:
                rules.append(eval("logic.Rule("+rule+")"))

        self.control = logic.FuzzyControl(rules)

    def __call__(self, Mode, History_Mode, History_Pattern, Intensity, Complexity, Time_In_Song, SlowVelocityAvg, Hype, High_Avg_Density,
                 Time_Since_Pedal, History_Mute_Kick, History_Mute_Snare, Low_Avg_Density, Time_In_Bar, Time_Since_Kick_Muted,
                 Time_Since_KS_Muted, current_time, cache):

        # Calculate regressions on the intensity
        # Moving window of the last three seconds
        self.intensities3sec.appendleft([current_time, Intensity])
        I_Slope_3sec, _, _, _, _ = linregress(self.intensities3sec)

        # Running regression that resets every 8 bars
        self.bar8regression.update(current_time, Intensity)
        I_slope_8bar = self.bar8regression.getSlope()
        # Reset regression every 8 bars
        offset = Time_In_Song % (8 * time_bar)
        if 0.015 < offset < 0.030:
            self.bar8regression.reset(current_time, Intensity)

        # Compute new pattern
        input_dict = {'Mode': Mode, 'History_Mode': History_Mode, 'History_Pattern': History_Pattern,
                                    'Intensity': Intensity, 'Complexity': Complexity, 'Bar': Time_In_Song,
                                    'Change_Intensity': I_slope_8bar, 'Time_In_Bar': Time_In_Bar, 'Hype': Hype,
                                    'High_Avg_Density': High_Avg_Density, 'Time_Since_Pedal': Time_Since_Pedal,
                                    'History_Mute_Kick': History_Mute_Kick, 'History_Mute_Snare': History_Mute_Snare,
                                    'Change_Intensity_Short': I_Slope_3sec, 'Time_Since_Kick_Muted': Time_Since_Kick_Muted,
                                    'Time_Since_KS_Muted': Time_Since_KS_Muted, 'Low_Avg_Density': Low_Avg_Density}
        pattern = self.control.compute(input_dict, cache=cache)

        return pattern


class Intensity:

    def __init__(self, custom_rules):
        # Initialize fuzzy logic
        ##############
        # Antecedent #
        ##############
        # Time since note
        Time_Since_Note = logic.Antecedent('Time_Since_Note', (0, inf))
        Time_Since_Note['Long'] = logic.AntecedentTerm('Long', [(2, 0), (8, 1), (10, 1)])

        # Avg Velocity
        Avg_Velocity = logic.Antecedent('Avg_Velocity', (0, 127))
        Avg_Velocity.auto_generate_terms(6, ['Low', 'Mid-Low', 'Middle', 'Mid-High', 'High', 'Max'])

        # Sudden Shift
        Sudden_Shift = logic.Antecedent('Sudden_Shift', (-1, 1))
        Sudden_Shift.auto_generate_terms(3, ['Down', 'None', 'Up'])

        #Time since shift
        Short_Time = 4.5
        Time_Since_Shift_Up = logic.Antecedent('Time_Since_Shift_Up', (0, inf))
        Time_Since_Shift_Up['Short'] = logic.AntecedentTerm('Short', [(0, 1), (1, 1), (Short_Time, 0)])

        Time_Since_Shift_Down = logic.Antecedent('Time_Since_Shift_Down', (0, inf))
        Time_Since_Shift_Down['Short'] = logic.AntecedentTerm('Short', [(0, 1), (1, 1), (Short_Time, 0)])

        ##############
        # Consequent #
        ##############
        # Intensity
        Intensity = logic.Consequent('Intensity', (0, 127), default_output=0)
        Intensity.auto_generate_terms(6, ['Low', 'Mid-Low', 'Middle', 'Mid-High', 'High', 'Max'])

        #########
        # Rules #
        #########
        # Part of rule
        rule_part = ~(Sudden_Shift['Down'] | Sudden_Shift['Up'] | Time_Since_Shift_Down['Short'] | Time_Since_Shift_Up['Short'])

        # Rules
        if custom_rules is None:
            Rule1 = logic.Rule(Avg_Velocity['Low'] | Sudden_Shift['Down'] | Time_Since_Shift_Down['Short'] |
                               Time_Since_Note['Long'], Intensity['Low'])
            Rule2 = logic.Rule(Avg_Velocity['Mid-Low'] & rule_part, Intensity['Mid-Low'])
            Rule3 = logic.Rule(Avg_Velocity['Middle'] & rule_part, Intensity['Middle'])
            Rule4 = logic.Rule(Avg_Velocity['Mid-High'] & rule_part, Intensity['Mid-High'])
            Rule5 = logic.Rule(Avg_Velocity['High'] & rule_part, Intensity['High'])
            Rule6 = logic.Rule(Avg_Velocity['Max'] | Sudden_Shift['Up'] | Time_Since_Shift_Up['Short'], Intensity['Max'])
            rules = [Rule1, Rule2, Rule3, Rule4, Rule5, Rule6]
        else:
            assert isinstance(custom_rules, dict)
            assert isinstance(custom_rules['Intensity'], list)
            rules = []
            for rule in custom_rules['Intensity']:
                rules.append(eval("logic.Rule("+rule+")"))

        self.control = logic.FuzzyControl(rules)

    def __call__(self, Avg_Velocity, Sudden_Shift, Time_Since_Shift_Up, Time_Since_Shift_Down, Time_since_note, cache):

        # Compute intensity
        intensity = self.control.compute({'Avg_Velocity': Avg_Velocity, 'Sudden_Shift': Sudden_Shift,
                                          'Time_Since_Shift_Up': Time_Since_Shift_Up,
                                          'Time_Since_Shift_Down': Time_Since_Shift_Down,
                                          'Time_Since_Note': Time_since_note}, cache=cache)

        return intensity


class Complexity:

    def __init__(self, custom_rules):
        # Initialize fuzzy logic
        ##############
        # Antecedent #
        ##############
        Full_Avg_Density = logic.Antecedent('Full_Avg_Density', (0, 127))
        Full_Avg_Density.auto_generate_terms(6, ['Low', 'Mid-Low', 'Middle', 'Mid-High', 'High', 'Max'])

        Low_Avg_Density = logic.Antecedent('Low_Avg_Density', (0, 127))
        Low_Avg_Density.auto_generate_terms(6, ['Low', 'Mid-Low', 'Middle', 'Mid-High', 'High', 'Max'])

        High_Avg_Density = logic.Antecedent('High_Avg_Density', (0, 127))
        High_Avg_Density.auto_generate_terms(4, ['Low', 'Middle', 'High', 'Max'])

        Pedal = logic.Antecedent('Pedal', (0, 1))
        Pedal['Down'] = logic.AntecedentTerm('Down', mf=[1], type_mf='Single')
        Pedal['Up'] = logic.AntecedentTerm('Up', mf=[0], type_mf='Single')

        Intensity = logic.Antecedent('Intensity', (0, 127))
        Intensity.auto_generate_terms(6, ['Low', 'Mid-Low', 'Middle', 'Mid-High', 'High', 'Max'])

        ##############
        # Consequent #
        ##############
        Complexity = logic.Consequent('Complexity', (0, 127), default_output=0)
        Complexity.auto_generate_terms(6, ['Low', 'Mid-Low', 'Middle', 'Mid-High', 'High', 'Max'])

        #########
        # Rules #
        #########
        if custom_rules is None:
            Rule1 = logic.Rule((Low_Avg_Density['Low'] &
                                ~(High_Avg_Density['Middle'] | High_Avg_Density['High'] | High_Avg_Density['Max']))
                               | (High_Avg_Density['Low'] & Low_Avg_Density['Low'])
                               | (Pedal['Down'] & ~(Intensity['Max'] | Intensity['High'] | Intensity['Mid-High'] | Intensity['Middle']))
                               , Complexity['Low'])

            Rule2 = logic.Rule((Low_Avg_Density['Mid-Low'] & ~(High_Avg_Density['High'] | High_Avg_Density['Max']))
                               | (High_Avg_Density['Middle'] & (Low_Avg_Density['Low'] | Low_Avg_Density['Mid-Low']))
                               , Complexity['Mid-Low'])

            Rule3 = logic.Rule((Low_Avg_Density['Middle'] & ~(High_Avg_Density['Max'])
                                | (High_Avg_Density['High'] & (Low_Avg_Density['Low'] | Low_Avg_Density['Mid-Low'] |
                                   Low_Avg_Density['Middle']))), Complexity['Middle'])

            Rule4 = logic.Rule(Low_Avg_Density['Mid-High'] | (High_Avg_Density['Max'] & (Low_Avg_Density['Low']
                               | Low_Avg_Density['Mid-Low'] | Low_Avg_Density['Middle'] | Low_Avg_Density['Mid-High']))
                               , Complexity['Mid-High'])

            Rule5 = logic.Rule(Low_Avg_Density['High'], Complexity['High'])

            Rule6 = logic.Rule(Low_Avg_Density['Max'], Complexity['Max'])
            rules = [Rule1, Rule2, Rule3, Rule4, Rule5, Rule6]
        else:
            assert isinstance(custom_rules, dict)
            assert isinstance(custom_rules['Complexity'], list)
            rules = []
            for rule in custom_rules['Complexity']:
                rules.append(eval("logic.Rule("+rule+")"))

        self.control = logic.FuzzyControl(rules)

    def __call__(self, Full_Avg_Density, Low_Avg_Density, High_Avg_Density, Pedal, Intensity, cache):

        # Compute complexity
        return self.control.compute({'Full_Avg_Density': Full_Avg_Density, 'Low_Avg_Density': Low_Avg_Density,
                                     'High_Avg_Density': High_Avg_Density, 'Pedal': Pedal,
                                     'Intensity': Intensity}, cache=cache)

