# -*- coding: utf-8 -*-
import random
import re
import namilib as nlib

NOTE_OFF_MARGIN = 20


class RandomGenerator:

    def __init__(self, key, func):
        self.description = []
        self.keynote = key
        self.tick_for_one_measure = 0
        self.midi_handler = func
        self.state_play = False
        self.next_tick = 0
        self.event_counter = 0
        self.max_measure_num = 0        # No Data
        self.last_note = 0
        self.chord_flow = []
        self.chord_flow_next = []
        self.rnd_rgn = 12
        self.rnd_ofs = 0
        self.rnd_dur = 8
        self.measure_flow = []      # 各 Pattern の小節数
        self.velocity_flow = []     # 各 Pattern のベロシティ

    def set_random(self, pattern, key):
        self.description = pattern
        self.keynote = key
        self._analyse_random_braces()
        return self.max_measure_num * self.tick_for_one_measure

    def _analyse_chord_brace(self, chord_description):
        chord_flow = chord_description.split(':')
        if '(' and ')' in chord_flow[0]:
            # check inside ()
            inside = re.findall("(?<=\().+?(?=\))", chord_flow[0])
            prms = inside[0].split(',')
            for prm in prms:
                elm = prm.strip().split('=')
                if elm[1].isdecimal():
                    value = int(elm[1])
                    if elm[0] == 'rgn':
                        if value < 1: value = 1
                        elif value > 12: value = 12
                        self.rnd_rgn = value
                    elif elm[0] == 'ofs':
                        if value < 0: value = 0
                        elif value > 11: value = 11
                        self.rnd_ofs = value
                    elif elm[0] == 'dur':
                        self.rnd_dur = value
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

    def _analyse_random_braces(self):
        self._analyse_chord_brace(self.description[0])
        self._analyse_measure_brace(self.description[1])
        self._analyse_velocity_brace(self.description[2])

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
        dtbl = nlib.CHORD_SCALE['diatonic']
        doremi_set = nlib.CHORD_SCALE.get(chord)
        if doremi_set is None:
            l1 = chord[0:1]     # 最初の一文字
            l2 = chord[1:2]     # 最初から二文字目
            if l1.isdecimal():
                root = dtbl[len(dtbl)//2+int(l1)-1]
            elif l1 == '+' and l2.isdecimal():
                root = dtbl[len(dtbl)//2+int(l2)-1] + 1
            elif l1 == '-' and l2.isdecimal():
                root = dtbl[len(dtbl)//2+int(l2)-1] - 1
            else:
                root = nlib.convert_doremi(chord)
            chord = '_' + chord[1:]
            doremi_set = nlib.CHORD_SCALE.get(chord, dtbl)
        return root, doremi_set

    def _detect_index(self, root, doremi_set):
        min_doremi = self.rnd_ofs - self.rnd_rgn - root
        start_idx = len(doremi_set)-1
        while doremi_set[start_idx] > min_doremi: start_idx -= 1
        max_doremi = self.rnd_ofs + self.rnd_rgn - root
        end_idx = 0
        while doremi_set[end_idx] < max_doremi: end_idx += 1
        return start_idx, end_idx

    def _detect_note_number(self, tick):
        # detect random chord array
        measure_num = self._detect_locate(tick)
        chord = self.chord_flow[measure_num]
        root, doremi_set = self._detect_chord_scale(chord)

        # Random の Index値を作るための最小値、最大値を算出
        start_idx, end_idx = self._detect_index(root, doremi_set)

        # Random な Index値を発生させて、Tableからノート番号を読み出す 
        while True:
            idx = random.randint(start_idx, end_idx)
            note = doremi_set[idx] + self.keynote + root
            if note != self.last_note:  # don't decide same note as last note
                break
        return note, self.velocity_flow[measure_num]
        # if self.event_counter >= 16: print("something wrong!")

    def _generate_rnd_pattern(self):
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
        if crnt_tick_for_one_measure % tick_reso == 0:    # Note On
            note, vel = self._detect_note_number(crnt_tick)
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

    def start(self):
        self.state_play = True
        self.event_counter = 0
        self.next_tick = 0
        self.chord_flow = self.chord_flow_next
        return self.generate_random(0)

    def return_to_top(self, tick_for_one_measure):
        self.event_counter = 0
        self.next_tick = 0
        self.tick_for_one_measure = tick_for_one_measure
        if self.chord_flow_next:
            self.chord_flow = self.chord_flow_next
        return self.max_measure_num * self.tick_for_one_measure

    def generate_random(self, tick):
        if tick >= self.next_tick:
            rtn_value = self._generate_rnd_pattern()
        else:
            rtn_value = self.next_tick
        return rtn_value

    def stop(self):
        self.state_play = False
