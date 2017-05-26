#!/usr/bin/python
# -*- coding: utf-8 -*-

# Docstring:
"""This module provides a series of tools to plot experiments data sets used
in Montepython altogether with the predictions computed by CLASS"""

import sys
import os
from collections import OrderedDict


class Data():
    """Data class parallel to MontePython's defined only with the required
    parameters to compute likelihoods"""

    def __init__(self, path_MP, path_likelihoods, experiments, path_data='data'):
        self.path_likelihoods = path_likelihoods
        self.path['root'] = os.path.abspath(path_MP)
        self.path['MontePython'] = self.path['root'] + '/montepython'
        self.data['data'] = os.path.join(self.path['root'], path_data)
        self.log_flag = False  # This makes Likelihood to not write a log file
        self.experiments = experiments
        self.cosmo_arguments = {}
        """
        Simple dictionary that will serve as a communication interface with the
        cosmological code. It contains all the parameters for the code that
        will not be set to their default values.

        :rtype:   dict

        Documentation from montepython/data.py (Modified)
        """
        self.mcmc_parameters = OrderedDict()
        """
        Ordered dictionary of dictionaries, it will contain the 'nuisance'
        parameters which are the only used from this variable in the Likelihood
        class.  Every parameter name will be the key of a dictionary, containing
        the current value and its scale.

        Example: OrderedDict(['A_planck', {'current': value, 'scale': value2}])

        :rtype: ordereddict

        Documentation from montepython/data.py (Modified)
        """
        self.cosmological_module_name = 'CLASS'

        sys.path.insert(0, self.path['root'])

    def get_mcmc_parameters(self, table_of_strings):
        """
        Returns an ordered array of parameter names filtered by
        `table_of_strings`.

        Parameters
        ----------
        table_of_strings : list
            List of strings whose role and status must be matched by a
            parameter. For instance,

            >>> data.get_mcmc_parameters(['varying'])
            ['omega_b', 'h', 'amplitude', 'other']

            will return a list of all the varying parameters, both
            cosmological and nuisance ones (derived parameters being `fixed`,
            they wont be part of this list). Instead,

            >>> data.get_mcmc_parameters(['nuisance', 'varying'])
            ['amplitude', 'other']

            will only return the nuisance parameters that are being varied.

        Copied from montepython/data.py

        """
        table = []
        for key, value in self.mcmc_parameters.iteritems():
            number = 0
            for subvalue in value.itervalues():
                for string in table_of_strings:
                    if subvalue == string:
                        number += 1
            if number == len(table_of_strings):
                table.append(key)
        return table

    def set_params(self, params):
        """
        Given a classy parameters dictionary fill the data.cosmo_arguments
        variable.

        Paramters_smg can be set as in classy or as in MontePython.
        """

        if 'parameters_smg' in params:
            parameters_smg = params['parameters_smg'].split(',')

            for i, value in enumerate(parameters_smg):
                params['parameters_smg__{i}'.format(i+1)] = value

            del params['paramters_smg']

        self.cosmo_arguments = params

    def set_nuisance(self, nuisance):
        """Input a dictionary or list of list containing the nuisance parameter
        name and its value. All scales are put to 1."""

        if type(nuisance) is dict:
            nuisance = nuisance.iteritems()

        for key, value in nuisance:
            self.mcmc_parameters[key] = {'current': value, 'scale': 1}

