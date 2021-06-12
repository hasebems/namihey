# -*- coding: utf-8 -*-
import random
import re
import namilib as nlib

NOTE_OFF_MARGIN = 20

class PatternGenerator:

    def __init__(self, key, func):
        self.description = []
        self.keynote = key
        self.tick_for_one_measure = 0
        self.midi_handler = func
        self.state_play = False
        self.random_ptn = True
        self.next_tick = 0
        self.event_counter = 0
        self.max_measure_num = 0        # No Data
        self.last_note = 0
        self.chord_flow = []
        self.chord_flow_next = []
        self.rnd_rgn = 12
        self.rnd_ofs = 0
        self.rnd_dur = 8
        self.arp_type = 'sawup'
        self.measure_flow = []      # 各 Pattern の小節数
        self.velocity_flow = []     # 各 Pattern のベロシティ

    def _analyse_chord_brace(self, chord_description):
        chord_flow = chord_description.split(':')
        if '(' and ')' in chord_flow[0]:
            # check inside ()
            inside = re.findall("(?<=\().+?(?=\))", chord_flow[0])
            prms = inside[0].split(',')
            for prm in prms:
                elm = prm.strip().split('=')
                if len(elm) < 2:
                    break
                if elm[1].isdecimal():
                    value = int(elm[1])
                    if elm[0] == 'rgn' and self.random_ptn:
                        if value < 1: value = 1
                        elif value > 12: value = 12
                        self.rnd_rgn = value
                    elif elm[0] == 'ofs':
                        if value < 0: value = 0
                        elif value > 11: value = 11
                        self.rnd_ofs = value
                    elif elm[0] == 'dur':
                        self.rnd_dur = value
                elif elm[0] == 'ptn' and not self.random_ptn:
                    self.arp_type = elm[1]
        if len(chord_flow) >= 2:
            self.chord_flow_next = chord_flow[1].strip().split(',') # chord
        else:
            # if no ':', set 'all" pattern
            self.chord_flow_next = ['all']

    def _analyse_measure_brace(self, measure_description):
        if measure_description is not None:
            self.measure_flow = measure_description.strip().split(',')
            for i, mes in enumerate(self.measure_flow):
                if mes.isdecimal():
                    self.measure_flow[i] = int(mes)
                else:
                    self.measure_flow[i] = 1
            if len(self.measure_flow) > len(self.chord_flow_next):
                del self.measure_flow[len(self.chord_flow_next):]
            elif len(self.measure_flow) < len(self.chord_flow_next):
                ext = [self.measure_flow[-1] for _ in range(len(self.chord_flow_next)-len(self.measure_flow))]
                self.measure_flow += ext
        else:
            self.measure_flow = [1 for _ in range(len(self.chord_flow_next))]
        self.max_measure_num = sum(self.measure_flow)

    def _analyse_velocity_brace(self, velocity_description):
        if velocity_description is not None:
            self.velocity_flow = velocity_description.strip().split(',')
            for i, mes in enumerate(self.velocity_flow):
                self.velocity_flow[i] = nlib.convert_exp2vel(self.velocity_flow[i])
            if len(self.velocity_flow) > len(self.chord_flow_next):
                del self.velocity_flow[len(self.chord_flow_next):]
            elif len(self.velocity_flow) < len(self.chord_flow_next):
                ext = [self.velocity_flow[-1] for _ in range(len(self.chord_flow_next)-len(self.velocity_flow))]
                self.velocity_flow += ext
        else:
            self.velocity_flow = [100 for _ in range(len(self.chord_flow_next))]

    def _analyse_ptn_braces(self, pattern, key):
        self.description = pattern
        self.keynote = key
        self._analyse_chord_brace(self.description[0])
        self._analyse_measure_brace(self.description[1])
        self._analyse_velocity_brace(self.description[2])
        return self.max_measure_num * self.tick_for_one_measure

    def _detect_locate(self, tick):
        current_num = int(tick/self.tick_for_one_measure)
        compare_num = 0
        index_locate = 0
        while True:
            compare_num += self.measure_flow[index_locate]
            if current_num < compare_num: break
            index_locate += 1
        return index_locate

    def _detect_chord_scale(self, chord):
        root = 0
        letter = chord[0]
        dtbl = nlib.CHORD_SCALE['diatonic']
        if letter == 'I' or letter == 'V':
            root_cnt = 0
            root_str = ''
            while letter == 'I' or letter == 'V':
                root_str += letter
                root_cnt += 1
                if len(chord) > root_cnt:
                    letter = chord[root_cnt]
                else:
                    break
            # #/b のチェック
            if letter == '#':
                root += 1
                root_cnt += 1
            elif letter == 'b':
                root -= 1
                root_cnt += 1
            # ローマ数字の文字列から root を求める
            try:
                ofs = nlib.ROOT_NAME.index(root_str)
                root += dtbl[len(dtbl)//2+ofs]
            except ValueError as error:
                root = 0
            
            if len(chord) > root_cnt:
                chord = '_' + chord[root_cnt:]
            else:
                chord = '_'

        chord_scale_tbl = nlib.CHORD_SCALE.get(chord, dtbl)
        return root, chord_scale_tbl

    def _detect_index_rnd(self, root, tbl):
        min_doremi = self.rnd_ofs - self.rnd_rgn - root
        start_idx = len(tbl)-1
        while tbl[start_idx] > min_doremi: start_idx -= 1
        max_doremi = self.rnd_ofs + self.rnd_rgn - root
        end_idx = 0
        while tbl[end_idx] < max_doremi: end_idx += 1
        return start_idx, end_idx

    def _detect_index_arp(self, root, tbl):
        # root より小さい、最も近い note を探す
        min_doremi = self.rnd_ofs - root
        start_idx = len(tbl)-1
        while tbl[start_idx] > min_doremi: start_idx -= 1
        return start_idx

    def _detect_note_number(self, measure_num, tick, reso):
        # detect random chord array
        chord = self.chord_flow[measure_num]
        root, chord_scale_tbl = self._detect_chord_scale(chord)

        if self.random_ptn == True:  # Random の場合
            # Random の Index値を作るための最小値、最大値を算出
            start_idx, end_idx = self._detect_index_rnd(root, chord_scale_tbl)

            # Random な Index値を発生させて、Tableからノート番号を読み出す 
            while True:
                idx = random.randint(start_idx, end_idx)
                note = chord_scale_tbl[idx] + self.keynote + root
                if note != self.last_note:  # don't decide same note as last note
                    break
            return note
            # if self.event_counter >= 16: print("something wrong!")

        else:   # Arpeggio の場合
            interval = nlib.DEFAULT_TICK_FOR_ONE_MEASURE//2 if reso >= 240 else nlib.DEFAULT_TICK_FOR_ONE_MEASURE//4
            if self.arp_type == 'tridwn':
                if (tick//interval)%2 == 0:
                    arp_count = int((interval-(tick%interval))//reso)
                else:
                    arp_count = int((tick%interval)//reso)
            elif self.arp_type == 'triup':
                if (tick//interval)%2 == 0:
                    arp_count = int((tick%interval)//reso)
                else:
                    arp_count = int((interval-(tick%interval))//reso)
            elif self.arp_type == 'sawdwn':
                arp_count = int((interval-(tick%interval))//reso) - 1
            else: # 'sawup' or others
                arp_count = int((tick%interval)//reso)
            start_idx = self._detect_index_arp(root, chord_scale_tbl)
            return chord_scale_tbl[start_idx+arp_count] + self.keynote + root

    def _generate_pattern_note(self):
        # print(self.next_tick)
        whole_tick = self.max_measure_num * self.tick_for_one_measure
        if not self.chord_flow:
            # Data がない場合
            self.next_tick = whole_tick
            return nlib.END_OF_DATA
        if self.next_tick >= whole_tick:
            return nlib.END_OF_DATA

        crnt_tick = self.next_tick                                              # 全体 Loop Size 中の tick
        crnt_tick_for_one_measure = crnt_tick % self.tick_for_one_measure       # １小節内の tick
        tick_reso = round(nlib.DEFAULT_TICK_FOR_ONE_MEASURE/self.rnd_dur, 0)    # 音価
        if crnt_tick_for_one_measure % tick_reso == 0:
            # Note On
            measure_num = self._detect_locate(crnt_tick)
            note = self._detect_note_number(measure_num, crnt_tick, tick_reso)
            vel = self.velocity_flow[measure_num]
            self.midi_handler(note, vel)
            self.last_note = note
            if self.tick_for_one_measure - crnt_tick_for_one_measure < tick_reso:
                # 小節最後の音符で、小節の残りが音価以下だったら
                crnt_tick += self.tick_for_one_measure - crnt_tick_for_one_measure - NOTE_OFF_MARGIN
            else:
                crnt_tick += tick_reso - NOTE_OFF_MARGIN
        else:                           # Note Off
            self.midi_handler(self.last_note, 0)
            crnt_tick += NOTE_OFF_MARGIN
        self.event_counter += 1

        if crnt_tick >= whole_tick:
            # Block の Loop Size を越えたとき 
            self.next_tick = whole_tick
            return nlib.END_OF_DATA
        else:
            self.next_tick = crnt_tick
            return crnt_tick

    # Public
    def set_random(self, pattern, key):
        self.random_ptn = True
        return self._analyse_ptn_braces(pattern, key)

    def set_arp(self, pattern, key):
        self.random_ptn = False
        return self._analyse_ptn_braces(pattern, key)

    def start(self):
        self.state_play = True
        self.event_counter = 0
        self.next_tick = 0
        self.chord_flow = self.chord_flow_next
        return self.generate_pattern(0)

    def return_to_top(self, tick_for_one_measure):
        self.event_counter = 0
        self.next_tick = 0
        self.tick_for_one_measure = tick_for_one_measure
        if self.chord_flow_next:
            self.chord_flow = self.chord_flow_next
        return self.max_measure_num * self.tick_for_one_measure

    def generate_pattern(self, tick):
        if tick >= self.next_tick:
            rtn_value = self._generate_pattern_note()
        else:
            rtn_value = self.next_tick
        return rtn_value

    def stop(self):
        self.state_play = False
