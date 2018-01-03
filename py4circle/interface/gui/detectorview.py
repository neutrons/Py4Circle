from six.moves import input
import numpy as np
import mplgraphicsview2d
from matplotlib.widgets import LassoSelector
from matplotlib.path import Path
from matplotlib.widgets import RectangleSelector
import matplotlib.pyplot as plt


class SelectFromCollection(object):
    """Select indices from a matplotlib collection using `LassoSelector`.

    Selected indices are saved in the `ind` attribute. This tool highlights
    selected points by fading them out (i.e., reducing their alpha values).
    If your collection has alpha < 1, this tool will permanently alter them.

    Note that this tool selects collection objects based on their *origins*
    (i.e., `offsets`).

    Parameters
    ----------
    ax : :class:`~matplotlib.axes.Axes`
        Axes to interact with.

    collection : :class:`matplotlib.collections.Collection` subclass
        Collection you want to select from.

    alpha_other : 0 <= float <= 1
        To highlight a selection, this tool sets all selected points to an
        alpha value of 1 and non-selected points to `alpha_other`.
    """

    def __init__(self, ax, collection, alpha_other=0.3):
        self.canvas = ax.figure.canvas
        self.collection = collection
        self.alpha_other = alpha_other

        self.xys = collection.get_offsets()
        self.Npts = len(self.xys)

        # Ensure that we have separate colors for each object
        self.fc = collection.get_facecolors()
        if len(self.fc) == 0:
            raise ValueError('Collection must have a facecolor')
        elif len(self.fc) == 1:
            self.fc = np.tile(self.fc, self.Npts).reshape(self.Npts, -1)

        self.lasso = LassoSelector(ax, onselect=self.onselect)
        self.ind = []

    def onselect(self, verts):
        path = Path(verts)
        self.ind = np.nonzero([path.contains_point(xy) for xy in self.xys])[0]
        self.fc[:, -1] = self.alpha_other
        self.fc[self.ind, -1] = 1
        self.collection.set_facecolors(self.fc)
        self.canvas.draw_idle()

    def disconnect(self):
        self.lasso.disconnect_events()
        self.fc[:, -1] = 1
        self.collection.set_facecolors(self.fc)
        self.canvas.draw_idle()


class DetectorView(mplgraphicsview2d.MplGraphicsView2D):
    """
    Detector counts 2D plot
    """
    ROI_Colors = ['red', 'white', 'black', 'green']

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

        # determine ROI rectangular color
        self._rectColorIndex = 0
        self._roiCollections = dict()

        # record for the size of ROI as all ROI shall have same sizes
        self._roiSizeX = None
        self._roiSizeY = None

        return

    def clear_canvas(self):
        """
        blabla
        """
        print 'Before Clear Canvas: ', self._myCanvas.axes
        super(DetectorView, self).clear_canvas()
        print 'After Clear Canvas: ', self._myCanvas.axes



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
        print event.key
        if event.key in ['R', 'r']:
            print('move to the right')
            self.move_rectangular_right()

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
        print('[DB...BAT...BAT] line_select_callback() is called at ({0}, {1})'.format(x2, y2))
        print("\t(%3.2f, %3.2f) --> (%3.2f, %3.2f)" % (x1, y1, x2, y2))
        print("\tThe button you used were: %s %s" % (eclick.button, erelease.button))

        # determine size of ROI/rectangular
        if self._roiSizeX is None or self._roiSizeY is None:
            self._roiSizeX = np.abs(x1 - x2)
            self._roiSizeY = np.abs(y1 - y2)

        # determine color
        color_index = self._rectColorIndex % len(DetectorView.ROI_Colors)
        roi_color = DetectorView.ROI_Colors[color_index]
        new_rect = plt.Rectangle((min(x1, x2), min(y1, y2)), self._roiSizeX, self._roiSizeY, # np.abs(x1 - x2), np.abs(y1 - y2),
                                 fill=True, alpha=0.2,
                                 color=roi_color, label='ROI {0}'.format(color_index),
                                 linewidth=5)
        patch_return = self._myCanvas.axes.add_patch(new_rect)

        # record rectangular
        self._roiCollections[color_index] = new_rect
       
        # color index increment
        self._rectColorIndex += 1


        # print 'Why cannot I draw a rectangular??? return = {0}.  Rectangualr = {1}'.format(patch_return, new_rect)

        self._lastRect = new_rect

        return self._lastRect

    def on_mouse_press_event(self, event):
        """

        @return:
        """
        print ('mouse pressed: ', event.xdata, event.ydata)

        self.toggle_selector(event)

        return

    def remove_roi(self, roi_index=None):
        """ remove specified ROI.  If not specified, then all ROI will be removed from canvas
        """
        # get roi indexes
        if roi_index is None:
            roi_index_list = self._roiCollections.keys()
        else:
            assert isinstance(roi_index, int), 'ROI index {0} shall be an integer but not a {1}.'.format(roi_index, type(roi_index))
            if roi_index not in self._roiCollections:
                raise RuntimeError('ROI with index {0} does not exist.'.format(roi_index))
            roi_index_list = [roi_index]
        # END-IF-ELSE

        # romove rectagular
        for roi_index in roi_index_list:
            self.remove_rectangular(self._roiCollections[roi_index])
            del self._roiCollections[roi_index]

        # reset roi index
        if roi_index is None:
            # reset ROI size
            self._roiSizeX = None
            self._roiSizeY = None

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
