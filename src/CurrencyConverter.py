##
# Author: Michal Ľaš
# Date: 17.07.2024

from currency_converter import CurrencyConverter, RateNotFoundError, ECB_URL
from datetime import date
import os.path as op
import urllib.request


class CurrencyConversion:

    
    def __init__(self) -> None:
        # TODO: delete old data .zip files, make separate directory for this
        # Download todays data
        filename = f"ecb_{date.today():%Y%m%d}.zip"
        if not op.isfile(filename):
            urllib.request.urlretrieve(ECB_URL, filename)
        # Create currency converter object
        self._c = CurrencyConverter(filename, fallback_on_missing_rate=True, fallback_on_wrong_date=True, fallback_on_missing_rate_method='last_known')


    def convert_usd_to_eur(self, amount:float|int, date:date|None=None) -> float:
        """
        Convert USD to EUR. If `date` parameter is None then is used most recent date.
        """
        return self.convert_to_eur(amount, 'USD', date)
        

    def convert_to_eur(self, amount: float|int, from_currency: str, date: date|None=None) -> float:
        """
        Convert to EUR from specified currency. If `date` parameter is None then is used most recent date.
        """

        # Pull conversion
        conversion: float = 0

        if date is None:
            # Use the most recent conversion rate
            conversion = self._c.convert(amount, from_currency, 'EUR')
        else:
            conversion = self._c.convert(amount, from_currency, 'EUR', date=date)
    
        return conversion


# END OF FILE #