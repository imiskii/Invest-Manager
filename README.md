# Invest-Manager

A simple application in Python for managing a financial portfolio


## PyInstaller

There is a command for PyInstaller. Keep in mind, that the application needs in its directory path another directory called `ecb_data` where it can download data for conversion rates.

**UNIX**
```
pyinstaller --onefile --name=InvestManager --add-data=src/ecb_data:ecb_data src/__main__.py
```

**Windows**
```
pyinstaller --onefile --name=InvestManager --windowed --icon=piggy.ico --add-data=src/ecb_data:ecb_data src/__main__.py
```