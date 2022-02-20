# -*- coding: utf-8 -*-
import  os

class NamiFile:

    def __init__(self):
        all_file_list = os.listdir('./')
        self.available_files = []
        for fl in all_file_list:
            fl_name, fl_ext = os.path.splitext(fl)
            if fl_ext == '.nmhy':
                self.available_files.append(fl_name)
        if len(self.available_files) > 0:
            print(self.available_files)
        else:
            print("No Namihey Files.")

    def save_file(self):
        pass
