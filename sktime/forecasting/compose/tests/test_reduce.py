#!/usr/bin/env python3 -u
# -*- coding: utf-8 -*-
# copyright: sktime developers, BSD-3-Clause License (see LICENSE file)

__author__ = ["Lovkush Agarwal", "luiszugasti"]
__all__ = []

import numpy as np
import pytest

from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline

from sktime.datasets import load_airline
from sktime.forecasting.base import ForecastingHorizon
from sktime.forecasting.model_selection import temporal_train_test_split
from sktime.transformations.panel.reduce import Tabularizer
from sktime.forecasting.compose._reduce import ReducedForecaster
from sktime.forecasting.compose._reduce import RecursiveRegressionForecaster
from sktime.forecasting.compose._reduce import DirectRegressionForecaster
from sktime.forecasting.compose._reduce import DirRecRegressionForecaster
from sktime.forecasting.compose._reduce import MultioutputRegressionForecaster
from sktime.forecasting.compose._reduce import RecursiveTimeSeriesRegressionForecaster
from sktime.forecasting.compose._reduce import DirectTimeSeriesRegressionForecaster
from sktime.performance_metrics.forecasting import smape_loss


@pytest.fixture
def get_data():
    y = load_airline()
    y_train, y_test = temporal_train_test_split(y, test_size=24)
    fh = ForecastingHorizon(y_test.index, is_relative=False)
    return y, y_train, y_test, fh


def test_factory_method_recursive(get_data):
    (y, y_train, y_test, fh) = get_data

    regressor = LinearRegression()
    f1 = ReducedForecaster(regressor, scitype="regressor", strategy="recursive")
    f2 = RecursiveRegressionForecaster(regressor)

    actual = f1.fit(y_train).predict(fh)
    expected = f2.fit(y_train).predict(fh)

    np.testing.assert_array_equal(actual, expected)


def test_factory_method_direct(get_data):
    y, y_train, y_test, fh = get_data

    regressor = LinearRegression()
    f1 = ReducedForecaster(regressor, scitype="regressor", strategy="direct")
    f2 = DirectRegressionForecaster(regressor)

    actual = f1.fit(y_train, fh=fh).predict(fh)
    expected = f2.fit(y_train, fh=fh).predict(fh)

    np.testing.assert_array_equal(actual, expected)


def test_factory_method_ts_recursive(get_data):
    y, y_train, y_test, fh = get_data

    ts_regressor = Pipeline(
        [("tabularize", Tabularizer()), ("model", LinearRegression())]
    )
    f1 = ReducedForecaster(ts_regressor, scitype="ts_regressor", strategy="recursive")
    f2 = RecursiveTimeSeriesRegressionForecaster(ts_regressor)

    actual = f1.fit(y_train).predict(fh)
    expected = f2.fit(y_train).predict(fh)

    np.testing.assert_array_equal(actual, expected)


def test_factory_method_ts_direct(get_data):
    y, y_train, y_test, fh = get_data

    ts_regressor = Pipeline(
        [("tabularize", Tabularizer()), ("model", LinearRegression())]
    )
    f1 = ReducedForecaster(ts_regressor, scitype="ts_regressor", strategy="direct")
    f2 = DirectTimeSeriesRegressionForecaster(ts_regressor)

    actual = f1.fit(y_train, fh=fh).predict(fh)
    expected = f2.fit(y_train, fh=fh).predict(fh)

    np.testing.assert_array_equal(actual, expected)


def test_factory_method_dirrec(get_data):
    y, y_train, y_test, fh = get_data

    regressor = LinearRegression()
    f1 = ReducedForecaster(regressor, scitype="regressor", strategy="dirrec")
    f2 = DirRecRegressionForecaster(regressor)

    actual = f1.fit(y_train, fh=fh).predict(fh)
    expected = f2.fit(y_train, fh=fh).predict(fh)

    np.testing.assert_array_equal(actual, expected)


def test_multioutput_direct_tabular(get_data):
    # multioutput and direct strategies with linear regression
    # regressor should produce same predictions
    y, y_train, y_test, fh = get_data

    regressor = LinearRegression()
    f1 = MultioutputRegressionForecaster(regressor)
    f2 = DirectRegressionForecaster(regressor)

    preds1 = f1.fit(y_train, fh=fh).predict(fh)
    preds2 = f2.fit(y_train, fh=fh).predict(fh)

    # assert_almost_equal does not seem to work with pd.Series objects
    np.testing.assert_almost_equal(preds1.to_numpy(), preds2.to_numpy(), decimal=5)


def test_dirrec_correctness(get_data):
    # recursive and dirrec regressor strategies
    # dirrec regressor should produce lower error due to less cumulative error
    y, y_train, y_test, fh = get_data

    regressor = LinearRegression()
    dirrec = ReducedForecaster(regressor, scitype="regressor", strategy="dirrec")
    recursive = ReducedForecaster(regressor, scitype="regressor", strategy="recursive")

    preds_dirrec = dirrec.fit(y_train, fh=fh).predict(fh)
    preds_recursive = recursive.fit(y_train, fh=fh).predict(fh)

    assert smape_loss(y_test, preds_dirrec) < smape_loss(y_test, preds_recursive)


def test_dirrec_overloading(get_data):
    y, y_train, y_test, fh = get_data

    # Both overloads of dirrec should give the same result
    regressor = [LinearRegression()] * len(fh)
    dirrec = ReducedForecaster(regressor, scitype="regressor", strategy="dirrec")

    preds_dirrec_multiple = dirrec.fit(y_train, fh=fh).predict(fh)

    regressor = LinearRegression()
    dirrec = ReducedForecaster(regressor, scitype="regressor", strategy="dirrec")

    preds_dirrec_single = dirrec.fit(y_train, fh=fh).predict(fh)

    assert (preds_dirrec_multiple == preds_dirrec_single).all()


def test_dirrec_incorrect_num_regressors(get_data):
    y, y_train, y_test, fh = get_data

    regressor = [LinearRegression()] * (len(fh) + 1)
    dirrec = ReducedForecaster(regressor, scitype="regressor", strategy="dirrec")

    with pytest.raises(ValueError):
        _ = dirrec.fit(y_train, fh=fh).predict(fh)

    regressor = [LinearRegression()] * (len(fh) - 1)
    dirrec = ReducedForecaster(regressor, scitype="regressor", strategy="dirrec")

    with pytest.raises(ValueError):
        _ = dirrec.fit(y_train, fh=fh).predict(fh)
