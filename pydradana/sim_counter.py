# Author: Chao Gu, 2018

import numpy

from .sim_reader import SimReader
from .sim_configs import electron as _electron
from .sim_configs import deuteron as _deuteron
from .sim_configs import target_center as _z_center
from .sim_configs import gem_resolution as _gem_res
from .sim_configs import binning as _binning

__all__ = ['count_good_events', 'count_yield', 'count_z_ave']


def _get_general_cuts(reader):
    # find hits on each detector
    found_rd_0, found_rd_1 = reader.find_hits('RD', det_type='tracking', n_copy=2, pid=_deuteron)
    found_gem_0, found_gem_0_1, found_gem_1, found_gem_1_1 = reader.find_hits('GEM', det_type='tracking', n_copy=4, pid=_electron)
    found_sp = reader.find_hits('SP', pid=_electron)
    found_hc = reader.find_hits('HC', pid=_electron)

    found_gem_0[found_gem_0 < 0] = found_gem_0_1[found_gem_0 < 0]
    found_gem_1[found_gem_1 < 0] = found_gem_1_1[found_gem_1 < 0]

    is_good = (found_rd_0 >= 0) & (found_gem_0 >= 0) & (found_gem_1 >= 0) & (found_sp >= 0) & (found_hc >= 0)

    return found_rd_0, found_rd_1, found_gem_0, found_gem_1, found_sp, found_hc, is_good


def count_good_events(filename, start, stop):
    r = SimReader(filename, start, stop)

    *_, is_good = _get_general_cuts(r)

    theta = r.GUN.Theta[0] * 180.0 / numpy.pi
    theta_good = theta[is_good]

    hist_theta, _ = numpy.histogram(theta, **_binning)
    hist_theta_good, _ = numpy.histogram(theta_good, **_binning)

    result = {}
    result['hist_theta'] = hist_theta
    result['hist_theta_good'] = hist_theta_good

    return result


def count_z_ave(filename, start, stop):
    r = SimReader(filename, start, stop)

    _, _, found_gem_0, found_gem_1, _, _, is_good = _get_general_cuts(r)

    z = r.GUN.Z[0][is_good] - _z_center

    # GEMs
    x_gem_0 = r.GEM.X[found_gem_0][is_good]
    y_gem_0 = r.GEM.Y[found_gem_0][is_good]
    z_gem_0 = r.GEM.Z[found_gem_0][is_good] - _z_center
    x_gem_1 = r.GEM.X[found_gem_1][is_good]
    y_gem_1 = r.GEM.Y[found_gem_1][is_good]
    z_gem_1 = r.GEM.Z[found_gem_1][is_good] - _z_center

    #
    r_gem_0 = numpy.sqrt(x_gem_0**2 + y_gem_0**2)
    r_gem_1 = numpy.sqrt(x_gem_1**2 + y_gem_1**2)
    theta_gem_0 = numpy.arctan(r_gem_0 / z_gem_0)
    theta_gem_1 = numpy.arctan(r_gem_1 / z_gem_1)
    theta = (theta_gem_0 + theta_gem_1) / 2

    theta = theta * 180 / numpy.pi

    bins = _binning['bins']
    low, high = _binning['range']
    bin_size = (high - low) / bins
    hist_z_sum, _ = numpy.histogram(theta, weights=z, bins=bins + 4, range=(low - 2 * bin_size, high + 2 * bin_size))
    hist_z_count, _ = numpy.histogram(theta, bins=bins + 4, range=(low - 2 * bin_size, high + 2 * bin_size))

    result = {}
    result['hist_z_sum'] = hist_z_sum
    result['hist_z_count'] = hist_z_count

    return result


def count_yield(filename, start, stop, z_correction=None):
    r = SimReader(filename, start, stop)

    _, _, found_gem_0, found_gem_1, _, _, is_good = _get_general_cuts(r)

    n_good = numpy.count_nonzero(is_good)

    # silicon detector (1st layer)
    # x_rd_0 = r.RD.X[found_rd_0][is_good]
    # y_rd_1 = r.RD.Y[found_rd_1][is_good]

    # GEMs
    x_gem_0 = r.GEM.X[found_gem_0][is_good] + numpy.random.normal(0, _gem_res, n_good)
    y_gem_0 = r.GEM.Y[found_gem_0][is_good] + numpy.random.normal(0, _gem_res, n_good)
    z_gem_0 = r.GEM.Z[found_gem_0][is_good] - _z_center
    x_gem_1 = r.GEM.X[found_gem_1][is_good] + numpy.random.normal(0, _gem_res, n_good)
    y_gem_1 = r.GEM.Y[found_gem_1][is_good] + numpy.random.normal(0, _gem_res, n_good)
    z_gem_1 = r.GEM.Z[found_gem_1][is_good] - _z_center

    # HC
    # p_hc = r.HC.P[found_hc][is_good]

    #
    r_gem_0 = numpy.sqrt(x_gem_0**2 + y_gem_0**2)
    r_gem_1 = numpy.sqrt(x_gem_1**2 + y_gem_1**2)
    theta_gem_0 = numpy.arctan(r_gem_0 / z_gem_0)
    theta_gem_1 = numpy.arctan(r_gem_1 / z_gem_1)
    theta = (theta_gem_0 + theta_gem_1) / 2

    if z_correction is not None:
        dz = z_correction(theta)
        theta_gem_0 = numpy.arctan(r_gem_0 / (z_gem_0 - dz))
        theta_gem_1 = numpy.arctan(r_gem_1 / (z_gem_1 - dz))
        theta = (theta_gem_0 + theta_gem_1) / 2

    hist_theta, _ = numpy.histogram(theta * 180 / numpy.pi, **_binning)

    result = {}
    result['hist_theta'] = hist_theta

    return result
