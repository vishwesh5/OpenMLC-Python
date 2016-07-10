import unittest

from MLC.matlab_engine import MatlabEngine
from MLC.individual.Individual import Individual


class IndividualTest(unittest.TestCase):
    def setUp(self):
        self._engine = MatlabEngine.engine()
        self._engine.workspace['wmlc'] = self._engine.MLC2()
        self._params = self._engine.eval('wmlc.parameters')

        self._individual_l0 = Individual()
        self._individual_l0.generate(self._params, "(root (cos 5.046))")

        self._individual_l1 = Individual()
        self._individual_l1.generate(self._params, "(root (log (sin (exp (tanh 3.628)))))")

        self._individual_l2 = Individual()
        self._individual_l2.generate(self._params, "(root (cos (* (+ (* -1.912 -9.178) (cos S0)) 3.113)))")

        self._individual_l3 = Individual()
        self._individual_l3.generate(self._params, "(root (log (/ (* (sin 4.37) (- -8.815 -3.902)) (log (+ 2.025 -8.685)))))")

        self._individual_l4 = Individual()
        self._individual_l4.generate(self._params, "(root S0)")

    def test_generate_from_value(self):
        individual = Individual()
        individual.generate(self._params, "(root (exp (tanh (- (tanh -8.049) (* 9.15 -6.848)))))")

        self.assertEquals(individual.get_value(), "(root (exp (tanh (- (tanh -8.049) (* 9.15 -6.848)))))")
        self.assertEquals(individual.get_type(), 'tree')
        self.assertEquals(len(individual.get_cost_history()), 0)
        self.assertEquals(len(individual.get_evaluation_time()), 0)
        self.assertEquals(individual.get_appearences(), 1)
        self.assertEquals(individual.get_hash(), -1.2245757275056848e-288)
        self.assertEquals(individual.get_formal(), "exp(tanh((tanh((-8.049)) - (9.15 .* (-6.848)))))")
        self.assertEquals(individual.get_complexity(), 20)

    def test_random_generate(self):
        # set random seed
        self._engine.rand('seed', 50.0, nargout=0)
        individual = Individual()
        individual.generate(self._params, 3)

        self.assertEquals(individual.get_value(),"(root (cos (+ (sin (log -0.7648)) (exp (tanh 3.628)))))")
        self.assertEquals(individual.get_type(), 'tree')
        self.assertEquals(len(individual.get_cost_history()), 0)
        self.assertEquals(len(individual.get_evaluation_time()), 0)
        self.assertEquals(individual.get_appearences(), 1)
        self.assertEquals(individual.get_hash(), -1.4777973157426358e-58)
        self.assertEquals(individual.get_formal(),"cos((sin(my_log((-0.7648))) + exp(tanh(3.628))))")
        self.assertEquals(individual.get_complexity(), 24)

    def test_compare(self):
        individual_1 = Individual()
        individual_1.generate(self._params, "(root (exp (tanh (- (tanh -8.049) (* 9.15 -6.848)))))")

        individual_2 = Individual()
        individual_2.generate(self._params, "(root (exp (tanh (- (tanh -8.049) (* 9.15 -6.848)))))")

        self.assertTrue(individual_1.compare(individual_2))
        self.assertEquals(individual_1.get_hash(), individual_2.get_hash())

        individual_different = Individual()
        individual_different.generate(self._params, "(root (cos (+ (sin (log -0.7648)) (exp (tanh 3.628)))))")

        self.assertFalse(individual_1.compare(individual_different))
        self.assertNotEquals(individual_1.get_hash(), individual_different.get_hash())

    def test_compare_random_individuals(self):
        self._engine.rand('seed', 50.0, nargout=0)
        individual_1 = Individual()
        individual_1.generate(self._params, 3)

        self._engine.rand('seed', 50.0, nargout=0)
        individual_2 = Individual()
        individual_2.generate(self._params, 3)

        self.assertTrue(individual_1.compare(individual_2))
        self.assertEquals(individual_1.get_hash(), individual_2.get_hash())

    def test_generate_individuals_types(self):
        self._engine.rand('seed', 50.0, nargout=0)
        individual = Individual()

        individual.generate(self._params, 0)
        self._assert_individual(individual, complexity=4,
                                hash=3.9424597980921636e+70,
                                value="(root (cos 5.046))",
                                formal="cos(5.046)")

        individual.generate(self._params, 1)
        self._assert_individual(individual, complexity=19,
                                hash=3.4383822393862387e+193,
                                value="(root (log (sin (exp (tanh 3.628)))))",
                                formal="my_log(sin(exp(tanh(3.628))))")

        individual.generate(self._params, 2)
        self._assert_individual(individual, complexity=13,
                                hash=3.159746489284278e-200,
                                value="(root (cos (* (+ (* -1.912 -9.178) (cos S0)) 3.113)))",
                                formal="cos(((((-1.912) .* (-9.178)) + cos(S0)) .* 3.113))")

        individual.generate(self._params, 3)
        self._assert_individual(individual, complexity=22,
                                hash=-6.231379895727156e-22,
                                value="(root (log (/ (* (sin 4.37) (- -8.815 -3.902)) (log (+ 2.025 -8.685)))))",
                                formal="my_log((my_div((sin(4.37) .* ((-8.815) - (-3.902))),my_log((2.025 + (-8.685))))))")

        individual.generate(self._params, 4)
        self._assert_individual(individual, complexity=1,
                                hash=6.356047396756108e+217,
                                value="(root S0)",
                                formal="S0")


    def test_crossover_same_level_0(self):
        self._engine.rand('seed', 50.0, nargout=0)

        individual_1 = Individual()
        individual_1.generate(self._params, "(root (cos 5.046))")
        individual_2 = Individual()
        individual_2.generate(self._params, "(root (cos 5.046))")
        new_ind_1, new_ind_2, fail = individual_1.crossover(individual_2, self._params)

        self.assertFalse(fail)

        self._assert_individual(new_ind_1, complexity=4,
                                hash=3.9424597980921636e+70,
                                value="(root (cos 5.046))",
                                formal="cos(5.046)")

        self._assert_individual(new_ind_2, complexity=4,
                                hash=3.9424597980921636e+70,
                                value="(root (cos 5.046))",
                                formal="cos(5.046)")

    def test_crossover_same_level_2(self):
        individual_1 = Individual()
        individual_1.generate(self._params, "(root (cos (* (+ (* -1.912 -9.178) (cos S0)) 3.113)))")
        individual_2 = Individual()
        individual_2.generate(self._params, "(root (cos (* (+ (* -1.912 -9.178) (cos S0)) 3.113)))")
        new_ind_1, new_ind_2, fail = individual_1.crossover(individual_2, self._params)

        self._assert_individual(new_ind_1, complexity=9,
                                hash=3.988734956834988e-46,
                                value="(root (cos (* (cos S0) 3.113)))",
                                formal="cos((cos(S0) .* 3.113))")

        self._assert_individual(new_ind_2, complexity=17,
                                hash=-4.5180143959687205e-194,
                                value="(root (cos (* (+ (* -1.912 -9.178) (+ (* -1.912 -9.178) (cos S0))) 3.113)))",
                                formal="cos(((((-1.912) .* (-9.178)) + (((-1.912) .* (-9.178)) + cos(S0))) .* 3.113))")

    def test_crossover_same_level_4(self):
        individual_1 = Individual()
        individual_1.generate(self._params, "(root S0)")
        individual_2 = Individual()
        individual_2.generate(self._params, "(root S0)")
        new_ind_1, new_ind_2, fail = individual_1.crossover(individual_2, self._params)

        # crossover with individual type 4 should fail
        self.assertTrue(fail)
        self.assertIsNone(new_ind_1)
        self.assertIsNone(new_ind_2)

    def test_crossover_same_individual(self):
        self._engine.rand('seed', 60.0, nargout=0)
        new_ind_1, new_ind_2, fail = self._individual_l2.crossover(self._individual_l2, self._params)

        self._assert_individual(new_ind_1, complexity=14,
                                hash=-5.513419727757863e-64,
                                value="(root (cos (* (+ (cos S0) (cos S0)) 3.113)))",
                                formal="cos(((cos(S0) + cos(S0)) .* 3.113))")

        self._assert_individual(new_ind_2, complexity=12,
                                hash=1.0176840735245977e-58,
                                value="(root (cos (* (+ (* -1.912 -9.178) (* -1.912 -9.178)) 3.113)))",
                                formal="cos(((((-1.912) .* (-9.178)) + ((-1.912) .* (-9.178))) .* 3.113))")

    def test_crossover_different_levels_2_3(self):
        self._engine.rand('seed', 60.0, nargout=0)
        new_ind_1, new_ind_2, fail = self._individual_l2.crossover(self._individual_l3, self._params)

        self.assertFalse(fail)

        self._assert_individual(new_ind_1, complexity=13,
                                hash=-9.469742614799921e-82,
                                value="(root (cos (* (+ (- -8.815 -3.902) (cos S0)) 3.113)))",
                                formal="cos(((((-8.815) - (-3.902)) + cos(S0)) .* 3.113))")

        self._assert_individual(new_ind_2, complexity=22, hash=1.1086575260573593e-164,
                                value="(root (log (/ (* (sin 4.37) (* -1.912 -9.178)) (log (+ 2.025 -8.685)))))",
                                formal="my_log((my_div((sin(4.37) .* ((-1.912) .* (-9.178))),my_log((2.025 + (-8.685))))))")

        # make another to crossover in order to check randomness
        new_ind_1, new_ind_2, fail = self._individual_l2.crossover(self._individual_l3, self._params)

        self.assertFalse(fail)

        self._assert_individual(new_ind_1, complexity=3,
                                hash=1.4944726960633078e+183,
                                value="(root (- -8.815 -3.902))",
                                formal="((-8.815) - (-3.902))")

        self._assert_individual(new_ind_2, complexity=32,
                                hash=-2.8342820253446463e-170,
                                value="(root (log (/ (* (sin 4.37) (cos (* (+ (* -1.912 -9.178) (cos S0)) 3.113))) (log (+ 2.025 -8.685)))))",
                                formal="my_log((my_div((sin(4.37) .* cos(((((-1.912) .* (-9.178)) + cos(S0)) .* 3.113))),my_log((2.025 + (-8.685))))))")

    def test_crossover_different_levels_0_3(self):
        self._engine.rand('seed', 60.0, nargout=0)
        new_ind_1, new_ind_2, fail = self._individual_l0.crossover(self._individual_l3, self._params)

        self.assertFalse(fail)

        self._assert_individual(new_ind_1, complexity=3,
                                hash=1.4944726960633078e+183,
                                value="(root (- -8.815 -3.902))",
                                formal="((-8.815) - (-3.902))")

        self._assert_individual(new_ind_2, complexity=23,
                                hash=-1.2921173740151353e-34,
                                value="(root (log (/ (* (sin 4.37) (cos 5.046)) (log (+ 2.025 -8.685)))))",
                                formal="my_log((my_div((sin(4.37) .* cos(5.046)),my_log((2.025 + (-8.685))))))")

    def test_crossover_different_levels_0_4(self):
        self._engine.rand('seed', 60.0, nargout=0)
        new_ind_1, new_ind_2, fail = self._individual_l0.crossover(self._individual_l4, self._params)

        # crossover with individual type 4 should fail
        self.assertTrue(fail)
        self.assertIsNone(new_ind_1)
        self.assertIsNone(new_ind_2)

    def test_mutate_remove_subtree_and_replace(self):
        self._engine.rand('seed', 60.0, nargout=0)
        new_ind, fail = self._individual_l3.mutate(self._params, Individual.MUTATION_REMOVE_SUBTREE_AND_REPLACE)

        self.assertFalse(fail)
        self._assert_individual(new_ind,complexity=138,
                                hash=-1.3367784216959267e-151,
                                value="(root (log (/ (* (sin 4.37) (- -8.815 -3.902)) (+ (+ (tanh (- -4.368 (+ (tanh (sin (/ (- (- (* (tanh S0) -6.729) -0.1076) S0) 8.669))) (log 5.463)))) (* (+ (- (/ (- 2.524 (log (cos (/ (* (- -2.225 -2.147) (* -5.252 0.2113)) -3.195)))) (cos (cos S0))) (sin S0)) (sin (cos S0))) (+ (- (cos -2.682) (/ -0.3451 (tanh (exp (sin (/ (- 3.137 S0) (* S0 (log -0.5594)))))))) (cos (tanh S0))))) (/ -4.114 -9.877)))))",
                                formal="my_log((my_div((sin(4.37) .* ((-8.815) - (-3.902))),((tanh(((-4.368) - (tanh(sin((my_div((((tanh(S0) .* (-6.729)) - (-0.1076)) - S0),8.669)))) + my_log(5.463)))) + ((((my_div((2.524 - my_log(cos((my_div((((-2.225) - (-2.147)) .* ((-5.252) .* 0.2113)),(-3.195)))))),cos(cos(S0)))) - sin(S0)) + sin(cos(S0))) .* ((cos((-2.682)) - (my_div((-0.3451),tanh(exp(sin((my_div((3.137 - S0),(S0 .* my_log((-0.5594))))))))))) + cos(tanh(S0))))) + (my_div((-4.114),(-9.877)))))))")

        # do a second mutation
        new_ind, fail = self._individual_l3.mutate(self._params, Individual.MUTATION_REMOVE_SUBTREE_AND_REPLACE)

        self.assertFalse(fail)
        self._assert_individual(new_ind, complexity=25,
                                hash=-3.1357260586196107e+180,
                                value="(root (log (/ (* (sin (sin 6.721)) (- -8.815 -3.902)) (log (+ 2.025 -8.685)))))",
                                formal="my_log((my_div((sin(sin(6.721)) .* ((-8.815) - (-3.902))),my_log((2.025 + (-8.685))))))")

    def test_mutate_reparametrization(self):
        self._engine.rand('seed', 60.0, nargout=0)
        new_ind, fail = self._individual_l3.mutate(self._params, Individual.MUTATION_REPARAMETRIZATION)

        self.assertFalse(fail)
        self._assert_individual(new_ind, complexity=22,
                                hash=14269175.128717355,
                                value="(root (log (/ (* (sin 5.491) (- 2.581 -9.526)) (log (+ 4.055 -9.595)))))",
                                formal="my_log((my_div((sin(5.491) .* (2.581 - (-9.526))),my_log((4.055 + (-9.595))))))")


        # do a second mutation
        new_ind, fail = self._individual_l3.mutate(self._params, Individual.MUTATION_REPARAMETRIZATION)

        self.assertFalse(fail)
        self._assert_individual(new_ind, complexity=22,
                                hash=-1.116096220690224e+75,
                                value="(root (log (/ (* (sin 1.082) (- 9.162 3.702)) (log (+ -6.897 -9.646)))))",
                                formal="my_log((my_div((sin(1.082) .* (9.162 - 3.702)),my_log(((-6.897) + (-9.646))))))")

    def test_mutate_hoist(self):
        self._engine.rand('seed', 60.0, nargout=0)
        new_ind, fail = self._individual_l3.mutate(self._params, Individual.MUTATION_HOIST)

        self.assertFalse(fail)
        self._assert_individual(new_ind, complexity=17,
                                hash=2.066009957759577e+180,
                                value="(root (/ (* (sin 4.37) (- -8.815 -3.902)) (log (+ 2.025 -8.685))))",
                                formal="(my_div((sin(4.37) .* ((-8.815) - (-3.902))),my_log((2.025 + (-8.685)))))")

        # do a second mutation
        new_ind, fail = self._individual_l3.mutate(self._params, Individual.MUTATION_HOIST)

        self.assertFalse(fail)
        self._assert_individual(new_ind, complexity=3,
                                hash=1.4944726960633078e+183,
                                value="(root (- -8.815 -3.902))",
                                formal="((-8.815) - (-3.902))")

    def test_mutate_shrink(self):
        self._engine.rand('seed', 60.0, nargout=0)
        new_ind, fail = self._individual_l3.mutate(self._params, Individual.MUTATION_SHRINK)

        self.assertFalse(fail)
        self._assert_individual(new_ind, complexity=15,
                                hash=-2.277899705381213e+222,
                                value="(root (log (/ (* (sin 4.37) (- -8.815 -3.902)) -9.526)))",
                                formal="my_log((my_div((sin(4.37) .* ((-8.815) - (-3.902))),(-9.526))))")

        # do a second mutation
        new_ind, fail = self._individual_l3.mutate(self._params, Individual.MUTATION_SHRINK)

        self.assertFalse(fail)
        self._assert_individual(new_ind, complexity=20,
                                hash=1.2070346203022018e+173,
                                value="(root (log (/ (* (sin 4.37) S0) (log (+ 2.025 -8.685)))))",
                                formal="my_log((my_div((sin(4.37) .* S0),my_log((2.025 + (-8.685))))))")

    def mutate_random_choice(self):
        self._engine.rand('seed', 60.0, nargout=0)

        # mutate random: 4
        new_ind, fail = self._individual_l3.mutate(self._params)
        self.assertFalse(fail)
        self._assert_individual(new_ind, complexity=20,
                                hash=1.2070346203022018e+173,
                                value="(root (log (/ (* (sin 4.37) S0) (log (+ 2.025 -8.685)))))",
                                formal="my_log((my_div((sin(4.37) .* S0),my_log((2.025 + (-8.685))))))")

        # mutate random: 1
        new_ind, fail = self._individual_l3.mutate(self._params)
        self.assertFalse(fail)
        self._assert_individual(new_ind, complexity=24,
                                hash=-9.739328993463583e+261,
                                value="(root (log (/ (* (log S0) (- -8.815 -3.902)) (log (+ 2.025 -8.685)))))",
                                formal="my_log((my_div((my_log(S0) .* ((-8.815) - (-3.902))),my_log((2.025 + (-8.685))))))")

        # mutate random: 2
        new_ind, fail = self._individual_l3.mutate(self._params)
        self.assertFalse(fail)
        self._assert_individual(new_ind, complexity=22,
                                hash=1.5210419679169233e+36,
                                value="(root (log (/ (* (sin 3.907) (- -8.597 4.057)) (log (+ 8.244 5.242)))))",
                                formal="my_log((my_div((sin(3.907) .* ((-8.597) - 4.057)),my_log((8.244 + 5.242)))))")

    def _assert_individual(self, individual, value, hash, formal, complexity):
        self.assertEquals(individual.get_value(), value)
        self.assertEquals(individual.get_type(), 'tree')
        self.assertEquals(len(individual.get_cost_history()), 0)
        self.assertEquals(len(individual.get_evaluation_time()), 0)
        self.assertEquals(individual.get_appearences(), 1)
        self.assertEquals(individual.get_hash(), hash)
        self.assertEquals(individual.get_formal(), formal)
        self.assertEquals(individual.get_complexity(), complexity)