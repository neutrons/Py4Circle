"""
This module is renamed from parse_xml_data.py
"""
import os
import xml.etree.ElementTree as ET
import numpy
import re
from math import sqrt


def get_counts_xml_file(xml_name):
    """Get detector counts from a SPICE XML file
    @param xml_name:
    @return:
    """
    # check input
    assert isinstance(xml_name, str), 'TODO'
    if os.path.exists(xml_name) is False:
        raise RuntimeError('TODO')

    # get root and 'Data' ndoe
    tree = ET.parse(xml_name)
    root = tree.getroot()
    data_node = None
    for child in root:
        if child.tag == 'Data':
            data_node = child
            break

    # parse detectors counts string to array
    det = data_node.find('Detector')
    det_str = str(det.text).strip()

    # split to 2D array
    det_count_list = re.split('\t|\n', det_str)
    num_pts = len(det_count_list)
    # get detector size and check
    det_size = int(sqrt(num_pts))
    if det_size * det_size != num_pts:
        raise RuntimeError('Detector size {0}**2 does not match number of counts {1}'.format(det_size, num_pts))

    # list to 1D array and convert to float
    # det_array = numpy.ndarray(shape=(num_pts,), dtype='int')
    det_array = numpy.array(det_count_list)
    det_array = det_array.astype('float')
    # 1D array to 2D array
    det_matrix = det_array.reshape(det_size, det_size)

    # transpose?
    det_matrix = numpy.rot90(det_matrix, 1)

    return det_matrix


if __name__ == '__main__':
    xml_name = 'HB3A_exp578_scan0001_0041.xml'
    #xml_name = 'HB3A_exp640_scan0219_0021.xml'
    get_counts_xml_file(xml_name)
