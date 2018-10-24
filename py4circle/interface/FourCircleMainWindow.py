import numpy as np
try:
    from PyQt5 import QtCore
    from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMessageBox
    from PyQt5.uic import loadUi as load_ui
except ImportError:
    from PyQt4 import QtCore
    from PyQt4.QtGui import QMainWindow, QFileDialog, QMessageBox, QVBoxLayout
    from PyQt4 import uic
    from PyQt4.uic import loadUi as load_ui
import os
import math

import guiutility as gutil
import py4circle.lib.polarized_neutron_processor as polarized_neutron_processor
from py4circle.interface.integrratedroiview import IntegratedROIView

# promoted widgets
from py4circle.interface.gui.dataanalysiswidget import GeneralPurposeDataView, GeneralTableView
from py4circle.interface.gui.detectorview import DetectorView
from py4circle.interface.gui.tablewidgets import ScanListTable
from py4circle.interface.gui.ipythonanalysiswidget import IPyAnalysisWidget

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s
  
# TODO FIXME : detector size shall be configurable
DETECTOR_SIZE = 256


class FourCircleMainWindow(QMainWindow):
    """ Main window for 4-circle polarized experiment
    """
    TabPage = {'ROI Setup': 1,
               'Calculate UB': 3,
               'UB Matrix': 4,
               'Peak Integration': 6,
               'Scans Processing': 5}

    Reserved_Command_List = ['integrate', 'plot', 'refresh']

    def __init__(self):
        """

        """
        super(FourCircleMainWindow, self).__init__(None)

        # define class variable
        self._myControl = polarized_neutron_processor.FourCirclePolarizedNeutronProcessor()
        self._expNumber = None
        self._iptsNumber = None
        
        self._homeDir = os.path.expanduser('~')

        # set up UI
        ui_path = os.path.join(os.path.dirname(__file__), 'gui/MainWindow.ui')
        self.ui = load_ui(ui_path, baseinstance=self)

        self._promote_widgets()

        self._init_widgets()

        # link
        self.ui.pushButton_setExp.clicked.connect(self.do_set_experiment)
        self.ui.pushButton_applySetup.clicked.connect(self.do_apply_setup)
        self.ui.pushButton_browseWorkDir.clicked.connect(self.do_browse_working_dir)

        self.ui.pushButton_browseLocalDataDir.clicked.connect(self.do_browse_local_spice_data)
        self.ui.pushButton_plotRawPt.clicked.connect(self.do_plot_pt_raw)
        self.ui.pushButton_exportMovie.clicked.connect(self.do_export_movie)

        # about set up ROI for polarized neutron
        self.ui.pushButton_viewSurveyPeak.clicked.connect(self.do_view_survey_peak)
        self.ui.pushButton_prevPtNumber.clicked.connect(self.do_plot_prev_pt_raw)
        self.ui.pushButton_nextPtNumber.clicked.connect(self.do_plot_next_pt_raw)

        # about list all scans
        self.ui.pushButton_survey.clicked.connect(self.do_survey)

        # ROI operation
        self.ui.pushButton_cancelROI.clicked.connect(self.do_remove_roi)
        self.ui.pushButton_integrateROI.clicked.connect(self.do_integrate_rois)

        # integrate ROI
        self.ui.pushButton_roiUp.clicked.connect(self.do_move_roi_up)
        self.ui.pushButton_roiDown.clicked.connect(self.do_move_roi_down)
        self.ui.pushButton_roiLeft.clicked.connect(self.do_move_roi_left)
        self.ui.pushButton_roiRight.clicked.connect(self.do_move_roi_right)

        self.ui.actionQuit.triggered.connect(self.do_quit)

        # menu
        self.ui.actionShow_Result_Window.triggered.connect(self.menu_show_result_view)
        # self.connect(self.ui.actionShow_Result_Window, QtCore.SIGNAL('triggered()'),
        #              self.menu_show_result_view)

        # list of ROI radio buttons
        self._roiSelectorDict = {-1: self.ui.radioButton_roiAll,
                                 0: self.ui.radioButton_roiNo1,
                                 1: self.ui.radioButton_roiNo2,
                                 2: self.ui.radioButton_roiNo3,
                                 3: self.ui.radioButton_roiNo4,
                                 4: self.ui.radioButton_roiNo5,
                                 5: self.ui.radioButton_roiNo6}

        # define child windows
        self._integratedViewWindow = IntegratedROIView(self)

        # instrument information: FIXME - this number shall be flexible with input
        self._pixelXYSize = DETECTOR_SIZE

        # other class variables
        self._homeSrcDir = ''

        return

    def _promote_widgets(self):
        """

        :return:
        """
        # set up "promoted" widgets
        mpl_layout = QVBoxLayout()
        self.ui.frame_generalPlotView.setLayout(mpl_layout)
        self.ui.graphicsView_generalPlotView = GeneralPurposeDataView(self.ui.tabAnalysis)
        self.setObjectName(_fromUtf8("graphicsView_generalPlotView"))
        mpl_layout.addWidget(self.ui.graphicsView_generalPlotView)

        mpl_layout = QVBoxLayout()
        self.ui.frame_detector2dPlot.setLayout(mpl_layout)
        self.graphicsView_detector2dPlot = DetectorView(self.ui.tab_determineROIs)
        mpl_layout.addWidget(self.graphicsView_detector2dPlot)

        gen_table_layout = QVBoxLayout()
        self.ui.frame_generalTableView.setLayout(gen_table_layout)
        self.ui.tableView_generalTableView = GeneralTableView(self.ui.tabAnalysis)
        gen_table_layout.addWidget(self.ui.tableView_generalTableView)

        # survey_table_layout = QVBoxLayout()
        # self.ui.frame_surveyTable.setLayout(survey_table_layout)
        self.ui.tableWidget_surveyTable = ScanListTable(self.ui)
        # survey_table_layout.addWidget(self.ui.tableWidget_surveyTable)
        row = 1
        col = 0
        self.ui.gridLayout_4.addWidget(self.ui.tableWidget_surveyTable, row, col)

        ipython_layout = QVBoxLayout()
        self.ui.frame_ipythonConsole.setLayout(ipython_layout)
        self.widget_analysis = IPyAnalysisWidget(self.tabAnalysis)
        ipython_layout.addWidget(self.widget_analysis)

        return

    def _init_widgets(self):
        """ Initialize widgets
        :return:
        """
        self.ui.tableWidget_surveyTable.setup()

        self.ui.widget_analysis.set_main_application(self)
        self.ui.tableView_generalTableView.setup()

        # debug setup ----
        self.ui.lineEdit_exp.setText('715')
        self.ui.lineEdit_workDir.setText('/SNS/users/wzz/Projects/HB3A/Exp715')
        self.ui.lineEdit_surveyStartPt.setText('1')
        self.ui.lineEdit_surveyEndPt.setText('300')
        self.ui.lineEdit_numSurveyOutput.setText('50')
        self.ui.lineEdit_run.setText('73')
        self.ui.lineEdit_rawDataPtNo.setText('1')

        self.ui.label_14.setStyleSheet('color: red')
        self.ui.radioButton_roiNo1.setStyleSheet('color: red')

        # FIXME - Remove this part after testing

        return

    def _get_selected_rois(self):
        """
        check radio buttons for selected ROI or all ROI
        :return:
        """
        # find the selected
        selected = None
        for roi_index in self._roiSelectorDict.keys():
            if self._roiSelectorDict[roi_index].isChecked():
                selected = roi_index
        # END-FOR

        if selected is None:
            raise RuntimeError('It is not possible to have no ROI selected')

        if selected == -1:
            roi_list = range(6)
        else:
            roi_list = [selected]

        return roi_list

    def calculate_polarization(self, integrated_counts_dict):
        """
        calculate polarization from a well integrated set of spin up and spin down
        :param integrated_counts_dict:
        :return:
        """
        # TODO FIXME - so far, this is not an elegant solution
        # integrated_counts_dict.keys(): 0, '0_upper_bkgd', '0_lower-bkgd'

        exp_number = int(self.ui.lineEdit_exp.text())
        scan_number = int(self.ui.lineEdit_run.text())
        pt_list = integrated_counts_dict[0][0]
        peak_count_vec = integrated_counts_dict[0][1]
        upper_bkgd_count_vec = integrated_counts_dict['0_upper_bkgd'][1]
        lower_bkgd_count_vec = integrated_counts_dict['0_lower_bkgd'][1]

        # vertical
        polarizers, single_spins = \
            self.controller.calculate_polarization(exp_number, scan_number, pt_list, peak_count_vec,
                                                   upper_bkgd_count_vec, lower_bkgd_count_vec, flag='vertical')

        # horizontal
        left_bkgd_count_vec = integrated_counts_dict['0_left_bkgd'][1]
        right_bkgd_count_vec = integrated_counts_dict['0_right_bkgd'][1]
        left_right_polarizers, left_right_single_spins = \
            self.controller.calculate_polarization(exp_number, scan_number, pt_list, peak_count_vec,
                                                   left_bkgd_count_vec, right_bkgd_count_vec, flag='horizontal')

        # encircle
        outer_bkgd_count_vec = integrated_counts_dict['0_encircle'][1]
        outer_bkgd_count_vec = outer_bkgd_count_vec - peak_count_vec
        zero_count_vec = np.zeros(shape=outer_bkgd_count_vec.shape, dtype=outer_bkgd_count_vec.dtype)
        encircle_polarizers, encircle_single_spins = \
            self.controller.calculate_polarization(exp_number, scan_number, pt_list, peak_count_vec,
                                                   outer_bkgd_count_vec, zero_count_vec, flag='outer')

        self._polarizers = polarizers

        return encircle_polarizers, encircle_single_spins

    @property
    def controller(self):
        return self._myControl

    def do_apply_setup(self):
        """
        Purpose:
         - Apply the setup to controller.
        Requirements:
         - data directory, working directory must be given; but not necessarily correct
         - URL must be given; but not necessary to be correct
        :return:
        """
        # get data directory, working directory and data server URL from GUI
        local_data_dir = str(self.ui.lineEdit_localSpiceDir.text()).strip()
        working_dir = str(self.ui.lineEdit_workDir.text()).strip()
        # pre_process_dir = str(self.ui.lineEdit_preprocessedDir.text()).strip()

        # set to my controller
        status, err_msg = self._myControl.set_local_data_dir(local_data_dir)
        if not status:
            raise RuntimeError(err_msg)
        self._myControl.set_working_directory(working_dir)

        # check
        error_message = ''

        # local data dir
        if local_data_dir == '':
            error_message += 'Local data directory is not specified!\n'
        elif os.path.exists(local_data_dir) is False:
            try:
                os.mkdir(local_data_dir)
            except OSError as os_error:
                error_message += 'Unable to create local data directory %s due to %s.\n' % (
                    local_data_dir, str(os_error))
                self.ui.lineEdit_localSpiceDir.setStyleSheet("color: red;")
            else:
                self.ui.lineEdit_localSpiceDir.setStyleSheet("color: green;")
        else:
            self.ui.lineEdit_localSpiceDir.setStyleSheet("color: green;")
        # END-IF-ELSE

        # working directory
        if working_dir == '':
            error_message += 'Working directory is not specified!\n'
        elif os.path.exists(working_dir) is False:
            try:
                os.mkdir(working_dir)
                self.ui.lineEdit_workDir.setStyleSheet("color: green;")
            except OSError as os_error:
                error_message += 'Unable to create working directory %s due to %s.\n' % (
                    working_dir, str(os_error))
                self.ui.lineEdit_workDir.setStyleSheet("color: red;")
        else:
            self.ui.lineEdit_workDir.setStyleSheet("color: green;")
        # END-IF-ELSE

        if len(error_message) > 0:
            self.pop_one_button_dialog(error_message)

        return

    def do_browse_local_spice_data(self):
        """ Browse local source SPICE data directory
        """
        src_spice_dir = str(QFileDialog.getExistingDirectory(self, 'Get Directory',
                                                                   self._homeSrcDir))
        # Set local data directory to controller
        status, error_message = self._myControl.set_local_data_dir(src_spice_dir)
        if status is False:
            self.pop_one_button_dialog(error_message)
            return

        self._homeSrcDir = src_spice_dir
        self.ui.lineEdit_localSpiceDir.setText(src_spice_dir)

        return

    def do_browse_working_dir(self):
        """
        Browse and set up working directory
        :return:
        """
        work_dir = str(QFileDialog.getExistingDirectory(self, 'Get Working Directory', self._homeDir))
        status, error_message = self._myControl.set_working_directory(work_dir)
        if status is False:
            self.pop_one_button_dialog(error_message)
        else:
            self.ui.lineEdit_workDir.setText(work_dir)

        return

    def do_export_movie(self):
        """

        @return:
        """
        self.ui.lineEdit_rawDataPtNo.setText('0')
        scan_number = str(self.ui.lineEdit_run.text())

        continue_plot = True
        counts = 0
        while continue_plot and counts < 1000:
            continue_plot = self.do_plot_next_pt_raw()
            file_name = os.path.join(self._myControl.working_dir,
                                     'scan{}_{:04}.png'
                                     ''.format(scan_number, int(self.ui.lineEdit_rawDataPtNo.text())))
            print ('[INFO] Save image for {} to {}'.format(self.ui.lineEdit_rawDataPtNo.text(),
                                                           file_name))
            self.ui.graphicsView_detector2dPlot.save_image(file_name)
            counts += 1
        # END-WHILE

        return

    def do_integrate_rois(self):
        """
        Integrate ROIs for user of a scan:
        :return:
        """
        # get all the ROI's region
        roi_dimension_dict = self.ui.graphicsView_detector2dPlot.get_roi_dimensions()
        roi_color_dict = self.ui.graphicsView_detector2dPlot.get_roi_colors()

        print ('[INFO] ROI to integrate: {}'.format(roi_dimension_dict.keys()))

        # integrate
        integrated_value_dict = dict()

        # create background ROI
        AUTOBACKGROND = True   # FIXME : shall be a user's choice!
        if AUTOBACKGROND is True:
            # get original ROIs to keep
            roi_names = roi_dimension_dict.keys()

            # add backgrounds' ROI
            for roi_name in roi_names:
                # dimension
                left_bottom_x = roi_dimension_dict[roi_name][0]
                left_bottom_y = roi_dimension_dict[roi_name][1]
                width = roi_dimension_dict[roi_name][2]
                height = roi_dimension_dict[roi_name][3]

                # add upper background
                upper_bkgd_left_bottom_y = left_bottom_y + height
                upper_bkgd_name = '{}_upper_bkgd'.format(roi_name)
                roi_dimension_dict[upper_bkgd_name] = [left_bottom_x, upper_bkgd_left_bottom_y, width, height/2]

                # add lower background
                lower_bkgd_left_bottom_y = left_bottom_y - height/2
                lower_bkgd_name = '{}_lower_bkgd'.format(roi_name)
                roi_dimension_dict[lower_bkgd_name] = [left_bottom_x, lower_bkgd_left_bottom_y, width, height/2]

                # add left background
                left_bkgd_left_bottom_x = left_bottom_x - width/2
                left_bkgd_name = '{}_left_bkgd'.format(roi_name)
                roi_dimension_dict[left_bkgd_name] = [left_bkgd_left_bottom_x, left_bottom_y, width/2, height]

                # add right background
                right_bkgd_left_bottom_x = left_bottom_x + width
                right_bkgd_name = '{}_right_bkgd'.format(roi_name)
                roi_dimension_dict[right_bkgd_name] = [right_bkgd_left_bottom_x, left_bottom_y, width/2, height]

                # add encircled background
                new_width = int(width * math.sqrt(2.))
                new_height = int(height*math.sqrt(2.))
                new_bkgd_left_bottom_x = left_bottom_x - (new_width - width)/2
                new_bkgd_left_bottom_y = left_bottom_y - (new_height - height)/2
                encircle_bkgd_name = '{}_encircle'.format(roi_name)
                roi_dimension_dict[encircle_bkgd_name] = [new_bkgd_left_bottom_x, new_bkgd_left_bottom_y,
                                                          new_width, new_height]

            # END-FOR
        # END-IF

        integration_info = 'ROI multiply factor: '
        for roi_name in roi_dimension_dict:
            # convert the ROI/rectangular dimension to pixels
            left_bottom_x = roi_dimension_dict[roi_name][0]
            left_bottom_y = roi_dimension_dict[roi_name][1]
            width = roi_dimension_dict[roi_name][2]
            height = roi_dimension_dict[roi_name][3]

            pixel_range = (left_bottom_x, left_bottom_y), (left_bottom_x + width, left_bottom_y + height)
            print ('[DB...BAT] Pixel Range: {0}'.format(pixel_range))

            # convert to numpy array range
            min_row = (DETECTOR_SIZE - 1) - int(left_bottom_y + height + 1)
            min_col = int(left_bottom_x - 1)
            max_row = min_row + int(height) + 2
            max_col = int(min_col + width)

            # check whether it is out of boundary
            original_size = (max_row - min_row + 1) * (max_col - min_col + 1)
            min_row = max(min_row, 0)
            max_row = min(max_row, DETECTOR_SIZE - 1)
            min_col = max(min_col, 0)
            max_col = min(max_col, DETECTOR_SIZE - 1)
            new_size = (max_row - min_row + 1) * (max_col - min_col + 1)

            matrix_range = (min_row, min_col), (max_row, max_col)
            multiply_factor = float(original_size) / float(new_size)

            pt_list, counts_vector = self._myControl.integrate_roi(int(self.ui.lineEdit_exp.text()),
                                                                   int(self.ui.lineEdit_run.text()),
                                                                   matrix_range)

            counts_vector *= multiply_factor
            if multiply_factor > 1.0000001:
                integration_info += '{} = {}; '.format(roi_name, multiply_factor)

            print ('[DB...BAT] multiplication factor: {}'.format(multiply_factor))
            integrated_value_dict[roi_name] = pt_list, counts_vector

        # END-FOR

        # create a dialog/window for the result
        if self._integratedViewWindow is None:
            raise NotImplementedError('Integrated view window shall be initialized during Main window init.')
        self._integratedViewWindow.show()
        self._integratedViewWindow.set_integrated_value(integrated_value_dict, roi_color_dict)
        self._integratedViewWindow.set_integration_info(integration_info)

        return

    def do_review_roi(self):
        """
        plot ROI on each measurement (pt. number) and export to PNG in order to make movie
        :return:
        """
        # FIXME - Remove this part after testing is over
        counts_matrix, count_sum = self._myControl.mask_roi(int(self.ui.lineEdit_exp.text()),
                                                            int(self.ui.lineEdit_run.text()),
                                                            int(self.ui.lineEdit_rawDataPtNo.text()),
                                                            matrix_range)
        det_shape = counts_matrix.shape
        self.ui.graphicsView_detector2dPlot.add_2d_plot(counts_matrix, x_min=0, x_max=det_shape[0], y_min=0,
                                                        y_max=det_shape[1],
                                                        hold_prev_image=False, plot_type='image')
        self.ui.plainTextEdit_rawDataInformation.setPlainText('Pixel Range: {0}; Matirix Range: {1}; Counts = {2}'
                                                              ''.format(pixel_range, matrix_range, count_sum))
        # END-OF-FIXME

        return

    def do_move_roi_down(self):
        """
        move selected ROIs down by some pixel number in integers
        :return:
        """
        # get selected ROIs by radio button
        roi_index_list = self._get_selected_rois()

        for roi_index in roi_index_list:
            self.ui.graphicsView_detector2dPlot.move_roi(roi_index=roi_index, dy=-1)

        return

    def do_move_roi_left(self):
        """
        move selected ROIs to left
        :return:
        """
        # get selected ROIs by radio button
        roi_index_list = self._get_selected_rois()

        for roi_index in roi_index_list:
            self.ui.graphicsView_detector2dPlot.move_roi(roi_index=roi_index, dx=-1)

        return

    def do_move_roi_right(self):
        """
        move selected ROIs to right
        :return:
        """
        # get selected ROIs by radio button
        roi_index_list = self._get_selected_rois()

        for roi_index in roi_index_list:
            self.ui.graphicsView_detector2dPlot.move_roi(roi_index=roi_index, dx=1)

        return

    def do_move_roi_up(self):
        """
        move selected ROIs up
        :return:
        """
        # get selected ROIs by radio button
        roi_index_list = self._get_selected_rois()

        for roi_index in roi_index_list:
            self.ui.graphicsView_detector2dPlot.move_roi(roi_index=roi_index, dy=1)

        return

    def do_plot_next_pt_raw(self):
        """ Plot the Pt.
        """
        # Get measurement pt and the file number
        status, ret_obj = gutil.parse_integers_editors([self.ui.lineEdit_exp,
                                                        self.ui.lineEdit_run,
                                                        self.ui.lineEdit_rawDataPtNo])
        if status is True:
            exp_no = ret_obj[0]
            scan_no = ret_obj[1]
            pt_no = ret_obj[2]
        else:
            self.pop_one_button_dialog(ret_obj)
            return

        # Next Pt
        pt_no += 1
        # get last Pt. number
        status, last_pt_no = self._myControl.get_pt_numbers(exp_no, scan_no)
        if status is False:
            error_message = last_pt_no
            self.pop_one_button_dialog('Unable to access Spice table for scan %d. Reason" %s.' % (
                scan_no, error_message))
        if pt_no > last_pt_no:
            self.pop_one_button_dialog('Pt. = %d is the last one of scan %d.' % (pt_no, scan_no))
            return
        else:
            self.ui.lineEdit_rawDataPtNo.setText('%d' % pt_no)

        # Plot
        is_plotted = self._plot_raw_xml_2d(exp_no, scan_no, pt_no)
        if is_plotted is False and pt_no % 2 == 1:
            # out of boundary: stop and rewind
            self.ui.lineEdit_rawDataPtNo.setText('{}'.format(pt_no-2))
            return False

        return True

    def do_plot_prev_pt_raw(self):
        """ Plot the Pt.
        """
        # Get measurement pt and the file number
        status, ret_obj = gutil.parse_integers_editors([self.ui.lineEdit_exp,
                                                        self.ui.lineEdit_run,
                                                        self.ui.lineEdit_rawDataPtNo])
        if status is True:
            exp_no = ret_obj[0]
            scan_no = ret_obj[1]
            pt_no = ret_obj[2]
        else:
            self.pop_one_button_dialog(ret_obj)
            return

        # Previous one
        pt_no -= 1
        if pt_no <= 0:
            self.pop_one_button_dialog('Pt. = 1 is the first one.')
            return
        else:
            self.ui.lineEdit_rawDataPtNo.setText('%d' % pt_no)

        # Plot
        self._plot_raw_xml_2d(exp_no, scan_no, pt_no)

        return

    def do_plot_pt_raw(self):
        """ Plot the Pt.
        """
        # Get measurement pt and the file number
        status, ret_obj = gutil.parse_integers_editors([self.ui.lineEdit_exp,
                                                        self.ui.lineEdit_run,
                                                        self.ui.lineEdit_rawDataPtNo])
        if status is True:
            exp_no = ret_obj[0]
            scan_no = ret_obj[1]
            pt_no = ret_obj[2]
        else:
            self.pop_one_button_dialog(ret_obj)
            return

        # Call to plot 2D
        self._plot_raw_xml_2d(exp_no, scan_no, pt_no)

        return

    def do_quit(self):
        self.close()

    def do_remove_roi(self):
        """
        remove a selected ROI (rectangular)
        :return:
        """
        # TODO FIXME - It is wrong!
        if False:
            roi_index_list = self._get_selected_rois()

            for roi_index in roi_index_list:
                self.ui.graphicsView_detector2dPlot.remove_roi(roi_index=roi_index)
        else:
            # Temporarily fix
            self.ui.graphicsView_detector2dPlot.remove_roi(roi_index=None)

        return

    def do_set_experiment(self):
        """ Set experiment
        :return:
        """
        # get exp number
        status, ret_obj = gutil.parse_integers_editors([self.ui.lineEdit_exp])
        if status:
            # new experiment number
            exp_number = ret_obj[0]
            # current experiment to be replaced: warning
            curr_exp_number = self._myControl.get_experiment()
            if curr_exp_number is not None and exp_number != curr_exp_number:
                self.pop_one_button_dialog('Changing experiment to %d.  Clean previous experiment %d\'s result'
                                           ' in Mantid manually.' % (exp_number, curr_exp_number))
            # set the new experiment number
            self._myControl.set_exp_number(exp_number)
            self.ui.lineEdit_exp.setStyleSheet('color: black')
            self.setWindowTitle('Experiment %d' % exp_number)

            # try to set the default
            if self._iptsNumber is not None:
                default_data_dir = '/HFIR/HB3A/IPTS-{0}/exp{1}/Datafiles'.format(self._iptsNumber, exp_number)
                default_work_dir = os.path.expanduser('~')
            else:
                default_data_dir = '/HFIR/HB3A/exp{0}/Datafiles'.format(exp_number)
                default_work_dir = os.path.expanduser('/HFIR/HB3A/exp{0}/Shared'.format(exp_number))
            if os.path.exists(default_data_dir):
                # set the directory in
                self.ui.lineEdit_localSpiceDir.setText(default_data_dir)
                # find out the detector type
                status, ret_obj = self._myControl.find_detector_size(default_data_dir, exp_number)
            if os.path.exists(default_work_dir):
                self.ui.lineEdit_workDir.setText(default_work_dir)
            else:
                print '[DB] Default data directory {0} does not exist.'.format(default_data_dir)

        else:
            err_msg = ret_obj
            self.pop_one_button_dialog('Unable to set experiment as %s' % err_msg)
            self.ui.lineEdit_exp.setStyleSheet('color: red')
            return

        self.ui.tabWidget.setCurrentIndex(0)

        # set the instrument geometry constants
        # status, ret_obj = gutil.parse_float_editors([self.ui.lineEdit_pixelSizeX,
        #                                              self.ui.lineEdit_pixelSizeY],
        #                                             allow_blank=False)
        # if status:
        #     self._myControl.set_default_detector_sample_distance(default_det_sample_distance)
        #     self._myControl.set_default_pixel_size(pixel_x_size, pixel_y_size)
        # else:
        #     self.pop_one_button_dialog('[ERROR] Unable to parse default instrument geometry constants '
        #                                'due to %s.' % str(ret_obj))
        #     return

        # # set the detector center
        # det_center_str = str(self.ui.lineEdit_defaultDetCenter.text())
        # try:
        #     terms = det_center_str.split(',')
        #     center_row = int(terms[0])
        #     center_col = int(terms[1])
        #     self._myControl.set_detector_center(exp_number, center_row, center_col, default=True)
        # except (IndexError, ValueError) as error:
        #     self.pop_one_button_dialog('[ERROR] Unable to parse default detector center %s due to %s.'
        #                                '' % (det_center_str, str(error)))

        return
    
    def do_survey(self):
        """
        Purpose: survey for the strongest reflections
        :return:
        """
        # Get experiment number
        exp_number = int(self.ui.lineEdit_exp.text())
        status, ret_obj = gutil.parse_integers_editors([self.ui.lineEdit_surveyStartPt,
                                                        self.ui.lineEdit_surveyEndPt])
        if status is False:
            err_msg = ret_obj
            self.pop_one_button_dialog(err_msg)
        start_scan = ret_obj[0]
        end_scan = ret_obj[1]

        max_number = int(self.ui.lineEdit_numSurveyOutput.text())

        # Get value
        status, ret_obj, err_msg = self._myControl.survey(exp_number, start_scan, end_scan)
        if status is False:
            self.pop_one_button_dialog(ret_obj)
            return
        elif err_msg != '':
            self.pop_one_button_dialog(err_msg)
        scan_sum_list = ret_obj
        self.ui.tableWidget_surveyTable.set_survey_result(scan_sum_list)
        self.ui.tableWidget_surveyTable.show_reflections(max_number)

        return

    def do_view_survey_peak(self):
        """ View selected peaks from survey table
        Requirements: one and only 1 run is selected
        Guarantees: the scan number and pt number that are selected will be set to
            tab 'View Raw' and the tab is switched.
        :return:
        """
        # get values
        try:
            scan_num, pt_num = self.ui.tableWidget_surveyTable.get_selected_run_surveyed()
        except RuntimeError as err:
            self.pop_one_button_dialog(str(err))
            return

        # clear selection
        self.ui.tableWidget_surveyTable.select_all_rows(False)

        # switch tab    FourCircleMainWindow
        self.ui.tabWidget.setCurrentIndex(FourCircleMainWindow.TabPage['ROI Setup'])
        self.ui.lineEdit_run.setText(str(scan_num))
        self.ui.lineEdit_rawDataPtNo.setText(str(pt_num))

        return

    def convert_roi_dim_to_pixels(self, bottom_left_coord, width, height):
        """
        convert a rectangular ROI with dimension to
        :param bottom_left_coord: 
        :param width: 
        :param height: 
        :return: a list of 2-tuples.  each tuple contains a range of pixels (start ID and end ID)
        """
        # check inputs
        assert isinstance(bottom_left_coord, tuple) and len(bottom_left_coord) == 2, \
            'bottom left coordinate {0} must be a 2-tuple but not a {1}' \
            ''.format(bottom_left_coord, type(bottom_left_coord))
        assert isinstance(width, float) and width > 0,\
            'Width {0} must be a positive float but not a {1}.'.format(width, type(width))
        assert isinstance(height, float) and height > 0, \
            'Height {0} must be a positive float but not a {1}.'.format(height, type(height))

        # map from dimension to pixel IDs
        print '[DB...BAT] Assuming that ROI coordinate is consistent with pixel arrangement.'

        pixel_range_list = list()

        # convert bottom left coordinate to integers
        bottom_left_x, bottom_left_y = bottom_left_coord
        bl_x_int = int(bottom_left_x)
        bl_y_int = int(bottom_left_y)
        height_int = int(height)
        width_int = int(width)
        for row_index in range(bl_y_int, bl_y_int + height_int):
            start_pixel_id = 1 + row_index * self._pixelXYSize
            pixel_range_list.append((start_pixel_id + bl_x_int, start_pixel_id + bl_x_int + width_int))
        # END-FOR

        return pixel_range_list

    def _plot_raw_xml_2d(self, exp_no, scan_no, pt_no):
        """ Plot raw workspace from XML file
        @param exp_no:
        @param scan_no:
        @param pt_no:
        @return:
        """
        # check whether this XML file has been loaded
        # TODO blabla
        try:
            raw_det_data = self._myControl.load_spice_xml_file2(exp_no, scan_no, pt_no)
        except RuntimeError as run_err:
            print ('[ERROR] Unable to load scan {} pt {} due to {}'.format(scan_no, pt_no, run_err))
            return False
        det_shape = raw_det_data.shape

        # max_index = np.argmax(raw_det_data)
        # irow = max_index / det_shape[1]
        # icol = max_index % det_shape[1]
        # print ('[DB...BAT] Maximum number {0}/{4} is at {1} / {2}, {3}'
        #        ''.format(raw_det_data[irow, icol], max_index, irow, icol, np.amax(raw_det_data)))

        self.ui.graphicsView_detector2dPlot.add_2d_plot(raw_det_data, x_min=0, x_max=det_shape[0], y_min=0,
                                                        y_max=det_shape[1],
                                                        hold_prev_image=False, plot_type='image',
                                                        title='Exp {} Scan {} Pt {}'
                                                              ''.format(exp_no, scan_no, pt_no))

        return

    def _plot_raw_xml_2d_old(self, exp_no, scan_no, pt_no):
        """ Plot raw workspace from XML file for a measurement/pt.
        """
        # Check and load SPICE table file
        does_exist = self._myControl.does_spice_loaded(exp_no, scan_no)
        if does_exist is False:
            # Load Spice (.dat) file (table)
            status, error_message = self._myControl.load_spice_scan_file(exp_no, scan_no)
            if status is False and self._allowDownload is False:
                self.pop_one_button_dialog(error_message)
                return
        # END-IF(does_exist)

        # Load Data for Pt's xml file
        does_exist = self._myControl.does_raw_loaded(exp_no, scan_no, pt_no)

        if does_exist is False:
            # Load SPICE xml file
            status, error_message = self._myControl.load_spice_xml_file(exp_no, scan_no, pt_no)
            if status is False:
                self.pop_one_button_dialog(error_message)
                return

        # Convert a list of vector to 2D numpy array for imshow()
        # Get data and plot
        raw_det_data = self._myControl.get_raw_detector_counts(exp_no, scan_no, pt_no)
        # raw_det_data = numpy.rot90(raw_det_data, 1)

        # get the configuration of detector from GUI
        #  FIXME/TODO/ISSUE/NOW/TODAY - use the detector size wrong!
        if 0:
            ret_obj = gutil.parse_integer_list(str(self.ui.lineEdit_detectorGeometry.text()), expected_size=2)
            x_max, y_max = ret_obj
        else:
            x_max, y_max = DETECTOR_SIZE, DETECTOR_SIZE

        # TODO/ISSUE/NOW/ASAP - Debugging now
        if self.ui.graphicsView_detector2dPlot.has_image_on_canvas():
            self.ui.graphicsView_detector2dPlot.canvas().update_image(array2d=raw_det_data)
        else:
            self.ui.graphicsView_detector2dPlot.add_2d_plot(raw_det_data, x_min=0, x_max=x_max, y_min=0, y_max=y_max,
                                                            hold_prev_image=False, plot_type='image')
        # END-IF-ELSE

        status, roi = self._myControl.get_region_of_interest(exp_no, scan_number=None)
        if status:
            self.ui.graphicsView_detector2dPlot.add_roi(roi[0], roi[1])
        else:
            error_msg = roi
            # self.pop_one_button_dialog(error_msg)
            print('[Error] %s' % error_msg)
        # END-IF

        # Information
        info = '%-10s: %d\n%-10s: %d\n%-10s: %d\n' % ('Exp', exp_no,
                                                      'Scan', scan_no,
                                                      'Pt', pt_no)
        self.ui.plainTextEdit_rawDataInformation.setPlainText(info)

        return

    def menu_show_result_view(self):
        """
        show result view window
        :return:
        """
        if self._integratedViewWindow is None:
            self.pop_one_button_dialog('Result window has not been initialized yet.')
        else:
            self._integratedViewWindow.show()

        return

    def execute_reserved_command(self, script):
        """

        :param script:
        :return:
        """
        print ('Reserved non-python command: {0}'.format(script))

        if script == 'refresh':
            # refresh existing workspsaces
            ws_name_list = self._myControl.get_existing_workspaces()
            self.ui.tableView_generalTableView.remove_all_rows()
            for ws_name, ws_type in ws_name_list:
                self.ui.tableView_generalTableView.add_workspace(ws_name, ws_type)
            # END-FOR
        else:
            print ''
        # END-IF

        return

    def is_reserved_command(self, script):
        """

        :param script:
        :return:
        """
        command = script.strip().split(',')[0].strip()

        return command in self.Reserved_Command_List

    def pop_one_button_dialog(self, message):
        """ Pop up a one-button dialog
        :param message:
        :return:
        """
        assert isinstance(message, str), 'Input message %s must a string but not %s.' \
                                         '' % (str(message), type(message))
        QMessageBox.information(self, '4-circle Data Reduction', message)

        return

