import os
import sys
sys.path.append('/Users/wzz/MantidBuild/debug-stable/bin/')
sys.path.append('/opt/mantidnightly/bin/')

import numpy
import mantid
import mantid.simpleapi as mantidsimple
from mantid.api import AnalysisDataService
try:
    from mantidqtpython import MantidQt
except ImportError as e:
    NO_SCROLL = True
else:
    NO_SCROLL = False
from fourcircle_utility import *
import parse_spice_xml


MAX_SCAN_NUMBER = 100000


class FourCirclePolarizedNeutronProcessor(object):
    """
    """
    def __init__(self):
        """
        initialization
        """
        self._instrumentName = 'HB3A'
        self._detectorSize = [256, 256]

        self._iptsNumber = None
        self._expNumber = None
        self._dataDir = None
        self._workDir = None

        self._mySpiceTableDict = dict()
        self._myRawDataWSDict = dict()

        self._refWorkspaceForMask = None
        self._roiDict = dict()

        # dictionary to hold loaded detector count matrix loaded from SPICE XML file
        self._loadedData = dict()

        return

    def _add_spice_workspace(self, exp_no, scan_no, spice_table_ws):
        """
        """
        assert isinstance(exp_no, int)
        assert isinstance(scan_no, int)
        assert isinstance(spice_table_ws, mantid.dataobjects.TableWorkspace)
        self._mySpiceTableDict[(exp_no, scan_no)] = str(spice_table_ws)

        return

    def _add_raw_workspace(self, exp_no, scan_no, pt_no, raw_ws):
        """ Add raw Pt.'s workspace
        :param exp_no:
        :param scan_no:
        :param pt_no:
        :param raw_ws: workspace or name of the workspace
        :return: None
        """
        # Check
        assert isinstance(exp_no, int)
        assert isinstance(scan_no, int)
        assert isinstance(pt_no, int)

        if isinstance(raw_ws, str):
            # Given by name
            matrix_ws = AnalysisDataService.retrieve(raw_ws)
        else:
            matrix_ws = raw_ws
        assert isinstance(matrix_ws, mantid.dataobjects.Workspace2D)

        self._myRawDataWSDict[(exp_no, scan_no, pt_no)] = matrix_ws

        return

    @staticmethod
    def _get_spice_workspace(exp_no, scan_no):
        """ Get SPICE's scan table workspace
        :param exp_no:
        :param scan_no:
        :return: Table workspace or None
        """
        # try:
        #     ws = self._mySpiceTableDict[(exp_no, scan_no)]
        # except KeyError:
        #     return None

        spice_ws_name = get_spice_table_name(exp_no, scan_no)
        if AnalysisDataService.doesExist(spice_ws_name):
            ws = AnalysisDataService.retrieve(spice_ws_name)
        else:
            raise KeyError('Spice table workspace %s does not exist in ADS.' % spice_ws_name)

        return ws

    def calculate_polarization_emil(self, exp_number, scan_number, pt_list, radius=10):
        """ Calculate polarization (flip ratio) by Emil's algorithm
        :param exp_number:
        :param scan_number:
        :param pt_list:
        :return:
        """
        import emil_flip_calculation

        pt_hkl_dict = self.retrieve_hkl_from_spice(exp_number, scan_number)

        # TODO FIXME - Pt number is all odd due to SPICE bug!
        if len(pt_list) % 2 == 1:
            print ('Number of Pts. = {} is odd... This is wrong! Talk with Huibo. \nFYI: Pt list: {}'
                   ''.format(len(pt_list), pt_list))
        # END-IF

        polarization_list = list()
        single_spin_counts = list()

        circle_shape = emil_flip_calculation.create_circle_shape(radius)

        for pair_index in range(len(pt_list)/2):
            # check spin up and spin down shall have same pt.
            spin_up_pt = pt_list[2*pair_index]
            spin_down_pt = pt_list[2*pair_index + 1]
            spin_up_hkl = pt_hkl_dict[spin_up_pt]
            spin_down_hkl = pt_hkl_dict[spin_down_pt]
            if sum((spin_up_hkl - spin_down_hkl)**2) >= 0.25:
                raise RuntimeError('For pt {} and {}, HKL {} and {} shall be same!'
                                   ''.format(spin_up_pt, spin_down_pt, spin_up_hkl, spin_down_hkl))

            fr, sfr, metadata = emil_flip_calculation.get_flipping_ratio(spin_up_xml, spin_down_xml, sigma=3,
                                                                         shape_in=circle_shape)

        # END-FOR

    def calculate_polarization(self, exp_number, scan_number, pt_list, peak_count_vec, upper_bkgd_count_vec,
                               lower_bkgd_count_vec, flag):
        """
        calculate polarization
        @param exp_number:
        @param scan_number:
        @param pt_list:
        @param peak_count_vec:
        @param upper_bkgd_count_vec:
        @param lower_bkgd_count_vec:
        @param flag: method of how the polarization is calculated and thus file name
        @return:
        """
        pt_hkl_dict = self.retrieve_hkl_from_spice(exp_number, scan_number)

        # TODO FIXME - Pt number is all odd due to SPICE bug!
        if len(pt_list) % 2 == 1:
            print ('Number of Pts. = {} is odd... This is wrong! Talk with Huibo. \nFYI: Pt list: {}'
                   ''.format(len(pt_list), pt_list))
        # END-IF

        polarization_list = list()
        single_spin_counts = list()
        for pair_index in range(len(pt_list)/2):
            # check spin up and spin down shall have same pt.
            spin_up_pt = pt_list[2*pair_index]
            spin_down_pt = pt_list[2*pair_index + 1]
            spin_up_hkl = pt_hkl_dict[spin_up_pt]
            spin_down_hkl = pt_hkl_dict[spin_down_pt]
            if sum((spin_up_hkl - spin_down_hkl)**2) >= 0.25:
                raise RuntimeError('For pt {} and {}, HKL {} and {} shall be same!'
                                   ''.format(spin_up_pt, spin_down_pt, spin_up_hkl, spin_down_hkl))
            # calculate spin up
            b1_up = upper_bkgd_count_vec[2*pair_index]
            b2_up = lower_bkgd_count_vec[2*pair_index]
            roi_up = peak_count_vec[2*pair_index]
            spin_up_bkgd = b1_up + b2_up
            intensity_spin_up = roi_up - spin_up_bkgd

            # calculate spin down
            b1_down = upper_bkgd_count_vec[2*pair_index + 1]
            b2_down = lower_bkgd_count_vec[2*pair_index + 1]
            roi_down = peak_count_vec[2*pair_index + 1]
            spin_down_bkgd = b1_down + b2_down
            intensity_spin_down = roi_down - spin_down_bkgd

            # calculate polarization
            polarization = intensity_spin_up / intensity_spin_down

            # propagating the error
            e_up = math.sqrt(roi_up**2 + b1_up**2 + b2_up**2)
            e_down = math.sqrt(roi_down**2 + b1_down**2 + b2_down**2)

            pol_err = \
                polarization * math.sqrt((e_up/(1 + intensity_spin_up))**2 + (e_down/(1 + intensity_spin_down))**2)

            polarization_list.append((spin_up_hkl, polarization, pol_err, intensity_spin_up, spin_up_bkgd,
                                      intensity_spin_down, spin_down_bkgd))
            single_spin_counts.append(intensity_spin_up)
            single_spin_counts.append(intensity_spin_down)
        # END-FOR

        # export to file automatically
        self.export_polarization(polarization_list,  exp_number, scan_number, flag)

        return polarization_list, single_spin_counts

    def retrieve_hkl_from_spice(self, exp_number, scan_number):
        """
        get HKL of each pt number
        :param exp_number:
        :param scan_number:
        :return:
        """
        spice_table_ws = self._get_spice_workspace(exp_number, scan_number)
        pt_index = spice_table_ws.getColumnNames().index('Pt.')
        h_index = spice_table_ws.getColumnNames().index('h')
        k_index = spice_table_ws.getColumnNames().index('k')
        l_index = spice_table_ws.getColumnNames().index('l')

        pt_hkl_dict = dict()
        for row_index in range(spice_table_ws.rowCount()):
            pt_hkl_dict[spice_table_ws.cell(row_index, pt_index)] = numpy.array([
                spice_table_ws.cell(row_index, h_index), spice_table_ws.cell(row_index, k_index), \
                spice_table_ws.cell(row_index, l_index)])
        # END-FOR

        return pt_hkl_dict

    def does_file_exist(self, exp_number, scan_number, pt_number=None):
        """
        Check whether data file for a scan or pt number exists on the
        :param exp_number: experiment number or None (default to current experiment number)
        :param scan_number:
        :param pt_number: if None, check SPICE file; otherwise, detector xml file
        :return:
        """
        # check inputs
        assert isinstance(exp_number, int) or pt_number is None
        assert isinstance(scan_number, int)
        assert isinstance(pt_number, int) or pt_number is None

        # deal with default experiment number
        if exp_number is None:
            exp_number = self._expNumber

        # 2 cases
        if pt_number is None:
            # no pt number, then check SPICE file
            spice_file_name = get_spice_file_name(self._instrumentName, exp_number, scan_number)
            try:
                file_name = os.path.join(self._dataDir, spice_file_name)
            except AttributeError:
                raise AttributeError('Unable to create SPICE file name from directory %s and file name %s.'
                                     '' % (self._dataDir, spice_file_name))
        else:
            # pt number given, then check
            xml_file_name = get_det_xml_file_name(self._instrumentName, exp_number, scan_number,
                                                  pt_number)
            file_name = os.path.join(self._dataDir, xml_file_name)
        # END-IF

        return os.path.exists(file_name)

    def does_raw_loaded(self, exp_no, scan_no, pt_no):
        """
        Check whether the raw Workspace2D for a Pt. exists
        :param exp_no:
        :param scan_no:
        :param pt_no:
        :return:
        """
        return (exp_no, scan_no, pt_no) in self._myRawDataWSDict

    def does_spice_loaded(self, exp_no, scan_no):
        """ Check whether a SPICE file has been loaded
        :param exp_no:
        :param scan_no:
        :return:
        """
        return (exp_no, scan_no) in self._mySpiceTableDict

    def export_polarization(self, polarization_list, exp_number, scan_number, flag):
        """

        :param polarization_list:
        :return:
        """
        import datetime
        now = datetime.datetime.now()
        base_name = 'PolarizeFlipExp{}Scan{}_Bkgd{}_{}-{}-{}_H{}_M{}.dat' \
                    ''.format(exp_number, scan_number, flag, now.year, now.month, now.date(), now.hour, now.minute)

        file_name = os.path.join(self._workDir, base_name)

        out_buffer = '# H  K  L  Flip  Error  SpinUp  SpinUpBk  SpinDown  SpinDownBk'
        for index in range(len(polarization_list)):
            hkl, flip, error, spin_up, spin_up_bkgd, spin_down, spin_down_bkgd = polarization_list[index]
            out_buffer += '{:4d}  {:4d}  {:4d}   {:3.5f}  {:3.5f}  {:3.5f}  {:3.5f}  {:3.5f}  {:3.5f}\n' \
                          ''.format(int(round(hkl[0])), int(round(hkl[1])), int(round(hkl[2])), flip, error,
                                    spin_up, spin_up_bkgd, spin_down, spin_down_bkgd)

        out_file = open(file_name, 'w')
        out_file.write(out_buffer)
        out_file.close()

        return

    @staticmethod
    def find_detector_size(exp_directory, exp_number):
        """
        find detector size from experiment directory
        :param exp_directory:
        :param exp_number
        :return:
        """
        # guess the file name
        first_xm_file = os.path.join(exp_directory, 'HB3A_Exp{0}_Scan0001_00001.xml'.format(exp_number))
        if os.path.exists(first_xm_file):
            file_size = os.path.getsize(first_xm_file)
            if file_size < 136132 * 2:
                det_size = 256, 256
            elif file_size < 529887 * 2:
                det_size = 512, 512
            else:
                raise RuntimeError('File size is over {0}.  It is not supported.')

            return True, det_size

        return False, 'Unable to find first Pt file {0}'.format(first_xm_file)

    def get_pt_numbers(self, exp_no, scan_no):
        """ Get Pt numbers (as a list) for a scan in an experiment
        :param exp_no:
        :param scan_no:
        :return: (Boolean, Object) as (status, pt number list/error message)
        """
        # Check
        if exp_no is None:
            exp_no = self._expNumber
        assert isinstance(exp_no, int)
        assert isinstance(scan_no, int)

        # Get workspace
        status, ret_obj = self.load_spice_scan_file(exp_no, scan_no)
        if status is False:
            return False, ret_obj
        else:
            table_ws_name = ret_obj
            table_ws = AnalysisDataService.retrieve(table_ws_name)

        # Get column for Pt.
        col_name_list = table_ws.getColumnNames()
        if 'Pt.' not in col_name_list:
            return False, 'No column with name Pt. can be found in SPICE table.'

        i_pt = col_name_list.index('Pt.')
        assert 0 <= i_pt < len(col_name_list), 'Impossible to have assertion error!'

        pt_number_list = []
        num_rows = table_ws.rowCount()
        for i in range(num_rows):
            pt_number = table_ws.cell(i, i_pt)
            pt_number_list.append(pt_number)

        return True, pt_number_list

    @staticmethod
    def get_existing_workspaces():
        """
        get the list of workspaces that are in ADS current
        :return:
        """
        ws_name_list = AnalysisDataService.getObjectNames()
        for index, ws_name in enumerate(ws_name_list):
            ws_i = AnalysisDataService.retrieve(ws_name)
            ws_type = ws_i.id()
            ws_name_list[index] = ws_name, ws_type

        return ws_name_list

    def get_raw_data_workspace(self, exp_no, scan_no, pt_no):
        """ Get raw workspace
        """
        try:
            ws = self._myRawDataWSDict[(exp_no, scan_no, pt_no)]
            assert isinstance(ws, mantid.dataobjects.Workspace2D)
        except KeyError:
            return None

        return ws

    def get_raw_detector_counts(self, exp_no, scan_no, pt_no):
        """
        Get counts on raw detector
        :param exp_no:
        :param scan_no:
        :param pt_no:
        :return: boolean, 2D numpy data
        """
        # Get workspace (in memory or loading)
        raw_ws = self.get_raw_data_workspace(exp_no, scan_no, pt_no)
        if raw_ws is None:
            return False, 'Raw data for Exp %d Scan %d Pt %d is not loaded.' % (exp_no, scan_no, pt_no)

        # Convert to numpy array
        det_shape = (self._detectorSize[0], self._detectorSize[1])
        array2d = numpy.ndarray(shape=det_shape, dtype='float')
        for i in range(det_shape[0]):
            for j in range(det_shape[1]):
                array2d[i][j] = raw_ws.readY(j * det_shape[0] + i)[0]

        # Flip the 2D array to look detector from sample
        array2d = numpy.flipud(array2d)

        return array2d

    def get_region_of_interest(self, exp_number, scan_number):
        """ Get region of interest
        :param exp_number:
        :param scan_number:
        :return: region of interest
        """
        # check
        assert isinstance(exp_number, int), 'Experiment number {0} must be an integer.'.format(exp_number)
        assert isinstance(scan_number, int) or scan_number is None, 'Scan number {0} must be either an integer or None.' \
                                                                    ''.format(scan_number)

        if (exp_number, scan_number) in self._roiDict:
            # able to find region of interest for this scan
            ret_status = True
            ret_value = self._roiDict[(exp_number, scan_number)]
        elif exp_number in self._roiDict:
            # able to find region of interest for this experiment
            ret_status = True
            ret_value = self._roiDict[exp_number]
        else:
            # region of interest of experiment is not defined
            ret_status = False
            ret_value = 'Unable to find ROI for experiment %d. Existing includes %s.' % (exp_number,
                                                                                         str(self._roiDict.keys()))

        return ret_status, ret_value

    def get_experiment(self):
        """
        Get experiment number
        :return:
        """
        return self._expNumber

    def mask_roi(self, exp_number, scan_number, pt_number, mask_range):
        """

        @param exp_number:
        @param scan_number:
        @param pt_number:
        @param mask_range:
        @return:
        """
        # load data
        # TODO shall check data holder first ... but not
        det_matrix = self.load_spice_xml_file2(exp_number, scan_number, pt_number)

        min_row = int(mask_range[0][0])
        min_col = int(mask_range[0][1])
        max_row = int(mask_range[1][0])
        max_col = int(mask_range[1][1])

        sum_count = numpy.sum(det_matrix[min_row:max_row, min_col:max_col])
        det_matrix[min_row:max_row, min_col:max_col] = 0

        return det_matrix, sum_count

    def integrate_roi(self, exp_number, scan_number, roi_range):
        """
        integrate counts in a given ROI
        :param exp_number:
        :param scan_number:
        :param roi_range:
        :return: (list, numpy.ndarray): list as the list of pt numbers.  numpy.ndarray (1D) for integrated values
        """
        # check inputs
        assert isinstance(exp_number, int), 'Experiment number {0} must be an integer but not a {1}' \
                                            ''.format(exp_number, type(exp_number))
        assert isinstance(scan_number, int), 'Scan number {0} must be an integer but not a {1}' \
                                             ''.format(scan_number, type(scan_number))
        if exp_number != self._expNumber:
            raise RuntimeError('Input experiment number {0} and stored experiment number {1} do '
                               'not match.'.format(exp_number, self._expNumber))

        # parse RIO range
        try:
            min_row = int(roi_range[0][0])
            min_col = int(roi_range[0][1])
            max_row = int(roi_range[1][0])
            max_col = int(roi_range[1][1])
        except IndexError as index_err:
            raise RuntimeError('Input ROI {0} does not have 2 x 2 elements. FYI: {1}'
                               ''.format(roi_range, index_err))

        # load all Pts. in this scan and do integration (simple summing)
        status, pt_number_list = self.get_pt_numbers(exp_number, scan_number)
        if not status:
            err_msg = pt_number_list
            raise RuntimeError('Unable to retrieve pt numbers from experiment {0} scan {1} due to {2}'
                               ''.format(exp_number, scan_number, err_msg))
        ws_pt_list = list()
        integrated_list = list()
        for pt_number in sorted(pt_number_list):
            count_matrix = self.load_spice_xml_file2(exp_no=exp_number, scan_no=scan_number, pt_no=pt_number)
            roi_counts = numpy.sum(count_matrix[min_row:max_row, min_col:max_col])
            if roi_counts < 0.0001:
                print ('[Warning] It is odd to have zero count on exp {} scan {} pt {}'
                       ''.format(exp_number, scan_number, pt_number))
            ws_pt_list.append(pt_number)
            integrated_list.append(roi_counts)
        # END-FOR

        # convert to numpy array
        vec_integrated = numpy.array(integrated_list)

        return pt_number_list, vec_integrated

    def load_spice_scan_file(self, exp_no, scan_no, spice_file_name=None):
        """
        Load a SPICE scan file to table workspace and run information matrix workspace.
        :param exp_no:
        :param scan_no:
        :param spice_file_name:
        :return: status (boolean), error message (string)
        """
        # Default for exp_no
        if exp_no is None:
            exp_no = self._expNumber

        # Check whether the workspace has been loaded
        assert isinstance(exp_no, int)
        assert isinstance(scan_no, int)
        out_ws_name = get_spice_table_name(exp_no, scan_no)
        if (exp_no, scan_no) in self._mySpiceTableDict:
            return True, out_ws_name

        # load the SPICE table data if the target workspace does not exist
        if not AnalysisDataService.doesExist(out_ws_name):
            # Form standard name for a SPICE file if name is not given
            if spice_file_name is None:
                spice_file_name = os.path.join(self._dataDir,
                                               get_spice_file_name(self._instrumentName, exp_no, scan_no))

            try:
                spice_table_ws, info_matrix_ws = mantidsimple.LoadSpiceAscii(Filename=spice_file_name,
                                                                             OutputWorkspace=out_ws_name,
                                                                             RunInfoWorkspace='TempInfo')
                mantidsimple.DeleteWorkspace(Workspace=info_matrix_ws)
            except RuntimeError as run_err:
                return False, 'Unable to load SPICE data %s due to %s' % (spice_file_name, str(run_err))
        else:
            spice_table_ws = AnalysisDataService.retrieve(out_ws_name)
        # END-IF

        # Store
        self._add_spice_workspace(exp_no, scan_no, spice_table_ws)

        return True, out_ws_name

    def load_spice_xml_file2(self, exp_no, scan_no, pt_no, xml_file_name=None):
        """ Load SPICE XML file using pure python method developed in this set
        @param exp_no:
        @param scan_no:
        @param pt_no:
        @param xml_file_name:
        @return:
        """
        # check input
        assert isinstance(exp_no, int), 'Experiment number {0} shall be integer but not a {1}' \
                                        ''.format(exp_no, type(exp_no))
        assert isinstance(scan_no, int), 'Scan number {0} shall be integer but not {1}' \
                                         ''.format(scan_no, type(scan_no))
        assert isinstance(pt_no, int), 'Pt number {0} shall be integer but not {1}'.format(pt_no, type(pt_no))

        # check whether it has been loaded
        if (exp_no, scan_no, pt_no) in self._loadedData:
            assert isinstance(self._loadedData[(exp_no, scan_no, pt_no)], numpy.ndarray),\
                'Loaded data must be a numpy ndarray'
            return self._loadedData[(exp_no, scan_no, pt_no)]

        # Get XML file name with full path
        if xml_file_name is None:
            # use default
            assert isinstance(exp_no, int) and isinstance(scan_no, int) and isinstance(pt_no, int),\
                'Experiment number {0} ({3}), Scan number {1} ({4}) and Pt number {2} ({5}) all shall be integers' \
                ''.format(exp_no, scan_no, pt_no, type(exp_no), type(scan_no), type(pt_no))
            xml_file_name = os.path.join(self._dataDir, get_det_xml_file_name(self._instrumentName,
                                                                              exp_no, scan_no, pt_no))
        # END-IF

        # check whether file exists
        if os.path.exists(xml_file_name) is False:
            raise RuntimeError('SPICE detector count XML file {0} for Exp {1} Scan {2} Pt {3} does not exist.'
                               ''.format(xml_file_name, exp_no, scan_no, pt_no))

        # load data
        count_matrix = parse_spice_xml.get_counts_xml_file(xml_file_name)
        assert isinstance(count_matrix, numpy.ndarray), 'Returned counts must be stored in numpy.ndarray'

        # store
        self._loadedData[(exp_no, scan_no, pt_no)] = count_matrix

        return count_matrix

    def load_spice_xml_file(self, exp_no, scan_no, pt_no, xml_file_name=None, over_write_existing=False):
        """
        Load SPICE's detector counts XML file from local data directory
        Requirements: the SPICE detector counts file does exist. The XML file's name is given either
                    explicitly by user or formed according to a convention with given experiment number,
                    scan number and Pt number
        :param exp_no:
        :param scan_no:
        :param pt_no:
        :param xml_file_name:
        :param over_write_existing: if workspace exists, load still
        :return: (bool, str) as (loaded or not, workspace name)
        """
        # Get XML file name with full path
        if xml_file_name is None:
            # use default
            assert isinstance(exp_no, int) and isinstance(scan_no, int) and isinstance(pt_no, int),\
                'Experiment number {0} ({3}), Scan number {1} ({4}) and Pt number {2} ({5}) all shall be integers' \
                ''.format(exp_no, scan_no, pt_no, type(exp_no), type(scan_no), type(pt_no))
            xml_file_name = os.path.join(self._dataDir, get_det_xml_file_name(self._instrumentName,
                                                                              exp_no, scan_no, pt_no))
        # END-IF

        # check whether file exists
        assert os.path.exists(xml_file_name)

        # retrieve and check SPICE table workspace
        spice_table_ws = self._get_spice_workspace(exp_no, scan_no)
        assert isinstance(spice_table_ws, mantid.dataobjects.TableWorkspace), 'SPICE table workspace must be a ' \
                                                                              'TableWorkspace but not %s.' \
                                                                              '' % type(spice_table_ws)
        spice_table_name = spice_table_ws.name()

        # load SPICE Pt.  detector file
        pt_ws_name = get_raw_data_workspace_name(exp_no, scan_no, pt_no)
        if AnalysisDataService.doesExist(pt_ws_name) and over_write_existing is False:
            pass
        else:
            try:
                mantidsimple.LoadSpiceXML2DDet(Filename=xml_file_name,
                                               OutputWorkspace=pt_ws_name,
                                               SpiceTableWorkspace=spice_table_name,
                                               PtNumber=pt_no)
                if self._refWorkspaceForMask is None or AnalysisDataService.doesExist(pt_ws_name) is False:
                    self._refWorkspaceForMask = pt_ws_name
            except RuntimeError as run_err:
                return False, str(run_err)
            # END-IF-ELSE

            # Add data storage
            assert AnalysisDataService.doesExist(pt_ws_name), 'Unable to locate workspace {0}.'.format(pt_ws_name)
            raw_matrix_ws = AnalysisDataService.retrieve(pt_ws_name)
            self._add_raw_workspace(exp_no, scan_no, pt_no, raw_matrix_ws)
        # END-IF

        return True, pt_ws_name
   
    def set_exp_number(self, exp_number):
        """ Add experiment number
        :param exp_number:
        :return:
        """
        assert isinstance(exp_number, int), 'Experiment number {0} must be an integer but not a {1}.' \
                                            ''.format(exp_number, type(exp_number))
        self._expNumber = exp_number

        return True
   
    def set_local_data_dir(self, local_dir):
        """
        Set local data storage
        :param local_dir:
        :return:
        """
        # Get absolute path
        if os.path.isabs(local_dir) is False:
            # Input is relative path to current working directory
            cwd = os.getcwd()
            local_dir = os.path.join(cwd, local_dir)

        # Create cache directory if necessary
        if os.path.exists(local_dir) is False:
            try:
                os.mkdir(local_dir)
            except OSError as os_err:
                return False, str(os_err)

        # Check whether the target is writable: if and only if the data directory is not from data server
        if not local_dir.startswith('/HFIR/HB3A/') and os.access(local_dir, os.W_OK) is False:
            return False, 'Specified local data directory %s is not writable.' % local_dir

        # Successful
        self._dataDir = local_dir

        return True, ''

    def set_working_directory(self, work_dir):
        """
        Set up the directory for working result
        :return: (boolean, string).
        """
        if os.path.exists(work_dir) is False:
            try:
                os.mkdir(work_dir)
            except OSError as os_err:
                return False, 'Unable to create working directory %s due to %s.' % (work_dir, str(os_err))
        elif os.access(work_dir, os.W_OK) is False:
            return False, 'User specified working directory %s is not writable.' % work_dir

        self._workDir = work_dir

        return True, ''

    def survey(self, exp_number, start_scan, end_scan):
        """ Load all the SPICE ascii file to get the big picture such that
        * the strongest peaks and their HKL in order to make data reduction and analysis more convenient
        :param exp_number: experiment number
        :param start_scan:
        :param end_scan:
        :return: 3-tuple (status, scan_summary list, error message)
        """
        # Check
        assert isinstance(exp_number, int), 'Experiment number must be an integer but not %s.' % type(exp_number)
        if isinstance(start_scan, int) is False:
            start_scan = 1
        if isinstance(end_scan, int) is False:
            end_scan = MAX_SCAN_NUMBER

        # Output workspace
        scan_sum_list = list()

        error_message = ''

        # Download and
        for scan_number in range(start_scan, end_scan+1):
            # check whether file exists
            if self.does_file_exist(exp_number, scan_number):
                spice_file_name = get_spice_file_name(self._instrumentName, exp_number, scan_number)
                spice_file_name = os.path.join(self._dataDir, spice_file_name)
            else:
                # SPICE file does not exist in data directory.
                print RuntimeError('Exp {0} Scan {1} does not exist.'.format(exp_number, scan_number))
                continue

            # Load SPICE file and retrieve information
            try:
                spice_table_ws_name = 'TempTable'
                mantidsimple.LoadSpiceAscii(Filename=spice_file_name,
                                            OutputWorkspace=spice_table_ws_name,
                                            RunInfoWorkspace='TempInfo')
                spice_table_ws = AnalysisDataService.retrieve(spice_table_ws_name)
                num_rows = spice_table_ws.rowCount()

                if num_rows == 0:
                    # it is an empty table
                    error_message += 'Scan %d: empty spice table.\n' % scan_number
                    continue

                col_name_list = spice_table_ws.getColumnNames()
                h_col_index = col_name_list.index('h')
                k_col_index = col_name_list.index('k')
                l_col_index = col_name_list.index('l')
                col_2theta_index = col_name_list.index('2theta')
                m1_col_index = col_name_list.index('m1')
                # optional as T-Sample
                if 'tsample' in col_name_list:
                    tsample_col_index = col_name_list.index('tsample')
                else:
                    tsample_col_index = None

                max_count = 0
                max_row = 0
                max_h = max_k = max_l = 0
                max_tsample = 0.

                two_theta = m1 = -1

                for i_row in range(num_rows):
                    det_count = spice_table_ws.cell(i_row, 5)
                    if det_count > max_count:
                        max_count = det_count
                        max_row = i_row
                        max_h = spice_table_ws.cell(i_row, h_col_index)
                        max_k = spice_table_ws.cell(i_row, k_col_index)
                        max_l = spice_table_ws.cell(i_row, l_col_index)
                        two_theta = spice_table_ws.cell(i_row, col_2theta_index)
                        m1 = spice_table_ws.cell(i_row, m1_col_index)
                        # t-sample is not a mandatory sample log in SPICE
                        if tsample_col_index is None:
                            max_tsample = 0.
                        else:
                            max_tsample = spice_table_ws.cell(i_row, tsample_col_index)
                # END-FOR

                # calculate wavelength
                wavelength = get_hb3a_wavelength(m1)
                if wavelength is None:
                    q_range = 0.
                    print('[ERROR] Scan number {0} has invalid m1 for wavelength.'.format(scan_number))
                else:
                    q_range = 4.*math.pi*math.sin(two_theta/180.*math.pi*0.5)/wavelength

                # appending to list
                scan_sum_list.append([max_count, scan_number, max_row, max_h, max_k, max_l,
                                      q_range, max_tsample])

            except RuntimeError as e:
                return False, None, str(e)
            except ValueError as e:
                # Unable to import a SPICE file without necessary information
                error_message += 'Scan %d: unable to locate column h, k, or l. See %s.' % (scan_number, str(e))
        # END-FOR (scan_number)

        if error_message != '':
            print('[Error]\n%s' % error_message)

        self._scanSummaryList = scan_sum_list

        return True, scan_sum_list, error_message

    @property
    def working_dir(self):
        return self._workDir
