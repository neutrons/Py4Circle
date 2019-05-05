#!/usr/bin/env python
# Test class FourCirclePolarizedNeutronProcessor
import sys
from py4circle.lib import polarized_neutron_processor


# TODO - TONIGHT 0 - Make this work such that Emil's migrated codes can be tested!
def main(args):
    """
    main test
    @param args:
    @return:
    """
    tester = polarized_neutron_processor.FourCirclePolarizedNeutronProcessor()
    tester.calculate_polarization_emil(exp_number=715,
                                       scan_number=73,
                                       pt_list=range(1, 829, 2))


if __name__ == '__main__':
    main(sys.argv)
