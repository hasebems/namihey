# -*- coding: utf-8 -*-
import  random


DEFAULT_WHOLE_TICK = 1920.0


class PatternGenerator():

    def __init__(self, pattern, key, func):
        self.sqdata = []
        self.description = pattern
        self.keynote = key
        self.whole_tick = DEFAULT_WHOLE_TICK
        self.midi_handler = func
        self.state_play = False
        self.next_tick = 0
        self.event_counter = 0
        self.last_note = 60

    def convertToMIDILikeFormat(self):
        if self.description[0] == None or len(self.description[0]) == 0:
            return 0, self.sqdata
        return self.whole_tick, self.sqdata

    def _generate_rnd_pattern(self):
        crnt_tick = self.next_tick
        if crnt_tick%240 == 0:
            note = random.randint(48,72)
            self.midi_handler(note,127)
            self.last_note = note
            crnt_tick += 100
            if self.event_counter >= 16: print("something wrong!")
        else:
            self.midi_handler(self.last_note,0)
            crnt_tick += 140
        self.event_counter += 1

        if crnt_tick >= self.whole_tick:
            return -1, self.whole_tick
        else:
            return crnt_tick, crnt_tick

    def play(self):
        self.state_play = True
        self.event_counter = 0
        return self.generate_random(0)

    def return_to_top(self):
        self.event_counter = 0
        self.next_tick = 0
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
