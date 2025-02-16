# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Tests for specific implementation aspects of the grib saver.
Ported here from 'iris.tests.integration.test_grib_save'.

"""

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else
import iris_grib.tests as tests

import os
import datetime

import cf_units
import numpy as np

import iris
import iris.cube
import iris.coord_systems
import iris.coords
import iris.exceptions
import iris.util

import eccodes
from iris_grib._load_convert import _MDI as MDI


class TestLoadSave(tests.TestGribMessage):
    def setUp(self):
        self.skip_keys = []

    def test_latlon_forecast_plev(self):
        source_grib = tests.get_data_path(("GRIB", "uk_t", "uk_t.grib2"))
        cubes = iris.load(source_grib)
        with self.temp_filename(suffix=".grib2") as temp_file_path:
            iris.save(cubes, temp_file_path)
            expect_diffs = {
                "totalLength": (4837, 4832),
                "productionStatusOfProcessedData": (0, 255),
                "scaleFactorOfRadiusOfSphericalEarth": (MDI, 0),
                "shapeOfTheEarth": (0, 1),
                "scaledValueOfRadiusOfSphericalEarth": (MDI, 6367470),
                "scaledValueOfEarthMajorAxis": (MDI, 0),
                "scaleFactorOfEarthMajorAxis": (MDI, 0),
                "scaledValueOfEarthMinorAxis": (MDI, 0),
                "scaleFactorOfEarthMinorAxis": (MDI, 0),
                "typeOfGeneratingProcess": (0, 255),
                "generatingProcessIdentifier": (128, 255),
            }
            self.assertGribMessageDifference(
                source_grib,
                temp_file_path,
                expect_diffs,
                self.skip_keys,
                skip_sections=[2],
            )

    def test_rotated_latlon(self):
        source_grib = tests.get_data_path(
            ("GRIB", "rotated_nae_t", "sensible_pole.grib2")
        )
        cubes = iris.load(source_grib)
        with self.temp_filename(suffix=".grib2") as temp_file_path:
            iris.save(cubes, temp_file_path)
            expect_diffs = {
                "totalLength": (648196, 648191),
                "productionStatusOfProcessedData": (0, 255),
                "scaleFactorOfRadiusOfSphericalEarth": (MDI, 0),
                "shapeOfTheEarth": (0, 1),
                "scaledValueOfRadiusOfSphericalEarth": (MDI, 6367470),
                "scaledValueOfEarthMajorAxis": (MDI, 0),
                "scaleFactorOfEarthMajorAxis": (MDI, 0),
                "scaledValueOfEarthMinorAxis": (MDI, 0),
                "scaleFactorOfEarthMinorAxis": (MDI, 0),
                "longitudeOfLastGridPoint": (392109982, 32106370),
                "latitudeOfLastGridPoint": (19419996, 19419285),
                "typeOfGeneratingProcess": (0, 255),
                "generatingProcessIdentifier": (128, 255),
            }
            self.assertGribMessageDifference(
                source_grib,
                temp_file_path,
                expect_diffs,
                self.skip_keys,
                skip_sections=[2],
            )

    def test_time_mean(self):
        # This test for time-mean fields also tests negative forecast time.
        source_grib = tests.get_data_path(
            ("GRIB", "time_processed", "time_bound.grib2")
        )
        cubes = iris.load(source_grib)
        expect_diffs = {
            "totalLength": (21232, 21227),
            "productionStatusOfProcessedData": (0, 255),
            "scaleFactorOfRadiusOfSphericalEarth": (MDI, 0),
            "shapeOfTheEarth": (0, 1),
            "scaledValueOfRadiusOfSphericalEarth": (MDI, 6367470),
            "scaledValueOfEarthMajorAxis": (MDI, 0),
            "scaleFactorOfEarthMajorAxis": (MDI, 0),
            "scaledValueOfEarthMinorAxis": (MDI, 0),
            "scaleFactorOfEarthMinorAxis": (MDI, 0),
            "longitudeOfLastGridPoint": (356249908, 356249809),
            "latitudeOfLastGridPoint": (-89999938, -89999944),
            "typeOfGeneratingProcess": (0, 255),
            "generatingProcessIdentifier": (128, 255),
            "typeOfTimeIncrement": (2, 255),
        }
        self.skip_keys.append("stepType")
        self.skip_keys.append("stepTypeInternal")
        with self.temp_filename(suffix=".grib2") as temp_file_path:
            iris.save(cubes, temp_file_path)
            self.assertGribMessageDifference(
                source_grib,
                temp_file_path,
                expect_diffs,
                self.skip_keys,
                skip_sections=[2],
            )


class TestCubeSave(tests.IrisGribTest):
    # save fabricated cubes

    def _load_basic(self):
        path = tests.get_data_path(("GRIB", "uk_t", "uk_t.grib2"))
        return iris.load_cube(path)

    def test_params(self):
        # TODO
        pass

    def test_originating_centre(self):
        # TODO
        pass

    def test_irregular(self):
        cube = self._load_basic()
        lat_coord = cube.coord("latitude")
        cube.remove_coord("latitude")

        new_lats = np.append(
            lat_coord.points[:-1], lat_coord.points[0]
        )  # Irregular
        cube.add_aux_coord(
            iris.coords.AuxCoord(
                new_lats,
                "latitude",
                units="degrees",
                coord_system=lat_coord.coord_system,
            ),
            0,
        )

        saved_grib = iris.util.create_temp_filename(suffix=".grib2")
        self.assertRaises(
            iris.exceptions.TranslationError, iris.save, cube, saved_grib
        )
        os.remove(saved_grib)

    def test_non_latlon(self):
        cube = self._load_basic()
        cube.coord(dimensions=[0]).coord_system = None
        saved_grib = iris.util.create_temp_filename(suffix=".grib2")
        self.assertRaises(
            iris.exceptions.TranslationError, iris.save, cube, saved_grib
        )
        os.remove(saved_grib)

    def test_forecast_period(self):
        # unhandled unit
        cube = self._load_basic()
        cube.coord("forecast_period").units = cf_units.Unit("years")
        saved_grib = iris.util.create_temp_filename(suffix=".grib2")
        self.assertRaises(
            iris.exceptions.TranslationError, iris.save, cube, saved_grib
        )
        os.remove(saved_grib)

    def test_unhandled_vertical(self):
        # unhandled level type
        cube = self._load_basic()
        # Adjust the 'pressure' coord to make it into an "unrecognised Z coord"
        p_coord = cube.coord("pressure")
        p_coord.rename("not the messiah")
        p_coord.units = "K"
        p_coord.attributes["positive"] = "up"
        saved_grib = iris.util.create_temp_filename(suffix=".grib2")
        with self.assertRaises(iris.exceptions.TranslationError):
            iris.save(cube, saved_grib)
        os.remove(saved_grib)

    def test_scalar_int32_pressure(self):
        # Make sure we can save a scalar int32 coordinate with unit conversion.
        cube = self._load_basic()
        cube.coord("pressure").points = np.array([200], dtype=np.int32)
        cube.coord("pressure").units = "hPa"
        with self.temp_filename(".grib2") as testfile:
            iris.save(cube, testfile)

    def test_bounded_level(self):
        cube = iris.load_cube(
            tests.get_data_path(("GRIB", "uk_t", "uk_t.grib2"))
        )
        with self.temp_filename(".grib2") as testfile:
            iris.save(cube, testfile)
            with open(testfile, "rb") as saved_file:
                g = eccodes.codes_new_from_file(
                    saved_file, eccodes.CODES_PRODUCT_GRIB
                )
                self.assertEqual(
                    eccodes.codes_get_double(
                        g, "scaledValueOfFirstFixedSurface"
                    ),
                    0.0,
                )
                self.assertEqual(
                    eccodes.codes_get_double(
                        g, "scaledValueOfSecondFixedSurface"
                    ),
                    2147483647.0,
                )


class TestHandmade(tests.IrisGribTest):
    def _lat_lon_cube_no_time(self):
        """
        Returns a cube with a latitude and longitude suitable for testing
        saving to GRIB.

        """
        cube = iris.cube.Cube(np.arange(12, dtype=np.int32).reshape((3, 4)))
        cs = iris.coord_systems.GeogCS(6371229)
        cube.add_dim_coord(
            iris.coords.DimCoord(
                np.arange(4) * 90 + -180,
                "longitude",
                units="degrees",
                coord_system=cs,
            ),
            1,
        )
        cube.add_dim_coord(
            iris.coords.DimCoord(
                np.arange(3) * 45 + -90,
                "latitude",
                units="degrees",
                coord_system=cs,
            ),
            0,
        )

        return cube

    def _cube_time_no_forecast(self):
        cube = self._lat_lon_cube_no_time()
        unit = cf_units.Unit(
            "hours since epoch", calendar=cf_units.CALENDAR_GREGORIAN
        )
        dt = datetime.datetime(2010, 12, 31, 12, 0)
        cube.add_aux_coord(
            iris.coords.AuxCoord(
                np.array([unit.date2num(dt)], dtype=np.float64),
                "time",
                units=unit,
            )
        )
        return cube

    def _cube_with_forecast(self):
        cube = self._cube_time_no_forecast()
        cube.add_aux_coord(
            iris.coords.AuxCoord(
                np.array([6], dtype=np.int32), "forecast_period", units="hours"
            )
        )
        return cube

    def _cube_with_pressure(self):
        cube = self._cube_with_forecast()
        cube.add_aux_coord(
            iris.coords.DimCoord(np.int32(10), "air_pressure", units="Pa")
        )
        return cube

    def _cube_with_time_bounds(self):
        cube = self._cube_with_pressure()
        cube.coord("time").bounds = np.array([[0, 100]])
        return cube

    def test_no_time_cube(self):
        cube = self._lat_lon_cube_no_time()
        saved_grib = iris.util.create_temp_filename(suffix=".grib2")
        self.assertRaises(
            iris.exceptions.TranslationError, iris.save, cube, saved_grib
        )
        os.remove(saved_grib)

    def test_cube_with_time_bounds(self):
        cube = self._cube_with_time_bounds()
        saved_grib = iris.util.create_temp_filename(suffix=".grib2")
        self.assertRaises(
            iris.exceptions.TranslationError, iris.save, cube, saved_grib
        )
        os.remove(saved_grib)


if __name__ == "__main__":
    tests.main()
