
import multiprocessing as mp
import threading as t
import sys, os, random, re
import copy
import re
import json

import mido
import requests

from fbs_runtime.application_context.PySide2 import ApplicationContext
from PySide2.QtCore import Slot, QObject, Property, Signal, QAbstractListModel
from PySide2.QtQml import QQmlApplicationEngine
from PySide2 import QtCore

QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
appctxt = None


def run(args):
    from Fuzzy.aidrummer import AiDrummer
    d = AiDrummer(**args)
    d.run()


class RuleModel(QAbstractListModel):
    AndOrRole = QtCore.Qt.UserRole + 1001
    AnteRole = QtCore.Qt.UserRole + 1002
    ConsRole = QtCore.Qt.UserRole + 1010
    ModifierRole = QtCore.Qt.UserRole + 1003
    AnteTermRole = QtCore.Qt.UserRole + 1004
    ConsTermRole = QtCore.Qt.UserRole + 1011
    AndOrRoleSel = QtCore.Qt.UserRole + 1005
    AnteRoleSel = QtCore.Qt.UserRole + 1006
    ConsRoleSel = QtCore.Qt.UserRole + 1012
    ModifierRoleSel = QtCore.Qt.UserRole + 1007
    TermRoleSel = QtCore.Qt.UserRole + 1008
    NameRole = QtCore.Qt.UserRole + 1009
    setAnteRoleSel = QtCore.Qt.UserRole + 1013
    setTermRoleSel = QtCore.Qt.UserRole + 1014
    setModifierRoleSel = QtCore.Qt.UserRole + 1015
    setAndOrRoleSel = QtCore.Qt.UserRole + 1016
    setConsRoleSel = QtCore.Qt.UserRole + 1017

    def __init__(self, ante_and_terms: dict, cons_and_terms: dict, parent=None):
        super(RuleModel, self).__init__(parent)
        self._entries = []
        self._anteAndTerms = ante_and_terms
        self._consAndTerms = cons_and_terms
        self._andOr = ['AND', 'OR']
        self._modifier = ['IS', 'NOT']
        self._consequent = 0
        self.appendRow('consequent')
        self.appendRow('start_condition')
        self.timer = None
        self._rulesList = []
        self._rulesListSelection = None
        self._editingRule = None

    # region rulesList
    rulesListChanged = Signal()
    rulesListSelectionChanged = Signal()
    editingRuleChanged = Signal()

    @Property(int, notify=editingRuleChanged)
    def editingRule(self):
        return self._editingRule

    @editingRule.setter
    def set_editingRule(self, val):
        print(val)
        if self._editingRule == val:
            return
        self._editingRule = val
        self.editingRuleChanged.emit()

    @Property('QVariantList', notify=rulesListChanged)
    def rulesList(self):
        return self._rulesList

    @rulesList.setter
    def set_rulesList(self, val):
        if self._rulesList == val:
            return
        self._rulesList = val[:]
        self.rulesListChanged.emit()

    @Property(int, notify=rulesListSelectionChanged)
    def rulesListSelection(self):
        return self._rulesListSelection

    @rulesListSelection.setter
    def set_rulesListSelection(self, val):
        if self._rulesListSelection == val:
            return
        self._rulesListSelection = val
        self.rulesListSelectionChanged.emit()
    # endregion

    @Property(list)
    def entries(self):
        return self._entries

    consequentChanged = Signal()
    @Property('QString', notify=consequentChanged)
    def consequent(self):
        return self._consequent

    @consequent.setter
    def set_consequent(self, val):
        if self._consequent == val:
            return
        self._consequent = val
        self.consequentChanged.emit()

    def rowCount(self, parent=QtCore.QModelIndex()):
        if parent.isValid(): return 0
        return len(self._entries)

    @Slot('QVariant', 'QVariant')
    def data(self, index, role=QtCore.Qt.DisplayRole):

        if 0 <= index.row() < self.rowCount() and index.isValid():
            item = self._entries[index.row()]
            if role == RuleModel.AndOrRole:
                return self._andOr

            elif role == RuleModel.AnteRole:
                selected_consequent = list(self._consAndTerms.keys())[self.consequent]
                return list(self._anteAndTerms[selected_consequent].keys())

            elif role == RuleModel.ConsRole:
                return list(self._consAndTerms.keys())

            elif role == RuleModel.ModifierRole:
                return self._modifier

            elif role == RuleModel.AnteTermRole:
                selected_consequent = list(self._consAndTerms.keys())[self.consequent]
                selected_antecedent = list(self._anteAndTerms[selected_consequent].keys())[item['AnteRoleSel']]
                return list(self._anteAndTerms[selected_consequent][selected_antecedent])

            elif role == RuleModel.ConsTermRole:
                return self._consAndTerms[list(self._consAndTerms.keys())[item['ConsRoleSel']]]

            elif role == RuleModel.AndOrRoleSel:
                return item['AndOrRoleSel']

            elif role == RuleModel.AnteRoleSel:
                return item['AnteRoleSel']

            elif role == RuleModel.ModifierRoleSel:
                return item['ModifierRoleSel']

            elif role == RuleModel.TermRoleSel:
                return item['TermRoleSel']

            elif role == RuleModel.ConsRoleSel:
                return item['ConsRoleSel']

            elif role == RuleModel.NameRole:
                return item['NameRole']

            elif role == RuleModel.setAnteRoleSel:
                return item['setAnteRoleSel']

            elif role == RuleModel.setTermRoleSel:
                return item['setTermRoleSel']

            elif role == RuleModel.setAndOrRoleSel:
                return item['setAndOrRoleSel']

            elif role == RuleModel.setModifierRoleSel:
                return item['setModifierRoleSel']

            elif role == RuleModel.setConsRoleSel:
                return item['setConsRoleSel']

    def roleNames(self):
        roles = dict()
        roles[RuleModel.AndOrRole] = b'AndOrRole'
        roles[RuleModel.AnteRole] = b'AnteRole'
        roles[RuleModel.ConsRole] = b'ConsRole'
        roles[RuleModel.ModifierRole] = b'ModifierRole'
        roles[RuleModel.AnteTermRole] = b'AnteTermRole'
        roles[RuleModel.ConsTermRole] = b'ConsTermRole'
        roles[RuleModel.AndOrRoleSel] = b'AndOrRoleSel'
        roles[RuleModel.AnteRoleSel] = b'AnteRoleSel'
        roles[RuleModel.ConsRoleSel] = b'ConsRoleSel'
        roles[RuleModel.ModifierRoleSel] = b'ModifierRoleSel'
        roles[RuleModel.TermRoleSel] = b'TermRoleSel'
        roles[RuleModel.NameRole] = b'NameRole'
        roles[RuleModel.setAnteRoleSel] = b'setAnteRoleSel'
        roles[RuleModel.setTermRoleSel] = b'setTermRoleSel'
        roles[RuleModel.setModifierRoleSel] = b'setModifierRoleSel'
        roles[RuleModel.setAndOrRoleSel] = b'setAndOrRoleSel'
        roles[RuleModel.setConsRoleSel] = b'setConsRoleSel'

        return roles

    def entry_dict(self, name):
        if name == 'condition':
            args = dict(AndOrRoleSel=0, AnteRoleSel=0, ModifierRoleSel=0, TermRoleSel=0, NameRole='condition',
                        setAnteRoleSel=0, setTermRoleSel=0, setModifierRoleSel=0, setAndOrRoleSel=0)
            return args
        if name == 'start_condition':
            args = dict(AnteRoleSel=0, ModifierRoleSel=0, TermRoleSel=0, NameRole='start_condition',
                        setAnteRoleSel=0, setTermRoleSel=0, setModifierRoleSel=0)
            return args
        if name == 'consequent':
            args = dict(ConsRoleSel=0, TermRoleSel=0, NameRole='consequent',
                        setConsRoleSel=0, setTermRoleSel=0)
            return args
        if name == 'open_parentheses':
            args = dict(NameRole='open_parentheses')
            return args
        if name == 'close_parentheses':
            args = dict(NameRole='close_parentheses')
            return args
        if name == 'not':
            args = dict(NameRole='not')
            return args

    def appendRow(self, name):
        self.beginInsertRows(QtCore.QModelIndex(), max(0,self.rowCount()-1), max(0,self.rowCount()-1))
        self._entries.insert(self.rowCount()-1, self.entry_dict(name))
        self.endInsertRows()

    def appendRowBefore(self, name):
        self.beginInsertRows(QtCore.QModelIndex(), 0, 0)
        self._entries.insert(0, self.entry_dict(name))
        self.endInsertRows()

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if isinstance(index, int):
            index = self.createIndex(index, 0)

        if not self.hasIndex(index.row(), index.column(), index.parent()):
            return False

        if role == RuleModel.AndOrRoleSel:
            self._entries[index.row()]['AndOrRoleSel'] = value
        elif role == RuleModel.AnteRoleSel:
            self._entries[index.row()]['AnteRoleSel'] = value
        elif role == RuleModel.ModifierRoleSel:
            self._entries[index.row()]['ModifierRoleSel'] = value
        elif role == RuleModel.TermRoleSel:
            self._entries[index.row()]['TermRoleSel'] = value
        elif role == RuleModel.NameRole:
            self._entries[index.row()]['NameRole'] = value
        elif role == RuleModel.ConsRoleSel:
            self._entries[index.row()]['ConsRoleSel'] = value
            self.consequent = value
            self.consequentChanged.emit()
            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(self.reset_set_values)
            self.timer.setSingleShot(True)
            self.timer.start(500)
            self.dataChanged.emit(self.createIndex(0,0), self.createIndex(self.rowCount(), 0))
        else:
            return False

        self.dataChanged.emit(index, index)
        return True

    def reset_set_values(self):
        for entry in self._entries:
            if entry['NameRole'] is 'start_condition':
                entry['setAnteRoleSel'] = 0
                entry['setTermRoleSel'] = 0
                entry['setModifierRoleSel'] = 0
            if entry['NameRole'] is 'condition':
                entry['setAnteRoleSel'] = 0
                entry['setTermRoleSel'] = 0
                entry['setModifierRoleSel'] = 0
                entry['setAndOrRoleSel'] = 0
            if entry['NameRole'] is 'consequent':
                entry['setConsRoleSel'] = 0
                entry['setTermRoleSel'] = 0


    @Slot(int)
    def removeRow(self, row, parent=QtCore.QModelIndex()):
        self.beginRemoveRows(QtCore.QModelIndex(), row, row)
        del self._entries[row]
        self.endRemoveRows()

    @Slot()
    def reset(self):
        self.editingRule = None
        self.beginRemoveRows(QtCore.QModelIndex(), 1, self.rowCount())
        for i in range(len(self._entries)-1, -1, -1):
            self.removeRow(i)
        self.endRemoveRows()
        self.beginInsertRows(QtCore.QModelIndex(), 0, 1)
        self._entries.insert(0, self.entry_dict('start_condition'))
        self._entries.insert(1, self.entry_dict('consequent'))
        self.endInsertRows()
        self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(self.rowCount(), 0))

    @Slot(result='QVariant')
    def save_rule(self):
        def check(myStr):
            open_list = ["("]
            close_list = [")"]
            stack = []
            for i in myStr:
                if i in open_list:
                    stack.append(i)
                elif i in close_list:
                    pos = close_list.index(i)
                    if ((len(stack) > 0) and
                            (open_list[pos] == stack[len(stack) - 1])):
                        stack.pop()
                    else:
                        return False
            if len(stack) == 0:
                return True

        result = {'passed': 1, 'message':'Rule has been saved!'}
        # Build the rule
        ruleParts = self._entries
        new_rule = ""
        parts = len(ruleParts)
        consequent = list(self._consAndTerms.keys())[self._consequent]
        antecedents = list(self._anteAndTerms[consequent].keys())
        terms_per_ante = self._anteAndTerms[consequent]
        for i, item in enumerate(ruleParts):
            if item['NameRole'] == 'start_condition':
                ante = antecedents[item['AnteRoleSel']]
                term = terms_per_ante[ante][item['TermRoleSel']]
                modifier = self._modifier[item['ModifierRoleSel']]
                if modifier == 'NOT':
                    new_rule += '~'
                new_rule += '{}'.format(ante)
                new_rule += '[\'{}\']'.format(term)
                new_rule += ' '
            elif item['NameRole'] == 'consequent':
                term = self._consAndTerms[consequent][item['TermRoleSel']]
                new_rule += ',{}[\'{}\']'.format(consequent, term)
            elif item['NameRole'] == 'condition':
                ante = antecedents[item['AnteRoleSel']]
                term = terms_per_ante[ante][item['TermRoleSel']]
                AndOr = self._andOr[item['AndOrRoleSel']]
                modifier = self._modifier[item['ModifierRoleSel']]
                if AndOr == 'AND':
                    new_rule += '&'
                if AndOr == 'OR':
                    new_rule += '|'
                if modifier == 'NOT':
                    new_rule += '~'
                new_rule += '{}'.format(ante)
                new_rule += '[\'{}\']'.format(term)
                new_rule += ' '
            elif item['NameRole'] == 'open_parentheses':
                new_rule += '('
                new_rule += ' '
            elif item['NameRole'] == 'close_parentheses':
                new_rule += ')'
                new_rule += ' '
            elif item['NameRole'] == 'not':
                new_rule += '~'
                new_rule += ' '
            else:
                raise ValueError('Error due to unknown rule part type')

        new_rule = re.sub(r"(\( *\) )", "", new_rule)

        s = r"(((~ )?\( ~? ?)+)"
        start = next(re.finditer(r'[^\( ~]+', new_rule)).start()
        open_parentheses = [m.start()+start for m in re.finditer(s, new_rule[start:])]
        for i in open_parentheses:
            modifier = [m.start() for m in re.finditer(r"[&|]", new_rule[i:])][0] + i
            if new_rule[i] == '(':
                new_rule = new_rule[:i] + new_rule[modifier] + new_rule[i+1:]
                new_rule = new_rule[:modifier] + '(' + new_rule[modifier + 1:]
            elif new_rule[i] == '~':
                new_rule = new_rule[:i] + new_rule[modifier] + ' ~' + new_rule[i + 1:]
                new_rule = new_rule[:modifier+1] + new_rule[modifier + 1+2:]

        if not check(new_rule):
            result['passed'] = 0
            result['message'] = 'Please balance your parentheses'
            return result

        rules = appctxt.get_resource('custom_rules.txt')
        if self.editingRule is None:
            with open(rules, 'a') as f:
                f.write(new_rule+"\n")
        else:
            copy_rulesList = copy.deepcopy(self.rulesList)
            copy_rulesList[self.editingRule] = new_rule
            self.rulesList = copy_rulesList
            with open(rules, 'w') as f:
                for rule in self.rulesList:
                    f.write(rule+"\n")
        self.reset()
        return result

    @Slot()
    def read_rules(self):
        rules = appctxt.get_resource('custom_rules.txt')
        with open(rules) as f:
            rulesList = [line.rstrip('\n') for line in f]
        self.rulesList = rulesList

    @Slot()
    def delete_rule(self):
        rules = copy.deepcopy(self.rulesList)
        del rules[self.rulesListSelection]
        self.rulesList = rules

        rules_file = appctxt.get_resource('custom_rules.txt')
        with open(rules_file, "w") as f:
            for rule in rules:
                f.write(rule+"\n")

    @Slot()
    def load_rule(self):
        rule = self.rulesList[self.rulesListSelection]
        self.editingRule = self.rulesListSelection

        # Clear rule
        self.beginRemoveRows(QtCore.QModelIndex(), 1, self.rowCount())
        for i in range(len(self._entries) - 1, -1, -1):
            self.removeRow(i)
        self.endRemoveRows()

        # Load new rule
        start_cons = rule.find(',') + 1
        end_cons = rule.find('[', start_cons)
        consequent = rule[start_cons: end_cons]

        ruleParts = rule.split(' ')
        len_ruleParts = len(ruleParts)

        self.beginInsertRows(QtCore.QModelIndex(), 0, len_ruleParts-1)

        for i, item in enumerate(ruleParts):
            if item in ['&', '|']:
                found_term = False
                for j in range(i, len(ruleParts)):
                    if len(ruleParts[j]) > 1 and ruleParts[j][0] == '(':
                        mod = ruleParts[i]
                        ruleParts[i] = ruleParts[j][0]
                        ruleParts[j] = mod + ruleParts[j][1:]
                        found_term = True
                    elif len(ruleParts[j]) == 1 and ruleParts[j][0] == '~':
                        mod = ruleParts[i]
                        ruleParts[i] = ruleParts[j][0]
                        ruleParts[j] = mod
                        i = j
                if not found_term:
                    raise ValueError('Wrong rule format')

        found_first_term = False
        for i, item in enumerate(ruleParts):
            if item == '(':
                args = self.entry_dict('open_parentheses')
                self._entries.insert(len(self._entries), args)
            elif item == ')':
                args = self.entry_dict('close_parentheses')
                self._entries.insert(len(self._entries), args)
            elif item == '~':
                args = self.entry_dict('not')
                self._entries.insert(len(self._entries), args)
            elif not found_first_term:
                found_first_term = True
                args = self.entry_dict('start_condition')

                ante_start = 0
                if '~' in item:
                    args['setModifierRoleSel'] = 1
                    ante_start = 1
                else:
                    args['setModifierRoleSel'] = 0

                ante = item.split('[')[0][ante_start:]
                ante_index = list(self._anteAndTerms[consequent].keys()).index(ante)
                args['setAnteRoleSel'] = ante_index

                term = item.split('\'')[1]
                term_index = list(self._anteAndTerms[consequent][ante]).index(term)
                args['setTermRoleSel'] = term_index
                self._entries.insert(len(self._entries), args)

            elif i == len_ruleParts - 1:
                args = self.entry_dict('consequent')

                consequent_index = list(self._consAndTerms.keys()).index(consequent)
                args['setConsRoleSel'] = consequent_index

                term = item.split('\'')[1]
                term_index = list(self._consAndTerms[consequent]).index(term)
                args['setTermRoleSel'] = term_index
                self._entries.insert(len(self._entries), args)

            else:
                args = self.entry_dict('condition')
                if '&' in item:
                    args['setAndOrRoleSel'] = 0    # AND
                elif '|' in item:
                    args['setAndOrRoleSel'] = 1  # OR
                else:
                    raise ValueError('Wrong rule format')

                ante_start =  1
                if '~' in item:
                    args['setModifierRoleSel'] = 1
                    ante_start = 2
                else:
                    args['setModifierRoleSel'] = 0

                ante = item.split('[')[0][ante_start:]
                ante_index = list(self._anteAndTerms[consequent].keys()).index(ante)
                args['setAnteRoleSel'] = ante_index

                term = item.split('\'')[1]
                term_index = self._anteAndTerms[consequent][ante].index(term)
                args['setTermRoleSel'] = term_index
                self._entries.insert(len(self._entries), args)
        self.endInsertRows()


class Api(QObject):

    proc = None

    def __init__(self):
        QObject.__init__(self)
        self._midi_out = []
        self._midi_out_selection = None
        self._midi_in = []
        self._midi_in_selection = None
        self._play_type = []
        self._play_type_selection = None
        self._instrument = []
        self._instrument_selection = None
        self._play_instrument = []
        self._play_instrument_selection = None
        self._midi_file = None
        self._location = []
        self._location_selection = None
        self._ip_text = None
        self._style = []
        self._style_selection = None
        self._useCustomRules = False
        self._model = None
        self._flags = {'stop': False}

    # region useCustomRules
    useCustomRulesChanged = Signal()

    @Property(bool, notify=useCustomRulesChanged)
    def useCustomRules(self):
        return self._useCustomRules

    @useCustomRules.setter
    def set_useCustomRules(self, val):
        if self._useCustomRules == val:
            return
        self._useCustomRules = val
        self.useCustomRulesChanged.emit()

    # region RuleModel
    ruleModelChanged = Signal()

    @Property(QObject, constant=False, notify=ruleModelChanged)
    def ruleModel(self):
        return self._model

    @ruleModel.setter
    def set_ruleModel(self, val):
        if self._model == val:
            return
        self._model = val
        self.ruleModelChanged.emit()

    @Slot()
    def add_condition(self):
        self.ruleModel.appendRow('condition')

    @Slot()
    def add_open_parentheses(self):
        self.ruleModel.appendRow('open_parentheses')

    @Slot()
    def add_open_parentheses_before(self):
        self.ruleModel.appendRowBefore('open_parentheses')

    @Slot()
    def add_close_parentheses(self):
        self.ruleModel.appendRow('close_parentheses')

    @Slot()
    def add_not(self):
        self.ruleModel.appendRow('not')

    @Slot()
    def add_not_before(self):
        self.ruleModel.appendRowBefore('not')

    @Slot()
    def add_rule(self):
        if self.ruleModel is not None:
            self.ruleModel.reset()

        consequents = {'Intensity': ['Low', 'Mid-Low', 'Middle', 'Mid-High', 'High', 'Max'],
                       'Complexity': ['Low', 'Mid-Low', 'Middle', 'Mid-High', 'High', 'Max'],
                       'Pattern': ['Intro-To-Chorus-1', 'Fill-To-Chorus-1', 'Fill-To-Chorus-2', 'Fill-To-Chorus-3',
                                   'Fill-To-Chorus-4', 'Fill-To-Chorus-5', 'Fill-To-Chorus-6', 'Fill-To-Chorus-7',
                                   'Chorus-1', 'Fill-1', 'Outro', 'None', 'Fill-4', 'Fill-3'],
                       'Mute_Kick': ['True', 'False', 'No-Change'],
                       'Mute_Snare': ['True', 'False', 'No-Change']}

        antecedents = dict(Intensity=None, Complexity=None)
        antecedents['Intensity'] = {'Time_Since_Note': ['Long'],
                                    'Avg_Velocity': ['Low', 'Mid-Low', 'Middle', 'Mid-High', 'High', 'Max', 'Anything'],
                                    'Sudden_Shift': ['Down', 'None', 'Up'],
                                    'Time_Since_Shift_Up': ['Short'],
                                    'Time_Since_Shift_Down': ['Short']}

        antecedents['Complexity'] = {'Full_Avg_Density': ['Low', 'Mid-Low', 'Middle', 'Mid-High', 'High', 'Max',
                                                          'Anything'],
                                     'Low_Avg_Density': ['Low', 'Mid-Low', 'Middle', 'Mid-High', 'High', 'Max',
                                                         'Anything'],
                                     'High_Avg_Density': ['Low', 'Middle', 'High', 'Max', 'Anything'],
                                     'Pedal': ['Down', 'Up'],
                                     'Intensity': ['Low', 'Mid-Low', 'Middle', 'Mid-High', 'High', 'Max', 'Anything']}

        pattern_and_mute_antecedents = {'Mode': ['Play', 'Stop'],
                                        'History_Mode': ['Play', 'Stop'],
                                        'History_Pattern': ['Intro-To-Chorus-1', 'Fill-To-Chorus-1', 'Fill-To-Chorus-2',
                                                            'Fill-To-Chorus-3', 'Fill-To-Chorus-4', 'Fill-To-Chorus-5',
                                                            'Fill-To-Chorus-6', 'Fill-To-Chorus-7', 'Chorus-1', 'Outro',
                                                            'None', 'Anything'],
                                        'Complexity': ['Low', 'Mid-Low', 'Middle', 'Mid-High', 'High', 'Max', 'Anything'],
                                        'Intensity': ['Low', 'Mid-Low', 'Middle', 'Mid-High', 'High', 'Max', 'Anything'],
                                        'Bar': ['8th', '16th', '24th', '32th', 'End-4th', 'End-12th', 'End-20th',
                                                'End-28th'],
                                        'Change_Intensity': ['Up', 'Same', 'Down'],
                                        'Change_Intensity_Short': ['Up', 'Same', 'Down'],
                                        'History_Mute_Snare': ['True', 'False'],
                                        'History_Mute_Kick': ['True', 'False'],
                                        'High_Avg_Density': ['None', 'Low', 'Mid-Low', 'Middle', 'Mid-High', 'High', 'Max'],
                                        'Low_Avg_Density': ['None', 'Low', 'Mid-Low', 'Middle', 'Mid-High', 'High', 'Max'],
                                        'Time_Since_Pedal': ['Very-Short'],
                                        'Time_Since_KS_Muted': ['Very-Long'],
                                        'Time_Since_Kick_Muted': ['Long'],
                                        'Time_In_Bar': ['Last-Quarter'],
                                        'Hype': ['Coming']}

        antecedents['Pattern'] = pattern_and_mute_antecedents

        antecedents['Mute_Kick'] = pattern_and_mute_antecedents

        antecedents['Mute_Snare'] = pattern_and_mute_antecedents

        self.ruleModel = RuleModel(antecedents, consequents)

    # endregion

    # region Style
    styleChanged = Signal()
    styleSelectionChanged = Signal()

    @Property('QVariantList', notify=styleChanged)
    def style(self):
        return self._style

    @style.setter
    def set_style(self, val):
        if self._style == val:
            return
        self._style = val[:]
        self.styleChanged.emit()

    @Property(int, notify=styleSelectionChanged)
    def styleSelection(self):
        return self._style_selection

    @styleSelection.setter
    def set_style_selection(self, val):
        if self._style_selection == val:
            return
        self._style_selection = val
        self.styleSelectionChanged.emit()

    @Slot(int)
    def setStyleSelection(self, val):
        self.set_style_selection(val)
    # endregion

    # region Ip Location
    ipTextChanged = Signal()

    @Property(str, notify=ipTextChanged)
    def ipText(self):
        return self._ip_text

    @ipText.setter
    def set_ip_text(self, val):
        if self._ip_text == val:
            return
        self._ip_text = val
        self.ipTextChanged.emit()
    # endregion

    # region Location
    locationChanged = Signal()
    locationSelectionChanged = Signal()

    @Property('QVariantList', notify=locationChanged)
    def location(self):
        return self._location

    @location.setter
    def set_location(self, val):
        if self._location == val:
            return
        self._location = val[:]
        self.locationChanged.emit()

    @Property(int, notify=locationSelectionChanged)
    def locationSelection(self):
        return self._location_selection

    @locationSelection.setter
    def set_location_selection(self, val):
        if self._location_selection == val:
            return
        self._location_selection = val
        self.locationSelectionChanged.emit()

    @Slot(int)
    def setLocationSelection(self, val):
        self.set_location_selection(val)
    # endregion

    # region MidiOut
    midiOutChanged = Signal()
    midiOutSelectionChanged = Signal()

    @Property('QVariantList', notify=midiOutChanged)
    def midiOut(self):
        return self._midi_out

    @midiOut.setter
    def set_midiOut(self, val):
        if self._midi_out == val:
            return
        self._midi_out = val[:]
        self.midiOutChanged.emit()

    @Property(int, notify=midiOutSelectionChanged)
    def midiOutSelection(self):
        return self._midi_out_selection

    @midiOutSelection.setter
    def set_midiOut_selection(self, val):
        if self._midi_out_selection == val:
            return
        self._midi_out_selection = val
        self.midiOutSelectionChanged.emit()

    @Slot(int)
    def setMidiOutSelection(self, val):
        self.set_midiOut_selection(val)
    # endregion

    # region MidiIn
    midiInChanged = Signal()
    midiInSelectionChanged = Signal()

    @Property('QVariantList', notify=midiInChanged)
    def midiIn(self):
        return self._midi_in

    @midiIn.setter
    def set_midiIn(self, val):
        if self._midi_in == val:
            return
        self._midi_in = val[:]
        self.midiInChanged.emit()

    @Property(int, notify=midiInSelectionChanged)
    def midiInSelection(self):
        return self._midi_in_selection

    @midiInSelection.setter
    def set_midiIn_selection(self, val):
        if self._midi_in_selection == val:
            return
        self._midi_in_selection = val
        self.midiInSelectionChanged.emit()

    @Slot(int)
    def setMidiInSelection(self, val):
        self.set_midiIn_selection(val)

    # endregion

    # region play_type
    playTypeChanged = Signal()
    playTypeSelectionChanged = Signal()

    @Property('QVariantList', notify=playTypeChanged)
    def playType(self):
        return self._play_type

    @playType.setter
    def set_playType(self, val):
        if self._play_type == val:
            return
        self._play_type = val[:]
        self.playTypeChanged.emit()

    @Property(int, notify=playTypeSelectionChanged)
    def playTypeSelection(self):
        return self._play_type_selection

    @playTypeSelection.setter
    def set_playType_selection(self, val):
        if self._play_type_selection == val:
            return
        self._play_type_selection = val
        self.playTypeSelectionChanged.emit()

    @Slot(int)
    def setPlayTypeSelection(self, val):
        self.set_playType_selection(val)

    # endregion

    # region instrumentPort
    instrumentChanged = Signal()
    instrumentSelectionChanged = Signal()

    @Property('QVariantList', notify=instrumentChanged)
    def instrument(self):
        return self._instrument

    @instrument.setter
    def set_instrument(self, val):
        if self._instrument == val:
            return
        self._instrument = val[:]
        self.instrumentChanged.emit()

    @Property(int, notify=instrumentSelectionChanged)
    def instrumentSelection(self):
        return self._instrument_selection

    @instrumentSelection.setter
    def set_instrument_selection(self, val):
        if self._instrument_selection == val:
            return
        self._instrument_selection = val
        self.instrumentSelectionChanged.emit()

    @Slot(int)
    def setInstrumentSelection(self, val):
        self.set_instrument_selection(val)
    # endregion

    # region playInstrument
    playInstrumentChanged = Signal()
    playInstrumentSelectionChanged = Signal()

    @Property('QVariantList', notify=playInstrumentChanged)
    def playInstrument(self):
        return self._play_instrument

    @playInstrument.setter
    def set_playInstrument(self, val):
        if self._play_instrument == val:
            return
        self._play_instrument = val
        self.playInstrumentChanged.emit()

    @Property(int, notify=playInstrumentSelectionChanged)
    def playInstrumentSelection(self):
        return self._play_instrument_selection

    @playInstrumentSelection.setter
    def set_playInstrumentSelection(self, val):
        if self._play_instrument_selection == val:
            return
        self._play_instrument_selection = val
        self.playInstrumentSelectionChanged.emit()

    @Slot(int)
    def setPlayInstrumentSelection(self, val):
        self.set_playInstrumentSelection(val)

    # endregion

    # region MidiFile
    @Slot(str)
    def set_MidiFile(self, val):
        if self._midi_file == val:
            return
        self._midi_file = re.sub(r"(file:/{3})", "", val)
    # endregion

    # region Play/Stop
    @Slot()
    def play(self):

        # Custom rules
        if self.useCustomRules:
            rules = appctxt.get_resource('custom_rules.txt')
            with open(rules) as f:
                customRulesList = [line.rstrip('\n') for line in f]
            customRulesDict = dict()
            for rule in customRulesList:
                start_cons = rule.find(',') + 1
                end_cons = rule.find('[', start_cons)
                consequent = rule[start_cons: end_cons]
                if consequent in customRulesDict.keys():
                    customRulesDict[consequent].append(rule)
                else:
                    customRulesDict[consequent] = []
                    customRulesDict[consequent].append(rule)
        else:
            customRulesDict = None

        # Mode
        if self._play_type_selection == -1:
            return
        else:
            mode = self._play_type[self._play_type_selection]
        # Location
        if self._location[self._location_selection] == 'remote':
            if customRulesDict is not None:
                customRulesDict = json.dumps(customRulesDict)
            if self._play_instrument_selection != -1:
                play_instrument = self._play_instrument[self._play_instrument_selection]
            else:
                play_instrument = 'no'
            if self._style_selection != -1:
                style = self._style[self._style_selection]
            else:
                style = 'NuJazz'
            if mode == 'playback':
                if os.name == 'posix':
                    self._midi_file = '/'+self._midi_file
                assert os.path.exists(self._midi_file) and self._midi_file.endswith('.mid'), 'File'
                midi_file = self._midi_file
                requests.post('http://'+self._ip_text+'/start', data={'mode': mode, 'play_instrument': play_instrument, 'style': style, 'custom_rules': customRulesDict},
                              files={'file': open(midi_file, 'rb')})
            if mode == 'live':
                requests.post('http://'+self._ip_text+'/start', data={'mode': mode, 'play_instrument': play_instrument, 'style': style, 'custom_rules': customRulesDict})

        elif mode == 'live':
            try:
                assert self._midi_in_selection != -1
                assert self._midi_out_selection != -1
                in_port = self._midi_in[self._midi_in_selection]
                out_port = self._midi_out[self._midi_out_selection]

                args = {
                    'mode': mode,
                    'in_port': in_port,
                    'out_port': out_port,
                    'flags': self._flags,
                    'custom_rules': customRulesDict
                }
                self._flags['stop'] = False

                if self._play_instrument_selection != -1:
                    play_instrument = self._play_instrument[self._play_instrument_selection]
                    if play_instrument == 'yes':
                        assert self._instrument_selection != -1
                        args['instrument_port'] = self._instrument[self._instrument_selection]
                        args['play_instrument'] = play_instrument

                self.proc = t.Thread(target=run, args=(args,))
                self.proc.daemon = True
                self.proc.start()
            except Exception as e:
                return

        elif mode == 'playback':
            try:
                assert self._midi_out_selection != -1, 'MidiOut'
                if os.name == 'posix':
                    self._midi_file = '/'+self._midi_file
                assert os.path.exists(self._midi_file) and self._midi_file.endswith('.mid'), 'File'
                out_port = self._midi_out[self._midi_out_selection]
                midi_file = self._midi_file
                args = {
                    'mode': mode,
                    'out_port': out_port,
                    'file': midi_file,
                    'flags': self._flags,
                    'custom_rules': customRulesDict
                }
                self._flags['stop'] = False
                if self._play_instrument_selection != -1:
                    play_instrument = self._play_instrument[self._play_instrument_selection]
                    if play_instrument == 'yes':
                        assert self._instrument_selection != -1, 'Play Instrument'
                        args['instrument_port'] = self._instrument[self._instrument_selection]
                        args['play_instrument'] = play_instrument

                self.proc = t.Thread(target=run, args=(args,))
                self.proc.daemon = True
                self.proc.start()
            except Exception as e:
                return

    @Slot()
    def stop(self):
        if self._location[self._location_selection] == 'local':
            try:
                self._flags['stop'] = True
            except:
                return
        else:
            requests.get('http://'+self._ip_text+'/stop')
            try:
                assert isinstance(self.proc, mp.Process)
                self.proc.kill()
            except:
                return
    # endregion

    def build(self):
        self.midiOut = mido.get_output_names()
        self.midiIn = mido.get_input_names()
        self.instrument = mido.get_output_names()
        self.playType = ['live', 'playback']
        self.playInstrument = ['yes', 'no']
        self.location = ['local', 'remote']
        self.ipText = "192.168.0.198"
        self.style = ['NuJazz', 'JazzBossa', 'BrushesSwing', 'BossaBrushes']


if __name__ == '__main__':
    appctxt = ApplicationContext()  # 1. Instantiate ApplicationContext

    engine = QQmlApplicationEngine()
    api = Api()
    api.build()

    engine.rootContext().setContextProperty("api", api)
    qml = appctxt.get_resource('main.qml')
    engine.load(qml)
    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(appctxt.app.exec_())


