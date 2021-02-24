# -*- coding: utf-8 -*-
import  random
import  re


DEFAULT_WHOLE_TICK = 1920.0
CHORD_SCALE = {
    'all':[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23],
    '_':[0,4,7,12,16,19],
    '_m':[0,3,7,12,15,19],
    '_7':[0,4,7,10,12,16,19,22],
    '_6':[0,4,7,9,12,16,19,21],
    '_m7':[0,3,7,10,12,15,19,22],
    '_M7':[0,4,7,11,12,16,19,23],
    '_maj7':[0,4,7,11,12,16,19,23],
    '_9':[0,2,4,7,10,12,14,19,22],
    '_m9':[0,2,3,7,10,12,14,15,19,22],
    '_M9':[0,2,4,7,11,12,14,19,23],
    '_maj9':[0,2,4,7,11,12,14,19,23],
    '_+5':[0,4,8,12,16,20],
    '_aug':[0,4,8,12,16,20],
    '_7+5':[0,4,8,10,12,16,20,22],
    '_aug7':[0,4,8,10,12,16,20,22],
    '_7-9':[0,1,4,7,10,12,13,16,19,22],
    '_7+9':[0,3,4,7,10,12,15,16,19,22],
    '_dim':[0,3,6,9,12,15,18,21],
    '_m7-5':[0,3,6,10,12,15,18,20],
    'diatonic':[0,2,4,5,7,9,11,12,14,16,17,19,21],
    'dorian':[0,2,3,5,7,9,10,12,14,15,17,19,21,22],
    'lydian':[0,2,4,6,7,9,11,12,14,16,18,19,21,23],
    'mixolydian':[0,2,4,5,7,9,10,12,14,16,17,19,21,22],
    'aeolian':[0,2,3,5,7,8,10,12,14,15,17,19,20,22]
}

DURATION = {
    1:[1920,100],
    2:[960,100],
    3:[640,100],
    4:[480,100],
    6:[320,100],
    8:[240,100],
    9:[213,100],
    12:[160,100],
    16:[120,100],
    24:[80,100],
    32:[60,100],
}


class RandomGenerator():

    def __init__(self, key, func):
        self.description = []
        self.keynote = key
        self.whole_tick = DEFAULT_WHOLE_TICK
        self.midi_handler = func
        self.state_play = False
        self.next_tick = 0
        self.event_counter = 0
        self.measure_counter = -1
        self.last_note = 0
        self.chord_flow = []
        self.chord_flow_next = []
        self.rnd_type = 0
        self.rnd_dur = 8
        self.note_reso = 240

    def set_random(self, pattern, key):
        self.description = pattern
        self.keynote = key
        self._makeRandomParameter()

    def _makeRandomParameter(self):
        chord_flow = self.description[0].split(':')
        if '(' and ')' in chord_flow[0]:
            # check inside ()
            inside = re.findall("(?<=\().+?(?=\))", chord_flow[0])
            prms = inside[0].split(',')
            for prm in prms:
                elm = prm.strip().split('=')
                if elm[0] == 'type':
                    self.rnd_type = elm[1]
                elif elm[0] == 'dur':
                    self.rnd_dur = elm[1]
        if len(chord_flow) >= 2:
            self.chord_flow_next = chord_flow[1].strip().split(',')
        else:
            # if no ':', set 'all" pattern
            self.chord_flow_next.append('all')

    def _detect_note_number(self):
        # detect random chord array
        chord = self.chord_flow[self.measure_counter]
        root = 0
        if str.isdecimal(chord[0:1]):
            root = int(chord[0:1])
            chord = '_' + chord[1:]
        doremi_set = CHORD_SCALE.get(chord, CHORD_SCALE['all'])

        while True:
            idx = random.randint(0,len(doremi_set)-1)
            note = doremi_set[idx]+48+root-1
            if note != self.last_note:  # don't decide same note as last note
                break
        self.midi_handler(note,100)
        self.last_note = note
        if self.event_counter >= 16: print("something wrong!")

    def _generate_rnd_pattern(self):
        crnt_tick = self.next_tick
        if self.measure_counter == -1:
            return -1, self.whole_tick

        if crnt_tick%self.note_reso == 0:
            self._detect_note_number()
            crnt_tick += abs(self.note_reso*2/5)
        else:
            self.midi_handler(self.last_note,0)
            crnt_tick += self.note_reso - abs(self.note_reso*2/5)
        self.event_counter += 1

        if crnt_tick >= self.whole_tick:
            return -1, self.whole_tick
        else:
            return crnt_tick, crnt_tick

    def start(self):
        self.state_play = True
        self.event_counter = 0
        self.chord_flow = self.chord_flow_next
        if self.chord_flow != []:
            self.measure_counter = 0
        return self.generate_random(0)

    def return_to_top(self):
        self.event_counter = 0
        self.next_tick = 0
        self.chord_flow = self.chord_flow_next
        if self.chord_flow == []:
            self.measure_counter = -1
        else:
            self.measure_counter += 1
            if len(self.chord_flow) <= self.measure_counter:
                self.measure_counter = 0
        return self.whole_tick

    def generate_random(self, tick):
        rtn_value = self.next_tick
        if tick >= self.next_tick:
            if tick >= self.whole_tick:
                return -1
            rtn_value, self.next_tick = self._generate_rnd_pattern()
        return rtn_value

    def stop(self):
        self.state_play = False
