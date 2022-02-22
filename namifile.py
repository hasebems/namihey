# -*- coding: utf-8 -*-
import  os
import  namiseq as sq

class NamiFile:

    def __init__(self):
        self.during_save = False
        self.list_up_files()
        if len(self.available_files) > 0:
            print(self.available_files)
        else:
            print("No Namihey Files.")

    def list_up_files(self):
        self.available_files = []
        all_file_list = os.listdir('./')
        for fl in all_file_list:
            fl_name, fl_ext = os.path.splitext(fl)
            if fl_ext == '.nmhy':
                self.available_files.append(fl_name)

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
        self.list_up_files()
        self.during_save = False

    def load_file(self, file):
        load_success = False
        self.load_lines = []
        if file in self.available_files:
            real_name = file + '.nmhy'
            with open(real_name) as ld:
                lines = ld.readlines()
                for i, line in enumerate(lines):
                    name = line.replace( '\n' , '' )
                    print(str(i+1) + ': ' + name)
                    self.load_lines.append((i,name))
                load_success = True # success for loading file then list up patterns
        return load_success

    def load_pattern(self, parse, input):
        num = input.replace( '\n' , '' )
        if num.isdecimal():
            line_num = int(num) - 1
            if line_num >= 0 and len(self.load_lines) > line_num:
                pattern = self.load_lines[line_num]
                #print(pattern)
                if pattern[1][0] == '[':
                    parse.letter_bracket(pattern[1])
                elif pattern[1][0] == '{':
                    parse.letter_brace(pattern[1])
        return True
