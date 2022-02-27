# -*- coding: utf-8 -*-
import  os
import  namiconf as ncf
import  namidscrpt as dsc

NO_NOTE = ['phrase','','','']

class NamiFile:

    def __init__(self):
        self.during_save = False
        self.list_up_files()
        self.chain_loading_state = False    # public
        self.chain_loading = [[] for _ in range(ncf.MAX_PART_COUNT)]
        self.chain_loading_idx = [0 for _ in range(ncf.MAX_PART_COUNT)]

    def list_up_files(self):
        # 起動時のファイル一覧取得
        self.available_files = []
        all_file_list = os.listdir('./')
        for fl in all_file_list:
            fl_name, fl_ext = os.path.splitext(fl)
            if fl_ext == '.nmhy':
                self.available_files.append(fl_name)

    def display_loadable_files(self, prfunc):
        # 起動時のファイル一覧表示
        if len(self.available_files) > 0:
            prfunc('<<Now you can load these files!!>>')
            for fl in self.available_files:
                print('>'+fl)
        else:
            prfunc("No Namihey Files!")

    def prepare_save_file(self, file_name):
        # 1.Save処理の準備
        if self.during_save:
            return False
        if file_name == '':
            return False
        self.during_save = True
        whole_name = file_name + '.nmhy'
        self.save_file = open(whole_name, 'a')
        return True

    def save_pattern(self, str):
        # 2.Save処理
        if self.during_save == False:
            return
        self.save_file.write(str+'\n')

    def close_save_file(self):
        # 3.Save File の Close
        if self.during_save == False:
            return
        self.save_file.close()
        self.list_up_files()
        self.during_save = False

    def is_chain(self):
        # Chain Load 読み込みと、その可否
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
        self.chain_loading_state = chain
        return chain

    def load_file(self, file):
        # 指定されたファイルをロードする
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
                if self.is_chain():  # check if chain, and load all chain data
                    pass
                else:
                    self.chain_loading_state = False
                    load_prompt = True  # [load] will appear
                load_success = True # success for loading file
        return load_success, load_prompt

    def load_pattern(self, input, blk):
        # Load a description selected form input number
        ret_flag = False
        num = input.replace( '\n' , '' )
        if num.isdecimal():
            line_num = int(num) - 1
            if line_num >= 0 and len(self.load_lines) > line_num:
                pattern = self.load_lines[line_num]
                #print(pattern)
                dscrpt, ptx = self.xxx(pattern[1])
                if dscrpt != None:
                    ptx.set_dscrpt_to_block(blk, dscrpt)
                    ret_flag = True
        return ret_flag

    def xxx(self, dscrpt_text):
        dscrpt = None
        ptx = dsc.Description()
        if dscrpt_text[0] == '[':
            dscrpt = ptx.complement_bracket(dscrpt_text)
        elif dscrpt_text[0] == '{':
            dscrpt, dialogue = ptx.complement_brace(dscrpt_text)
        return dscrpt, ptx

    def read_first_chain_loading(self, blk):
        # for all part
        if self.chain_loading_state is False: return
        for i in range(blk.max_part()):
            dscrpt, ptx = self.xxx(self.chain_loading[i][0])
            if dscrpt != None:
                blk.part(i).add_seq_description(dscrpt)
        self.chain_loading_idx = [1 for _ in range(ncf.MAX_PART_COUNT)]

    def read_second_chain_loading(self, blk):
        # for all part
        if self.chain_loading_state is False: return
        for i in range(blk.max_part()):
            idx = self.chain_loading_idx[i]
            if len(self.chain_loading[i]) >= idx+1:
                self.chain_loading_idx[i] = idx+1
                dscrpt, ptx = self.xxx(self.chain_loading[i][idx])
                if dscrpt != None:
                    blk.part(i).add_seq_description(dscrpt)

    def read_next_chain_loading(self, part_num):
        # for one part
        if self.chain_loading_state is False: return NO_NOTE
        idx = self.chain_loading_idx[part_num]
        if len(self.chain_loading[part_num]) >= idx+1:
            self.chain_loading_idx[part_num] = idx+1
            # print(idx) # debug
            dscrpt, ptx = self.xxx(self.chain_loading[part_num][idx])
            if dscrpt != None:
                return dscrpt
        return NO_NOTE

