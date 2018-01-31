import threading
import types
import inspect
import os

# IPython monkey patches the  pygments.lexer.RegexLexer.get_tokens_unprocessed method
# and breaks Sphinx when running within MantidPlot.
# We store the original method definition here on the pygments module before importing IPython
from pygments.lexer import RegexLexer
# Monkeypatch!
RegexLexer.get_tokens_unprocessed_unpatched = RegexLexer.get_tokens_unprocessed

#from IPython.qt.console.rich_ipython_widget import RichIPythonWidget
#from IPython.qt.inprocess import QtInProcessKernelManager

from qtconsole.rich_ipython_widget import RichIPythonWidget
from qtconsole.inprocess import QtInProcessKernelManager

try:
    from PyQt5 import QtGui, QtWidgets
    from PyQt5.QtWidgets import QApplication
except ImportError:
    from PyQt4.QtGui import QApplication


def our_run_code(self, code_obj, result=None):
    """ Method with which we replace the run_code method of IPython's InteractiveShell class.
        It calls the original method (renamed to ipython_run_code) on a separate thread
        so that we can avoid locking up the whole of MantidPlot while a command runs.
        Parameters

    @param self:
    @param code_obj: code object
          A compiled code object, to be executed
    @param result: ExecutionResult, optional
          An object to store exceptions that occur during execution.
    @return: False : Always, as it doesn't seem to matter.
    """
    thread = threading.Thread()

    # ipython 3.0 introduces a third argument named result
    nargs = len(inspect.getargspec(self.ipython_run_code).args)
    if nargs == 3:
        thread = threading.Thread(target=self.ipython_run_code, args=[code_obj,result])
    else:
        thread = threading.Thread(target=self.ipython_run_code, args=[code_obj])
    thread.start()
    while thread.is_alive():
        QApplication.processEvents()
    # We don't capture the return value of the ipython_run_code method but as far as I can tell
    #   it doesn't make any difference what's returned
    return 0


class IPyAnalysisWidget(RichIPythonWidget):
    """ Extends IPython's qt widget to include setting up and in-process kernel as well as the
        Mantid environment, plus our trick to avoid blocking the event loop while processing commands.
        This widget is set in the QDockWidget that houses the script interpreter within ApplicationWindow.
    """

    def __init__(self, *args, **kw):
        """
        initialization
        @param args:
        @param kw:
        """
        super(IPyAnalysisWidget, self).__init__(*args, **kw)

        # Create an in-process kernel
        kernel_manager = QtInProcessKernelManager()
        kernel_manager.start_kernel()
        kernel = kernel_manager.kernel
        kernel.gui = 'qt4'
        shell = kernel.shell

        # TODO/FIXME - Prototype
        dir(shell)
        print dir(shell)
        print
        # print shell.__dict__.keys()
        # print shell.user_variables()
        # print type(shell.user_variables())

        vdict = dict()
        vdict['a'] = 1232
        vdict['b'] = 12.11
        shell.push(vdict)
        print '\n----------------\n'

        # define Mantid. It is disabled now
        if False:
            # Figure out the full path to the mantidplotrc.py file and then %run it
            # create a python file to import mantid dynamically
            mantidplot_path = os.path.expanduser('~')
            mantidplot_run = os.path.join(mantidplot_path, 'mantidplotrc.py')
            self.generate_script_file(mantidplot_run)
            shell.run_line_magic('run', mantidplot_run)
            os.remove(mantidplot_run)
        # END-IF

        # These 3 lines replace the run_code method of IPython's InteractiveShell class (of which the
        # shell variable is a derived instance) with our method defined above. The original method
        # is renamed so that we can call it from within the our_run_code method.
        f = shell.run_code
        shell.run_code = types.MethodType(our_run_code, shell)
        shell.ipython_run_code = f

        kernel_client = kernel_manager.client()
        kernel_client.start_channels()

        self.kernel_manager = kernel_manager
        self.kernel_client = kernel_client

        self._mainApplication = None

        # self.start_mantid()
        # TODO/FIXME - Find out why there is such a debug section
        vdict2 = dict()
        import numpy
        vdict2['r1'] = numpy.array([2, 2, 34])
        shell.push(vdict2)

        return

    @staticmethod
    def _retrieve_non_python_command(script):
        """
        IPython widget might support some non-pyton command.  It might start with some prefix
        such as 'Run:' if user presses 'up-arrow'.
        Retrieve the correct command from the input string
        :param script:
        :return:
        """
        # convert previous command "Run: vbin, ipts=18420, runs=139148, tag='C', output='\tmp'" to a property command
        if script.startswith('"Run: '):
            # strip "Run: and " away
            script = script.split('Run: ')[1]
            if script[-1] == '"':
                script = script[:-1]
        elif script.startswith('Run: '):
            # strip Run: away
            script = script.split('Run: ')[1]

        return script

    def execute(self, source=None, hidden=False, interactive=False):
        """ Override super's execute() in order to emit customized signals to main application
        @param source:
        @param hidden:
        @param interactive:
        @return:
        """
        # process input script/command
        script = str(self.input_buffer).strip()

        # # prototype
        # if script.startswith('a') is False:
        #     source = 'a = 5\naa = 20\nfor i in range(10):\n  print (i)\n\n'
        #
        # super(RichIPythonWidget, self).execute(source, hidden, interactive=True)
        #
        # # TODO/FIXME - Debug return
        # return

        script = self._retrieve_non_python_command(script)

        # main application is workspace viewer
        is_reserved = False
        if self._mainApplication is not None and self._mainApplication.is_reserved_command(script):
            is_reserved = True
            exec_message = self._mainApplication.execute_reserved_command(script)
            script_transformed = script[:]
            script_transformed = script_transformed.replace('"', "'")
            source = '\"Run: %s\"' % script_transformed
        else:
            exec_message = None

        # call base class to execute
        super(RichIPythonWidget, self).execute(source, hidden, interactive)

        # then others
        if is_reserved:
            self._append_plain_text('\n%s\n' % exec_message)

        # NOTE/TODO - This section can be enabled to link current session to parent workspace

        if False and self._mainApplication is not None:
            # post_workspace_names = set(mtd.getObjectNames())
            # diff_set = post_workspace_names - prev_workspace_names
            # self._mainApplication.process_workspace_change(list(diff_set))
            pass

        return

    @staticmethod
    def generate_script_file(mantidplotrc):
        """
        generate a script file to launch mantid
        @param mantidplotrc:
        @return:
        """
        # check
        assert isinstance(mantidplotrc, str)

        # write
        file_content = ''
        file_content += 'import mantid\n'
        file_content += 'from mantid.kernel import *\n'
        file_content += 'from mantid.simpleapi import *\n'
        file_content += 'from mantid.geometry import *\n'
        file_content += 'from mantid.api import *\n'
        file_content += 'from mantid.api import AnalysisDataService as mtd'

        ofile = open(mantidplotrc, 'w')
        ofile.write(file_content)
        ofile.close()

        return

    def set_main_application(self, main_app):
        """ Set the main application to the iPython widget to call
        @param main_app:  main UI application
        @return:
        """
        # check
        assert main_app is not None

        # set
        self._mainApplication = main_app

        return

    def write_command(self, command):
        """
        Write a command to the iPython console
        Args:
            command: string for a python command

        Returns:
            None
        """
        # check
        assert isinstance(command, str)

        # set
        self._store_edits()
        self.input_buffer = command

        return

