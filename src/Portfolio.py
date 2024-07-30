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


class Asset():
    
    def __init__(self, ticker: str, portfolio_data: dict, history_data: pd.Series) -> None:
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

        self.current_value_eur:float = self._get_current_eur_value() # Current value in EUR
        self.evolution_eur:pd.DataFrame = self._count_evolution_in_eur() # evolution of value of this asset in portfolio
    


    def _get_current_eur_value(self) -> int|float:
        """
        Return current value of the owned asset in EUR.
        """
        if self.currency != 'EUR':
            return curr_conv.convert_to_eur(self.owned / self._multiply * self._history_data[-1], self.currency)
        else:
            return self.owned / self._multiply * self._history_data[-1]
        

    def _count_evolution_in_eur(self) -> pd.DataFrame:
        """
        Count the evolution of this asset value in EUR.
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
        if self.category != 'EUR':
            return result.apply(lambda x: curr_conv.convert_to_eur(x.iloc[0], self.currency, x.name.date()), axis=1)
        else:
            return result 

    
    def get_current_asset_value(self) -> int|float:
        """
        Return current value of asset unit in its currency. (It is not converted to EUR!)
        """
        return self._history_data[-1]


    def get_current_value(self) -> int|float:
        """
        Return current value of owned asset in its currency. (It is not converted to EUR!)
        """
        return self.owned / self._multiply * self._history_data[-1]


class CSP1Asset(Asset):

    def __init__(self, ticker: str, portfolio_data: dict, history_data: pd.Series) -> None:
        super().__init__(ticker, portfolio_data, history_data)
        self._multiply = 100 # CSP1.L has a 100x multiply
        # Recount thes attributes, because _multiply have changed
        self.current_value_eur:float = self._get_current_eur_value()
        self.evolution_eur:pd.DataFrame = self._count_evolution_in_eur()

    


class Portfolio:

    def __init__(self, portfolio_data_loader: dl.DataLoader, history_data_puller: fdp.FinanceData) -> None:
        self._dl:dl.DataLoader = portfolio_data_loader
        self._fdp:fdp.FinanceData = history_data_puller
        self._assets:list[Asset] = [] # list of assets
        self._portfolio_value_eur:float = 0
        # Get categories
        self._categories = self._dl.get_categories()


    def construct_asset(self, ticker: str) -> Asset|None:
        asset = None
        portfolio_data:dict|None = self._dl.get_ticker_data(ticker)
        if portfolio_data is None:
            return None
        
        # TODO: try: catch: ConnectionError
        self._fdp.pull_ticker_history_data(ticker, portfolio_data['info']['First buy'])

        history_data:pd.Series = self._fdp.get_history_data(ticker)

        if ticker == 'CSP1.L':
            asset = CSP1Asset(ticker, portfolio_data, history_data)
        else:
            asset = Asset(ticker, portfolio_data, history_data)
        
        self._portfolio_value_eur += asset.current_value_eur
        self._assets.append(asset)
        return asset
    

    def get_summary_data(self) -> dict[str, dl.TableRow]:
        """ 
        Get agregated values for summary table. 
        These are: Asset category, invested (€), current value (€), percentage (%)
        """

        # Initialize 'table'
        result:dict[str, dl.TableRow] = {} # category: col_name: value
        invested = 0
        for category, goal in self._categories.items():
            result[category] = {'invested': 0, 'current': 0, 'percentage': 0, 'goal': goal}

        # Make calculation - all assets have to be in existing category!
        for asset in self._assets:
            result[asset.category]['invested'] += asset.invested
            invested += asset.current_value_eur
            result[asset.category]['current'] += asset.current_value_eur

        # Count percentage
        for cat, val in result.items():
            result[cat]['percentage'] = result[cat]['current'] / invested

        return result

    
    def get_buys_data(self) -> dict[str, dl.TableRow]:
        """
        Get agregated values for average value of portfolio buys and results.
        These are: TICKER of asset, average buy value, current value, owned, asset_val, asset_val (%)
        """

        result:dict[str, dl.TableRow] = {} # ticker: col_name: value

        for asset in self._assets:
            result[asset.ticker] = {'average buy value': asset.avg_buy, 'current value': asset.get_current_asset_value(), 'owned shares': asset.owned, 
                                    'value of owned asset': asset.get_current_value(), 'portfolio percentage': asset.current_value_eur / self._portfolio_value_eur}
            
        return result


    def get_total_invested(self) -> int:
        """ Money invested into the portfolio in EUR """
        result:float = 0
        for asset in self._assets:
            result += asset.invested
        return result


    def get_current_portfolio_value(self) -> int:
        """ Current value of invested money in EUR """
        return self._portfolio_value_eur
    

    def get_evolution_data(self) -> pd.DataFrame|None:
        if len(self._assets) == 0:
            return None

        result:pd.DataFrame = self._assets[0].evolution_eur
        for asset in self._assets[1:]:
            result = result.add(asset.evolution_eur, axis=0, fill_value=0)
        return result
        

"""
f = fdp.FinanceData()
d = dl.DataLoader()
p = Portfolio(d, f)
d.read_portfolio_excel('../portfolio.xlsx')


print("Tickers: " , d.get_all_tickers())

asset_list:list[Asset] = []
for asset in d.get_all_tickers():
    asset_list.append(p.construct_asset(asset))


tmp = p.get_buys_data()
for key,val in tmp.items():
    print(f"{key}: {val}")

tmp = p.get_summary_data()
for key,val in tmp.items():
    print(f"{key}: {val}")


print(f"Invested: {p.get_total_invested()}, Portfolio value: {p.get_current_portfolio_value()}")


for asset in asset_list:
    print(f"Ticker: {asset.ticker}, Category: {asset.category}, Currency: {asset.currency}")
    print(asset.evolution_eur)



print(p.get_evolution_data())


for i,j in a._history_data.items():
    if a._records[0]['Buy Date'].date() == i.date():
        print(i, j)
"""

# END OF FILE #