import os
import sys
import time

from MLC.api.mlc import DuplicatedExperimentError
from MLC.Common import util
from MLC.Log.log import get_gui_logger
from MLC.mlc_parameters.mlc_parameters import Config

logger = get_gui_logger()

"""
Object that will encapsulate all the operations related with the ABM of projects
"""


class ExperimentsManager():

    def __init__(self, mlc_local, gui_config):
        self._gui_config = gui_config
        self._mlc_local = mlc_local

        self._experiment_list = []
        self._experiment_info_dict = {}

    def load_experiments_info(self):
        # Clean the experiment list before filling it
        start_time = time.time()
        self._experiment_list = []

        # Find all the projects in the workspace directory
        workspace_dir = self._gui_config.get('MAIN', 'workspace')
        self._experiment_list = self._mlc_local.get_workspace_experiments()

        logger.info('[GUI_EXPERIMENT_MANAGER] [LOAD_EXPERIMENTS_INFO] - '
                    'Projects in the workspace: {0}'
                    .format(self._experiment_list))
        self._experiment_list.sort()
        self._load_experiment_info_per_project()

        elapsed_time = time.time() - start_time
        logger.debug("[GUI_EXPERIMENT_MANAGER] [LOAD_EXPERIMENTS_INFO] - "
                     "Experiments info updated. Time elapsed: {0}"
                     .format(elapsed_time))

    def load_experiment_info(self, experiment_name):
        start_time = time.time()
        self._mlc_local.open_experiment(experiment_name)
        experiment_info = self._mlc_local.get_experiment_info(experiment_name)
        self._mlc_local.close_experiment(experiment_name)

        # Update the experiment description
        description = ""
        for key, value in experiment_info.iteritems():
            description += "<b>" + str(key) + ":</b> " + str(value) + "<br>"
        self._experiment_info_dict[experiment_name] = description

        # Log the amount of time spent in every experiment info update
        amount_individuals = experiment_info["individuals"]
        elapsed_time = time.time() - start_time
        logger.debug("[GUI_EXPERIMENT_MANAGER] [LOAD_EXPERIMENTS_INFO] - "
                     "Experiment {0} info updated. "
                     "Amount Individuals: {1}. Time elapsed: {2}"
                     .format(experiment_name, amount_individuals, elapsed_time))

    def add_experiment(self, experiment_name):
        try:
            self._mlc_local.new_experiment(experiment_name)
            logger.info("[GUI_EXPERIMENT_MANAGER] [ADD_EXPERIMENT] - "
                        "Added experiment {0}".format(experiment_name))
        except DuplicatedExperimentError:
            logger.error("[GUI_EXPERIMENT_MANAGER] [ADD_EXPERIMENT] - "
                         "Error while adding experiment {0}"
                         .format(experiment_name))
            return False

        # Experiment succesfully loaded. Update its experiment_info
        self._experiment_list.append(experiment_name)
        self.load_experiment_info(experiment_name)
        return True

    def add_experiment_even_if_repeated(self, experiment_name):
        if experiment_name in self._experiment_list:
            logger.debug("[GUI_EXPERIMENT_MANAGER] [ADD_EXPERIMENT_EVEN_IF_REPEATED] "
                         "Proceed to remove a experiment without one of its files")
            self._mlc_local.delete_experiment(experiment_name)
        self.add_experiment(experiment_name)

    def remove_experiment(self, experiment_name):
        try:
            self._mlc_local.delete_experiment(experiment_name)
        except OSError:
            logger.error("[GUI_EXPERIMENT_MANAGER] [REMOVE_EXPERIMENT] - "
                         "Experiment file {0} could not be removed".format(file))
            return False

        self._experiment_list.remove(experiment_name)
        del self._experiment_info_dict[experiment_name]
        return True

    def import_experiment(self, experiment_path):
        experiment_name = os.path.split(experiment_path)[1].split(".")[0]
        self._mlc_local.import_experiment(experiment_path)
        self._experiment_list.append(experiment_name)
        self.load_experiment_info(experiment_name)

    def export_experiment(self, export_dir, experiment_name):
        try:
            export_path = os.path.join(export_dir, experiment_name + ".mlc")
            source_path = os.path.join(self._mlc_local.get_working_dir(), experiment_name)
            util.make_tarfile(export_path, source_path)
            logger.info("[GUI_EXPERIMENT_MANAGER] [EXPORT] - "
                        "Experiment {0} was succesfully exported. It is stored in {1}"
                        .format(experiment_name, export_dir))
        except Exception, err:
            logger.error("[GUI_EXPERIMENT_MANAGER] [EXPORT] - "
                         "An error ocurred while exporting project {0}. "
                         "Error {1}".format(experiment_name, err))
            raise

    def get_experiment_list(self):
        return self._experiment_list

    def get_experiment_info(self, experiment_name):
        try:
            return self._experiment_info_dict[experiment_name]
        except KeyError:
            logger.debug("[GUI_EXPERIMENT_MANAGER] [GET_EXPERIMENTS_INFO] - "
                         "Experiment {0} info not found.".format(experiment_name))
        return None

    def _load_experiment_info_per_project(self):
        self._experiment_info_dict = {}
        for experiment_name in self._experiment_list:
            self.load_experiment_info(experiment_name)
