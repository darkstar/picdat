"""
Is responsible for collecting all information of note from PerfStat output
"""
import logging
import sys

import sysstat_module
import statit_module
import per_iteration_module

__author__ = 'Marie Lohbeck'
__copyright__ = 'Copyright 2017, Advanced UniByte GmbH'


# license notice:
#
# This file is part of PicDat.
# PicDat is free software: you can redistribute it and/or modify it under the terms of the GNU
# General Public (at your option) any later version.
#
# PicDat is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with PicDat. If not,
# see <http://www.gnu.org/licenses/>.


def search_for_number_of_iterations(line):
    """
    Recognizes and, if applicable, filters the number of iterations planned in a
    PerfStat measuring from a string.
    :param line: A string from a PerfStat output file which should be searched
    :return: the planned number of iteration, if given, or zero otherwise
    """
    if 'ITERATIONS,' in line:
        # get the 3rd word of this line, which should be the number of iterations
        number_string = (line.split()[2])
        # get rid of a quotation mark and parse to int
        return int(number_string[1:-1])
    else:
        return 0


def found_iteration_begin(line, start_times, last_end_time):
    """
    Searches for an iteration begin marker in a string and, if applicable,
    adds the timestamp given in this marker to start_times.
    :param line: A string from a PerfStat output file which should be searched
    :param start_times: A list of all iteration start timestamps
    :param last_end_time: The last collected timestamp of an iteration's end. It would be
    used as recent timestamp, in case that there is no timestamp available in line on account of
    a PerfStat bug.
    :return: True, if the line contains an iteration begin marker, or False otherwise
    """
    if 'BEGIN Iteration' in line:
        start_times.append(per_iteration_module.get_iteration_timestamp(line, last_end_time))
        return True
    else:
        return False


def found_iteration_end(line, end_times, last_start_time):
    """
    Searches for an iteration end marker in a string and, if applicable,
    adds the timestamp given in this marker to end_times.
    :param line: A string from a PerfStat output file which should be searched
    :param end_times: A list of all iteration end timestamps
    :param last_start_time: The last collected timestamp of an iteration's beginning. It would be
    used as recent timestamp, in case that there is no timestamp available in line on account of
    a PerfStat bug.
    :return: True, if the line contains an iteration end marker, or False otherwise
    """
    if 'END Iteration' in line:
        end_times.append(per_iteration_module.get_iteration_timestamp(line, last_start_time))
        return True
    else:
        return False


def final_iteration_validation(expected_iteration_number, iteration_beginnings, iteration_endings):
    """
    Test whether the PerfStat terminated and is complete
    :param expected_iteration_number: the iteration number as it is defined in the PerfStat
    output header
    :param iteration_beginnings: the number of iterations which were actually started
    :param iteration_endings: the number of iterations which actually terminated
    :return: a string which informs the user whether the data are complete and how they will be
    handled
    """
    if expected_iteration_number == iteration_beginnings == iteration_endings:
        logging.info('Planned number of iterations was executed correctly.')
    elif expected_iteration_number != iteration_beginnings:
        logging.warning('Warning: PerfStat output is incomplete; some iterations weren\'t '
                        'executed. If there is an iteration which wasn\'t finished correctly, '
                        'it won\'t be considered in the resulting charts!')
    else:
        logging.warning('PerfStat output is incomplete; the last iteration didn\'t terminate. It '
                        'won\'t be considered in the resulting charts!')


def combine_results(per_iteration_object, sysstat_object, statit_object):
    """
    This function sticks the results of all three request types together.
    :param per_iteration_object: object that holds all relevant information about 
    per_iteration_requests.
    :param sysstat_object: objet that holds all relevant information about sysstat_requests.
    :param statit_object: object that holds all relevant inforamtion read from statit blocks.
    :return: All headers in one list, followed by all values in one list.
    """

    per_iteration_headers = per_iteration_object.flat_headers
    per_iteration_values = per_iteration_object.flat_values

    sysstat_percent_headers = sysstat_object.percent_headers
    sysstat_percent_values = sysstat_object.percent_values
    sysstat_mbs_headers = sysstat_object.mbs_headers
    sysstat_mbs_values = sysstat_object.mbs_values
    sysstat_iops_headers = sysstat_object.iops_headers
    sysstat_iops_values = sysstat_object.iops_values

    statit_headers = statit_object.flat_headers
    statit_values = statit_object.flat_values

    logging.debug('per_iteration_headers: %s', per_iteration_headers)
    logging.debug('per_iteration_values: %s', per_iteration_values)
    logging.debug('sysstat_percent_headers: %s', sysstat_percent_headers)
    logging.debug('sysstat_percent_values: %s', sysstat_percent_values)
    logging.debug('sysstat_mbs_headers: %s', sysstat_mbs_headers)
    logging.debug('sysstat_mbs_values: %s', sysstat_mbs_values)
    logging.debug('sysstat_iops_headers: %s', sysstat_iops_headers)
    logging.debug('sysstat_iops_values: %s', sysstat_iops_values)
    logging.debug('statit_headers: %s', statit_headers)
    logging.debug('statit_values: %s', statit_values)

    combined_headers = per_iteration_headers + [sysstat_percent_headers, sysstat_mbs_headers,
                                                sysstat_iops_headers, statit_headers]
    combined_values = per_iteration_values + [sysstat_percent_values, sysstat_mbs_values,
                                              sysstat_iops_values, statit_values]

    combined_requests = [per_iteration_object, sysstat_object, statit_object]

    return combined_requests, combined_headers, combined_values


def read_data_file(perfstat_data_file):
    """
    Reads the requested information from a PerfStat output file and collects them into several lists
    :param perfstat_data_file: file which should be read
    :return: a list of all headers and a list of all values. The headers are grouped by table.
    The values are grouped by table and by row. Each value row already starts with its timestamp.
    Additionally, it returns the luns_available boolean which says, whether lun values appeared in
    the PerfStat at all.
    """

    # initialisation

    # number of iterations like it is defined in the file's header:
    number_of_iterations = 0

    # number of iterations that actually has been started:
    iteration_begin_counter = 0
    # the relating time stamps:
    start_times = []

    # number of iterations that actually terminated:
    iteration_end_counter = 0
    # the relating time stamps:
    end_times = []

    # this object collects all information the program finds outside of sysstat and statit blocks
    per_iteration_object = per_iteration_module.PerIterationClass()

    # this object collects all information the program finds during processing sysstat_x_1sec blocks
    sysstat_object = sysstat_module.SysstatClass()

    # this object collects all information the program finds during processing statit blocks
    statit_object = statit_module.StatitClass()

    # collecting data

    with open(perfstat_data_file, 'r') as data:
        for line in data:
            if not sysstat_object.inside_sysstat_block or not sysstat_object.sysstat_header_needed:
                line = line.strip()

            # first, search for the planned number of iteration in the file's header.
            # Once set, skip this check.
            if number_of_iterations == 0:
                number_of_iterations = search_for_number_of_iterations(line)
                continue

            if sysstat_object.inside_sysstat_block:
                sysstat_object.process_sysstat_block(line)
                continue

            if '=-=-=-=-=-=' in line:
                # filter for iteration beginnings and endings
                if len(end_times) == 0:
                    last_end_time = None
                else:
                    last_end_time = end_times[-1]
                if found_iteration_begin(line, start_times, last_end_time):
                    iteration_begin_counter += 1
                elif found_iteration_end(line, end_times, start_times[-1]):
                    iteration_end_counter += 1
                    # write an empty line into the sysstat tables to cut line in resulting charts
                    # between different iterations (not after the last):
                    if iteration_end_counter != number_of_iterations:
                        sysstat_object.add_empty_lines()

                elif sysstat_object.found_sysstat_1sec_begin(line):
                    sysstat_object.collect_sysstat_timestamp(next(data), start_times[-1])

                    line = next(data)
                    while len(line.strip()) == 0:
                        line = next(data)

                continue

            if statit_object.inside_statit_block:
                statit_object.process_disc_stats(line)
                continue

            if statit_object.check_statit_begin(line):
                continue
            if start_times:
                per_iteration_object.process_per_iteration_requests(line, start_times[-1])

    data.close()

    # postprocessing

    if number_of_iterations == 0:
        logging.warning('The file you entered as PerfStat output doesn\'t even contain, how many '
                        'iterations it handles. Maybe, it isn\'t a PerfStat file at all.')
        sys.exit(1)

    final_iteration_validation(number_of_iterations, iteration_begin_counter, iteration_end_counter)

    # simplify data structures for per-iteration data
    per_iteration_object.rework_per_iteration_data(start_times)

    statit_object.rework_statit_data(end_times)

    sysstat_object.rework_sysstat_data()

    return combine_results(per_iteration_object, sysstat_object, statit_object)
