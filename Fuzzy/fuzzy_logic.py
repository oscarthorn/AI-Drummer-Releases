"""
Defines the necessary components of a fuzzy_logic system.
"""

import json

import matplotlib
from numpy import interp

matplotlib.use('TKAgg')
import matplotlib.pyplot as plt


class FuzzyControl:

    def __init__(self, rules):
        """
        :param rules: A list of one or more rule objects
        """
        assert isinstance(rules, list) or rules is None
        self.rules = rules

    def add_rules(self, rules):
        """
        :param rules: A list of one or more rules
        """
        if self.rules is None:
            self.rules = rules
        else:
            assert isinstance(self.rules, list)
            for rule in rules:
                self.rules.append(rule)

    def calculate_membership(self, input_value, cache):
        """
        Utility function used by compute
        :param input_value: A dict of one or more inputs, corresponding to linguistic variables
        """
        membership = {}
        assert isinstance(cache, dict)
        for rule in self.rules:
            term_membership = rule.antecedent_term(input_value, cache)
            parent = rule.consequent_term.parent.name
            if parent not in membership.keys():
                membership[parent] = {}
            if rule.consequent_term.label in membership[parent].keys():
                new = term_membership
                old = membership[parent][rule.consequent_term.label]
                membership[parent][rule.consequent_term.label] = max(new, old)
            else:
                membership[parent][rule.consequent_term.label] = term_membership
        return membership

    def compute(self, input_value, use_functions=False, cache=None):
        """
        :param input_value: A dict of one or more inputs, corresponding to linguistic variables
        :param use_functions:
        :return:
        """

        assert self.rules is not None
        if cache is not None:
            assert isinstance(cache, dict)
            assert 'Antecedents' in cache
            assert 'Consequents' in cache
        else:
            cache = {}
            cache['Antecedents'] = {}
            cache['Consequents'] = {}
        membership = self.calculate_membership(input_value, cache)
        cache['Consequents'].update(membership)
        crisp_values = {}
        for rule in self.rules:
            parent = rule.consequent_term.parent.name
            if parent not in crisp_values.keys():
                if use_functions:
                    crisp_values[parent] = rule.consequent_term.parent.defuzz_func(membership[parent])
                else:
                    crisp_values[parent] = rule.consequent_term.parent.defuzz(membership[parent])

        return crisp_values

    def print_computation(self, input_value, cache, use_functions=False):

        assert self.rules is not None

        terms = []
        for rule in self.rules:
            if isinstance(rule.antecedent_term, AntecedentTerm):
                terms.append(rule.antecedent_term)
            elif isinstance(rule.antecedent_term, Accumulator):
                terms = terms + rule.antecedent_term.get_antecedent_terms()

        antecedents = {}
        for term in terms:
            assert isinstance(term.parent, Antecedent)
            if term.parent.name not in antecedents.keys():
                antecedents[term.parent.name] = {}
                for single_term in term.parent.terms.values():
                    assert isinstance(single_term, AntecedentTerm)
                    antecedents[term.parent.name].update({single_term.label: single_term(input_value, cache)})

        membership = {}
        for rule in self.rules:
            term_membership = rule.antecedent_term(input_value, cache)
            parent = rule.consequent_term.parent.name
            if parent not in membership.keys():
                membership[parent] = {}
            if rule.consequent_term.label in membership[parent].keys():
                new = term_membership
                old = membership[parent][rule.consequent_term.label]
                membership[parent][rule.consequent_term.label] = max(new, old)
            else:
                membership[parent][rule.consequent_term.label] = term_membership

        rule_activations = {}
        for rule in self.rules:
            rule_activations.update({rule.__str__(): membership[rule.consequent_term.parent.name][rule.consequent_term.label]})

        crisp_values = {}
        for rule in self.rules:
            parent = rule.consequent_term.parent.name
            if parent not in crisp_values.keys():
                if use_functions:
                    crisp_values[parent] = rule.consequent_term.parent.defuzz_func(membership[parent])
                else:
                    crisp_values[parent] = rule.consequent_term.parent.defuzz(membership[parent])

        print(json.dumps(antecedents, sort_keys=False, indent=4))
        print(json.dumps(membership, sort_keys=False, indent=4))
        print(json.dumps(rule_activations, sort_keys=False, indent=4, separators=(',\n', ': ')))
        print(json.dumps(crisp_values, sort_keys=False, indent=4))

        return


class Rule:
    """
    A rule is a pair between an accumulator object(or a single term) and a consequent term
    """
    def __init__(self, antecedent, consequent):
        """
        :type consequent: ConsequentTerm
        """
        self.antecedent_term = antecedent
        self.consequent_term = consequent

    def __call__(self, input_dict):
        """
        Resolves a rule and returns the membership in the consequent term
        :param input_dict: A dict of inputs where [variable name] resolves to a scalar
        """
        return self.antecedent_term(input_dict)

    def __str__(self):
        return "If: {0} then: {1}".format(self.antecedent_term, self.consequent_term)


class TermPrimitive:
    """
    A base class for Term and Accumulator. Used to define shared logical operators.
    """
    def __init__(self):
        pass

    def __and__(self, other):
        assert isinstance(self, TermPrimitive)
        assert isinstance(other, TermPrimitive)
        return Accumulator('and', self, other)

    def __or__(self, other):
        assert isinstance(self, TermPrimitive)
        assert isinstance(other, TermPrimitive)
        return Accumulator('or', self, other)

    def __invert__(self):
        assert isinstance(self, TermPrimitive)
        return Accumulator('not', self)


class Term:
    """
    A linguistic value of a linguistic variable. Base-class for Antecedent and Consequent Term
    """
    def __init__(self, label):
        self.label = label
        self.parent = None
        self.universe = None


class AntecedentTerm(Term, TermPrimitive):
    """
    A term of an antecedent variable
    Defined by a label, membership function and a universe.
    """
    def __init__(self, label, mf, type_mf='Function'):
        """
        :param label: Name of term, eg high, good, bad...
        :param mf: A list of tuples [(X1,Y1)...(Xn,Yn)]
        """
        TermPrimitive.__init__(self)
        Term.__init__(self, label)
        self.type_mf = type_mf

        if self.type_mf == 'Function':
            x_plane = []
            y_plane = []
            for point in mf:
                x_plane.append(point[0])
                y_plane.append(point[1])
            self.member_function = (x_plane, y_plane)
        elif self.type_mf == 'Single':
            self.member_function = mf
        else:
            raise ValueError('Does not recognise the mf type')

    def __eq__(self, other):
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        return NotImplemented

    def __str__(self):
        return "{0} is {1}".format(self.parent, self.label)

    def __call__(self, input_dict, cache):
        """
        Computes the membership given a scalar input.
        The scalar input should be a value in the universe.
        :param input_dict: A dict where [parent] is a key to a scalar value or a string
        :return: Membership
        """
        if self.parent.name not in cache['Antecedents']:
            cache['Antecedents'][self.parent.name] = {}

        if self.label in cache['Antecedents'][self.parent.name] and self == cache['Antecedents'][self.parent.name][self.label][0]:
            return cache['Antecedents'][self.parent.name][self.label][1]
        else:
            input_value = input_dict[self.parent.name]

            if self.type_mf == 'Function':
                membership = self.function_membership(input_value)
                cache['Antecedents'][self.parent.name][self.label] = (self, membership)
                return membership

            elif self.type_mf == 'Single':
                membership = self.single_membership(input_value)
                cache['Antecedents'][self.parent.name][self.label] = (self, membership)
                return membership

    def single_membership(self, input_value):
        assert self.universe[0] <= input_value <= self.universe[1]
        if input_value in self.member_function:
            return True
        else:
            return False

    def function_membership(self, input_value):
        assert self.universe[0] - 0.000005 <= input_value <= self.universe[1] + 0.000005
        return interp(input_value, self.member_function[0], self.member_function[1])


class ConsequentTerm(Term):
    """
    A term of a consequent variable
    """
    def __init__(self, label, output_value):
        """
        :param label: Name of the term
        :param output_value: The crisp output value iff this term only is activated and fully so.
        """
        super().__init__(label)
        self.output_value = output_value

    def __str__(self):
        return "{0} is {1}".format(self.parent, self.label)


class Accumulator(TermPrimitive):
    """
    Defines an 'execution graph' for resolving a combination of terms
    """
    def __init__(self, mode, lh, rh=None):
        """
        :param mode: A string, 'and', 'or', 'not'
        :param lh: A single term or accumulator object
        :param rh: A single term or accumulator object
        """
        super().__init__()
        assert mode in ['and', 'or', 'not']
        if mode in ['and', 'or']:
            assert rh is not None
        self.mode = mode
        self.left_hand = lh
        self.right_hand = rh

    def __call__(self, input_dict, cache):
        """
        Calling the accumulator object
        :param input_dict:
        :return:
        """
        if self.mode == 'and':
            lh = self.left_hand(input_dict, cache)
            rh = self.right_hand(input_dict, cache)
            return min(lh, rh)
        elif self.mode == 'or':
            lh = self.left_hand(input_dict, cache)
            rh = self.right_hand(input_dict, cache)
            return max(lh, rh)
        else:   # mode is 'not'
            lh = self.left_hand(input_dict, cache)
            return 1 - lh

    def __str__(self):
        if self.mode == 'and':
            return "{0} and {1}".format(str(self.left_hand), str(self.right_hand))
        elif self.mode == 'or':
            return "{0} or {1}".format(str(self.left_hand), str(self.right_hand))
        else:   # mode is 'not'
            return "not {0}".format(str(self.left_hand))

    def get_antecedent_terms(self):
        def step(self, terms):
            lh = self.left_hand
            rh = self.right_hand

            if lh is not None:
                if isinstance(lh, Accumulator):
                    step(lh, terms)
                elif isinstance(lh, AntecedentTerm):
                    terms.append(lh)
            if rh is not None:
                if isinstance(rh, Accumulator):
                    step(rh, terms)
                elif isinstance(rh, AntecedentTerm):
                    terms.append(rh)
            return terms

        terms = []
        lh = self.left_hand
        rh = self.right_hand

        if lh is not None:
            if isinstance(lh, Accumulator):
                step(lh, terms)
            elif isinstance(lh, AntecedentTerm):
                terms.append(lh)
        if rh is not None:
            if isinstance(rh, Accumulator):
                step(rh, terms)
            elif isinstance(rh, AntecedentTerm):
                terms.append(rh)
        return terms


class LinguisticVariable:

    def __init__(self, name, universe):
        """
        :param name: String
        :param universe: A tuple (lower-bound, upper-bound)
        """
        self.name = name
        self.universe = universe
        self.terms = {}

    def __setitem__(self, term, term_object):
        """
        :param term: String, name
        :param term_object: A term object
        """
        assert isinstance(term_object, Term)
        term_object.parent = self
        term_object.universe = self.universe
        self.terms[term] = term_object

    def __getitem__(self, key):
        """
        :param key: String
        """
        assert key in self.terms.keys()
        return self.terms[key]


class Antecedent(LinguisticVariable):
    """
    An antecedent variable
    """
    def __init__(self, name, universe):
        super().__init__(name, universe)
        anything_term = AntecedentTerm('Anything', [(self.universe[0], 1), (self.universe[1], 1)])
        anything_term.parent = self
        anything_term.universe = self.universe
        self.terms['Anything'] = anything_term

    def auto_generate_terms(self, number, labels):
        """
        Generates overlapping, triangular terms evenly spaced throughout the universe
        :param number: The number of terms
        :param labels: A list of names, ordered from the lower bound of the universe to the upper, len == number
        """
        assert len(labels) == number
        assert number > 0
        width_universe = self.universe[1] - self.universe[0]
        width = width_universe / (number - 1)
        current_position = self.universe[0]
        for i in range(0, number):
            label = labels[i]
            start = max(self.universe[0], current_position - width)
            center = current_position
            end = min(self.universe[1], current_position + width)
            if center == self.universe[0]:
                self[label] = AntecedentTerm(label, [(start, 1), (center, 1), (end, 0)])
            elif center == self.universe[1]:
                self[label] = AntecedentTerm(label, [(start, 0), (center, 1), (end, 1)])
            else:
                self[label] = AntecedentTerm(label, [(start, 0), (center, 1), (end, 0)])
            current_position += width

    def __str__(self):
        return "{0}".format(self.name)

    def display(self, title='', range=None):
        if range is not None:
            plt.axis(xmin=range[0] - 1, xmax=range[1] + 1, ymin=0, ymax=1.5)
        else:
            plt.axis(xmin=self.universe[0]-1, xmax=self.universe[1]+1, ymin=0, ymax=1.5)
        plt.ylabel('Activation')
        plt.xlabel('Value')
        legend = []
        for key, term in self.terms.items():
            assert isinstance(term, AntecedentTerm)
            if term.type_mf == 'Function':
                x = term.member_function[0]
                y = term.member_function[1]
                plt.plot(x, y)
            elif term.type_mf == 'Single':
                for single in term.member_function:
                    plt.plot([single, single], [0, 1])
            legend.append(term.label)
        plt.legend(legend)
        plt.title(title)
        plt.show()


class Consequent(LinguisticVariable):

    def __init__(self, name, universe, output_function=lambda x: x, default_output=None, output_type='Continuous',
                 discrete_threshold=0.5):
        """
        :param name: Name
        :param universe: The range of possible output values
        :param output_function: A function, can be used to object other than simply crisp values
        :param output_type: Continuous or Discrete
        """
        assert output_type == 'Continuous' or 'Discrete'
        super().__init__(name, universe)
        self.output_function = output_function
        self.default_output = default_output
        self.output_type = output_type
        self.discrete_threshold = discrete_threshold

    def defuzz(self, membership_dict):
        """
        Returns a crisp value output
        :param membership_dict: A dict giving the membership in the terms of the variable
        """
        def Continuous(consequent, membership):
            sum_weighted_output = 0
            sum_activations = 0
            for term in consequent.terms.keys():
                if term in membership:
                    sum_weighted_output += membership[term] * consequent.terms[term].output_value
                    sum_activations += membership[term]
            if sum_activations != 0:
                return sum_weighted_output / sum_activations
            else:
                return consequent.default_output

        def Discrete(consequent, membership):
            sum_activations = sum(membership.values())
            if sum_activations != 0:
                max_term = max(membership.keys(), key=(lambda k: membership[k]))
                if membership[max_term] >= self.discrete_threshold:
                    return consequent.terms[max_term].output_value
                else:
                    return consequent.default_output
            else:
                return consequent.default_output

        if self.output_type == 'Continuous':
            return Continuous(self, membership_dict)
        elif self.output_type == 'Discrete':
            return Discrete(self, membership_dict)
        else:
            raise ValueError('Consequent type mismatch')

    def defuzz_func(self, membership_dict):
        """
        Returns the output of the consequent as defined by the output function
        :param membership_dict: A dict giving the membership in the terms of the variable
        """
        crisp_value = self.defuzz(membership_dict)
        return self.output_function(crisp_value)

    def auto_generate_terms(self, number, labels):
        """
        Generates consequent terms with output_values evenly spaced through universe (precision varies with system)
        :param number: The number of terms
        :param labels: A list of names, ordered from the lower bound of the universe to the upper, len == number
        """
        assert len(labels) == number
        assert number > 0
        width_universe = self.universe[1] - self.universe[0]
        width = width_universe / (number - 1)
        current_position = self.universe[0]
        for i in range(0, number):
            label = labels[i]
            self[label] = ConsequentTerm(label, current_position)
            current_position += width

    def __str__(self):
        return "{0}".format(self.name)
