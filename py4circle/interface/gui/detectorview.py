from six.moves import input
import numpy as np
import mplgraphicsview2d
# from matplotlib.widgets import LassoSelector
# from matplotlib.path import Path
from matplotlib.widgets import RectangleSelector
import matplotlib.pyplot as plt


class DetectorView(mplgraphicsview2d.MplGraphicsView2D):
    """
    Detector counts 2D plot
    """
    ROI_Colors = ['red', 'green', 'blue', 'orange', 'yellow', 'black']

    def __init__(self, parent):
        """

        @param parent:
        """
        # initialization on base class
        super(DetectorView, self).__init__(parent)

        self.current_ax = self._myCanvas.axes

        # connect events and their handlers
        self._myCanvas.mpl_connect('button_press_event', self.on_mouse_press_event)
        self._myCanvas.mpl_connect('key_press_event', self.move_rectangular)

        line_props = dict(color='green', linestyle='-',
                          linewidth=2, alpha=0.5)
        self._myRS = RectangleSelector(self._myCanvas.axes, self.line_select_callback,
                                       drawtype='box',
                                       useblit=False,  # NOTE: this is the key for leaving rectangular on the map
                                       button=[1, 3],  # don't use middle button
                                       minspanx=5, minspany=5,
                                       spancoords='pixels',
                                       # interactive=True,
                                       lineprops=line_props)

        # record for last painted rectangular
        self._lastRect = None

        # determine ROI rectangular color
        self._rectColorIndex = 0
        self._roiCollections = dict()

        # record for the size of ROI as all ROI shall have same sizes
        self._roiSizeX = None
        self._roiSizeY = None

        return

    def clear_canvas(self):
        """ clear canvas
        :return:
        """
        print ('[DB...BAT] Before Clear Canvas: ', self._myCanvas.axes)
        super(DetectorView, self).clear_canvas()
        print ('[DB...BAT] After Clear Canvas: ', self._myCanvas.axes)

        return

    def get_roi_colors(self):
        """
        get all the ROI colors
        :return:
        """
        color_dict = dict()
        for roi_name in self._roiCollections.keys():
            roi_color = self._roiCollections[roi_name][1]
            assert isinstance(roi_color, str), 'ROI color {0} must be a string but not a {1}' \
                                               ''.format(roi_color, type(roi_color))
            color_dict[roi_name] = roi_color

        return color_dict

    def get_roi_dimensions(self):
        """
        get all the ROI/rectangular's dimensions (x0, y0), (x1, y1)
        :return: a dictionary with rectangular dimensions: left-bottom x, left-bottom y, width, height
        """
        dim_dict = {}
        for roi_name in self._roiCollections.keys():
            roi_rect = self._roiCollections[roi_name][0]
            assert isinstance(roi_rect, plt.Rectangle),\
                'Rectangular/ROI of {0} must be a a plt.Rectangle instance but not a {1}' \
                ''.format(roi_name, type(roi_rect))
            lb_x, lb_y = roi_rect.get_xy()
            width = roi_rect.get_width()
            height = roi_rect.get_height()

            dim_dict[roi_name] = (lb_x, lb_y, width, height)  #

            # # debug output
            # print '[DB...BAT] ROI {0}. Bottom-left ({1}, {2}). Width = {3}; Height = {4}' \
            #       ''.format(roi_name, lb_x, lb_y, width, height)

        # END-FOR

        return dim_dict

    def toggle_selector(self, event):
        """
        toggle the state of selector (on or off)
        @param event:
        @return:
        """
        print(' Key pressed.')
        if event.key in ['Q', 'q'] and self._myRS.active:
            print(' RectangleSelector deactivated.')
            self._myRS.set_active(False)
        if event.key in ['A', 'a'] and not self._myRS.active:
            print(' RectangleSelector activated.')
            self._myRS.set_active(True)

        return

    def line_select_callback(self, eclick, erelease):
        """
        for Rectangular selector
        @param eclick:
        @param erelease:
        @return:
        """
        # eclick and erelease are the press and release events
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata
        print ('[DB...BAT...BAT] line_select_callback() is called at ({0}, {1})'.format(x2, y2))
        print ("\t(%3.2f, %3.2f) --> (%3.2f, %3.2f)" % (x1, y1, x2, y2))
        print ("\tThe button you used were: %s %s" % (eclick.button, erelease.button))
        print ('\tROI size: {}, {}'.format(self._roiSizeX, self._roiSizeY))

        # determine size of ROI/rectangular
        if self._roiSizeX is None or self._roiSizeY is None:
            self._roiSizeX = int(np.abs(x1 - x2))
            self._roiSizeY = int(np.abs(y1 - y2))

        # determine color
        color_index = self._rectColorIndex % len(DetectorView.ROI_Colors)
        roi_color = DetectorView.ROI_Colors[color_index]

        # Set rectangular on coordinates on integers
        min_x = int(min(x1, x2))
        min_y = int(min(y1, y2))

        # add
        new_rect = self.canvas().add_rectangular(min_x, min_y, size_x=self._roiSizeX, size_y=self._roiSizeY,
                                                 color=roi_color, label='ROI {0}'.format(color_index))

        # record rectangular
        self._roiCollections[color_index] = new_rect, roi_color
       
        # color index increment
        self._rectColorIndex += 1
        # print 'Why cannot I draw a rectangular??? return = {0}.  Rectangular = {1}'.format(patch_return, new_rect)

        self._lastRect = new_rect

        return self._lastRect

    def move_roi(self, roi_index, dx=0, dy=0):
        """
        move region of interest (rectangular) from canvas
        :param roi_index:
        :param dx:
        :param dy:
        :return:
        """
        # check input
        assert isinstance(roi_index, int), 'Region of interest\'s index {0} must be an integer but not a {1}' \
                                           ''.format(roi_index, type(roi_index))
        if roi_index not in self._roiCollections:
            raise RuntimeError('ROI index {0} does not exist in collection dictionary with keys {1}'
                               ''.format(roi_index, self._roiCollections.keys()))

        # get rectangular
        roi_rect = self._roiCollections[roi_index][0]

        # move along X
        if dx != 0:
            x = roi_rect.get_x()
            roi_rect.set_x(x+dx)

        # move along Y
        if dy != 0:
            y = roi_rect.get_y()
            roi_rect.set_y(y+dy)

        # flush
        self.canvas()._flush()

        return

    def move_rectangular_right(self):
        """
        move the rectangular to right
        @return:
        """
        w = self._lastRect.get_width()
        x = self._lastRect.get_x()
        self._lastRect.set_x(x + w * 0.1)
        #  plt.show()

    def move_rectangular(self, event):
        """
        move the rectangular from with key pressed
        @param event:
        @return:
        """
        if event.key in ['R', 'r']:
            self.move_rectangular_right()

        return

    def on_mouse_press_event(self, event):
        """

        @return:
        """
        self.toggle_selector(event)

        return

    def remove_roi(self, roi_index=None):
        """ remove specified ROI.  If not specified, then all ROI will be removed from canvas
        """
        # reset roi index
        if roi_index is None:
            # reset ROI size
            self._roiSizeX = None
            self._roiSizeY = None

        # get roi indexes
        if roi_index is None:
            roi_index_list = self._roiCollections.keys()
        else:
            assert isinstance(roi_index, int), 'ROI index {0} shall be an integer but not a {1}.' \
                                               ''.format(roi_index, type(roi_index))
            if roi_index not in self._roiCollections:
                raise RuntimeError('ROI with index {0} does not exist.  Existing ROIs are {1}'
                                   ''.format(roi_index, self._roiCollections.keys()))
            roi_index_list = [roi_index]
        # END-IF-ELSE

        # remove rectangular
        for roi_index in roi_index_list:
            rectangular, color = self._roiCollections[roi_index]
            rectangular.remove()
            del self._roiCollections[roi_index]

        # flush
        self.canvas()._flush()

        return


# if __name__ == '__main__':
#         import matplotlib.pyplot as plt
#
#         plt.ion()
#         data = np.random.rand(100, 3)
#
#         subplot_kw = dict(xlim=(0, 1), ylim=(0, 1), autoscale_on=False)
#         fig, ax = plt.subplots(subplot_kw=subplot_kw)
#
#         pts = ax.scatter(data[:, 0], data[:, 1], s=80, c=data[:, 2])
#         selector = SelectFromCollection(ax, pts)
#
#         plt.draw()
#         input('Press Enter to accept selected points')
#         print("Selected points:")
#         print(selector.xys[selector.ind])
#         selector.disconnect()
#
#         # Block end of script so you can check that the lasso is disconnected.
#         input('Press Enter to quit')
