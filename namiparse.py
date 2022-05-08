# -*- coding: utf-8 -*-
import namilib as nlib
import namidscrpt as dscrpt

T_WATER = '\033[96m'
T_PINK = '\033[95m'
T_WHITE = '\033[97m'
T_END = '\033[0m'

PAN_TRANS_TBL = ('L10','L9','L8','L7','L6','L5','L4','L3','L2','L1','C',
                 'R1','R2','R3','R4','R5','R6','R7','R8','R9','R10')

class Prompt:
    NORMAL = 0
    LOAD = 1

class Parsing:
    #   入力した文字列の解析
    #   一行単位で入力されるたびに生成される
    def __init__(self, seq, nfl, md):
        self.prompt_mode = Prompt.NORMAL
        self.sq = seq
        self.fl = nfl
        self.md = md
        self.input_part = 1  # 1origin
        self.prompt_str = self.get_prompt_string('0', self.input_part)
        self.back_color = 2
        self.fl.display_loadable_files(self.print_dialogue)

    @staticmethod
    def get_prompt_string(blk, part):
        # return T_WATER + '[' + str(blk) + '][' + str(part) + ']~~> ' + T_END
        return '[' + blk + '][' + str(part) + ']~~> '

    @staticmethod
    def print_dialogue(rpy):
        print(T_PINK + rpy + T_END)

    @staticmethod
    def get_complete_pattern_string(blk, part):
        ele = blk.part(part).description
        ptn_str = None
        if ele[0] == 'phrase':
            ptn_str = '[' + str(ele[1]) + '][' + str(ele[2]) + '][' + str(ele[3]) + ']'
        elif ele[0] == 'random' or ele[0] == 'arp':
            ptn_str = '{' + str(ele[1]) + '}{' + str(ele[2]) + '}{' + str(ele[3]) + '}'
        return ptn_str

    def change_beat(self, text):
        if '/' in text:
            beat_list = text.strip().split('/')
            btnum = onpu = 0
            btnum_str = beat_list[0].strip()
            if btnum_str.isdecimal():
                btnum = int(btnum_str)
            onpu_str = beat_list[1].strip()
            if onpu_str.isdecimal():
                onpu = int(onpu_str)
            if btnum >= 1 and onpu >= 1:
                self.sq.blk().stock_beat_info(  \
                    [(nlib.DEFAULT_TICK_FOR_ONE_MEASURE/onpu)*btnum, btnum, onpu])
                self.print_dialogue("Beat has changed!")
            else:
                self.print_dialogue("what?")

    def change_key(self, key_text, all):
        def change_note(ptx, keyx, octx):
            if octx == nlib.NONE:
                octx = ptx.keynote // 12
            keyx += octx * 12
            keyx = nlib.note_limit(keyx, 0, 127)
            ptx.change_keynote(keyx)

        key = 0
        oct = nlib.NONE
        first_letter = key_text[0]
        if first_letter == 'C':
            key += 0
        elif first_letter == 'D':
            key += 2
        elif first_letter == 'E':
            key += 4
        elif first_letter == 'F':
            key += 5
        elif first_letter == 'G':
            key += 7
        elif first_letter == 'A':
            key += 9
        elif first_letter == 'B':
            key += 11
        else:
            return
        if len(key_text) > 1:
            octave_letter = key_text[1:]
            if key_text[1] == '#':
                key += 1
                if len(key_text) > 2:
                    octave_letter = key_text[2:]
            elif key_text[1] == 'b':
                key -= 1
                if len(key_text) > 2:
                    octave_letter = key_text[2:]
            if octave_letter.isdecimal():
                oct = int(octave_letter) + 1
        curbk = self.sq.blk()
        if all:
            for i in range(nlib.MAX_PART_COUNT):
                change_note(curbk.part(i), key, oct)
        else:
            pt = curbk.part(self.input_part-1)
            change_note(pt, key, oct)

    def change_oct(self, text, all):
        def change_oct_to_part(ptx, octx):
            newoct = ptx.keynote // 12 + octx
            key = newoct * 12 + ptx.keynote % 12
            key = nlib.note_limit(key, 0, 127)
            ptx.change_keynote(key)

        def generate_oct_number(text):
            octave_letter = text
            pm = 1
            if len(text) > 1:
                if text[0] == '+':
                    octave_letter = text[1:]
                elif text[0] == '-':
                    pm = -1
                    octave_letter = text[1:]
            if octave_letter.isdecimal():
                return int(octave_letter) * pm
            else:
                return 0

        curbk = self.sq.blk()
        if type(text) == list:
            for i, letter in enumerate(text):
                oct = generate_oct_number(letter)
                change_oct_to_part(curbk.part(i), oct)
        else:
            oct = generate_oct_number(text)
            if all:
                for i in range(nlib.MAX_PART_COUNT):
                    change_oct_to_part(curbk.part(i), oct)
            else:
                pt = curbk.part(self.input_part-1)
                change_oct_to_part(pt, oct)

    def change_cc(self, cc_num, cc_list):
        if len(cc_list) > nlib.MAX_PART_COUNT:
            del cc_list[nlib.MAX_PART_COUNT:]
        curbk = self.sq.blk()
        for i, vol in enumerate(cc_list):
            self.sq.blk().send_midi_cc(i, cc_num, int(vol))

    CONFIRM_MIDI_OUT_ID = -1

    def midi_setting(self, num):
        if num == self.CONFIRM_MIDI_OUT_ID:
            ports = self.md.all_ports
        else:
            ports = self.md.scan_midi_all_port()
        self.print_dialogue("==MIDI OUT LIST==")
        for i, pt in enumerate(ports):
            self.print_dialogue(str(i) + ": " + str(pt[1]) + '(' + str(pt[0]) + ')')

        self.print_dialogue("==SELECTED MIDI OUT==")
        if num == self.CONFIRM_MIDI_OUT_ID:  # 設定せず、設定内容をみたい場合
            for pt in ports:
                if pt[2]:
                    self.print_dialogue(pt[1] + '(' + str(pt[0]) + ')')
        else:
            real_id = self.md.set_midi_port(num)
            if real_id != -1:
                for pt in ports:
                    if pt[0] == real_id:
                        break
                self.print_dialogue(pt[1] + '(' + str(pt[0]) + ')')
            else:
                self.print_dialogue("MIDI setting is something wrong!")

    def parse_set_command(self, input_text):
        prm_text = input_text.strip()
        if '=' in prm_text:
            tx = prm_text.split('=',2)
        else:
            return

        command = tx[0].strip()
        if command == 'part':
            pass
        elif command == 'block':
            pass
        elif command == 'key':
            key_list = tx[1].strip().split()
            self.change_key(key_list[0], 'all' in prm_text)
            self.print_dialogue("Key has changed!")
        elif command == 'oct':
            if ',' in tx[1]:
                oct_list = tx[1].strip().split(',')
                self.change_oct(oct_list, True)
            else:
                oct_list = tx[1].strip().split()
                self.change_oct(oct_list[0], 'all' in prm_text)
            self.print_dialogue("Octave has changed!")
        elif command == 'beat':
            beat_list = tx[1].strip().split()
            self.change_beat(beat_list[0])
        elif command == 'bpm':
            bpmnumlist = tx[1].strip().split()
            if bpmnumlist[0].isdecimal():
                self.sq.change_tempo(int(bpmnumlist[0]))
                self.print_dialogue("BPM has changed!")
        elif command == 'balance' or command == 'volume':
            bl_list = tx[1].strip().split(',')
            cc_list = [88 for _ in range(5)] # default: 7
            for i, var in enumerate(bl_list):
                if var.isdecimal():
                    cc_list[i] = int(int(var)*12.7)
            self.change_cc(7, cc_list)
            self.print_dialogue("Balance has changed!")
        elif command == 'pan':
            bl_list = tx[1].strip().split(',')
            cc_list = [64 for _ in range(5)] # default: C
            for i, var in enumerate(bl_list):
                try:
                    pan = int(PAN_TRANS_TBL.index(var) * 6.4)
                    cc_list[i] = pan if pan <= 127 else 127
                except ValueError as error:
                    continue
            self.change_cc(10, cc_list)
            self.print_dialogue("Pan has changed!")
        elif command == 'pgn':
            bl_list = tx[1].strip().split(',')
            for i, var in enumerate(bl_list):
                if var.isdecimal():
                    num = int(var)
                    if num > 0 and num <= 128:
                        self.sq.blk().send_midi_pgn(i,num-1)
            self.print_dialogue("Program number has changed!")

    def letterB(self, input_text):
        self.print_dialogue("what?")

    def letterP(self, input_text):
        if input_text[0:4] == 'play':
            arg = input_text.split()
            if len(arg) == 1:
                well_done = self.sq.play()
                if well_done:
                    self.print_dialogue("Phrase has started!")
                else:
                    self.print_dialogue("Unable to start!")
        elif input_text[0:4] == 'part':
            tx = input_text[4:].replace(' ', '')
            if tx.isdecimal():
                part = int(tx)
                if 0 < part <= nlib.MAX_PART_COUNT:
                    self.print_dialogue("Changed current part to " + str(part) + ".")
                    self.input_part = part
                    self.prompt_str = self.get_prompt_string('0', part)
        elif input_text[0:5] == 'panic':
            blk = self.sq.blk()
            for i in range(nlib.MAX_PART_COUNT):
                blk.part(i).change_cc(120, 0)          
        else:
            self.print_dialogue("what?")

    def letterS(self, input_text):
        if input_text[0:5] == 'start':
            well_done = self.sq.play()
            if well_done:
                self.print_dialogue("Phrase has started!")
            else:
                self.print_dialogue("Unable to start!")
        elif input_text[0:4] == 'stop':
            self.sq.stop()
            self.print_dialogue("Stopped!")
        elif input_text[0:3] == 'set':
            self.parse_set_command(input_text[3:])
        elif input_text[0:4] == 'show':
            option = input_text[4:].replace(' ', '')
            blk = self.sq.blk()
            if option == 'all':
                for i in range(nlib.MAX_PART_COUNT):
                    ptn_str = self.get_complete_pattern_string(blk, i)
                    if ptn_str is not None:
                        self.print_dialogue('['+str(i+1)+']'+'~~> '+ptn_str)
            else:
                ptn_str = self.get_complete_pattern_string(blk, self.input_part-1)
                if ptn_str is not None: self.print_dialogue('~~> '+ptn_str)
        elif input_text[0:4] == 'save':
            file = input_text[4:].replace(' ', '')
            if self.fl.prepare_save_file(file):
                blk = self.sq.blk()
                for i in range(nlib.MAX_PART_COUNT):
                    ptn_str = self.get_complete_pattern_string(blk, i)
                    if ptn_str is not None:
                        self.fl.save_pattern(ptn_str)
                self.fl.close_save_file()
                self.print_dialogue('Saved!')
        else:
            self.print_dialogue("what?")

    def letterI(self, input_text):
        if input_text[0:5] == 'input':
            tx = input_text[5:].replace(' ', '')
            if tx.isdecimal():
                part = int(tx)
                if 0 < part <= nlib.MAX_PART_COUNT:
                    self.print_dialogue("Changed current part to " + str(part) + ".")
                    self.input_part = part
                    self.prompt_str = self.get_prompt_string('0', part)
        else:
            self.print_dialogue("what?")

    def letterC(self, input_text):
        if input_text[0:6] == 'copyto':
            tx = input_text[7:].replace(' ', '')
            if tx.isdecimal():
                part = int(tx)
                if 0 < part <= nlib.MAX_PART_COUNT:
                    self.sq.blk().copy_phrase(part - 1)
                    self.print_dialogue("Phrase copied to part" + tx + ".")
        elif input_text[0:5] == 'color':
            color = input_text[6:].replace(' ','')
            if color.isdecimal() and int(color) < 3:
                self.back_color = int(color)
                self.print_dialogue("Back color has changed!")
        else:
            self.print_dialogue("what?")

    def letterF(self, input_text):
        if input_text[0:4] == "fine":
            self.sq.fine()
            self.print_dialogue('Will be ended!')
        else:
            self.print_dialogue("what?")

    def letterQm(self, input_text):
        self.print_dialogue("what?")

    def letterM(self, input_text):
        if input_text[0:4] == "midi":
            picked_txt = input_text[input_text.find('midi') + 4:].strip().split()
            if picked_txt and picked_txt[0].isdecimal():
                self.midi_setting(int(picked_txt[0]))
            else:
                self.midi_setting(self.CONFIRM_MIDI_OUT_ID)

    def letterL(self, input_text):
        if input_text[0:4] == "load":
            file = input_text[4:].replace(' ', '')
            success, prompt = self.fl.load_file(file)
            if success:
                if prompt:
                    # normal load
                    self.prompt_mode = Prompt.LOAD
                    self.prompt_str = '[load]~~> '
                else:
                    # chain loading
                    self.print_dialogue("Completed chain loading!")
                    self.sq.stop()
                    self.fl.read_first_chain_loading(self.sq.blk())
        else:
            self.print_dialogue("what?")

    def letter_bracket(self, input_text):
        dx = dscrpt.Description()
        description = dx.complement_bracket(input_text)
        if description != None:
            dx.set_dscrpt_to_block(self.input_part-1, self.sq.blk(), description)
            self.print_dialogue("set Phrase!")
        else:
            self.print_dialogue("what?")

    def letter_brace(self, input_text):
        dx = dscrpt.Description()
        description, dialogue = dx.complement_brace(input_text)
        if description != None:
            dx.set_dscrpt_to_block(self.input_part-1, self.sq.blk(), description)
            self.print_dialogue(dialogue)
        else:
            self.print_dialogue("what?")

    def during_load(self, input_text):
        if self.fl.load_pattern(input_text, self.sq.blk()):
            self.print_dialogue("description loaded!")
        else:
            self.print_dialogue("what?")            
        self.prompt_mode = Prompt.NORMAL
        self.prompt_str = self.get_prompt_string('0', self.input_part)

    def startParsing(self, input_text):
        first_letter = input_text[0:1]
        if self.prompt_mode == Prompt.LOAD:
            self.during_load(input_text)
        elif first_letter == '[':
            self.letter_bracket(input_text)
        elif first_letter == '{':
            self.letter_brace(input_text)
        elif first_letter == 'b':
            self.letterB(input_text)
        elif first_letter == 'c':
            self.letterC(input_text)
        elif first_letter == 'f':
            self.letterF(input_text)
        elif first_letter == 'i':
            self.letterI(input_text)
        elif first_letter == 'l':
            self.letterL(input_text)
        elif first_letter == 'p':
            self.letterP(input_text)
        elif first_letter == 's':
            self.letterS(input_text)
        elif first_letter == 'm':
            self.letterM(input_text)
        elif first_letter == '?':
            self.letterQm(input_text)
        else:
            self.print_dialogue("what?")
