##
# Author.: Michal Ľaš
# Date: 18.07.2024

import yfinance as yf
import pandas as pd
from datetime import datetime, date


# Global variable for today timedate
today:datetime = datetime.now().date()


class FinanceDataError(Exception):

    def __init__(self, message) -> None:
        self.message = message
        super().__init__(message)

    def __str__(self) -> str:
        return f"FinanceDataError: {self.message}"


class FinanceData:
    
    def __init__(self) -> None:
        self._adfs:dict[str, pd.DataFrame] = {} # assets data frames
        

    def pull_ticker_history_data(self, ticker: str, date_from: date) -> None:
        """ 
        Pull history data of one ticker
        ticker: Asset ticker
        date_from: date from which data will be pulled. 
        """
        if ticker not in self._adfs:
            date_range = pd.date_range(start=date_from, end=today, freq='D')
            asset_values = yf.Ticker(ticker).history(start=date_from, end=today, raise_errors=True).Close
            # Remove timezone information
            asset_values.index = asset_values.index.tz_convert(None).normalize()
            # Fill gaps in dates and fill in forwared mode
            self._adfs[ticker] = asset_values.reindex(date_range, method='ffill', copy=False).bfill()


    def pull_tickers_history_data(self, assets_tickers: list[str], date_from: str) -> None:
        """ 
        This function will pull many ticker history data at once. The disadvantage is that all thicker data 
        Will be from the same date.
        assets_ticker: list of assets that data will be pulled.
        date_from: date from which data will be pulled (in format 'YYYY-mm-dd').
        """
        for ticker in assets_tickers:
            self.pull_ticker_history_data(ticker, date_from)


    def get_history_data(self, ticker:str, date_from:str|None=None, date_to:str|None=None) -> pd.DataFrame:
        """
        Get date in tpye 'pandas.core.series.Series' (Date, value). Some day may missing because market was closed that day!
        Required argements is ticker which specifie the specific asset.
        Optional arguments are date_from and date_to (in string format 'YYYY-mm-dd') which can filter the output data.

        IMPORTANT: data of specified ticker has to be pulled first before calling this function! otherwise it throws Exception.
        """

        if ticker not in self._adfs:
            raise FinanceDataError('get_history_data: missing ticker symbol. Data has to be pulled first!')

        if date_from is None and date_to is None:
            return self._adfs[ticker]
        elif date_from is None and date_to is not None:
            return self._adfs[ticker].loc[:date_to]
        elif date_to is None and date_from is not None:
            return self._adfs[ticker].loc[date_from:]
        else:
            return self._adfs[ticker].loc[date_from:date_to]
            

# END OF FILE #