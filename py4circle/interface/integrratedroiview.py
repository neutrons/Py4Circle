from PyQt4 import QtGui, QtCore
import gui.ResultViewWindow_ui
import numpy as np


class IntegratedROIView(QtGui.QMainWindow):
    """
    Extended QMainWindow class for plotting and processing integrated ROI for polarized neutron experiment
    """
    def __init__(self, parent):
        """
        initialization
        :param parent:
        """
        super(IntegratedROIView, self).__init__(parent)

        # set up UI
        self.ui = gui.ResultViewWindow_ui.Ui_MainWindow()
        self.ui.setupUi(self)

        # initialize widget
        self.ui.graphicsView_result.set_subplots(1, 1)

        # define event handling related with widgets
        self.connect(self.ui.pushButton_saveResult, QtCore.SIGNAL('clicked()'),
                     self.do_save_integrated)

        self.connect(self.ui.pushButton_closeWindow, QtCore.SIGNAL('clicked()'),
                     self.do_close_window)

        self.connect(self.ui.pushButton_showExamples, QtCore.SIGNAL('clicked()'),
                     self.do_show_examples)

        self.connect(self.ui.pushButton_calculate, QtCore.SIGNAL('clicked()'),
                     self.do_calculation)

        self.connect(self.ui.pushButton_plotTableData, QtCore.SIGNAL('clicked()'),
                     self.do_plot_data)

        self.connect(self.ui.pushButton_clearImage, QtCore.SIGNAL('clicked()'),
                     self.do_clear_plots)

        return

    @staticmethod
    def calculate_by_formula(formula, value_dict):
        """
        calculate a formula
        :param formula:
        :param value_dict: 
        :return: 
        """
        # check inputs
        assert isinstance(formula, str), 'Input formula {0} must be a string but not a {1}.' \
                                         ''.format(formula, type(formula))
        assert isinstance(value_dict, dict), 'Values {0} shall be given in a dictionary but not {1}' \
                                             ''.format(value_dict, type(value_dict))

        # replace the variables with real value
        print ('[DB...BAT] Input formula: {0}'.format(formula))
        for var_name in value_dict.keys():
            formula = formula.replace(var_name, str(value_dict[var_name]))
        print ('[DB...BAT] Translated formula: {0}'.format(formula))

        # execute
        try:
            if formula.count('=') == 0:
                formula = '_cal_value = {0}'.format(formula)
            dynamic_code = compile(formula, '<string>', 'exec')
            # dynamic_code = compile('a = 1 + 2', '<string>', 'exec')
            exec dynamic_code
        except NameError as name_err:
            raise name_err

        return _cal_value

    def clear_plots(self):
        """
        clear the plotted lines
        :return:
        """
        self.ui.graphicsView_result.clear_all_lines(0, 0, include_right=False)

        return

    def clear_table(self):
        """
        clear the tables
        :return:
        """
        self.ui.tableView_result.remove_rows()

    def do_clear_plots(self):
        """
        clear plots
        :return:
        """
        self.clear_plots()

    def do_close_window(self):
        """
        close window
        :return:
        """
        self.close()

        return

    def do_plot_data(self):
        """
        plot data
        :return:
        """
        # parse what to plot
        col_name_list = str(self.ui.lineEdit_tableColsToPlot.text()).strip().split(',')

        # get data
        vec_x = self.ui.tableView_result.get_column_data('Pt')
        for col_name in col_name_list:
            col_name = col_name.strip()
            vec_y = self.ui.tableView_result.get_column_data(col_name)
            self.ui.graphicsView_result.plot_roi(vec_x, vec_y, color='black', roi_name=col_name, title_x='Pt',
                                                 unit='')
        # END-FOR

        return

    def do_save_integrated(self):
        """
        save integrated value from current view
        :return:
        """
        # get the target directory
        file_filter = 'Data Files (*.dat);;All Files (*.*)'
        target_dir = str(QtGui.QFileDialog.getOpenFileName(self, self._workingDir, file_filter))
        if len(target_dir) == 0:
            # quit if user cancel the operation
            return

        # save result

        return

    def do_calculation(self):
        """
        do calculation of the ROIs
        :return:
        """
        # read the formula
        cal_formula = str(self.ui.lineEdit_roiFormular.text())
        print ('[DB] Input is {0}'.format(cal_formula))

        # calculate
        num_rows = self.ui.tableView_result.rowCount()
        for row_index in range(num_rows):
            integrated_counts = self.ui.tableView_result.get_integrated_counts(row_number=row_index)
            value = self.calculate_by_formula(cal_formula, integrated_counts)
            pt_number = integrated_counts['Pt']
            self.ui.tableView_result.set_calculated_value(pt_number=pt_number, value=value)
        # END-FOR

        return

    def do_show_examples(self):
        """
        show some examples of formula to  calculate polarized value
        :return:
        """
        message = 'roi1 - roi2 + 3 * (roi3)'

        QtGui.QMessageBox.information(self, 'Polarized Data Analysis Example', message)

        return

    def plot_counts(self, vec_x, vec_y, x_axis_label, line_color):
        """
        plot counts
        :param vec_x: 
        :param vec_y: 
        :param x_axis_label:
        :param line_color:
        :return: 
        """
        # check input
        assert len(vec_x) == len(vec_y), 'Vector X and Y must have same sizes.'

        self.ui.graphicsView_result.add_plot(vec_x, vec_y, x_label=x_axis_label, color=line_color)

        return

    def set_integrated_value(self, integrated_value_dict, roi_color_dict):
        """
        set integrated value to this window
        :param integrated_value_dict:
        :param roi_color_dict:
        :return:
        """
        # check input
        assert isinstance(integrated_value_dict, dict), \
            'Integrated values {0} must be given in a dictionary but not a {1}' \
            ''.format(integrated_value_dict, type(integrated_value_dict))
        assert isinstance(roi_color_dict, dict), \
            'ROI counts {0} must be given in a dictionary but not a {1}'.format(roi_color_dict, type(roi_color_dict))

        # clear previous table and etc
        self.ui.tableView_result.remove_all_rows()
        # clear previous image
        self.clear_plots()

        # plot
        for roi_name in integrated_value_dict.keys():
            pt_list, count_vec = integrated_value_dict[roi_name]
            roi_color = roi_color_dict[roi_name]
            self.plot_counts(np.array(pt_list), count_vec, 'Pt', roi_color)
        # END-FOR

        # set up the table
        self.set_counts_table(integrated_value_dict)

        return

    def set_counts_table(self, integrated_value_dict):
        """ set the counts to the table
        :param integrated_value_dict:
        :return:
        """
        # check input
        assert isinstance(integrated_value_dict, dict), \
            'Integrated values {0} must be given in a dictionary but not a {1}' \
            ''.format(integrated_value_dict, type(integrated_value_dict))

        # convert the dictionary to rows
        pt_dict = dict()
        for roi_name in integrated_value_dict.keys():
            pt_list, value_vector = integrated_value_dict[roi_name]

            for ipt, pt_number in enumerate(pt_list):
                # set up the pt_dict by checking whether certain pt has been added
                if pt_number not in pt_dict:
                    pt_dict[pt_number] = dict()
                # END-IF

                # set value
                pt_dict[pt_number][roi_name] = value_vector[ipt]
            # END-FOR
        # END-FOR

        # determine roi and set up table
        self.ui.tableView_result.setup('Pt', 'int', sorted(integrated_value_dict.keys()))

        # add cells
        for pt_number in sorted(pt_dict.keys()):
            # add row
            self.ui.tableView_result.append_integrated_pt_row(pt_number)
            for roi_name in pt_dict[pt_number].keys():
                self.ui.tableView_result.set_integrated_value(pt_number, roi_name, pt_dict[pt_number][roi_name])
            # END-FOR
        # END-FOR

        return
