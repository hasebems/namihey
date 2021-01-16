# -*- coding: utf-8 -*-
import  random


DEFAULT_WHOLE_TICK = 1920.0


class PatternGenerator():

    def __init__(self, pattern, key, func):
        self.sqdata = []
        self.description = pattern
        self.keynote = key
        self.__midi_handler = func
        self.__state_play = False
        self.__current_tick = 0
        self.__next_tick = 0
        self.__event_counter = 0
        self.__last_note = 60

    def convertToMIDILikeFormat(self):
        if self.description[0] == None or len(self.description[0]) == 0:
            return 0, self.sqdata
        return DEFAULT_WHOLE_TICK, self.sqdata

    def play(self):
        self.__state_play = True
        self.__event_counter = 0
        return self.generate_random(0)

    def return_to_top(self):
        self.__event_counter = 0
        return DEFAULT_WHOLE_TICK

    def generate_random(self, tick):
        current_tick = self.__next_tick
        if tick > current_tick:
            if current_tick%240 == 0:
                note = random.randint(48,72)
                self.__midi_handler(note,127)
                self.__last_note = note
            else:
                self.__midi_handler(self.__last_note,0)
            self.__event_counter += 1
            if current_tick+120 < DEFAULT_WHOLE_TICK:
                self.__next_tick = current_tick+120
            else:
                self.__next_tick = 0
                return DEFAULT_WHOLE_TICK
        return self.__next_tick

    def stop(self):
        self.__state_play = False
