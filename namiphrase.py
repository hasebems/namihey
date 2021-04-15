# -*- coding: utf-8 -*-
import re
import math
import namilib as nlib

REPEAT_START = -1
NO_REPEAT = 0
REPEAT_END = 1  # 1,2,3 の数値はリピート回数


class PhraseGenerator:
    #   文字情報を MIDI で使う数値に変換
    #   変換の際、一回生成されるだけ

    def __init__(self, phrase_data, key):
        self.baseNote = 4  # base note type
        self.durPer = 100  # 100%
        self.playData = []
        self.noteData = phrase_data
        self.keynote = key

    def __add_note(self, tick, notes, duration, velocity=100):
        for note in notes:
            if note != nlib.REST:
                self.playData.append([tick, note, velocity])
        for note in notes:
            if note != nlib.REST:
                real_dur = math.floor(duration * self.durPer * 480 * 4 / (100 * self.baseNote))  # 切り捨て
                off_tick = tick + real_dur - 1
                self.playData.append([off_tick, note, 0])

    def __fill_omitted_note_data(self):
        # スペース削除し、',' '|' 区切りでリスト化
        note_flow = re.split('[,|]', self.noteData[0].replace(' ', ''))
        while '' in note_flow:
            note_flow.remove('')

        # If find Repeat mark, expand all event.
        no_repeat = False
        while not no_repeat:
            no_repeat = True
            repeat_start = 0
            for i, nt in enumerate(note_flow):  # |: :n|
                if ':' in nt:
                    no_repeat = False
                    locate = nt.find(':')
                    if locate == 0:
                        note_flow[i] = nt[1:]
                        repeat_start = i
                    else:
                        repeat_count = 0
                        num = nt.rfind(':') - len(nt)
                        note_flow[i] = nt[0:num]
                        if num == -1:
                            repeat_count = 1
                        else:
                            if nt[num + 1:].isdecimal():
                                repeat_count = int(nt[num + 1:])
                        repeat_end_ptr = i + 1
                        for j in range(repeat_count):
                            ins_ptr = repeat_end_ptr + j * (repeat_end_ptr - repeat_start)
                            note_flow[ins_ptr:ins_ptr] = note_flow[repeat_start:repeat_end_ptr]
                        break
            # end of for

            repeat_start = 0
            first_bracket = False
            for i, nt in enumerate(note_flow):  # <  >*n
                if '<' in nt:
                    no_repeat = False
                    locate = nt.find('<')
                    if locate == 0:
                        note_flow[i] = nt[1:]
                        repeat_start = i
                        first_bracket = True
                elif '>' in nt:
                    repeat_count = 0
                    re_cnt = nt.rfind('>')
                    note_flow[i] = nt[0:re_cnt]
                    if nt[re_cnt + 1:re_cnt + 2] == '*' and first_bracket is True:
                        if nt[re_cnt + 2:].isdecimal():
                            repeat_count = int(nt[re_cnt + 2:])
                        if repeat_count > 1:
                            repeat_end_ptr = i + 1
                            for j in range(repeat_count - 1):
                                ins_ptr = repeat_end_ptr + j * (repeat_end_ptr - repeat_start)
                                note_flow[ins_ptr:ins_ptr] = note_flow[repeat_start:repeat_end_ptr]
                    break
            # end of for
        # end of while

        # Same note repeat
        no_repeat = False
        while not no_repeat:
            no_repeat = True
            for i, nt in enumerate(note_flow):
                if '*' in nt:
                    no_repeat = False
                    locate = nt.find('*')
                    note_flow[i] = nt[0:locate]
                    repeat_count = 0
                    if nt[locate + 1:].isdecimal():
                        repeat_count = int(nt[locate + 1:])
                    if repeat_count > 1:
                        for j in range(repeat_count - 1):
                            note_flow.insert(i + 1, nt[0:locate])
                    break
            # end of for
        # end of while

        return note_flow, len(note_flow)

    @staticmethod
    def __fill_omitted_dur_data(dur_text, note_num):
        dur_flow = []
        if ',' in dur_text:
            dur_flow = re.split('[,|]', dur_text.replace(' ', ''))
        else:
            # ','が無い場合、全体を一つの文字列にし、リストとして追加
            dur_flow.append(dur_text)

        no_repeat = False
        while not no_repeat:
            no_repeat = True
            repeat_start = 0
            first_bracket = False
            for i, dur in enumerate(dur_flow):  # <  >*n
                if '<' in dur:
                    no_repeat = False
                    locate = dur.find('<')
                    if locate == 0:
                        dur_flow[i] = dur[1:]
                        repeat_start = i
                        first_bracket = True
                elif '>' in dur:
                    re_cnt = dur.rfind('>')
                    dur_flow[i] = dur[0:re_cnt]
                    if dur[re_cnt + 1:re_cnt + 2] == '*' and first_bracket is True:
                        repeat_count = 0
                        if dur[re_cnt + 2:].isdecimal():
                            repeat_count = int(dur[re_cnt + 2:])
                        if repeat_count > 1:
                            repeat_end_ptr = i + 1
                            for j in range(repeat_count - 1):
                                ins_ptr = repeat_end_ptr + j * (repeat_end_ptr - repeat_start)
                                dur_flow[ins_ptr:ins_ptr] = dur_flow[repeat_start:repeat_end_ptr]
                    elif i + 1 == len(dur_flow) and first_bracket is True:
                        cntr = 0
                        while True:
                            dur_flow.append(dur_flow[repeat_start + cntr])
                            cntr += 1
                            if note_num <= len(dur_flow):
                                break
                    break
            # end of for
        # end of while

        dur_num = len(dur_flow)
        if dur_num < note_num:
            for _ in range(note_num - dur_num):
                dur_flow.append(dur_flow[dur_num - 1])  # 足りない要素を補填
        elif dur_num > note_num:
            del dur_flow[note_num:]  # 多い要素を削除
        return dur_flow

    @staticmethod
    def __fill_omitted_vel_data(vel_text, note_num):
        vel_flow = []
        if ',' in vel_text:
            vel_flow = re.split('[,|]', vel_text.replace(' ', ''))
        else:
            # ','が無い場合、全体を一つの文字列にし、リストとして追加
            vel_flow.append(vel_text)

        no_repeat = False
        while not no_repeat:
            no_repeat = True
            repeat_start = 0
            first_bracket = False
            for i, vel in enumerate(vel_flow):  # <  >*n
                if '<' in vel:
                    no_repeat = False
                    locate = vel.find('<')
                    if locate == 0:
                        vel_flow[i] = vel[1:]
                        repeat_start = i
                        first_bracket = True
                elif '>' in vel:
                    re_cnt = vel.rfind('>')
                    vel_flow[i] = vel[0:re_cnt]
                    if vel[re_cnt + 1:re_cnt + 2] == '*' and first_bracket is True:
                        repeat_count = 0
                        if vel[re_cnt + 2:].isdecimal():
                            repeat_count = int(vel[re_cnt + 2:])
                        if repeat_count > 1:
                            repeat_end_ptr = i + 1
                            for j in range(repeat_count - 1):
                                ins_ptr = repeat_end_ptr + j * (repeat_end_ptr - repeat_start)
                                vel_flow[ins_ptr:ins_ptr] = vel_flow[repeat_start:repeat_end_ptr]
                    elif i + 1 == len(vel_flow) and first_bracket is True:
                        cntr = 0
                        while True:
                            vel_flow.append(vel_flow[repeat_start + cntr])
                            cntr += 1
                            if note_num <= len(vel_flow):
                                break
                    break
            # end of for
        # end of while

        vel_num = len(vel_flow)
        if vel_num < note_num:
            for _ in range(note_num - vel_num):
                vel_flow.append(vel_flow[vel_num - 1])  # 足りない要素を補填
        return vel_flow

    def __change_basic_note_value(self, dur_text):
        # コロンで設定されている基本音価の調査し、変更があれば差し替え
        if ':' in dur_text:
            sp_txt = dur_text.split(':')
            base_note_text = '4'
            # 基本音価はコロンの前か後か？
            if (',' in sp_txt[0]) or ('(' and ')' in sp_txt[1]):
                dur_text = sp_txt[0]
                base_note_text = sp_txt[1]
            elif (',' in sp_txt[1]) or ('(' and ')' in sp_txt[0]):
                base_note_text = sp_txt[0]
                dur_text = sp_txt[1]
            elif sp_txt[0] == '':
                dur_text = '1'
                base_note_text = sp_txt[1]
            elif sp_txt[0].isdecimal() and sp_txt[1].isdecimal() and int(sp_txt[0]) < int(sp_txt[1]):
                dur_text = sp_txt[0]
                base_note_text = sp_txt[1]
            else:
                base_note_text = sp_txt[0]
                dur_text = sp_txt[1]

            if '(' and ')' in base_note_text:
                percent = re.findall("(?<=\().+?(?=\))", base_note_text)
                if '%' in percent[0]:
                    per = percent[0].strip('%')
                    if per.isdecimal() is True and int(per) <= 100:
                        self.durPer = int(per)  # % の数値
                elif percent[0] == 'stacc.':
                    self.durPer = 50
            dur_len = re.sub("\(.+?\)", "", base_note_text)
            if dur_len.isdecimal() is True:
                self.baseNote = int(dur_len)
            else:
                self.baseNote = 4
        return dur_text

    def __fill_omitted_data(self):
        # Note
        note_flow, note_num = self.__fill_omitted_note_data()

        # Duration
        dur_text = self.__change_basic_note_value(self.noteData[1])
        dur_flow = self.__fill_omitted_dur_data(dur_text, note_num)

        # Velocity
        vel_flow = self.__fill_omitted_vel_data(self.noteData[2], note_num)

        return note_flow, dur_flow, vel_flow, note_num

    def __cnv_note_to_pitch(self, note_text):
        nlists = note_text.replace(' ', '').split('=')  # 和音検出
        bpchs = []
        for nx in nlists:
            base_pitch = self.keynote + nlib.convert_doremi(nx)
            bpchs.append(base_pitch)
        return bpchs

    @staticmethod
    def __cnv_duration(dur_text):
        if dur_text.isdecimal() is True:
            return int(dur_text)
        else:
            return 1

    def convert_to_MIDI_like_format(self):
        if self.noteData[0] is None or len(self.noteData[0]) == 0:
            return 0, self.playData

        note_flow, dur_flow, vel_flow, note_num = self.__fill_omitted_data()
        tick = 0
        read_ptr = 0
        while read_ptr < note_num:
            cnts = self.__cnv_note_to_pitch(note_flow[read_ptr])
            dur = self.__cnv_duration(dur_flow[read_ptr])
            vel = nlib.convert_exp2vel(vel_flow[read_ptr])
            self.__add_note(tick, cnts, dur, vel)
            tick += dur * 480 * 4 / self.baseNote
            read_ptr += 1  # out from repeat

        return tick, self.playData
