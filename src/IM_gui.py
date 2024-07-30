##
# Author: Michal Ľaš
# Date: 14.07.2024

import PySimpleGUI as sg
import Controller as ct

sg.theme('Light Blue 2')

class IMMainGui:

    _loading_layout = [
        [sg.Push(), sg.Text("Inves Manager", justification='center', font=('Luxida',20)), sg.Push()],
        [sg.Text("Enter .xlsx file with investment records: ", size=(34, 1)), sg.Input(), sg.FileBrowse(file_types=(('MS Excel Files', '*.xlsx'),))],
        [sg.Submit(), sg.Exit()],
        [sg.ProgressBar(50, size=(60,20), border_width=4, key='-PROGRESS_BAR-', visible=False)],
        [sg.Text("", key='-LOG_TEXT-', text_color='Black', visible=False)]
    ]

    _summary_layout = [
        [sg.Table(values=[], headings=['CATEGORY', 'INVESTED', 'CURRENT VALUE', 'PERCENTAGE', 'GOAL'],
                      auto_size_columns=True,
                      display_row_numbers=False,
                      justification='center', key='-SUM_TABLE-',
                      enable_events=False,
                      expand_x=True, expand_y=True)],
        [sg.Text("Total Invested EUR: X", key="-TOTAL_INVESTED-"), sg.Text("Current Portfolio Value: X", key='-CURRENT_PORTFOLIO_VALUE-')]
    ]


    _asset_info_layout = [
        [sg.Table(values=[], headings=['TICKER', 'AVERAGE BUY VALUE', 'CURRENT VALUE', 'OWNED SHARES', 'VALUE OF SHARES', 'PORTFOLIO PERCENTAGE'],
                      auto_size_columns=True,
                      display_row_numbers=False,
                      justification='center', key='-ASSET_TABLE-',
                      enable_events=False,
                      expand_x=True, expand_y=True)]
    ]

    _chart_space_layout = [
        []
    ]

    _main_layout = [[sg.TabGroup([[sg.Tab('Summary', _summary_layout), sg.Tab('Assets info', _asset_info_layout), sg.Tab('Charts', _chart_space_layout)]])],
                    [sg.Button("Change .xlsx file"), sg.Button('Close Invest Manager Appliaction')]]

    _layout = [
        [sg.Column(_loading_layout, key='-COL1-'), sg.Column(_main_layout, key='-COL2-', visible=False)]
    ]


    def __init__(self, controller:ct.Controller) -> None:
        self._window:sg.Window = sg.Window('Invest Manager', self._layout)
        self._selected_layout:int = 1
        self._controller = controller


    def open_main_window(self):
        while True:
            event, values = self._window.read()
            if event in (sg.WIN_CLOSED, 'Exit', 'Close Invest Manager Appliaction'):
                break
            else:
                self._event_load_file(event, values)
                

        self.close_main_window()


    def close_main_window(self):
        self._window.close()

    
    def update_login_log_progress_bar(self, progress_bar_percentage:float, log:str) -> None:
        self._window['-PROGRESS_BAR-'].update(round(50 * progress_bar_percentage))
        self._window['-LOG_TEXT-'].update(log)


    def _event_load_file(self, event, values) -> None:
        if event == 'Submit':
            self._window['-PROGRESS_BAR-'].update(visible=True)
            self._window['-LOG_TEXT-'].update(visible=True)
            self._controller.load_assets_data(values['Browse'])
            self._update_loaded_layouts_content()
            self._change_layout()


    def _update_loaded_layouts_content(self) -> None:
        self._update_summary_layout(self._controller._portfolio.get_summary_data())
        self._update_assets_data(self._controller._portfolio.get_buys_data())
        self._update_chart_data(self._controller._portfolio.get_evolution_data())

    
    def _update_summary_layout(self, summary_data:dict[str, any]) -> None:
        rows = []
        for category, tablerow in summary_data.items():
            new_row = list()
            new_row.append(category)
            new_row.append(f"{round(tablerow['invested'], 2)}€")
            new_row.append(f"{round(tablerow['current'], 2)}€")
            new_row.append(f"{round(tablerow['percentage'] * 100, 4)}%")
            new_row.append(f"{tablerow['goal'] * 100}%")
            rows.append(new_row)
            
        self._window['-SUM_TABLE-'].update(values=rows)

        invested:str = f"Total Invested: {round(self._controller._portfolio.get_total_invested(), 2)}€"
        current:str = f"Current Portfolio Value: {round(self._controller._portfolio.get_current_portfolio_value(), 2)}€"
        self._window['-TOTAL_INVESTED-'].update(invested)
        self._window['-CURRENT_PORTFOLIO_VALUE-'].update(current)


    def _update_assets_data(self, assets_data:dict[str, any]) -> None:
        rows = []
        for ticker, tablerow in assets_data.items():
            new_row = list()
            new_row.append(ticker)
            new_row.append(round(tablerow['average buy value'], 2))
            new_row.append(round(tablerow['current value'], 2))
            new_row.append(round(tablerow['owned shares'], 4))
            new_row.append(round(tablerow['value of owned asset'], 2))
            new_row.append(f"{round(tablerow['portfolio percentage'] * 100, 4)}%")
            rows.append(new_row)

        self._window['-ASSET_TABLE-'].update(values=rows)
        


    def _update_chart_data(self, chart_data) -> None:
        pass


    def _change_layout(self) -> None:
        self._window[f"-COL{self._selected_layout}-"].update(visible=False)

        if self._selected_layout == 1:
            self._selected_layout = 2
        else:
            self._selected_layout = 1
        
        self._window[f"-COL{self._selected_layout}-"].update(visible=True)

# END OF FILE #