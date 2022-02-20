# -*- coding: utf-8 -*-
import  os
import  namiseq as sq

class NamiFile:

    def __init__(self, seq):
        self.sq = seq
        self.during_save = False
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

    def prepare_save_file(self, file_name):
        if self.during_save:
            return False
        if file_name == '':
            return False
        self.during_save = True
        whole_name = file_name + '.nmhy'
        self.save_file = open(whole_name, 'a')
        return True

    def save_pattern(self, str):
        if self.during_save == False:
            return
        self.save_file.write(str+'\n')

    def close_save_file(self):
        if self.during_save == False:
            return
        self.save_file.close()
        self.during_save = False

    def load_file(self, file):
        return True

    def load_pattern(self, input):
        return True
