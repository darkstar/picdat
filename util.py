"""
Provides some functions other modules may use.
"""
import os
from zipfile import ZipFile

try:
    import pytz
except ImportError:
    pytz = None

from orderedset import OrderedSet
from table import Table
from requests import PER_ITERATION_REQUESTS, SYSSTAT_PERCENT_UNIT, SYSSTAT_MBS_UNIT, SYSSTAT_NO_UNIT
import constants
import tempfile

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

def data_type(filepath):
    """
    Gets a file's data type.
    :param filepath: The path from a file as String, you want to have the data type for.
    :return: The data type as String.
    """
    return filepath.split('.')[-1]


def get_month_number(month_string):
    """
    Find the corresponding month number to a simple month string
    :param month_string: String describing a month's shortcut, three letters long, first letter
    upper case.
    :return: The corresponding month number
    """
    return {
        'Jan': 1,
        'Feb': 2,
        'Mar': 3,
        'Apr': 4,
        'May': 5,
        'Jun': 6,
        'Jul': 7,
        'Aug': 8,
        'Sep': 9,
        'Oct': 10,
        'Nov': 11,
        'Dec': 12
    }[month_string]


def get_timezone(tz_string):
    """
    Creates a pytz.timezone object from a timezone String as it appears in a PerfStat file.
    Usually, the module pytz can handle such Strings by itself, but some timezone identifiers
    need translation. (For example, CEST is no real timezone but the summer equivalent of CET,
    and pytz wants to handle it as CET.)
    :param tz_string: A timezone identifier from a PerfStat file as String.
    :return: A pytz.timezone object.
    """

    print(tz_string)

    tz_switch = {
        'CEST': pytz.timezone('CET')
    }

    if tz_string in tz_switch:
        return tz_switch[tz_string]

    else:
        try:
            return pytz.timezone(tz_string)
        except pytz.UnknownTimeZoneError:
            print('Warning: PerfStat file contains timezone information PicDat is unable to handle '
                  'with. Be aware of possible confusion with time values in charts.')
            print('Unexpected timezone identifier: ' + tz_strin)


def inner_ord_set_insertion(outer_list, index, item):
    """
    Inserts an item into a list of OrderedDicts. Inserts the item in the OrderedDict at the place of
    index. Is index bigger than the number of existing OrderedDicts, new OrderedDicts inside the
    list will be created.
    :param outer_list: The list of OrderedDicts you want to insert an item in.
    :param index: The OrderedDict's number, in which the item should be inserted in.
    :param item: The item you want insert.
    :return: None
    """
    if len(outer_list) <= index:
        missing_entries = index + 1 - len(outer_list)
        for _ in range(missing_entries):
            outer_list.append(OrderedSet())

    outer_list[index].add(item)


def tablelist_insertion(tablelist, list_index, iteration, instance, item):
    """
    Inserts a table item into a specific table in a list of tables. If the list index is bigger
    than the number of table elements in the list, table elements will be created.
    :param tablelist: A list of tables. The function will insert the item in one of those.
    :param list_index: The table's index in tablelist, you want to insert your item in.
    :param iteration: The number of iteration, your item belongs to - is needed to arrange
    elements inside one table.
    :param instance: The name as string of the instance, your item (which should be a value for
    this instance) belongs to - is needed to arrange
    elements inside one table.
    :param item: The table value you want to insert. It's related to a specific time and object
    instance, therefore it is the basis for a single measuring point in final charts.
    """
    if len(tablelist) <= list_index:
        missing_entries = list_index + 1 - len(tablelist)
        for _ in range(missing_entries):
            tablelist.append(Table())

    tablelist[list_index].insert(iteration, instance, item)


def empty_directory(preferred_directory_path):
    """
    Creates a directory which doesn't exist yet with a path, as close as possible to the
    preferred path.
    :param preferred_directory_path: The path you want to have the directory at.
    :return: The directory's name created actually.
    """
    directory_name = preferred_directory_path

    if os.path.exists(directory_name):
        i = 1
        while os.path.exists(directory_name):
            directory_name = preferred_directory_path + str(i)
            i += 1

    os.makedirs(directory_name)
    return directory_name


def get_units(luns_available):
    """
    Gets all units from a per_iteration_request dict. Also adds units for sysstat charts.
    :param luns_available: A boolean, whether lun values appeared in the PerfStat at all.
    :return: A list of all units.
    """
    unit_list = []
    for object_type in PER_ITERATION_REQUESTS:
        if not luns_available and object_type == 'lun':
            continue
        for request_tuple in PER_ITERATION_REQUESTS.get(object_type):
            unit = request_tuple[1]
            unit_list.append(unit)

    unit_list.append(SYSSTAT_PERCENT_UNIT)
    unit_list.append(SYSSTAT_MBS_UNIT)
    unit_list.append(SYSSTAT_NO_UNIT)

    return unit_list


def get_titles(luns_available):
    """
    Generates proper titles for charts.
    :param luns_available: A boolean, whether lun values appeared in the PerfStat at all.
    :return: A list of chart titles.
    """
    title_list = []
    for object_type in PER_ITERATION_REQUESTS:
        if not luns_available and object_type == 'lun':
            continue
        for request_tuple in PER_ITERATION_REQUESTS.get(object_type):
            aspect = request_tuple[0]
            title_list.append(object_type + ':' + aspect)

    title_list.append(constants.SYSSTAT_CHART_TITLE + ':percent')
    title_list.append(constants.SYSSTAT_CHART_TITLE + ':MBs')
    title_list.append(constants.SYSSTAT_CHART_TITLE + ':IOPS')

    return title_list


def get_object_ids(luns_available):
    """
    Gets all object IDs from a per_iteration_request. Also adds IDs for sysstat charts.
    :param luns_available: A boolean, whether lun values appeared in the PerfStat at all.
    :return: A list of all object IDs.
    """
    id_list = []
    for object_type in PER_ITERATION_REQUESTS:
        if not luns_available and object_type == 'lun':
            continue
        for request_tuple in PER_ITERATION_REQUESTS.get(object_type):
            aspect = request_tuple[0]
            id_list.append(object_type + '_' + aspect)

    id_list.append(constants.SYSSTAT_CHART_TITLE + '_percent')
    id_list.append(constants.SYSSTAT_CHART_TITLE + '_mbs')
    id_list.append(constants.SYSSTAT_CHART_TITLE + '_iops')

    return id_list


def get_csv_filenames(output_identifier, luns_available):
    """
    Generates proper names for CSV files containing a selection of PerfStat Data.
    :return: A list of csv file names.
    :param luns_available: A boolean, whether lun values appeared in the PerfStat at all.
    """
    name_list = []
    for object_type in PER_ITERATION_REQUESTS:
        if not luns_available and object_type == 'lun':
            continue
        for request_tuple in PER_ITERATION_REQUESTS.get(object_type):
            aspect = request_tuple[0]
            name_list.append(output_identifier + object_type + '_' + aspect +
                             constants.CSV_FILE_ENDING)

    name_list.append(output_identifier + constants.SYSSTAT_CHART_TITLE + '_percent' +
                     constants.CSV_FILE_ENDING)
    name_list.append(output_identifier + constants.SYSSTAT_CHART_TITLE + '_mbs' +
                     constants.CSV_FILE_ENDING)
    name_list.append(output_identifier + constants.SYSSTAT_CHART_TITLE + '_iops' +
                     constants.CSV_FILE_ENDING)

    return name_list


def extract_to_temp_dir(zip_folder):
    """
    This function takes a zip folder, distracts it to a temporary directory and selects all .data
    files from it, but it ignores all files in folders named host.
    :param zip_folder: The path to a .zip file
    :return: A tuple of the temporary directory's path and a list of all .output file paths.
    """
    temp_path = tempfile.mkdtemp()
    with ZipFile(zip_folder, 'r') as zip_file:
        zip_file.extractall(temp_path)

    output_files = []
    for path, _, files in os.walk(temp_path):
        if 'host' in path:
            continue
        for filename in files:
            file = os.path.join(path, filename)
            if data_type(file) == 'data':
                output_files.append(file)
    return temp_path, output_files
