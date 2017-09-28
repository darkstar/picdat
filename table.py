"""
Contains the class Table.
"""
import logging
from collections import defaultdict

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


class Table:
    """
    This is a data structure to represent table content. It's a dict of dicts; each outer dict maps
    an iteration or statit number (equates row) to an inner dict, each inner dict maps an 
    instance/disk name (equates table column) to a specific table value. So each table value has 
    a determined row and column.
    """

    def __init__(self):
        self.outer_dict = defaultdict(dict)

    def __str__(self):
        return str(self.outer_dict)

    def insert(self, row, column, item):
        """
        Inserts an value dependably into a specific place in the Table.
        :param row: Number of the iteration/statit, the value belongs to (equates table row).
        :param column: Name of the instance/disk, the value belongs to (equates table column).
        :param item: Value you want to insert.
        :return: None.
        """
        if row not in self.outer_dict:
            inner_dict = {column: item}
            self.outer_dict[row] = inner_dict
        else:
            inner_dict = self.outer_dict[row]
            if column not in inner_dict:
                inner_dict[column] = item
            else:
                self.outer_dict[row][column] = item

    def flatten(self):
        """
        Simplifies the data structure into lists of table content equating table rows.
        :return: A list containing all column headers and a list of list, which is a list of
        rows, containing the table values. The order of the values equates the order of the headers.
        """
        row_names = set()
        column_names = set()
        for row_name, inner_dict in self.outer_dict.items():
            row_names.add(row_name)
            for column_name in inner_dict:
                column_names.add(column_name)

        header_row = []
        for instance in sorted(column_names):
            header_row.append(instance)

        value_rows = []
        for row in sorted(row_names):
            row_dict = self.outer_dict[row]
            value_row = [str(row)]
            for column in sorted(column_names):
                if column in row_dict:
                    value_row.append(row_dict[column])
                else:
                    value_row.append(' ')
                    logging.info('Gap in table: Value is missing in row %s, column %s',
                                 column, str(row))
            value_rows.append(value_row)

        logging.debug(value_rows)
        return header_row, value_rows
