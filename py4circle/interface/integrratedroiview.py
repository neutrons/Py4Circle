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

        return

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

    def do_close_window(self):
        """
        close window
        :return:
        """
        self.close()

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
