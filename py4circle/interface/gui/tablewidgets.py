#pylint: disable=W0403,C0103,R0901,R0904,R0913,C0302
from __future__ import (absolute_import, division, print_function)
from six.moves import range
import numpy
import sys
# from HFIR_4Circle_Reduction import fourcircle_utility
# from HFIR_4Circle_Reduction import guiutility

import py4circle.interface.gui.MyTableWidget as tableBase

class ScanListTable(tableBase.NTableWidget):
    """
    Extended table widget for peak integration
    """
    Table_Setup = [('Scan', 'int'),
                   ('Max Counts Pt', 'int'),
                   ('Max Counts', 'float'),
                   ('H', 'float'),
                   ('K', 'float'),
                   ('L', 'float'),
                   ('Q-range', 'float'),
                   ('Sample Temp', 'float'),
                   ('Selected', 'checkbox')]

    def __init__(self, parent):
        """
        :param parent:
        """
        tableBase.NTableWidget.__init__(self, parent)

        self._myScanSummaryList = list()

        self._currStartScan = 0
        self._currEndScan = sys.maxsize
        self._currMinCounts = 0.
        self._currMaxCounts = sys.float_info.max

        self._colIndexH = None
        self._colIndexK = None
        self._colIndexL = None

        return

    def filter_and_sort(self, start_scan, end_scan, min_counts, max_counts,
                        sort_by_column, sort_order):
        """
        Filter the survey table and sort
        Note: it might not be efficient here because the table will be refreshed twice
        :param start_scan:
        :param end_scan:
        :param min_counts:
        :param max_counts:
        :param sort_by_column:
        :param sort_order: 0 for ascending, 1 for descending
        :return:
        """
        # check
        assert isinstance(start_scan, int) and isinstance(end_scan, int) and end_scan >= start_scan
        assert isinstance(min_counts, float) and isinstance(max_counts, float) and min_counts < max_counts
        assert isinstance(sort_by_column, str), \
            'sort_by_column requires a string but not %s.' % str(type(sort_by_column))
        assert isinstance(sort_order, int), \
            'sort_order requires an integer but not %s.' % str(type(sort_order))

        # get column index to sort
        col_index = self.get_column_index(column_name=sort_by_column)

        # filter on the back end row contents list first
        self.filter_rows(start_scan, end_scan, min_counts, max_counts)

        # order
        self.sort_by_column(col_index, sort_order)

        return

    def filter_rows(self, start_scan, end_scan, min_counts, max_counts):
        """
        Filter by scan number, detector counts on self._myScanSummaryList
        and reset the table via the latest result
        :param start_scan:
        :param end_scan:
        :param min_counts:
        :param max_counts:
        :return:
        """
        # check whether it can be skipped
        if start_scan == self._currStartScan and end_scan == self._currEndScan \
                and min_counts == self._currMinCounts and max_counts == self._currMaxCounts:
            # same filter set up, return
            return

        # clear the table
        self.remove_all_rows()

        # go through all rows in the original list and then reconstruct
        for index in range(len(self._myScanSummaryList)):
            sum_item = self._myScanSummaryList[index]
            # check
            assert isinstance(sum_item, list)
            assert len(sum_item) == len(self._myColumnNameList) - 1
            # check with filters: original order is counts, scan, Pt., ...
            scan_number = sum_item[1]
            if scan_number < start_scan or scan_number > end_scan:
                continue
            counts = sum_item[0]
            if counts < min_counts or counts > max_counts:
                continue

            # modify for appending to table
            row_items = sum_item[:]
            counts = row_items.pop(0)
            row_items.insert(2, counts)
            row_items.append(False)

            # append to table
            self.append_row(row_items)
        # END-FOR (index)

        # Update
        self._currStartScan = start_scan
        self._currEndScan = end_scan
        self._currMinCounts = min_counts
        self._currMaxCounts = max_counts

        return

    def get_hkl(self, row_index):
        """
        Get peak index (HKL) from survey table (i.e., SPICE file)
        :param row_index:
        :return:
        """
        index_h = self.get_cell_value(row_index, self._colIndexH)
        index_k = self.get_cell_value(row_index, self._colIndexK)
        index_l = self.get_cell_value(row_index, self._colIndexL)

        return index_h, index_k, index_l

    def get_scan_numbers(self, row_index_list):
        """
        Get scan numbers with specified rows
        :param row_index_list:
        :return:
        """
        scan_list = list()
        scan_col_index = self.Table_Setup.index(('Scan', 'int'))
        for row_index in row_index_list:
            scan_number_i = self.get_cell_value(row_index, scan_col_index)
            scan_list.append(scan_number_i)
        scan_list.sort()

        return scan_list

    def get_selected_run_surveyed(self, required_size=1):
        """
        Purpose: Get selected pt number and run number that is set as selected
        Requirements: there must be one and only one run that is selected
        Guarantees: a 2-tuple for integer for return as scan number and Pt. number
        :param required_size: if specified as an integer, then if the number of selected rows is different,
                              an exception will be thrown.
        :return: a 2-tuple of integer if required size is 1 (as old implementation) or a list of 2-tuple of integer
        """
        # check required size?
        assert isinstance(required_size, int) or required_size is None, 'Required number of runs {0} must be None ' \
                                                                        'or an integer but not a {1}.' \
                                                                        ''.format(required_size, type(required_size))

        # get the selected row indexes and check
        row_index_list = self.get_selected_rows(True)

        if required_size is not None and required_size != len(row_index_list):
            raise RuntimeError('It is required to have {0} runs selected, but now there are {1} runs that are '
                               'selected.'.format(required_size, row_index_list))

        # get all the scans and rows that are selected
        scan_run_list = list()
        for i_row in row_index_list:
            # get scan and pt.
            scan_number = self.get_cell_value(i_row, 0)
            pt_number = self.get_cell_value(i_row, 1)
            scan_run_list.append((scan_number, pt_number))

        # special case for only 1 run that is selected
        if len(row_index_list) == 1 and required_size is not None:
            # get scan and pt
            return scan_run_list[0]
        # END-IF

        return scan_run_list

    def show_reflections(self, num_rows):
        """
        :param num_rows:
        :return:
        """
        assert isinstance(num_rows, int)
        assert num_rows > 0
        assert len(self._myScanSummaryList) > 0

        for i_ref in range(min(num_rows, len(self._myScanSummaryList))):
            # get counts
            scan_summary = self._myScanSummaryList[i_ref]
            # check
            assert isinstance(scan_summary, list)
            assert len(scan_summary) == len(self._myColumnNameList) - 1
            # modify for appending to table
            row_items = scan_summary[:]
            max_count = row_items.pop(0)
            row_items.insert(2, max_count)
            row_items.append(False)
            # append
            self.append_row(row_items)
        # END-FOR

        return

    def set_survey_result(self, scan_summary_list):
        """

        :param scan_summary_list:
        :return:
        """
        # check
        assert isinstance(scan_summary_list, list)

        # Sort and set to class variable
        scan_summary_list.sort(reverse=True)
        self._myScanSummaryList = scan_summary_list

        return

    def setup(self):
        """
        Init setup
        :return:
        """
        self.init_setup(ScanSurveyTable.Table_Setup)
        self.set_status_column_name('Selected')

        self._colIndexH = ScanSurveyTable.Table_Setup.index(('H', 'float'))
        self._colIndexK = ScanSurveyTable.Table_Setup.index(('K', 'float'))
        self._colIndexL = ScanSurveyTable.Table_Setup.index(('L', 'float'))

        return

    def reset(self):
        """ Reset the inner survey summary table
        :return:
        """
        self._myScanSummaryList = list()

