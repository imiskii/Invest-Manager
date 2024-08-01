#!/usr/bin/python3

##
# Author: Michal Ľaš
# Date: 14.07.2024


import IM_gui as gui
import Controller as ct

if __name__ == "__main__":
    controller = ct.Controller()
    view = gui.IMMainGui(controller)
    controller.set_view(view)

    view.open_main_window()

    
    