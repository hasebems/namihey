# -*- coding: utf-8 -*-
import random
import re
import namilib as nlib

class RandomGenerator():

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
        self.rnd_type = 0
        self.rnd_dur = 8
        self.measure_flow = []
        self.velocity_flow = []

    def set_random(self, pattern, key):
        self.description = pattern
        self.keynote = key
        self._analyse_random_parameter()
        return self.max_measure_num * self.tick_for_one_measure

    def _analyse_chord_param(self, chord_description):
        chord_flow = chord_description.split(':')
        if '(' and ')' in chord_flow[0]:
            # check inside ()
            inside = re.findall("(?<=\().+?(?=\))", chord_flow[0])
            prms = inside[0].split(',')
            for prm in prms:
                elm = prm.strip().split('=')
                if elm[0] == 'type':
                    self.rnd_type = elm[1]
                elif elm[0] == 'dur':
                    if elm[1].isdecimal() == True:
                        self.rnd_dur = int(elm[1])
        if len(chord_flow) >= 2:
            self.chord_flow_next = chord_flow[1].strip().split(',') # chord
        else:
            # if no ':', set 'all" pattern
            self.chord_flow_next = ['all']

    def _analyse_measure_param(self, measure_description):
        if measure_description != None:
            self.measure_flow = measure_description.strip().split(',')
            for i, mes in enumerate(self.measure_flow):
                if mes.isdecimal():
                    self.measure_flow[i] = int(mes)
                else:
                    self.measure_flow[i] = 1
            if len(self.measure_flow) > len(self.chord_flow_next):
                del self.measure_flow[len(self.chord_flow_next):]
            elif len(self.measure_flow) < len(self.chord_flow_next):
                ext = [self.measure_flow[-1] for i in range(len(self.chord_flow_next)-len(self.measure_flow))]
                self.measure_flow += ext
        else:
            self.measure_flow = [1 for i in range(len(self.chord_flow_next))]
        self.max_measure_num = sum(self.measure_flow)

    def _analyse_velocity_param(self, velocity_description):
        if velocity_description != None:
            self.velocity_flow = velocity_description.strip().split(',')
            for i, mes in enumerate(self.velocity_flow):
                self.velocity_flow[i] = nlib.convert_exp2vel(self.velocity_flow[i])
            if len(self.velocity_flow) > len(self.chord_flow_next):
                del self.velocity_flow[len(self.chord_flow_next):]
            elif len(self.velocity_flow) < len(self.chord_flow_next):
                ext = [self.velocity_flow[-1] for i in range(len(self.chord_flow_next)-len(self.velocity_flow))]
                self.velocity_flow += ext
        else:
            self.velocity_flow = [100 for i in range(len(self.chord_flow_next))]

    def _analyse_random_parameter(self):
        self._analyse_chord_param(self.description[0])
        self._analyse_measure_param(self.description[1])
        self._analyse_velocity_param(self.description[2])

    def _detect_locate(self, tick):
        current_num = int(tick/self.tick_for_one_measure)
        compare_num = 0
        index_locate = 0
        while True:
            compare_num += self.measure_flow[index_locate]
            if current_num < compare_num: break
            index_locate += 1
        return index_locate

    def _detect_note_number(self, tick):
        # detect random chord array
        index_number = self._detect_locate(tick)
        chord = self.chord_flow[index_number]
        root = 0
        if chord[0:1].isdecimal() == True or chord[0:1] == '+' or chord[0:1] == '-':
            diatonic = [0,0,2,4,5,7,9,11,12,2]
            if chord[0:1] == '+':
                root = diatonic[int(chord[1:2])] + 1
            elif chord[0:1] == '-':
                root = diatonic[int(chord[1:2])] - 1
            else:
                root = diatonic[int(chord[0:1])]
            chord = '_' + chord[1:]
        doremi_set = nlib.CHORD_SCALE.get(chord, nlib.CHORD_SCALE['all'])

        while True:
            idx = random.randint(0,len(doremi_set)-1)
            note = doremi_set[idx] + self.keynote + root
            if note != self.last_note:  # don't decide same note as last note
                break
        self.midi_handler(note,self.velocity_flow[index_number])
        self.last_note = note
        # if self.event_counter >= 16: print("something wrong!")

    def _generate_rnd_pattern(self):
        whole_tick = self.max_measure_num * self.tick_for_one_measure
        crnt_tick = self.next_tick
        if self.chord_flow == []:
            return -1, whole_tick

        tick_reso = round(nlib.DEFAULT_TICK_FOR_ONE_MEASURE/self.rnd_dur,0)
        if crnt_tick%tick_reso == 0:    # Note On
            self._detect_note_number(crnt_tick)
            crnt_tick += round(tick_reso/2,0)-20
        else:                           # Note Off
            self.midi_handler(self.last_note,0)
            crnt_tick += tick_reso-round(tick_reso/2,0)+20
        self.event_counter += 1

        if crnt_tick >= whole_tick:
            return -1, whole_tick
        else:
            return crnt_tick, crnt_tick

    def start(self):
        self.state_play = True
        self.event_counter = 0
        self.chord_flow = self.chord_flow_next
        return self.generate_random(0)

    def return_to_top(self, tick_for_one_measure):
        self.event_counter = 0
        self.next_tick = 0
        self.tick_for_one_measure = tick_for_one_measure
        if self.chord_flow_next != []:
            self.chord_flow = self.chord_flow_next
        return self.max_measure_num * self.tick_for_one_measure

    def generate_random(self, tick):
        rtn_value = self.next_tick
        if tick >= self.next_tick:
            if tick >= self.max_measure_num * self.tick_for_one_measure:
                return -1
            rtn_value, self.next_tick = self._generate_rnd_pattern()
        return rtn_value

    def stop(self):
        self.state_play = False
