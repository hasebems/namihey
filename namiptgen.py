# -*- coding: utf-8 -*-
import namiphrase as nph


class PartGenPlay:

    def __init__(self, func):
        self.midi_handler = func
        self.sqdata = []
        self.play_counter = 0
        self.whole_tick = 0             # a length of whole tick that needs to play
        self.state_play = False

    def set_phrase(self, description, keynote):
        pg = nph.PhraseGenerator(description, keynote)
        self.whole_tick, self.sqdata = pg.convert_to_MIDI_like_format()
        return self.whole_tick

    def generate_event(self, tick):
        max_ev = len(self.sqdata)
        if max_ev == 0:
            # データを持っていない
            return -1

        if tick == 0:
            self.play_counter = 0

        trace = self.play_counter
        next_tick = 0
        while True:
            if max_ev <= trace:
                next_tick = -1   # means sequence finished
                break
            next_tick = self.sqdata[trace][0]
            if next_tick < tick:
                nt = self.sqdata[trace][1]
                vel = self.sqdata[trace][2]
                self.midi_handler(nt, vel)
            else:
                break
            trace += 1

        self.play_counter = trace
        return next_tick

    def start(self):
        self.play_counter = 0
        self.state_play = True
        self.generate_event(0)

    def return_to_top(self):
        self.play_counter = 0
        return self.whole_tick

    def stop(self):
        self.state_play = False
