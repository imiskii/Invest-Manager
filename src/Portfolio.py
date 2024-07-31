##
# Author: Michal Ľaš
# Date: 26.07.2024

import pandas as pd
import FinDataPuller as fdp
import DataLoader as dl
import CurrencyConverter as cc
from datetime import date
from functools import reduce


# Global variable for currency conversions
curr_conv:cc.CurrencyConversion = cc.CurrencyConversion()
# Headers of tables created by Portfolio
SUMMARY_HEADER:list = ['CATEGORY', 'INVESTED', 'CURRENT VALUE', 'PERCENTAGE', 'GOAL']
ASSETS_HEADER:list = ['TICKER', 'AVERAGE BUY VALUE', 'CURRENT VALUE', 'OWNED SHARES', 'VALUE OF SHARES', 'PORTFOLIO PERCENTAGE', 'RESULT']
# Usable portfolio currencies (they can be used as uniform currencies)
CURRENCIES:list = ['EUR', 'USD'] 

class Asset():
    
    def __init__(self, ticker: str, portfolio_data: dict, history_data: pd.Series, currency_conversion: str) -> None:
        self._records:dict = portfolio_data['records'] # dictionary with buy records
        self.ticker:str = ticker # ticker name
        self.name:str = portfolio_data['info']['Name'] # Whole name of asset
        self.category:str = portfolio_data['info']['Category'] # asset category
        self.currency:str = portfolio_data['info']['Currency'] # currency of asset
        self.field:str = portfolio_data['info']['Field'] 
        self.first_buy:date = portfolio_data['info']['First buy'] # day of the first buy
        self.invested:float = portfolio_data['results']['INVESTED'] # how much money was invested
        self.avg_buy:float = portfolio_data['results']['Average buy value'] # what is the average buy
        self.owned:float = portfolio_data['results']['OWNED'] # how much shares is owned
        self._history_data:pd.Series = history_data # asset price evolution
        self._multiply = 1 # conversion value for some assets like CSP1.L

        self.currency_conversion = currency_conversion # Uniform currency (There is choosen one currency as uniform)
        self.current_uniform_value:float = self._get_current_uniform_value() # Value of owned asset in uniform currency
        self.invested_uniform_value:float = self._get_invested_uniform_value() # Value of investment in this asset at current currency conversion rate
        self.evolution_uniform:pd.DataFrame = self._count_evolution_in_uniform_currency() # Evolution of value of this asset in uniform currency
    


    def _get_current_uniform_value(self) -> int|float:
        """
        Return current value of the owned asset in the chosen uniform currency.
        """
        if self.currency != self.currency_conversion:
            return curr_conv.convert(self.owned / self._multiply * self._history_data[-1], self.currency, self.currency_conversion)
        else:
            return self.owned / self._multiply * self._history_data[-1]
        

    def _get_invested_uniform_value(self) -> int|float:
        """ Return invested value in the chosen uniform currency. """
        if self.currency != self.currency_conversion:
            return curr_conv.convert(self.invested, self.currency, self.currency_conversion)
        else:
            return self.invested
        

    def _count_evolution_in_uniform_currency(self) -> pd.DataFrame:
        """
        Count the evolution of this asset value in chosen uniform currency.
        """
        owned_shares_frame = pd.DataFrame(0, columns=['value'], index=self._history_data.index)

        # Update the DataFrame based on transactions
        for tx in self._records:
            buy_date = tx['Buy Date']
            sell_date = tx['Sell Date'] or fdp.today
            amount = tx['Amount'] / self._multiply
            owned_shares_frame[buy_date:sell_date] += amount

        result = owned_shares_frame.mul(self._history_data, axis=0)

        # Conversion to EUR
        if self.category != self.currency_conversion:
            return result.apply(lambda x: curr_conv.convert(x.iloc[0], self.currency, self.currency_conversion, x.name.date()), axis=1)
        else:
            return result 


    def change_uniform_currency(self, currency_conversion: str) -> None:
        if self.currency_conversion != currency_conversion:
            self.currency_conversion = currency_conversion
            self.current_uniform_value = self._get_current_uniform_value()
            self.invested_uniform_value = self._get_invested_uniform_value()
            self.evolution_uniform = self._count_evolution_in_uniform_currency()
    

    def get_current_asset_value(self) -> int|float:
        """
        Return current value of asset unit in its currency. (It is not converted to uniform currency!)
        """
        return self._history_data[-1]


    def get_current_value(self) -> int|float:
        """
        Return current value of owned asset in its currency. (It is not converted to uniform currency!)
        """
        return self.owned / self._multiply * self._history_data[-1]


class CSP1Asset(Asset):

    def __init__(self, ticker: str, portfolio_data: dict, history_data: pd.Series, currency_conversion: str) -> None:
        super().__init__(ticker, portfolio_data, history_data, currency_conversion)
        self._multiply = 100 # CSP1.L has a 100x multiply
        # Recount thes attributes, because _multiply have changed
        self.current_uniform_value:float = self._get_current_uniform_value()
        self.evolution_uniform:pd.DataFrame = self._count_evolution_in_uniform_currency()

    


def format_value(value:float, currency:str) -> str:
    """
    Return value rounded to two decimal spaces and adds currency symbol.
    
    value:float - number to be formated
    currency:str - name of currency such EUR, USE, GBP. When conversion from currency ticker to symbol is not supported, insted of currency ticker can be
    placed the actual symbol. For example in case of percent `currency='%'`
    """
    symbol:str = ""
    match currency:
        case 'EUR':
            symbol = '€'
        case 'USD':
            symbol = '$'
        case 'GBP':
            symbol = '£'
        case _:
            symbol = currency

    return f"{round(value, 2)}{symbol}"



class Portfolio:

    def __init__(self, portfolio_data_loader: dl.DataLoader, history_data_puller: fdp.FinanceData, currency_conversion: str='EUR') -> None:
        """
        Constructor for Portfolio.

        portfolio_data_loader: dl.DataLoader - data loader for excel files
        history_data_puller: fdp.FinanceData - data puller for history stock data
        currency_conversion: str - ticker of currency to which will be final portfolio value converted, default is EUR
        """
        self._dl:dl.DataLoader = portfolio_data_loader
        self._fdp:fdp.FinanceData = history_data_puller
        self._assets:list[Asset] = [] # list of assets
        self._portfolio_uniform_value:float = 0 # Value of portfolio in uniform currency (currency_conversion)
        # Get categories
        self.currency_conversion = currency_conversion # Uniform currency (one of the currencies like EUR, USD,...)
        self._evolution_data = None


    def reset_portfolio(self) -> None:
        self._assets = list()
        self._portfolio_uniform_value = 0
        self._evolution_data = None


    def make_currency_conversion(self, currency_conversion: str) -> None:
        """ Set currency conversion. For example EUR, USD, GBP """
        if self.currency_conversion != currency_conversion:
            self.currency_conversion = currency_conversion
            self._portfolio_uniform_value = 0
            for asset in self._assets:
                asset.change_uniform_currency(currency_conversion)
                self._portfolio_uniform_value += asset.current_uniform_value



    def construct_asset(self, ticker: str) -> Asset|None:
        """
        Creates Asset object. Return `None` on failure
        """
        asset = None
        portfolio_data:dict|None = self._dl.get_ticker_data(ticker)
        if portfolio_data is None:
            return None
        
        # TODO: try: catch: ConnectionError
        self._fdp.pull_ticker_history_data(ticker, portfolio_data['info']['First buy'])

        history_data:pd.Series = self._fdp.get_history_data(ticker)

        if ticker == 'CSP1.L':
            asset = CSP1Asset(ticker, portfolio_data, history_data, self.currency_conversion)
        else:
            asset = Asset(ticker, portfolio_data, history_data, self.currency_conversion)
        
        self._portfolio_uniform_value += asset.current_uniform_value
        self._assets.append(asset)
        return asset
    

    def get_summary_data(self) -> list[list[any]]:
        """ 
        Get agregated values for summary table. 
        These are based on `SUMMARY_HEADER`: ['CATEGORY', 'INVESTED' (€), 'CURRENT VALUE' (€), 'PERCENTAGE' (%), 'GOAL' (%)]
        """

        # Initialize 'table'
        tmp_result:dict[str, dl.TableRow] = {} # category: col_name: value
        result:list[list[any]] = list()
        invested = 0
        for category, goal in self._dl.get_categories().items():
            tmp_result[category] = {'category': category, 'invested': 0, 'current': 0, 'percentage': 0, 'goal': format_value(goal * 100, '%')}

        # Make calculation - all assets have to be in existing category!
        for asset in self._assets:
            tmp_result[asset.category]['invested'] += asset.invested_uniform_value
            invested += asset.invested_uniform_value
            tmp_result[asset.category]['current'] += asset.current_uniform_value

        # Count percentage and final 2D table
        for cat in tmp_result.keys():
            tmp_result[cat]['percentage'] = tmp_result[cat]['current'] / invested
            tmp_result[cat]['invested'] = format_value(tmp_result[cat]['invested'], self.currency_conversion)
            tmp_result[cat]['current'] = format_value(tmp_result[cat]['current'], self.currency_conversion)
            tmp_result[cat]['percentage'] = format_value(tmp_result[cat]['percentage'] * 100, '%')
            result.append(list(tmp_result[cat].values()))

        return result

    
    def get_assets_data(self) -> list[list[any]]:
        """
        Get agregated values for average value of portfolio buys and results.
        These are based on ASSETS_HEADER: ['TICKER', 'AVERAGE BUY VALUE' (CURR.), 'CURRENT VALUE' (CURR.), 'OWNED SHARES', 'VALUE OF SHARES' (CURR.), 'PORTFOLIO PERCENTAGE' (%), 'RESULT' (%)]
        """
        result:list[list[any]] = list()

        for asset in self._assets:
            row = list()
            row.append(asset.ticker)
            row.append(format_value(asset.avg_buy, asset.currency))
            row.append(format_value(asset.get_current_asset_value(), asset.currency))
            row.append(round(asset.owned, 4))
            row.append(format_value(asset.get_current_value(), asset.currency))
            row.append(format_value((asset.current_uniform_value / self._portfolio_uniform_value) * 100, '%'))
            row.append(format_value((asset.current_uniform_value - asset.invested_uniform_value) / asset.invested_uniform_value * 100, '%'))
            result.append(row)

        return result


    def get_total_invested(self) -> float:
        """ Return money invested into the portfolio in uniform currency."""
        result:float = 0
        for asset in self._assets:
            result += curr_conv.convert(asset.invested, asset.currency, self.currency_conversion)

        return result


    def get_current_portfolio_value(self) -> float:
        """ Current value of invested money in uniform currency. """
        return self._portfolio_uniform_value
    

    def get_evolution_data(self) -> pd.DataFrame|None:
        """
        Return evolution data of this portfolio
        """
        if self._evolution_data is not None:
            return self._evolution_data

        if len(self._assets) == 0:
            return None

        result:pd.DataFrame = self._assets[0].evolution_uniform
        for asset in self._assets[1:]:
            result = result.add(asset.evolution_uniform, axis=0, fill_value=0)

        self._evolution_data = result
        return result
    

    def get_ticker_evolution_data(self, ticker: str) -> pd.DataFrame|None:
        """
        Return evolution chart data of an Asset with the given `ticker`
        """
        for asset in self._assets:
            if asset.ticker == ticker:
                return asset.evolution_uniform
            
        return None
        


# END OF FILE #