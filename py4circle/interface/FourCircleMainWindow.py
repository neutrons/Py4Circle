from PyQt4 import QtCore, QtGui
import gui.MainWindow_ui as MainWindow_ui


class FourCircleMainWindow(QtGui.QMainWindow):
    """
    blabla
    """
    def __init__(self):
        """

        """
        super(FourCircleMainWindow, self).__init__(None)

        # define class variable

        # set up UI
        self.ui = MainWindow_ui.Ui_MainWindow()
        self.ui.setupUi(self)

        # link
        self.ui.pushButton_applySetup
        self.ui.pushButton_browseWorkDir

        self.ui.pushButton_addROI
        self.ui.pushButton_integrateROI


        return
