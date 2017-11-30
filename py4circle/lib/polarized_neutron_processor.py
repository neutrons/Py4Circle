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


