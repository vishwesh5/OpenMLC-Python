#!/usr/bin/python3.6.1
# -*- coding: utf-8 -*-
# MLC (Machine Learning Control): A genetic algorithm library to solve chaotic problems
# Copyright (C) 2015-2017, Thomas Duriez (thomas.duriez@gmail.com)
# Copyright (C) 2015, Adrian Durán (adrianmdu@gmail.com)
# Copyright (C) 2015-2017, Ezequiel Torres Feyuk (ezequiel.torresfeyuk@gmail.com)
# Copyright (C) 2016-2017, Marco Germano Zbrun (marco.germano@intraway.com)
# Copyright (C) 2016-2017, Raúl Lopez Skuba (raulopez0@gmail.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

import numpy as np #checked
import importlib #checked
from MLC.Application import Application #checked
from MLC.Common.RandomManager import RandomManager #checked
from MLC.mlc_parameters.mlc_parameters import Config #checked
from MLC.Simulation import Simulation #checked
from MLC.Log.log import set_logger #checked


def initialize_config(): #checked
    config = Config.get_instance()
    config.read('conf/configuration.ini')
    return config


def main():
    # MATLAB random numbers, used in integration tests
    RandomManager.load_random_values("./tests/integration_tests/matlab_randoms.txt") #checked

    # load configuration
    config = initialize_config() #checked

    # set logger
    log_mode = config.get('LOGGING', 'logmode') #checked
    set_logger(log_mode) #checked

    simulation = Simulation("tmpExperiment") #checked
    mlc = Application(simulation)
    mlc.go(to_generation=3, display_best=False)
    raw_input("Press enter to continue...")

if __name__ == "__main__":
    main()
