# -*- coding: utf-8 -*-
import  random


DEFAULT_WHOLE_TICK = 1920.0


class PatternGenerator():

    def __init__(self, pattern, key, func):
        self.sqdata = []
        self.description = pattern
        self.keynote = key
        self.__whole_tick = DEFAULT_WHOLE_TICK
        self.__midi_handler = func
        self.__state_play = False
        self.__current_tick = 0
        self.__next_tick = 0
        self.__event_counter = 0
        self.__last_note = 60

    def convertToMIDILikeFormat(self):
        if self.description[0] == None or len(self.description[0]) == 0:
            return 0, self.sqdata
        return self.__whole_tick, self.sqdata

    def __generate_rnd_pattern(self):
        crnt_tick = self.__next_tick
        if crnt_tick%240 == 0:
            note = random.randint(48,72)
            self.__midi_handler(note,127)
            self.__last_note = note
            crnt_tick += 100
            if self.__event_counter >= 16: print("something wrong!")
        else:
            self.__midi_handler(self.__last_note,0)
            crnt_tick += 140
        self.__event_counter += 1

        if crnt_tick >= self.__whole_tick:
            return -1, self.__whole_tick
        else:
            return crnt_tick, crnt_tick

    def play(self):
        self.__state_play = True
        self.__event_counter = 0
        return self.generate_random(0)

    def return_to_top(self):
        self.__event_counter = 0
        self.__next_tick = 0
        return self.__whole_tick

    def generate_random(self, tick):
        rtn_value = self.__next_tick
        if tick >= self.__next_tick:
            if tick >= self.__whole_tick:
                return -1
            rtn_value, self.__next_tick = self.__generate_rnd_pattern()
        return rtn_value

    def stop(self):
        self.__state_play = False
