import numpy as np
import math
import MLC.Log.log as lg
import re
from collections import Counter
from MLC.matlab_engine import MatlabEngine
from MLC.Config.Config import Config
from MLC.Common.Operations import Operations


class Individual(object):
    """
    MLCind constructor of the Machine Learning Control individual class.
    Part of the MLC2 Toolbox.

    Implements the individual type, value and costs. Archives history of
    evaluation and other informations.

    This class requires a valid MLCparameters object for most of its
    functionnalities.

    MLCind properties:
        type:
            type of individual (expression trees only now)
        value:
            string or matrice representing the individual in the representation
            considered in 'type'
        cost:
            current cost value of the individual (average of cost_history)
        cost_history:
            history of raw values returned by the evaluation function
        evaluation_time:
            date and time (on the computer clock) of sending of the indivs
            to the evaluation function
        appearances:
            number of time the individual appears in a generation
        hash:
            hash of 'value' to help finding identical individuals
            (will be turned to private)
        formal:
            matlab interpretable expression of the individual
        complexity:
            weighted addition of operators

    MLCind methods:
        generate:
            creates one indiv according to the current MLCparameters object
            and type of individual.
        evaluate:
            evaluates one individual according to the current MLCparameters
            object.
        mutate:
            mutates one individual according to the current MLCparameters
            object and type of indiv.
        crossover:
            crosses two indiv according to the current MLCparameters object
            and type of individuals.
        compare:
            stricly compares two individuals' values
        textoutput:
            display indiviudal value as text string
        preev:
            calls preevaluation function

    See also MLCPARAMETERS, MLCTABLE, MLCPOP, MLC2
    """

    MUTATION_ANY = 0
    MUTATION_REMOVE_SUBTREE_AND_REPLACE = 1
    MUTATION_REPARAMETRIZATION = 2
    MUTATION_HOIST = 3
    MUTATION_SHRINK = 4

    def __init__(self, mlc_ind=None, value=None):
        self._eng = MatlabEngine.engine()
        self._config = Config.get_instance()

        if mlc_ind:
            self._mlc_ind = mlc_ind
        else:
            if value:
                self._mlc_ind = self._eng.MLCind(value)
            else:
                self._mlc_ind = self._eng.MLCind()

    def get_matlab_object(self):
        return self._mlc_ind

    def generate(self, mlc_parameters, varargin):
        """
        generate individual from scratch or from unfinished individual.

        MLCIND.generate(MLC_PARAMETERS,MODE) creates an individual using mode MODE.
        MODE is a number which interpretation depends on the MLCIND.type property.
        (Not designed to be played with by user, code dive for details)

        MLCIND.generate(MLC_PARAMETERS,VALUE) creates an individual with MLCIND.value VALUE.

        matlab_impl: return self._eng.generate(self._mlc_ind, mlc_parameters, varargin)
        """

        # TODO: refactor MLCParameters access
        param_individual_type = self._config.get_param('POPULATION', 'individual_type')
        param_controls = int(self._config.get_param('POPULATION', 'controls'))

        if param_individual_type == 'tree':
            self.set_type('tree')

            if type(varargin) == int:
                value = '(root @' + ' @' * (param_controls - 1) + ')'
                for i in range(1, param_controls + 1):
                    value = self.__generate_indiv_regressive_tree(value, mlc_parameters, varargin)
                self.set_value(value)
            else:
                self.set_value(varargin)

            self.set_value(self.__simplify_and_sensors_tree(self.get_value(), mlc_parameters))
            #string_hash = DataHash(mlcind.value);
            string_hash = self._eng.calculate_hash_from_value(self.get_matlab_object())
            self.set_hash(self._eng.eval("hex2num('%s')" % string_hash[0:16]))
            self.set_formal(self._eng.readmylisp_to_formal_MLC(self.get_value(), mlc_parameters))
            self.set_complexity(self.__tree_complexity(self.get_value(), mlc_parameters))
            return

        raise NotImplementedError("Individual::generate() is not implemented for type %s" % param_individual_type)

    def evaluate(self, mlc_parameters, varargin):
        return self._eng.evaluate(self._mlc_ind, mlc_parameters, varargin)

    def mutate(self, mlc_parameters, mutation_type=MUTATION_ANY):
        # TODO: refactor MLCParameters access
        param_individual_type = self._eng.eval('wmlc.parameters.individual_type')

        if param_individual_type == 'tree':
            new_value, fail = self.__mutate_tree(self.get_value(), mlc_parameters, mutation_type)

            if fail:
                return None, fail

            new_individual = Individual()
            new_individual.generate(mlc_parameters, new_value)
            return new_individual, fail

        raise NotImplementedError("Individual::generate() not implemented for type %s" % param_individual_type)

    def crossover(self, other_individual, mlc_parameters):
        """
        CROSSOVER crosses two MLCind individuals.
        [NEW_IND1,NEW_IND2,FAIL]=CROSSOVER(MLCIND1,MLCIND2,MLC_PARAMETERS)
        """
        # TODO: refactor MLCParameters access
        param_individual_type = self._eng.eval('wmlc.parameters.individual_type')

        if param_individual_type == 'tree':
            m1, m2, fail = self.__crossover_tree(self.get_value(),
                                                 other_individual.get_value(),
                                                 mlc_parameters)
            if fail:
                return None, None, fail

            new_ind1 = Individual()
            new_ind1.generate(mlc_parameters, m1)

            new_ind2 = Individual()
            new_ind2.generate(mlc_parameters, m2)

            return new_ind1, new_ind2, fail

        raise NotImplementedError("Individual::generate() not implemented for type %s" % param_individual_type)

    def compare(self, other_individual):
        """
        Compare two MLCind value properties.
        ISEQUAL=COMPARE(MLCIND1,MLCIND2) returns 1 if both values are equal.
        """
        if self.get_type() == 'tree':
            return self.get_value() == other_individual.get_value()

        raise NotImplementedError("Individual::compare() is not implemented for type %s" % self.get_type())

    def textoutput(self):
        return self._eng.textoutput(self._mlc_ind)

    def preev(self, mlc_patameters):
        return self._eng.textoutput(self._mlc_ind, mlc_patameters)

    def get_value(self):
        return self._eng.get_value(self._mlc_ind)

    def set_value(self, value):
        return self._eng.set_value(self._mlc_ind, value)

    def get_type(self):
        return self._eng.get_type(self._mlc_ind)

    def set_type(self, type):
        return self._eng.set_type(self._mlc_ind, type)

    def get_cost(self):
        return int(self._eng.get_cost(self._mlc_ind))

    def get_cost_history(self):
        return self._eng.get_cost_history(self._mlc_ind)

    def get_evaluation_time(self):
        return self._eng.get_evaluation_time(self._mlc_ind)

    def get_appearences(self):
        return int(self._eng.get_appearences(self._mlc_ind))

    def get_hash(self):
        return self._eng.get_hash(self._mlc_ind)

    def set_hash(self, hash):
        return self._eng.set_hash(self._mlc_ind, hash)

    def get_formal(self):
        return self._eng.get_formal(self._mlc_ind)

    def set_formal(self, formal):
        return self._eng.set_formal(self._mlc_ind, formal)

    def get_complexity(self):
        return int(self._eng.get_complexity(self._mlc_ind))

    def set_complexity(self, complexity):
        return self._eng.set_complexity(self._mlc_ind, complexity)

    def __simplify_and_sensors_tree(self, value, mlc_parameters):
        """
        return self._eng.private_simplify_and_sensors_tree(self.get_matlab_object(),
                                                           value,
                                                           mlc_parameters)
        """
        sensor_list = ()
        replace_list = ()

        if int(self._config.get_param('POPULATION', 'sensor_spec')):
            # TODO: Get the sensors as a list. Not tested for obvious reasons
            config_sensor_list = sorted((1, 9, 4))
            sensor_list = ['S' + str(x) for x in config_sensor_list]
            replace_list = ['z' + str(x) for x in config_sensor_list]
        else:
            amount_sensors = int(self._config.get_param('POPULATION', 'sensors'))
            # Replace the available sensors in the individual expression
            sensor_list = ['S' + str(x) for x in range(amount_sensors)]
            replace_list = ['z' + str(x) for x in range(amount_sensors)]

        for i in range(len(replace_list)):
            value = value.replace(replace_list[i], sensor_list[i])

        if int(self._config.get_param('OPTIMIZATION', 'simplify')):
            return self.__simplify_my_LISP(value, mlc_parameters)

        return value

    def __simplify_my_LISP(self, value, mlc_parameters):
        return self._eng.simplify_my_LISP(value, mlc_parameters)

    def __tree_complexity(self, value, mlc_parameters):
        return self._eng.private_tree_complexity(self.get_matlab_object(), value, mlc_parameters)

    def __generate_indiv_regressive_tree(self, value, mlc_parameters, indiv_type=None):
        return self._eng.private_generate_indiv_regressive_tree(self.get_matlab_object(),
                                                                value,
                                                                mlc_parameters,
                                                                indiv_type)

        min_depth = 0
        max_depth = 0
        new_value = ""

        # FIXME: Don't use the config to generate the depth values because the mlc_parameters has altered
        # parameters compared to the defaults values
        """
        if indiv_type:
            if indiv_type == 1:
                min_depth = int(self._config.get_param('GP', 'maxdepthfirst'))
                max_depth = int(self._config.get_param('GP', 'maxdepthfirst'))
            elif indiv_type == 2 or indiv_type == 3:
                min_depth = int(self._config.get_param('GP', 'mindepth'))
                max_depth = int(self._config.get_param('GP', 'maxdepthfirst'))
            elif indiv_type == 4:
                min_depth = int(self._config.get_param('GP', 'mindepth'))
                max_depth = 1
            else:
                min_depth = int(self._config.get_param('GP', 'mindepth'))
                max_depth = int(self._config.get_param('GP', 'maxdepth'))

        else:
            min_depth = int(self._config.get_param('GP', 'mindepth'))
            max_depth = int(self._config.get_param('GP', 'maxdepth'))
        """

        if indiv_type:
            if indiv_type == 1:
                min_depth = int(self._eng.eval('wmlc.parameters.maxdepthfirst'))
                max_depth = int(self._eng.eval('wmlc.parameters.maxdepthfirst'))
            elif indiv_type == 2 or indiv_type == 3:
                min_depth = int(self._eng.eval('wmlc.parameters.mindepth'))
                max_depth = int(self._eng.eval('wmlc.parameters.maxdepthfirst'))
            elif indiv_type == 4:
                min_depth = int(self._eng.eval('wmlc.parameters.mindepth'))
                max_depth = 1
            else:
                min_depth = int(self._eng.eval('wmlc.parameters.mindepth'))
                max_depth = int(self._eng.eval('wmlc.parameters.maxdepth'))

        else:
            min_depth = int(self._eng.eval('wmlc.parameters.mindepth'))
            max_depth = int(self._eng.eval('wmlc.parameters.maxdepth'))

        # Check if the seed character is in the string
        index = value.find('@')
        if index == -1:
            return

        # Split the value in two strings, not containing the first seed character
        begin_str = value[:index]
        end_str = value[index+1:]

        # Count the amounts of '(' until the first seed character (This is the depth of the seed)
        counter = Counter(begin_str)
        begin_depth = counter['('] - counter[')']

        leaf_node = False
        if begin_depth >= max_depth:
            leaf_node = True
        elif (begin_depth < min_depth and end_str.find('@') == -1) or indiv_type == 3:
            leaf_node = False
        else:
            leaf_node = MatlabEngine.rand() < float(self._config.get_param('POPULATION', 'leaf_prob'))

        if leaf_node:
            use_sensor = MatlabEngine.rand() < float(self._config.get_param('POPULATION', 'sensor_prob'))
            if use_sensor:
                sensor_number = math.ceil(MatlabEngine.rand() * int(self._config.get_param('POPULATION', 'sensors'))) - 1
                new_value = begin_str + 'z' + str(sensor_number).rstrip('0').rstrip('.') + end_str
            else:
                range = float(self._config.get_param('POPULATION', 'range'))
                precision = str(int(self._config.get_param('POPULATION', 'precision')))
                # Generate a float number between -range and +range with a precision of 'precision'
                new_exp = (("%." + precision + "f") % ((MatlabEngine.rand() - 0.5) * 2 * range))
                new_value = begin_str + new_exp + end_str
        else:
            # Create a node
            op_num = math.ceil(MatlabEngine.rand() * Operations.get_instance().length())
            op = Operations.get_instance().get_operation(op_num)
            if (op["nbarg"] == 1):
                new_value = begin_str + '(' + op["op"] + ' @)' + end_str
                new_value = self.__generate_indiv_regressive_tree(new_value, mlc_parameters, indiv_type)
            else:
                # nbrag == 2
                new_value = begin_str + '(' + op["op"] + ' @ @)' + end_str
                new_value = self.__generate_indiv_regressive_tree(new_value, mlc_parameters, indiv_type)
                new_value = self.__generate_indiv_regressive_tree(new_value, mlc_parameters, indiv_type)

        return new_value

    def __crossover_tree(self, value_1, value_2, gen_param):
        res = self._eng.private_crossover_tree(self.get_matlab_object(), value_1, value_2, gen_param)
        return res[0], res[1], res[2] != 0

    def __mutate_tree(self, value, gen_param, mutation_type):
        res = self._eng.private_mutate_tree(self.get_matlab_object(), value, gen_param, mutation_type)
        return res[0], res[1] != 0

    def __str__(self):
        return "value: %s\n" % self.get_value() + \
               "type: %s\n" % self.get_type() + \
               "cost_history: %s\n" % self.get_cost_history() + \
               "evaluation_time: %s\n" % self.get_evaluation_time() + \
               "appearences: %s\n" % self.get_appearences() + \
               "hash: %s\n" % self.get_hash().__repr__() + \
               "formal: %s\n" % self.get_formal() + \
               "complexity: %s\n" % self.get_complexity()
