from PyQt4 import QtCore, QtGui
import os
import gui.MainWindow_ui as MainWindow_ui
import guiutility as gutil
import py4circle.lib.polarized_neutron_processor as polarized_neutron_processor
from py4circle.interface.integrratedroiview import IntegratedROIView


class FourCircleMainWindow(QtGui.QMainWindow):
    """
    blabla
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
        self.ui = MainWindow_ui.Ui_MainWindow()
        self.ui.setupUi(self)

        self._init_widgets()

        # link
        self.connect(self.ui.pushButton_setExp, QtCore.SIGNAL('clicked()'),
                     self.do_set_experiment)
        self.connect(self.ui.pushButton_applySetup, QtCore.SIGNAL('clicked()'),
                     self.do_apply_setup)
        self.connect(self.ui.pushButton_browseWorkDir, QtCore.SIGNAL('clicked()'),
                     self.do_browse_working_dir)
        self.connect(self.ui.pushButton_browseLocalDataDir, QtCore.SIGNAL('clicked()'),
                     self.do_browse_local_spice_data)
        self.connect(self.ui.pushButton_plotRawPt, QtCore.SIGNAL('clicked()'),
                     self.do_plot_pt_raw)

        # about set up ROI for polarized neutron
        self.connect(self.ui.pushButton_viewSurveyPeak, QtCore.SIGNAL('clicked()'),
                     self.do_view_survey_peak)
        self.connect(self.ui.pushButton_prevPtNumber, QtCore.SIGNAL('clicked()'),
                     self.do_plot_prev_pt_raw)
        self.connect(self.ui.pushButton_nextPtNumber, QtCore.SIGNAL('clicked()'),
                     self.do_plot_next_pt_raw)

        # about list all scans
        self.connect(self.ui.pushButton_survey, QtCore.SIGNAL('clicked()'),
                     self.do_survey)

        # ROI operation
        self.connect(self.ui.pushButton_cancelROI, QtCore.SIGNAL('clicked()'),
                     self.do_remove_roi)
        self.connect(self.ui.pushButton_integrateROI, QtCore.SIGNAL('clicked()'),
                     self.do_integrate_rois)

        #: integrate ROI
        self.connect(self.ui.pushButton_roiUp, QtCore.SIGNAL('clicked()'),
                     self.do_move_roi_up)
        self.connect(self.ui.pushButton_roiDown, QtCore.SIGNAL('clicked()'),
                     self.do_move_roi_down)
        self.connect(self.ui.pushButton_roiLeft, QtCore.SIGNAL('clicked()'),
                     self.do_move_roi_left)
        self.connect(self.ui.pushButton_roiRight, QtCore.SIGNAL('clicked()'),
                     self.do_move_roi_right)

        # list of ROI radio buttons
        self._roiSelectorDict = {-1: self.ui.radioButton_roiAll,
                                 0: self.ui.radioButton_roiNo1,
                                 1: self.ui.radioButton_roiNo2,
                                 2: self.ui.radioButton_roiNo3,
                                 3: self.ui.radioButton_roiNo4,
                                 4: self.ui.radioButton_roiNo5,
                                 5: self.ui.radioButton_roiNo6}

        # define child windows
        self._integratedViewWindow = None

        # instrument information: FIXME - this number shall be flexible with input
        self._pixelXYSize = 256

        # other class variables
        self._homeSrcDir = '/tmp'

        return

    def _init_widgets(self):
        """ Initialize widgets
        :return:
        """
        self.ui.tableWidget_surveyTable.setup()

        self.ui.widget_analysis.set_main_application(self)
        self.ui.tableView_generalTableView.setup()

        # debug setup ----
        self.ui.lineEdit_exp.setText('640')
        self.ui.lineEdit_workDir.setText('/tmp')
        self.ui.lineEdit_surveyStartPt.setText('10')
        self.ui.lineEdit_surveyEndPt.setText('300')
        self.ui.lineEdit_numSurveyOutput.setText('50')

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
        src_spice_dir = str(QtGui.QFileDialog.getExistingDirectory(self, 'Get Directory',
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
        work_dir = str(QtGui.QFileDialog.getExistingDirectory(self, 'Get Working Directory', self._homeDir))
        status, error_message = self._myControl.set_working_directory(work_dir)
        if status is False:
            self.pop_one_button_dialog(error_message)
        else:
            self.ui.lineEdit_workDir.setText(work_dir)

        return

    def do_integrate_rois(self):
        """
        Integrate ROIs for user
        :return:
        """
        # get all the ROI's region
        roi_dimension_dict = self.ui.graphicsView_detector2dPlot.get_roi_dimensions()

        # integrate
        integrated_value_dict = dict()

        for roi_name in roi_dimension_dict:
            # convert the ROI/rectangular dimension to pixels
            left_bottom_x = roi_dimension_dict[roi_name][0]
            left_bottom_y = roi_dimension_dict[roi_name][1]
            width = roi_dimension_dict[roi_name][2]
            height = roi_dimension_dict[roi_name][3]
            pixel_range_list = self.convert_roi_dim_to_pixels((left_bottom_x, left_bottom_y), width=width,
                                                              height=height)
            integrated_value_dict[roi_name] = self._myControl.integrate_roi(int(self.ui.lineEdit_exp.text()),
                                                                            int(self.ui.lineEdit_run.text()),
                                                                            pixel_range_list)

        # create a dialog/window for the result
        self._integratedViewWindow = IntegratedROIView(self)
        self._integratedViewWindow.show()

        return

    def do_move_roi_down(self):
        """
        move selected ROIs down
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
        self._plot_raw_xml_2d(exp_no, scan_no, pt_no)

        return

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

    def do_remove_roi(self):
        """
        remove a selected ROI (rectangular)
        :return:
        """
        roi_index_list = self._get_selected_rois()

        for roi_index in roi_index_list:
            self.ui.graphicsView_detector2dPlot.remove_roi(roi_index=roi_index)

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
            else:
                default_data_dir = '/HFIR/HB3A/exp{0}/Datafiles'.format(exp_number)
            if os.path.exists(default_data_dir):
                # set the directory in
                self.ui.lineEdit_localSpiceDir.setText(default_data_dir)
                # find out the detector type
                status, ret_obj = self._myControl.find_detector_size(default_data_dir, exp_number)
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
            x_max, y_max = 256, 256

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

    def execute_reserved_command(self, script):
        """

        :param script:
        :return:
        """
        print 'Reserved non-python command: {0}'.format(script)

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
        QtGui.QMessageBox.information(self, '4-circle Data Reduction', message)

        return

