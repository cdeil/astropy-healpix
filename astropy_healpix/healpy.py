# Licensed under a 3-clause BSD style license - see LICENSE.rst

from __future__ import absolute_import, print_function, division

"""
This submodule provides a healpy-compatible interface.
"""

import numpy as np
from astropy import units as u
from astropy.coordinates.representation import CartesianRepresentation, UnitSphericalRepresentation

from .core import (nside_to_pixel_resolution, nside_to_pixel_area,
                   nside_to_npix, npix_to_nside, nested_to_ring, ring_to_nested,
                   level_to_nside, lonlat_to_healpix, healpix_to_lonlat,
                   boundaries_lonlat, bilinear_interpolation_weights,
                   interpolate_bilinear_lonlat)

RAD2DEG = 180 / np.pi

__all__ = ['nside2resol',
           'nside2pixarea',
           'nside2npix',
           'npix2nside',
           'pix2ang',
           'ang2pix',
           'order2nside',
           'nest2ring',
           'ring2nest',
           'boundaries']


def _healpy_lonlat(lon, lat, lonlat=False):
    # We use in-place operations below to avoid making temporary arrays - this
    # is safe because the lon/lat arrays returned from healpix_to_lonlat are
    # new and not used elsewhere.
    if lonlat:
        return lon.to(u.deg).value, lat.to(u.deg).value
    else:
        lat, lon = lat.to(u.rad).value, lon.to(u.rad).value
        if np.isscalar(lon):
            return 0.5 * np.pi - lat, lon
        else:
            lat = np.subtract(0.5 * np.pi, lat, out=lat)
            return lat, lon


def nside2resol(nside, arcmin=False):
    """Drop-in replacement for healpy `~healpy.pixelfunc.nside2resol`."""
    resolution = nside_to_pixel_resolution(nside)
    if arcmin:
        return resolution.to(u.arcmin).value
    else:
        return resolution.to(u.rad).value


def nside2pixarea(nside, degrees=False):
    """Drop-in replacement for healpy `~healpy.pixelfunc.nside2pixarea`."""
    area = nside_to_pixel_area(nside)
    if degrees:
        return area.to(u.deg ** 2).value
    else:
        return area.to(u.sr).value


def nside2npix(nside):
    """Drop-in replacement for healpy `~healpy.pixelfunc.nside2npix`."""
    return nside_to_npix(nside)


def npix2nside(npix):
    """Drop-in replacement for healpy `~healpy.pixelfunc.npix2nside`."""
    return npix_to_nside(npix)


def order2nside(order):
    """Drop-in replacement for healpy `~healpy.pixelfunc.order2nside`."""
    return level_to_nside(order)


def pix2ang(nside, ipix, nest=False, lonlat=False):
    """Drop-in replacement for healpy `~healpy.pixelfunc.pix2ang`."""
    lon, lat = healpix_to_lonlat(ipix, nside, order='nested' if nest else 'ring')
    return _healpy_lonlat(lon, lat, lonlat=lonlat)


def ang2pix(nside, theta, phi, nest=False, lonlat=False):
    """Drop-in replacement for healpy `~healpy.pixelfunc.ang2pix`."""
    # Unlike in pix2ang, we don't use in-place operations since we don't
    # want to modify theta and phi since the user may be using them elsewhere.
    if lonlat:
        lon = np.asarray(theta) / RAD2DEG
        lat = np.asarray(phi) / RAD2DEG
    else:
        lat = np.pi / 2. - np.asarray(theta)
        lon = np.asarray(phi)
    lon, lat = u.Quantity(lon, u.rad, copy=False), u.Quantity(lat, u.rad, copy=False)
    return lonlat_to_healpix(lon, lat, nside, order='nested' if nest else 'ring')


def nest2ring(nside, ipix):
    """Drop-in replacement for healpy `~healpy.pixelfunc.nest2ring`."""
    ipix = np.atleast_1d(ipix).astype(np.int64, copy=False)
    return nested_to_ring(ipix, nside)


def ring2nest(nside, ipix):
    """Drop-in replacement for healpy `~healpy.pixelfunc.ring2nest`."""
    ipix = np.atleast_1d(ipix).astype(np.int64, copy=False)
    return ring_to_nested(ipix, nside)


def boundaries(nside, pix, step=1, nest=False):
    """Drop-in replacement for healpy `~healpy.boundaries`."""
    pix = np.asarray(pix)
    if pix.ndim > 1:
        # For consistency with healpy we only support scalars or 1D arrays
        raise ValueError("Array has to be one dimensional")
    lon, lat = boundaries_lonlat(pix, step, nside, order='nested' if nest else 'ring')
    rep_sph = UnitSphericalRepresentation(lon, lat)
    rep_car = rep_sph.to_cartesian().xyz.value.swapaxes(0, 1)
    if rep_car.shape[0] == 1:
        return rep_car[0]
    else:
        return rep_car


def vec2ang(vectors, lonlat=False):
    """Drop-in replacement for healpy `~healpy.vec2ang`."""
    x, y, z = vectors.transpose()
    rep_car = CartesianRepresentation(x, y, z)
    rep_sph = rep_car.represent_as(UnitSphericalRepresentation)
    return _healpy_lonlat(rep_sph.lon.ravel(), rep_sph.lat.ravel(), lonlat=lonlat)


def get_interp_weights(nside, theta, phi=None, nest=False, lonlat=False):
    """
    Drop-in replacement for healpy `~healpy.get_interp_weights`, although
    note that the order of the weights and pixels may differ.
    """
    if phi is None:
        theta, phi = pix2ang(theta, nest=nest)
    if lonlat:
        lon = np.asarray(theta) / RAD2DEG
        lat = np.asarray(phi) / RAD2DEG
    else:
        lat = np.pi / 2. - np.asarray(theta)
        lon = np.asarray(phi)
    lon, lat = u.Quantity(lon, u.rad, copy=False), u.Quantity(lat, u.rad, copy=False)
    return bilinear_interpolation_weights(lon, lat, nside, order='nested' if nest else 'ring')


def get_interp_val(m, theta, phi, nest=False, lonlat=False):
    """
    Drop-in replacement for healpy `~healpy.get_interp_val`.
    """
    if lonlat:
        lon = np.asarray(theta) / RAD2DEG
        lat = np.asarray(phi) / RAD2DEG
    else:
        lat = np.pi / 2. - np.asarray(theta)
        lon = np.asarray(phi)
    lon, lat = u.Quantity(lon, u.rad, copy=False), u.Quantity(lat, u.rad, copy=False)
    return interpolate_bilinear_lonlat(lon, lat, m, order='nested' if nest else 'ring')
