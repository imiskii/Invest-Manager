##
# Author: Michal Ľaš
# Date: 17.07.2024

from currency_converter import CurrencyConverter, RateNotFoundError, ECB_URL
from datetime import date
import os.path as op
from os import remove, listdir
import urllib.request


class CurrencyConversion:

    
    def __init__(self) -> None:
        directory = "ecb_data"
        filename = f"ecb_{date.today():%Y%m%d}.zip"
        latest = op.join(directory, filename)
        # Delete old data ECB .zip files
        for item in listdir(directory):
            item_path = op.join(directory, item)
            if op.isfile(item_path) and item_path != latest:
                try:
                    remove(item_path)
                except Exception as e:
                    pass
        # Download todays data
        if not op.isfile(latest):
            urllib.request.urlretrieve(ECB_URL, latest)
        # Create currency converter object
        self._c = CurrencyConverter(latest, fallback_on_missing_rate=True, fallback_on_wrong_date=True, fallback_on_missing_rate_method='last_known')


    def convert_usd_to_eur(self, amount:float|int, date:date|None=None) -> float:
        """
        Convert USD to EUR. If `date` parameter is None then is used most recent date.
        """
        return self.convert_to_eur(amount, 'USD', date)
        

    def convert_to_eur(self, amount: float|int, from_currency: str, date: date|None=None) -> float:
        """
        Convert to EUR from specified currency. If `date` parameter is None then is used most recent date.
        """
        return self.convert(amount, from_currency, 'EUR', date)
    

    def convert(self, amount: float|int, from_currency: str, to_currency: str, date: date|None=None) -> float:
        """
        Convert choosen currency to different currency. If `date` parameter is None then is used most recent date.
        """
        conversion: float = 0

        if date is None:
            # Use the most recent conversion rate
            conversion = self._c.convert(amount, from_currency, to_currency)
        else:
            conversion = self._c.convert(amount, from_currency, to_currency, date=date)
    
        return conversion
    

# END OF FILE #