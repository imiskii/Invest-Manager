##
# Author: Michal Ľaš
# Date: 14.07.2024


import PySimpleGUI as sg
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import Controller as ct
from Portfolio import SUMMARY_HEADER, ASSETS_HEADER, CURRENCIES, format_value


DEFAULT_CHART_TICKERS:list = ['PORTFOLIO']


sg.theme('Light Blue 2')

class IMMainGui:

    _loading_layout = [
        [sg.Push(), sg.Text("Inves Manager", justification='center', font=('Courier New',26)), sg.Push()],
        [sg.Text("Enter .xlsx file with investment records: ", size=(34, 1)), sg.Input(), sg.FileBrowse(file_types=(('MS Excel Files', '*.xlsx'),))],
        [sg.Submit(), sg.Exit()],
        [sg.ProgressBar(50, size=(60,20), border_width=4, key='-PROGRESS_BAR-', visible=False, expand_x=True)],
        [sg.Text("", key='-LOG_TEXT-', text_color='Black', visible=False)]
    ]

    _summary_layout = [
        [sg.Table(values=[], headings=SUMMARY_HEADER,
                      auto_size_columns=True,
                      display_row_numbers=False,
                      justification='left', key='-SUM_TABLE-',
                      enable_events=False,
                      expand_x=True, expand_y=True)],
        [sg.Text("Total Invested EUR: X", key="-TOTAL_INVESTED-"), sg.Text("Current Portfolio Value: X", key='-CURRENT_PORTFOLIO_VALUE-'), sg.Text("Result: ", key='-RESULT_PERCENTAGE-')]
    ]


    _asset_info_layout = [
        [sg.Table(values=[], headings=ASSETS_HEADER,
                      auto_size_columns=True,
                      display_row_numbers=False,
                      justification='left', key='-ASSET_TABLE-',
                      enable_events=False,
                      expand_x=True, expand_y=True)]
    ]

    _chart_space_layout = [
        [sg.Text("Change chart: "), sg.Combo(values=DEFAULT_CHART_TICKERS, enable_events=True, readonly=False, key='-COMBO_CHART-'), sg.Button('Plot')],
        [sg.Canvas(size=(800,1400), key='-EVOLUTION_CHART-', expand_x=True)]
    ]

    _main_layout = [[sg.Text("Used Currency: "), sg.Combo(CURRENCIES, enable_events=True, readonly=True, key='-CURRENCY_COMBO-', default_value=CURRENCIES[0])],
                    [sg.TabGroup([[sg.Tab('Summary', _summary_layout), sg.Tab('Assets info', _asset_info_layout), sg.Tab('Charts', _chart_space_layout)]])],
                    [sg.Button('Change .xlsx file'), sg.Button('Close Invest Manager Appliaction')],
                    [sg.Text("", key='-LOG_LINE-')]]

    _layout = [
        [sg.Column(_loading_layout, key='-COL1-'), sg.Column(_main_layout, key='-COL2-', visible=False)]
    ]


    def __init__(self, controller:ct.Controller) -> None:
        self._window:sg.Window = sg.Window('Invest Manager', self._layout, font=("Arial", 14), finalize=True)
        self._selected_layout:int = 1
        self._controller = controller
        self._chart_tickers = DEFAULT_CHART_TICKERS
        # Link matplotlib to PySimpleGUI Graph
        self._figure, self._ax = plt.subplots()
        canvas = FigureCanvasTkAgg(self._figure, self._window['-EVOLUTION_CHART-'].TKCanvas)
        canvas.get_tk_widget().pack(side='top', fill='both', expand=1)


    def open_main_window(self):
        while True:
            event, values = self._window.read()
            if event in (sg.WIN_CLOSED, 'Exit', 'Close Invest Manager Appliaction'):
                break
            else:
                self._event_load_file(event, values)
                self._event_change_xlsx(event)
                self._event_change_currency(event, values)
                self._event_change_chart(event, values)
                self._event_plot(event)
                

        self.close_main_window()


    def close_main_window(self):
        self._window.close()

    
    def update_login_log_progress_bar(self, progress_bar_percentage:float, log:str) -> None:
        self._window['-PROGRESS_BAR-'].update(round(50 * progress_bar_percentage))
        self._window['-LOG_TEXT-'].update(log)


    def update_log_line(self, log: str) -> None:
        self._window['-LOG_LINE-'].update(log)


    def _event_load_file(self, event, values) -> None:
        if event == 'Submit':
            self._window['-PROGRESS_BAR-'].update(visible=True)
            self._window['-LOG_TEXT-'].update(visible=True)
            self._controller.load_assets_data(values['Browse'])
            self._update_loaded_layouts_content()
            self._change_layout()


    def _event_change_xlsx(self, event) -> None:
        if event == 'Change .xlsx file':
            self._controller.reset_loaded()
            self._chart_tickers = DEFAULT_CHART_TICKERS
            plt.cla() # Clear canvas
            self._change_layout()
            self.update_login_log_progress_bar(0, "")


    def _event_change_currency(self, event, values) -> None:
        if event == '-CURRENCY_COMBO-':
            self._controller.change_uniform_currency(values['-CURRENCY_COMBO-'])
            self._update_loaded_layouts_content()


    def _event_change_chart(self, event, values) -> None:
        if event == '-COMBO_CHART-':
            chart = self._controller.get_evolution_chart(values['-COMBO_CHART-'])
            self._update_chart_data(chart, values['-COMBO_CHART-'])


    def _event_plot(self, event) -> None:
        if event == 'Plot':
            self._show_chart_plot()


    def _change_layout(self) -> None:
        self._window[f"-COL{self._selected_layout}-"].update(visible=False)

        if self._selected_layout == 1:
            self._selected_layout = 2
        else:
            self._selected_layout = 1
        
        self._window[f"-COL{self._selected_layout}-"].update(visible=True)


    def _update_loaded_layouts_content(self) -> None:
        tables = self._controller.get_table_data()
        chart = self._controller.get_evolution_chart()
        self._update_summary_layout(tables[0], tables[2], tables[3]) # 0: summary data, 2: total invested money, 3: current portfolio value
        self._update_assets_data(tables[1]) # 1: assets data
        self._window['-COMBO_CHART-'].update(values=['PORTFOLIO'] + [ticker[0] for ticker in tables[1]], value='PORTFOLIO') # values are assets tickers
        self._update_chart_data(chart, 'PORTFOLIO')

    
    def _update_summary_layout(self, summary_data:list[list[any]], total_invested: float, current_value: float) -> None:     
        self._window['-SUM_TABLE-'].update(values=summary_data)

        invested:str = f"Total Invested: {format_value(total_invested, self._controller.get_current_currency())}"
        current:str = f"Current Portfolio Value: {format_value(current_value, self._controller.get_current_currency())}"
        percentage_formula: float = (current_value - total_invested) / total_invested * 100
        percentage:str = f"Result: {format_value(percentage_formula, '%')}"
        self._window['-TOTAL_INVESTED-'].update(invested)
        self._window['-CURRENT_PORTFOLIO_VALUE-'].update(current)
        self._window['-RESULT_PERCENTAGE-'].update(percentage)


    def _update_assets_data(self, assets_data:list[list[any]]) -> None:
        self._window['-ASSET_TABLE-'].update(values=assets_data)
        

    def _update_chart_data(self, chart_data, ticker: str) -> None:
        plt.cla()
        self._plot_chart(chart_data, ticker)
        self._figure.canvas.draw()


    def _plot_chart(self, data, ticker:str):
        self._ax.set_title(f"Evolution of {ticker}", fontsize=14)
        self._ax.set_xlabel('Time', fontsize=14)
        self._ax.set_ylabel(f"Value in {self._controller.get_current_currency()}", fontsize=14)
        self._ax.grid(True)
        plt.plot(data)
        return plt.gcf()


    def _show_chart_plot(self) -> None:
        # There should be plt.show(block=False), but the application get stuck if is this used.  Without this however, if the plot window is shown and
        # it is manipulated with main window the chart plotting broke, and wont be plotting properly anymore.
        plt.show()


# END OF FILE #