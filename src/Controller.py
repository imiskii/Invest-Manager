

from DataLoader import DataLoader
from FinDataPuller import FinanceData
from Portfolio import Portfolio


class Controller():

    def __init__(self) -> None:
        self._excel_data = DataLoader()
        self._fin_data = FinanceData()
        self._portfolio = Portfolio(self._excel_data, self._fin_data)


    def set_view(self, view) -> None:
        self._view = view


    def load_assets_data(self, excel_path:str) -> None:
        failed = "" # just for failed asset tickers log
        try:
            self._view.loading_layout.update_login_log_progress_bar(1, f"Loading excel file data")
            self._excel_data.read_portfolio_excel(excel_path)
            tickers:list = self._excel_data.get_all_tickers()
        except Exception as e:
            print(e)
            self._view.loading_layout.update_login_log_progress_bar(0, e)

        for i, asset_ticker in enumerate(tickers):
            try:
                progress:float = (i+1)/len(tickers)
                self._view.loading_layout.update_login_log_progress_bar(progress, f"Processing asset: {asset_ticker}")
                asset = self._portfolio.construct_asset(asset_ticker)
                if asset is None:
                    failed = failed + ", " + asset_ticker
                    self._view.update_log_line(f"Asset {failed} failed to load.")
                    self._view.loading_layout.update_login_log_progress_bar(progress, f"Processing asset: {asset_ticker}")
            except Exception as e:
                print(e)
                self._view.loading_layout.update_login_log_progress_bar(0, e)
        


    def reset_loaded(self) -> None:
        self._portfolio.reset_portfolio()


    def change_uniform_currency(self, currency: str) -> None:
        self._portfolio.make_currency_conversion(currency)


    def get_current_currency(self) -> str:
        return self._portfolio.currency_conversion


    def get_summary_data(self) -> list:
        result = []
        result.append(self._portfolio.get_summary_data()) # index: 0
        result.append(self._portfolio.get_total_invested()) # index: 1
        result.append(self._portfolio.get_current_portfolio_value()) # index: 2
        return result


    def get_asset_table_data(self) -> list:
        return self._portfolio.get_assets_data()


    def get_asset_tickers(self) -> list[str]:
        return self._portfolio.get_tickers()


    def get_evolution_graph(self, ticker: str|None=None, date_from:str|None=None, date_to:str|None=None):
        """
        Get graph with evolution of selected asset with given `ticker`. If `ticker` is None, then graph with evolution of whole portfolio is returned.
        Optional arguments are date_from and date_to (in string format 'YYYY-mm-dd') which can filter the output data.
        """

        if ticker in (None, 'PORTFOLIO'):
            graph_data = self._portfolio.get_evolution_data()
        else:
            graph_data = self._portfolio.get_ticker_evolution_data(ticker)
            
        if graph_data is None:
            return None

        if date_from is None and date_to is None:
            return graph_data
        elif date_from is None and date_to is not None:
            return graph_data.loc[:date_to]
        elif date_to is None and date_from is not None:
            return graph_data.loc[date_from:]
        else:
            return graph_data.loc[date_from:date_to]

# END OF FILE #