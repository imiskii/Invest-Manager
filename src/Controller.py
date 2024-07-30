

from DataLoader import DataLoader, DataLoaderError
from FinDataPuller import FinanceData, FinanceDataError
from Portfolio import Portfolio


class Controller():

    def __init__(self) -> None:
        self._excel_data = DataLoader()
        self._fin_data = FinanceData()
        self._portfolio = Portfolio(self._excel_data, self._fin_data)


    def set_view(self, view) -> None:
        self._view = view


    def load_assets_data(self, excel_path:str) -> None:
        try:
            self._view.update_login_log_progress_bar(1, f"Loading excel file data")
            self._excel_data.read_portfolio_excel(excel_path)
            tickers:list = self._excel_data.get_all_tickers()
            for i, asset_ticker in enumerate(tickers):
                progress:float = (i+1)/len(tickers)
                self._view.update_login_log_progress_bar(progress, f"Processing asset: {asset_ticker}")
                self._portfolio.construct_asset(asset_ticker)
        except Exception as e:
            self._view.update_login_log_progress_bar(0, e)

    