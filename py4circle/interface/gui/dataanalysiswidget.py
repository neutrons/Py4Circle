########################################################################
#
# General-purposed plotting window
#
########################################################################
from ipythonanalysiswidget import IPyAnalysisWidget

try:
    from PyQt5 import QtCore
    from PyQt5.QtWidgets import QWidget
except ImportError:
    from PyQt4 import QtCore
    from PyQt4.QtGui import QWidget
from MyTableWidget import NTableWidget
from mplgraphicsview1d import MplGraphicsView1D

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s


# TODO/FIXME - class WorkspaceViewWidget does not work here!
class WorkspaceViewWidget(QWidget):
    """ Class for general-purposed plot window
    """

    # reserved command
    Reserved_Command_List = ['plot', 'refresh', 'exit']

    def __init__(self, parent=None):
        """ Init
        """
        import ui_WorkspacesView_ui as ui_WorkspacesView

        # call base
        QWidget.__init__(self)

        # Parent & others
        self._myMainWindow = None
        self._myParent = parent

        # set up UI
        self.ui = ui_WorkspacesView.Ui_Form()
        self.ui.setupUi(self)

        self.ui.tableWidget_dataStructure.setup()
        self.ui.widget_ipython.set_main_application(self)

        # define event handling methods
        self.connect(self.ui.pushButton_plot, QtCore.SIGNAL('clicked()'),
                     self.do_plot_workspace)
        self.connect(self.ui.pushButton_toIPython, QtCore.SIGNAL('clicked()'),
                     self.do_write_to_console)
        self.connect(self.ui.pushButton_clear, QtCore.SIGNAL('clicked()'),
                     self.do_clear_canvas)
        self.connect(self.ui.pushButton_fitCanvas, QtCore.SIGNAL('clicked()'),
                     self.do_fit_canvas)

        return

    def do_clear_canvas(self):
        """
        clear the plots on the canvas
        :return:
        """
        self.ui.graphicsView_general.reset_canvas()

        return

    def do_fit_canvas(self):
        """
        resize the canvas to make the plots fit (0 to 5% above max value)
        :return:
        """
        self.ui.graphicsView_general.resize_canvas(0, 1.05)

        return

    def do_plot_workspace(self):
        """
        plot selected workspace
        :return:
        """
        # get selected workspace name
        selected_workspace_name_list = self.ui.tableWidget_dataStructure.get_selected_workspaces()

        # get the data from main application
        # controller = self._myMainWindow.get_controller()

        for workspace_name in selected_workspace_name_list:
            # data_set = controller.get_data_from_workspace(workspace_name)
            self.ui.graphicsView_general.plot_workspace(workspace_name)

        return

    def do_write_to_console(self):
        """
        write the workspace name to IPython console
        :return:
        """
        # get workspace name
        ws_name_list = self.ui.tableWidget_dataStructure.get_selected_workspaces()

        # output string
        ipython_str = ''
        for ws_name in ws_name_list:
            ipython_str += '"{0}"    '.format(ws_name)

        # export the ipython
        self.ui.widget_ipython.write_command(ipython_str)

        return

    def execute_reserved_command(self, script):
        """
        override execute?
        :param script:
        :return:
        """
        script = script.strip()
        command = script.split()[0]

        print '[DB...BAT] Going to execute: ', script

        if command == 'plot':
            print 'run: ', script
            err_msg = self.plot(script)

        elif command == 'refresh':
            err_msg = self.refresh_workspaces()

        elif command == 'exit':
            self._myParent.close()
            # self.close()
            err_msg = None

        elif command == 'vhelp' or command == 'what':
            # output help
            err_msg = self.get_help_message()
        else:
            try:
                status, err_msg = self._myMainWindow.execute_command(script)
            except AssertionError as ass_err:
                status = False
                err_msg = 'Failed to execute VDRIVE command due to %s.' % str(ass_err)

            if status:
                err_msg = 'VDRIVE command %s is executed successfully.\n%s.' % (command, err_msg)
            else:
                err_msg = 'Failed to execute VDRIVE command %s due to\n%s.' % (command, err_msg)

        return err_msg

    @staticmethod
    def get_command_help(command):
        """
        get a help line for a specific command
        :param command:
        :return:
        """
        if command == 'plot':
            help_str = 'Plot a workspace.  Example: plot <workspace name>'

        elif command == 'refresh':
            help_str = 'Refresh the graph above.'

        elif command == 'exit':
            help_str = 'Exist the application.'

        elif command == 'vhelp' or command == 'what':
            # output help
            help_str = 'Get help.'

        else:
            help_str = 'Reserved VDRIVE command.  Run> %s' % command

        return help_str

    def get_help_message(self):
        """

        :return:
        """
        message = 'LAVA Reserved commands:\n'\

        for command in sorted(self.Reserved_Command_List):
            message += '%-15s: %s\n' % (command, self.get_command_help(command))

        return message

    def is_reserved_command(self, script):
        """

        :param script:
        :return:
        """
        command = script.strip().split(',')[0].strip()
        print '[DB...Test Reserved] command = ', command, 'is reserved command'

        return command in self.Reserved_Command_List

    def plot(self, script):
        """

        :param script:
        :return:
        """
        terms = script.split()

        if len(terms) == 1:
            # no given option, plot selected workspace
            return 'Not implemented yet'

        elif terms[1] == 'clear':
            # clear canvas
            self.ui.graphicsView_general.clear_all_lines()

        else:
            # plot workspace
            for i_term in range(1, len(terms)):
                ws_name = terms[i_term]
                try:
                    self.ui.graphicsView_general.plot_workspace(ws_name)
                except KeyError as key_err:
                    return str(key_err)

        return ''

    def process_workspace_change(self, diff_set):
        """

        :param diff_set:
        :return:
        """
        # TODO/NOW/ISSUE/51 - Implement!

        return

    def refresh_workspaces(self):
        """

        :return:
        """
        workspace_names = AnalysisDataService.getObjectNames()

        self.ui.tableWidget_dataStructure.remove_all_rows()
        error_message = ''
        for ws_name in workspace_names:
            try:
                self.ui.tableWidget_dataStructure.add_workspace(ws_name)
            except Exception as ex:
                error_message += 'Unable to add %s to table due to %s.\n' % (ws_name, str(ex))
        # END-FOR

        return error_message

    def set_main_window(self, main_window):
        """
        Set up the main window which generates this window
        :param main_window:
        :return:
        """
        # check
        assert main_window is not None
        try:
            main_window.get_reserved_commands
        except AttributeError as att_err:
            raise AttributeError('Parent window does not have required method get_reserved_command. FYI: {0}'
                                 ''.format(att_err))

        # set
        self._myMainWindow = main_window
        reserved_command_list = main_window.get_reserved_commands()
        self.Reserved_Command_List.extend(reserved_command_list)

        return


class GeneralTableView(NTableWidget):
    """
    Extended table widget for general purpose
    """

    SetupList = [('Workspace', 'str'),
                 ('Type', 'str'),
                 ('', 'checkbox')]

    def __init__(self, parent):
        """
        initialization
        :param parent:
        """
        super(GeneralTableView, self).__init__(parent)

        return

    def add_workspace(self, ws_name, ws_type):
        """
        add an entry as a workspace
        :param ws_name:
        :param ws_type:
        :return:
        """
        assert isinstance(ws_name, str), 'Workspace name must be a string'
        assert isinstance(ws_type, str), 'Workspace type {0} must be a string but not a {1}' \
                                         ''.format(ws_type, type(ws_type))
        self.append_row([ws_name, ws_type, False])

        return

    def get_selected_workspaces(self):
        """
        get the names of workspace in the selected rows
        :return:
        """
        selected_rows = self.get_selected_rows(True)

        ws_name_list = list()
        for i_row in selected_rows:
            ws_name = self.get_cell_value(i_row, 0)
            ws_name_list.append(ws_name)

        return ws_name_list

    def setup(self):
        """
        set up the workspace
        :return:
        """
        self.init_setup(self.SetupList)

        # column width
        self.setColumnWidth(0, 360)
        self.setColumnWidth(1, 120)

        return


class GeneralPurposeDataView(MplGraphicsView1D):
    """
    Extended table widget for general purpose
    """
    def __init__(self, parent):
        """
        initialization
        :param parent:
        """
        super(GeneralPurposeDataView, self).__init__(parent)

        return
