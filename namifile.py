# -*- coding: utf-8 -*-
import  os
import  namiconf as ncf

class NamiFile:

    def __init__(self):
        self.during_save = False
        self.list_up_files()
        self.chain_loading = [[] for _ in range(ncf.MAX_PART_COUNT)]
        if len(self.available_files) > 0:
            print('<<Now you can load these files!!>>')
            for fl in self.available_files:
                print('>'+fl)
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

    def is_chain(self):
        chain = True
        next_lines = [0 for _ in range(ncf.MAX_PART_COUNT)]
        for line in self.load_lines:
            strtmp0 = line[1]
            line_num = line[0] + 1
            if '->' in strtmp0:
                strtmp1 = strtmp0.split('->')
                part = 0
                if line_num in next_lines:
                    part = next_lines.index(line_num)
                else:
                    i=0
                    while next_lines[i] != 0: i=i+1
                    part = i
                self.chain_loading[part].append(strtmp1[0].strip()) # set chain loading
                next = strtmp1[1].strip()
                if next.isdecimal():
                    next_lines[part] = int(next)
                    continue
                elif next == 'end':
                    next_lines[part] = -1 # this part is end
                    continue
            chain = False
            break
        #print(self.chain_loading) # debug
        #print(next_lines) # debug
        return chain

    def load_file(self, file):
        load_success = False
        load_prompt = False
        self.load_lines = []
        if file in self.available_files:
            real_name = file + '.nmhy'
            with open(real_name) as ld:
                lines = ld.readlines()
                for i, line in enumerate(lines):
                    name = line.replace( '\n' , '' )
                    print(str(i+1) + ': ' + name)
                    self.load_lines.append((i,name))
                if self.is_chain():
                    pass
                else:
                    load_prompt = True  # [load] will appear
                load_success = True # success for loading file
        return load_success, load_prompt

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