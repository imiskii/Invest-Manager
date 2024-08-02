##
# Author: Michal Ľaš
# Date: 14.07.2024


import PySimpleGUI as sg
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import Controller as ct
from Portfolio import SUMMARY_HEADER, ASSETS_HEADER, CURRENCIES, format_value


DEFAULT_GRAPH_TICKERS:list = ['PORTFOLIO']
ASSET_SHOW_OPTIONS:list = ['All', 'Owned', 'Sold']

sg.theme('Light Blue 2')

class IMMainGui:

    def __init__(self, controller:ct.Controller) -> None:
        self._controller = controller
        # Create Layout
        self._construct_layout()
        # Initialize GUI attributes
        self._selected_layout:int = 1
        self._graph_tickers = DEFAULT_GRAPH_TICKERS


    def _construct_layout(self) -> None:
        # Create sub layouts
        self.loading_layout:LoadingLayout = LoadingLayout()
        self.summary_layout:SummaryLayout = SummaryLayout()
        self.assets_layout:AssetLayout = AssetLayout()
        self.graph_layout:GraphLayout = GraphLayout()
        # Main window layout
        _main_layout = [[sg.Text("Used Currency: "), sg.Combo(CURRENCIES, enable_events=True, readonly=True, key='-CURRENCY_COMBO-', default_value=CURRENCIES[0])],
                    [sg.TabGroup([[sg.Tab('Summary', self.summary_layout.layout), sg.Tab('Assets info', self.assets_layout.layout), sg.Tab('Graphs', self.graph_layout.layout)]])],
                    [sg.Button('Change .xlsx file'), sg.Button('Close Invest Manager Appliaction')],
                    [sg.Text("", key='-LOG_LINE-')]]
        # Loading + Main layout
        _layout = [
            [sg.Column(self.loading_layout.layout, key='-COL1-'), sg.Column(_main_layout, key='-COL2-', visible=False)]
        ]
        # Create window
        self._window:sg.Window = sg.Window('Invest Manager', _layout, font=("Arial", 14), finalize=True)
        # Connect sub layouts to main window
        self.loading_layout.connect_to_main_window(self._window, self._controller)
        self.summary_layout.connect_to_main_window(self._window, self._controller)
        self.assets_layout.connect_to_main_window(self._window, self._controller)
        self.graph_layout.connect_to_main_window(self._window, self._controller)


    def open_main_window(self):
        while True:
            event, values = self._window.read()
            if event in (sg.WIN_CLOSED, 'Exit', 'Close Invest Manager Appliaction'):
                break
            else:
                self._event_load_file(event, values)
                self._event_change_xlsx(event)
                self._event_change_currency(event, values)
                self._event_update_graph(event, values)
                self._event_plot(event)
                self._event_filter_summary_table(event, values)



        self.close_main_window()


    def close_main_window(self):
        self._window.close()


    def update_log_line(self, log: str) -> None:
        self._window['-LOG_LINE-'].update(log)


    def _change_layout(self) -> None:
        self._window[f"-COL{self._selected_layout}-"].update(visible=False)

        if self._selected_layout == 1:
            self._selected_layout = 2
        else:
            self._selected_layout = 1
        
        self._window[f"-COL{self._selected_layout}-"].update(visible=True)


    def _initialize_layouts_content(self) -> None:
        """ Updates content in whole main application """
        self._update_currency_related_content()

    
    def _update_currency_related_content(self) -> None:
        """ Updates just content which is related to currency conversions """
        summary_data = self._controller.get_summary_data()
        self.summary_layout.update_summary_layout(summary_data[0], summary_data[1], summary_data[2]) # 0: summary data, 1: total invested money, 2: current portfolio value
        self.assets_layout.update_assets_layout() # This is not necessary currency related
        self.graph_layout.upadte_graph_layout()

    ### ------------------------- EVENTS ------------------------- ###

    def _event_load_file(self, event, values) -> None:
        if event == 'Submit':
            self._window['-PROGRESS_BAR-'].update(visible=True)
            self._window['-LOG_TEXT-'].update(visible=True)
            self._controller.load_assets_data(values['Browse'])
            self._initialize_layouts_content()
            self._change_layout()


    def _event_change_xlsx(self, event) -> None:
        if event == 'Change .xlsx file':
            self._controller.reset_loaded()
            self._graph_tickers = DEFAULT_GRAPH_TICKERS
            plt.cla() # Clear canvas
            self._change_layout()
            self.loading_layout.update_login_log_progress_bar(0, "")


    def _event_change_currency(self, event, values) -> None:
        if event == '-CURRENCY_COMBO-':
            self._controller.change_uniform_currency(values['-CURRENCY_COMBO-'])
            self._initialize_layouts_content()


    def _event_update_graph(self, event, values) -> None:
        if event == '-GRAPH_LIST_BOX-':
            self.graph_layout.update_graph(values['-GRAPH_LIST_BOX-'])


    def _event_plot(self, event) -> None:
        if event == 'Plot':
            self.graph_layout.show_graph_plot()


    def _event_filter_summary_table(self, event, values) -> None:
        if event == '-ASSET_FILTER_COMBO-':
            self.assets_layout.update_table(values['-ASSET_FILTER_COMBO-'])



class SubLayout:

    def __init__(self) -> None:
        pass

    def connect_to_main_window(self, window, controller) -> None:
        self._window:sg.Window = window
        self._controller:ct.Controller = controller


class LoadingLayout(SubLayout):

    def __init__(self) -> None:
        # Layout
        self.layout =  [
            [sg.Push(), sg.Text("Inves Manager", justification='center', font=('Courier New',26)), sg.Push()],
            [sg.Text("Enter .xlsx file with investment records: ", size=(34, 1)), sg.Input(), sg.FileBrowse(file_types=(('MS Excel Files', '*.xlsx'),))],
            [sg.Submit(), sg.Exit()],
            [sg.ProgressBar(50, size=(60,20), border_width=4, key='-PROGRESS_BAR-', visible=False, expand_x=True)],
            [sg.Text("", key='-LOG_TEXT-', text_color='Black', visible=False)]
        ]


    def update_login_log_progress_bar(self, progress_bar_percentage:float, log:str) -> None:
        self._window['-PROGRESS_BAR-'].update(round(50 * progress_bar_percentage))
        self._window['-LOG_TEXT-'].update(log)



class SummaryLayout(SubLayout):

    def __init__(self) -> None:
        # Layout
        self.layout = [
            [sg.Table(values=[], headings=SUMMARY_HEADER,
                        auto_size_columns=True,
                        display_row_numbers=False,
                        justification='left', key='-SUM_TABLE-',
                        enable_events=False,
                        expand_x=True, expand_y=True)],
            [sg.Text("Total Invested EUR: X", key="-TOTAL_INVESTED-"), sg.Text("Current Portfolio Value: X", key='-CURRENT_PORTFOLIO_VALUE-'), sg.Text("Result: ", key='-RESULT_PERCENTAGE-')]
        ]
        # Initialize attribute


    def update_summary_layout(self, summary_data:list[list[any]], total_invested: float, current_value: float) -> None:     
        self._window['-SUM_TABLE-'].update(values=summary_data)

        invested:str = f"Total Invested: {format_value(total_invested, self._controller.get_current_currency())}"
        current:str = f"Current Portfolio Value: {format_value(current_value, self._controller.get_current_currency())}"
        percentage_formula: float = (current_value - total_invested) / total_invested * 100
        percentage:str = f"Result: {format_value(percentage_formula, '%')}"
        self._window['-TOTAL_INVESTED-'].update(invested)
        self._window['-CURRENT_PORTFOLIO_VALUE-'].update(current)
        self._window['-RESULT_PERCENTAGE-'].update(percentage)


class AssetLayout(SubLayout):

    def __init__(self) -> None:
        # Layout
        self.layout = [
            [sg.Combo(values=ASSET_SHOW_OPTIONS, key='-ASSET_FILTER_COMBO-', enable_events=True, default_value='All')],
            [sg.Table(values=[], headings=ASSETS_HEADER,
                        auto_size_columns=True,
                        display_row_numbers=False,
                        justification='left', key='-ASSET_TABLE-',
                        enable_events=False,
                        expand_x=True, expand_y=True)]
        ]
        # Initialize attribute


    def update_assets_layout(self) -> None:
        self._window['-ASSET_TABLE-'].update(values=self._filter_asset_value(self._controller.get_asset_table_data(), self._window['-ASSET_FILTER_COMBO-'].get()))


    def _filter_asset_value(self, asset_data:list[list[any]], filter: str) -> list[list[any]]:
        match filter:
            case 'All':
                return asset_data
            case 'Owned':
                return [row for row in asset_data if row[3] >= 0]
            case 'Sold':
                return [row for row in asset_data if row[3] <= 0]
            

    def update_table(self, filter: str) -> None:
        self._window['-ASSET_TABLE-'].update(values=self._filter_asset_value(self._controller.get_asset_table_data(), filter))


class GraphLayout(SubLayout):

    def __init__(self) -> None:
        # Layout
        self.layout = [
            [sg.Column([[sg.Text("Change graph")], [sg.Listbox(values=DEFAULT_GRAPH_TICKERS, default_values=DEFAULT_GRAPH_TICKERS, enable_events=True, key='-GRAPH_LIST_BOX-', select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE, expand_x=True, expand_y=True)]], expand_x=True, expand_y=True),
             sg.Column([[sg.Button('Plot')], [sg.Canvas(key='-EVOLUTION_GRAPH-', expand_x=True, expand_y=True)]], expand_x=True, expand_y=True)]
        ]
        self._figure, self._ax = plt.subplots()
        self._lines:dict[str, list] = dict()
        

    def connect_to_main_window(self, window, controller) -> None:
            super().connect_to_main_window(window, controller)
            # Link matplotlib to PySimpleGUI Graph
            canvas = FigureCanvasTkAgg(self._figure, self._window['-EVOLUTION_GRAPH-'].TKCanvas)
            canvas.get_tk_widget().pack(side='top', fill='both', expand=1)
            

    def upadte_graph_layout(self) -> None:
        ticker_list = DEFAULT_GRAPH_TICKERS + self._controller.get_asset_tickers()
        default_tickers = self._window['-GRAPH_LIST_BOX-'].get()
        self._window['-GRAPH_LIST_BOX-'].update(values=ticker_list)
        self._window['-GRAPH_LIST_BOX-'].set_value(default_tickers)
        self._lines:dict[str, list] = dict() # Reset lines dictionary
        plt.cla() # clear plot canvas
        self.update_graph(default_tickers)
        # Set axis x_lable and y_label - It is there, because it changes only if currency or whole layout changes
        self._ax.set_xlabel('Time', fontsize=14)
        self._ax.set_ylabel(f"Value in {self._controller.get_current_currency()}", fontsize=14)
        self._ax.grid(True)


    def update_graph(self, tickers: list) -> None:
        """ Update displayed graph with given tickers graphs """
        # Remove lines
        line_keys = list(self._lines.keys()) # There has to be created separate list to avoid RuntimeError caused by changing dictionary size during iteration
        for ticker in line_keys:
            if ticker not in tickers:
                line = self._lines.pop(ticker)
                line.remove()
        # Add lines
        for ticker in tickers:
            if ticker not in self._lines:
                graph = self._controller.get_evolution_graph(ticker)
                line, = self._ax.plot(graph, label=ticker)
                self._lines[ticker] = line

        self._ax.set_title(f"Value evolution of {', '.join(tickers)}", fontsize=14)
        if self._lines:
            self._ax.relim()
            self._ax.autoscale_view()
            self._ax.legend()
        plt.draw()
        # Draw in PySimpleGui Canvas
        self._figure.canvas.draw()


    def show_graph_plot(self) -> None:
        # There should be plt.show(block=False), but the application get stuck if is this used.  Without this however, if the plot window is shown and
        # it is manipulated with main window the graph plotting broke, and wont be plotting properly anymore.
        plt.show()


# END OF FILE #