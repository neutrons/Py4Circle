import mplgraphicsview1d


class ResultView1D(mplgraphicsview1d.MplGraphicsView1D):
    """
    Extended graphic viewer for integrated ROIs
    """
    def __init__(self, parent):
        """
        initialization
        :param parent:
        """
        # init
        super(ResultView1D, self).__init__(parent)

        # unit of X-axis
        self._titleX = None
        self._unitX = None
        self._labelX = None

        return

    def plot_roi(self, vec_x, vec_y, color, roi_name, title_x, unit):
        """

        :param vec_x:
        :param vec_y:
        :return:
        """
        # check inputs type
        assert isinstance(title_x, str), 'Title must be a string'
        assert isinstance(unit, str), 'Unit must be a string'

        # check against X-label and unit
        if self._titleX is not None and self._titleX != title_x:
            # a new title
            self._labelX = '{0} ({1})'.format(title_x, unit)
            self._titleX = title_x
            self._unitX = unit

            # clear the image
            self.clear_all_lines()

            # set X label
            self.set_axis_labels(x_axis=self._labelX)
        # END-IF

        # plot
        self.add_plot(vec_x, vec_y, color=color, label=roi_name)

        return
