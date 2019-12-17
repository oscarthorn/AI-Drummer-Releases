
from collections import deque

from math import inf
from scipy.stats import linregress

from Fuzzy import fuzzy_logic as logic


class TemporalFilters:

    def __init__(self):
        self.history = {'Average Velocity': 0,
                        'Slow Average Velocity': 0,
                        'Full Average Density': 0,
                        'Low Average Density': 0,
                        'High Average Density': 0}
        self.Velocity_Filter = VelocityFilter(0.6)
        self.Slow_Velocity_Filter = VelocityFilter(0.15)
        self.Density_Filter = DensityFilter()
        self.Shift_Filter = ShiftFilter()
        self.HypeFilter = HypeFilter()

    def filter(self, features):

        filtered_features = {}

        # Filters
        # Average Velocity
        avg_vel = self.Velocity_Filter(features['Velocity'], self.history['Average Velocity'])
        filtered_features['Average Velocity'] = avg_vel
        self.history['Average Velocity'] = avg_vel

        # Slow Velocity Avg
        slow_avg_vel = self.Velocity_Filter(features['Velocity'], self.history['Slow Average Velocity'])
        filtered_features['Slow Average Velocity'] = slow_avg_vel
        self.history['Slow Average Velocity'] = slow_avg_vel

        # Average Density
        # Full range average
        avg_den = self.Density_Filter(features['Full range density'], self.history['Full Average Density'])
        filtered_features['Full Average Density'] = avg_den
        self.history['Full Average Density'] = avg_den
        # Low range average
        avg_den = self.Density_Filter(features['Low range density'], self.history['Low Average Density'])
        filtered_features['Low Average Density'] = avg_den
        self.history['Low Average Density'] = avg_den
        # High range average
        avg_den = self.Density_Filter(features['High range density'], self.history['High Average Density'])
        filtered_features['High Average Density'] = avg_den
        self.history['High Average Density'] = avg_den

        # Sudden Shift Filter
        sudden_shift, TimeSinceShiftUp, TimeSinceShiftDown = self.Shift_Filter(features['Current second velocity'],
                                                                               features['Previous second velocity'],
                                                                               features['History Intensity'],
                                                                               features['Time'])
        filtered_features['Sudden Shift'] = sudden_shift
        filtered_features['Time Since Shift Up'] = TimeSinceShiftUp
        filtered_features['Time Since Shift Down'] = TimeSinceShiftDown

        # Crescendo filter
        hype = self.HypeFilter(features['History Intensity'], features['History_Complexity'], features['Time'])
        filtered_features['Hype'] = hype

        # Add more filters here

        # Return features
        return filtered_features


class VelocityFilter:
    """
    Input: Current velocity, avg velocity
    Output: New avg velocity
    """
    def __init__(self, speed=0.6):
        # Initialize fuzzy logic
        ##############
        # Antecedent #
        ##############
        Velocity_diff = logic.Antecedent('Velocity_diff', (-127, 127))
        Velocity_diff.auto_generate_terms(9, ['Neg-Max', 'Neg-High', 'Neg-Middle', 'Neg-Low', 'None',
                                               'Low', 'Middle', 'High', 'Max'])

        ##############
        # Consequent #
        ##############
        Change_Velocity = logic.Consequent('Change_Velocity', (-speed, speed))
        Change_Velocity.auto_generate_terms(9, ['Max-Down', 'High-Down', 'Middle-Down', 'Low-Down', 'None',
                                                'Low-Up', 'Middle-Up', 'High-Up', 'Max-Up'])
        # Change_Velocity['Max-Down'] = logic.ConsequentTerm('Max-Down', -0.5)
        # Change_Velocity['High-Down'] = logic.ConsequentTerm('High-Down', -0.375)
        # Change_Velocity['Middle-Down'] = logic.ConsequentTerm('Middle-Down', -0.25)
        # Change_Velocity['Low-Down'] = logic.ConsequentTerm('Low-Down', -0.125)
        Change_Velocity['None'] = logic.ConsequentTerm('None', 0)
        # Change_Velocity['Low-Up'] = logic.ConsequentTerm('Low-Up', 0.125)
        # Change_Velocity['Middle-Up'] = logic.ConsequentTerm('Middle-Up', 0.25)
        # Change_Velocity['High-Up'] = logic.ConsequentTerm('High-Up', 0.375)
        # Change_Velocity['Max-Up'] = logic.ConsequentTerm('Max-Up', 0.5)

        #########
        # Rules #
        #########
        Rule1 = logic.Rule(Velocity_diff['Neg-Max'], Change_Velocity['Max-Down'])
        Rule2 = logic.Rule(Velocity_diff['Neg-High'], Change_Velocity['High-Down'])
        Rule3 = logic.Rule(Velocity_diff['Neg-Middle'], Change_Velocity['Middle-Down'])
        Rule4 = logic.Rule(Velocity_diff['Neg-Low'], Change_Velocity['Low-Down'])
        Rule5 = logic.Rule(Velocity_diff['None'], Change_Velocity['None'])
        Rule6 = logic.Rule(Velocity_diff['Low'], Change_Velocity['Low-Up'])
        Rule7 = logic.Rule(Velocity_diff['Middle'], Change_Velocity['Middle-Up'])
        Rule8 = logic.Rule(Velocity_diff['High'], Change_Velocity['High-Up'])
        Rule9 = logic.Rule(Velocity_diff['Max'], Change_Velocity['Max-Up'])

        # Control
        self.control = logic.FuzzyControl([Rule1, Rule2, Rule3, Rule4, Rule5, Rule6, Rule7, Rule8, Rule9])

    def __call__(self, Current_Velocity, History_Avg_Velocity):

        # Calculate velocity difference
        diff = Current_Velocity - History_Avg_Velocity

        # Fuzzy calculate increase / decrease
        crisp = self.control.compute({'Velocity_diff': diff})

        # Calculate new average
        Average_Velocity = History_Avg_Velocity + crisp['Change_Velocity']

        return Average_Velocity


class DensityFilter:
    """
    Input: Current density, Average density
    Output: New avg density
    """
    def __init__(self):
        # Initialize fuzzy logic
        ##############
        # Antecedent #
        ##############
        Density_diff = logic.Antecedent('Density_diff', (-127, 127))
        Density_diff.auto_generate_terms(9, ['Neg-Max', 'Neg-High', 'Neg-Middle', 'Neg-Low', 'None',
                                             'Low', 'Middle', 'High', 'Max'])

        ##############
        # Consequent #
        ##############
        Change_Density = logic.Consequent('Change_Density', (-0.6, 0.6), lambda x: x)
        Change_Density.auto_generate_terms(9, ['Max-Down', 'High-Down', 'Middle-Down', 'Low-Down', 'None',
                                               'Low-Up', 'Middle-Up', 'High-Up', 'Max-Up'])

        Rule1 = logic.Rule(Density_diff['Neg-Max'], Change_Density['Max-Down'])
        Rule2 = logic.Rule(Density_diff['Neg-High'], Change_Density['High-Down'])
        Rule3 = logic.Rule(Density_diff['Neg-Middle'], Change_Density['Middle-Down'])
        Rule4 = logic.Rule(Density_diff['Neg-Low'], Change_Density['Low-Down'])
        Rule5 = logic.Rule(Density_diff['None'], Change_Density['None'])
        Rule6 = logic.Rule(Density_diff['Low'], Change_Density['Low-Up'])
        Rule7 = logic.Rule(Density_diff['Middle'], Change_Density['Middle-Up'])
        Rule8 = logic.Rule(Density_diff['High'], Change_Density['High-Up'])
        Rule9 = logic.Rule(Density_diff['Max'], Change_Density['Max-Up'])

        #########
        # Rules #
        #########
        self.control = logic.FuzzyControl([Rule1, Rule2, Rule3, Rule4, Rule5, Rule6, Rule7, Rule8, Rule9])

    def __call__(self, Current_Density, Average_Density):

        # Calculate density difference
        diff = Current_Density - Average_Density

        # Fuzzy calculate increase / decrease
        crisp = self.control.compute({'Density_diff': diff})

        # Calculate new average
        Average_Density += crisp['Change_Density']

        return Average_Density


class ShiftFilter:
    """
    Determines if there is a sudden shift in velocity
    Input: Averages of velocity
    Output: Truth of sudden shift up or down
    """
    def __init__(self):
        self.TimeShiftUp = -inf
        self.TimeShiftDown = -inf
        # Initialize fuzzy logic
        ##############
        # Antecedent #
        ##############
        Current_second_velocity = logic.Antecedent('Current_second_velocity', (0, 127))
        Current_second_velocity.auto_generate_terms(6, ['Low', 'Mid-Low', 'Middle', 'Mid-High', 'High', 'Max'])

        Previous_second_velocity = logic.Antecedent('Previous_second_velocity', (0, 127))
        Previous_second_velocity.auto_generate_terms(6, ['Low', 'Mid-Low', 'Middle', 'Mid-High', 'High', 'Max'])

        Intensity = logic.Antecedent('Intensity', (0, 127))
        Intensity.auto_generate_terms(6, ['Low', 'Mid-Low', 'Middle', 'Mid-High', 'High', 'Max'])

        ##############
        # Consequent #
        ##############
        Sudden_Shift = logic.Consequent('Sudden_Shift', (-1, 1), default_output=0)
        Sudden_Shift['Up'] = logic.ConsequentTerm('Up', 1)
        Sudden_Shift['None'] = logic.ConsequentTerm('None', 0)
        Sudden_Shift['Down'] = logic.ConsequentTerm('Down', -1)

        #########
        # Rules #
        #########
        Rule1 = logic.Rule((Current_second_velocity['Low']
                            & (Previous_second_velocity['Max']
                               | Previous_second_velocity['High']
                               | Previous_second_velocity['Mid-High'])
                            & ~(Intensity['Low']
                                | Intensity['Mid-Low']
                                | Intensity['Middle'])), Sudden_Shift['Down'])

        Rule2 = logic.Rule(Current_second_velocity['Max'] & (Previous_second_velocity['Low']
                                                             | Previous_second_velocity['Mid-Low']), Sudden_Shift['Up'])

        Rule3 = logic.Rule(~Rule1.antecedent_term & ~Rule2.antecedent_term, Sudden_Shift['None'])

        self.control = logic.FuzzyControl([Rule1, Rule2, Rule3])

    def __call__(self, Current_second_velocity, Previous_second_velocity, Intensity, current_time):

        # Infer sudden shift
        input_dict = {'Current_second_velocity': Current_second_velocity,
                      'Previous_second_velocity': Previous_second_velocity,
                      'Intensity': Intensity}
        Sudden_shift = self.control.compute(input_dict)

        crisp = Sudden_shift['Sudden_Shift']
        threshold = 0.6
        if crisp >= threshold:
            self.TimeShiftUp = current_time
        elif crisp <= -threshold:
            self.TimeShiftDown = current_time
        else:
            crisp = 0

        TimeSinceShiftUp = current_time - self.TimeShiftUp
        TimeSinceShiftDown = current_time - self.TimeShiftDown

        return crisp, TimeSinceShiftUp, TimeSinceShiftDown


class HypeFilter:
    """
    Looks at the past to anticipate if a crescendo is approaching
    """
    def __init__(self):
        self.cycles = 150
        self.intensities = deque(maxlen=self.cycles)
        self.complexities = deque(maxlen=self.cycles)
        # Initialize fuzzy logic
        ##############
        # Antecedent #
        ##############
        Complexity = logic.Antecedent('Complexity', (0, 127))
        Complexity.auto_generate_terms(6, ['Low', 'Mid-Low', 'Middle', 'Mid-High', 'High', 'Max'])

        Intensity = logic.Antecedent('Intensity', (0, 127))
        Intensity.auto_generate_terms(6, ['Low', 'Mid-Low', 'Middle', 'Mid-High', 'High', 'Max'])

        Intensity_slope = logic.Antecedent('Intensity_slope', (-inf, inf))
        Intensity_slope['Increasing'] = logic.AntecedentTerm('Increasing', mf=[(1, 0), (10, 1)])
        Intensity_slope['Decreasing'] = logic.AntecedentTerm('Decreasing', mf=[(-1, 0), (-10, 1)])

        Complexity_slope = logic.Antecedent('Complexity_slope', (-inf, inf))
        Complexity_slope['Increasing'] = logic.AntecedentTerm('Increasing', mf=[(1, 0), (10, 1)])
        Complexity_slope['Decreasing'] = logic.AntecedentTerm('Decreasing', mf=[(-1, 0), (-10, 1)])

        ##############
        # Consequent #
        ##############
        Hype = logic.Consequent('Hype', (0, 1), default_output=0)
        Hype['Coming'] = logic.ConsequentTerm('Coming', 1)

        #########
        # Rules #
        #########
        Rule1 = logic.Rule((Intensity['Max'] | Intensity['High']) & ~(Complexity['Low'] | Complexity['Mid-Low'] | Complexity['Middle'])
                           & Intensity_slope['Increasing'] & Complexity_slope['Increasing'],
                           Hype['Coming'])

        self.control = logic.FuzzyControl([Rule1])

    def __call__(self, Current_Intensity, Current_Complexity, current_time):

        # Calculate intensity slope
        if len(self.intensities) == self.cycles:
            Intensity_slope, _, _, _, _ = linregress(self.intensities)
        else:
            Intensity_slope = 0
        self.intensities.appendleft([current_time, Current_Intensity])

        # Calculate complexity slope
        if len(self.complexities) == self.cycles:
            Complexity_slope, _, _, _, _ = linregress(self.complexities)
        else:
            Complexity_slope = 0
        self.complexities.appendleft([current_time, Current_Complexity])

        # Compute
        Hype = self.control.compute({'Intensity': Current_Intensity, 'Complexity': Current_Complexity,
                                     'Intensity_slope': Intensity_slope, 'Complexity_slope': Complexity_slope})

        return Hype['Hype']
