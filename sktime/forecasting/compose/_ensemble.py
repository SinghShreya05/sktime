#!/usr/bin/env python3 -u
# -*- coding: utf-8 -*-
# copyright: sktime developers, BSD-3-Clause License (see LICENSE file)

__author__ = ["Markus Löning"]
__all__ = ["EnsembleForecaster"]

import pandas as pd

from sktime.forecasting.base._base import DEFAULT_ALPHA
from sktime.forecasting.base._meta import _HeterogenousEnsembleForecaster
from sktime.forecasting.base._sktime import _OptionalForecastingHorizonMixin


class EnsembleForecaster(
    _OptionalForecastingHorizonMixin, _HeterogenousEnsembleForecaster
):
    """Ensemble of forecasters

    Parameters
    ----------
    forecasters : list of (str, estimator) tuples
    n_jobs : int or None, optional (default=None)
        The number of jobs to run in parallel for fit. None means 1 unless
        in a joblib.parallel_backend context.
        -1 means using all processors.
    """

    _required_parameters = ["forecasters"]

    def __init__(self, forecasters, n_jobs=None, aggfunc="mean"):
        super(EnsembleForecaster, self).__init__(forecasters=forecasters, n_jobs=n_jobs)
        self.aggfunc = aggfunc

    def fit(self, y, X=None, fh=None):
        """Fit to training data.

        Parameters
        ----------
        y : pd.Series
            Target time series to which to fit the forecaster.
        fh : int, list or np.array, optional (default=None)
            The forecasters horizon with the steps ahead to to predict.
        X : pd.DataFrame, optional (default=None)
            Exogenous variables are ignored
        Returns
        -------
        self : returns an instance of self.
        """
        self._set_y_X(y, X)
        self._set_fh(fh)
        names, forecasters = self._check_forecasters()
        self._fit_forecasters(forecasters, y, X, fh)
        self._is_fitted = True
        return self

    def update(self, y, X=None, update_params=True):
        """Update fitted parameters

        Parameters
        ----------
        y : pd.Series
        X : pd.DataFrame
        update_params : bool, optional (default=True)

        Returns
        -------
        self : an instance of self
        """
        self.check_is_fitted()
        self._update_y_X(y, X)
        for forecaster in self.forecasters_:
            forecaster.update(y, X, update_params=update_params)
        return self

    def _predict(self, fh, X=None, return_pred_int=False, alpha=DEFAULT_ALPHA):
        """return the predicted reduction

        Parameters
        ----------
        fh : int, list or np.array, optional (default=None)
        X : pd.DataFrame
        return_pred_int : boolean, optional (default=False)
        alpha : fh : float, (default=DEFAULT_ALPHA)

        Returns
        -------
        DataFrame : aggregate dataframe reduction.
        """
        valid_agg_funcs = ("median", "mean", "min", "max")
        d_frame = pd.concat(self._predict_forecasters(fh, X), axis=1)
        if return_pred_int:
            raise NotImplementedError()
        if self.aggfunc not in valid_agg_funcs:
            raise ValueError(f"Invalid agg value. Valid values are {valid_agg_funcs}")
        if self.aggfunc == "median":
            return d_frame.median(axis=1)
        if self.aggfunc == "min":
            return d_frame.min(axis=1)
        if self.aggfunc == "max":
            return d_frame.max(axis=1)
        return d_frame.mean(axis=1)
