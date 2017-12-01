import os

class FourCirclePolarizedNeutronProcessor(object):
    """
    """
    def __init__(self):
        """
        initialization
        """
        self._iptsNumber = None
        self._expNumber = None
        self._dataDir = None
        self._workDir = None
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

    def get_experiment(self):
        """
        Get experiment number
        :return:
        """
        return self._expNumber
   
    def set_exp_number(self, exp_number):
       """ Add experiment number
       :param exp_number:
       :return:
       """
       assert isinstance(exp_number, int), 'blabla'
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
        :return: (boolean, string)
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


