from PyQt4 import QtGui, QtCore
import gui.ResultViewWindow_ui


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

        # define event handling related with widgets
        self.connect(self.ui.pushButton_saveResult, QtCore.SIGNAL('clicked()'),
                     self.do_save_integrated)

        self.connect(self.ui.pushButton_closeWindow, QtCore.SIGNAL('clicked()'),
                     self.do_close_window)

        return

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
        target_dir = str(QtGui.QFileDialog.getOpenFileName(self, self._workingDir, file_filter))
        if len(target_dir) == 0:
            # quit if user cancel the operation
            return

        # save result

        return