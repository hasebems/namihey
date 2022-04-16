# -*- coding: utf-8 -*-
import  os
import  namiconf as ncf
import  namidscrpt as dsc

NO_NOTE = ['phrase','','','']
INDEX_END = 10000

class NamiFile:

    def __init__(self):
        self.during_save = False
        self.list_up_files()
        self.chain_loading_state = False    # public
        self.chain_loading = [[] for _ in range(ncf.MAX_PART_COUNT)]
        self.chain_loading_idx = [0 for _ in range(ncf.MAX_PART_COUNT)]
        self.auto_stop = False
        self.loaded_file = None

    def clear_chain_loading(self):
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

    def is_chain(self, load_lines):
        # Chain Load 読み込みと、その可否
        chain = True
        self.clear_chain_loading()
        next_lines = [0 for _ in range(ncf.MAX_PART_COUNT)] # 各パートごとに次の行番号を格納する
        for line in load_lines:
            strtmp0 = line[1]
            line_num = line[0] + 1
            if len(strtmp0) == 0: 
                continue            # nothing in the line
            if strtmp0[0] == '#':
                continue            # comment 
            elif '->' in strtmp0:
                strtmp1 = strtmp0.split('->')
                part = 0
                if line_num in next_lines:
                    part = next_lines.index(line_num)
                else:
                    i=0
                    while next_lines[i] != 0 and i<ncf.MAX_PART_COUNT-1: i=i+1
                    part = i
                self.chain_loading[part].append(strtmp1[0].strip()) # set chain loading
                next = strtmp1[1].strip()
                if next[0] == '+' and next[1:].isdecimal():
                    next_lines[part] = line_num + int(next[1:]) # 次の行番号を調べ格納
                    continue
                elif next.isdecimal():
                    next_lines[part] = int(next) # その数値をそのまま次の行番号とする
                    continue
                elif next == 'end': # end なら最終行
                    self.chain_loading[part].append('[]') # not to repeat
                    next_lines[part] = -1 # this part is end
                    continue
            chain = False
            break
        #print(self.chain_loading) # debug
        #print(next_lines) # debug
        return chain

    def load_file(self, file):
        # 指定されたファイルをロードする
        load_success = False
        load_prompt = False
        self.load_lines = []
        if file in self.available_files:
            real_name = file + '.nmhy'
            with open(real_name) as ld:
                self.loaded_file = file
                lines = ld.readlines()
                for i, line in enumerate(lines):
                    name = line.replace( '\n' , '' )
                    print(str(i+1) + ': ' + name)
                    self.load_lines.append((i,name))
                if self.is_chain(self.load_lines):  # check if chain, and load all chain data
                    self.chain_loading_state = True
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
                ni, ptx = self.gen_ni(pattern[1])
                if ni != None:
                    ptx.set_dscrpt_to_block(blk, ni)
                    ret_flag = True
        return ret_flag

    def gen_ni(self, dscrpt_text): # generate note_info
        ni = None
        ptx = dsc.Description()
        if dscrpt_text[0] == '[':
            ni = ptx.complement_bracket(dscrpt_text)
        elif dscrpt_text[0] == '{':
            ni, dialogue = ptx.complement_brace(dscrpt_text)
        return ni, ptx

    def disp_ni(self, ni):
        disp = '~~>'
        if ni[1] != '': disp += '['+ni[1]+']'
        if ni[2] != '': disp += '['+ni[2]+']'
        if ni[3] != '': disp += '['+ni[3]+']'
        if disp != '~~>': print(disp)    # display chain data

    def read_first_chain_loading(self, blk):
        # for all part (just after file load)
        if self.chain_loading_state is False: return
        # set first description
        for i in range(ncf.MAX_PART_COUNT):
            ni, ptx = self.gen_ni(self.chain_loading[i][0])
            if ni != None:
                blk.part(i).add_seq_description(ni)
                # self.disp_ni(ni) # load時は表示しない
        self.chain_loading_idx = [1 for _ in range(ncf.MAX_PART_COUNT)]

    def read_second_chain_loading(self, blk):
        # for all part (play/start command)
        if self.chain_loading_state is False: return
        for i in range(ncf.MAX_PART_COUNT):
            if len(self.chain_loading[i]) >= 2:
                self.chain_loading_idx[i] = 2
                ni, ptx = self.gen_ni(self.chain_loading[i][1])
                if ni != None:
                    blk.part(i).add_seq_description(ni)
                    self.disp_ni(ni)
                    continue
            self.chain_loading_idx[i] = INDEX_END

    def read_next_chain_loading(self, part_num):
        # for one part (return to top)
        if self.chain_loading_state is False: return NO_NOTE
        idx = self.chain_loading_idx[part_num]
        if len(self.chain_loading[part_num]) > idx:
            self.chain_loading_idx[part_num] = idx+1
            # print(idx) # debug
            ni, ptx = self.gen_ni(self.chain_loading[part_num][idx])
            if ni != None:
                self.disp_ni(ni)
                return ni
        self.chain_loading_idx[part_num] = INDEX_END
        # 全パートが終了したかチェック
        if all([True if num == INDEX_END else False for num in self.chain_loading_idx]):
            self.auto_stop = True
        return NO_NOTE

