# -*- coding: utf-8 -*-
import copy
#import namipattern
import namiptgen as nptgen


DEFAULT_NOTE_NUMBER = 60


class Part:
    #   Part 単位で、演奏情報を保持
    #   演奏時に、適切なタイミングで MIDI データを出力
    def __init__(self, blk, part_num):
        self.description = [None for _ in range(4)]
        self.retained_note = []
        self.blk = blk
        self.midich = part_num
        self.whole_tick = 0             # a length of whole tick that needs to play
        self.state_play = False         # during Playing
        self.state_reserve = False       # Change Phrase at next loop top
        self.keynote = DEFAULT_NOTE_NUMBER
        self.volume = 100
        self.ptgen = nptgen.PartGenPlay(self._send_midi_note)

    def _send_midi_note(self, nt, vel):
        if nt > 127 or vel > 127: return
        self.blk.midi().send_midi_note(self.midich, nt, vel)
        # stop 時に直ちに Note Off を出すため、現在 Note On 中の音を保持しておく
        if vel != 0:
            self.retained_note.append(nt)
        elif nt in self.retained_note:
            self.retained_note.remove(nt)

    def _generate_sequence(self):
        seq_type = self.description[0]
        if seq_type == 'phrase':
            self.whole_tick = self.ptgen.set_phrase(self.description[1:], self.keynote)

    # Settings IF
    def change_keynote(self, nt):
        self.keynote = nt
        if self.state_play:
            self.state_reserve = True
        else:
            self._generate_sequence()

    # Controller IF
    def change_cc(self, cc_num, val):
        if val >= 0 and val < 128:
            self.volume = val
            self.blk.midi().send_control(self.midich, cc_num, val)

    # Data Input IF
    def clear_description(self):
        self.add_seq_description(['phrase',None,None,None])

    # Data Input IF
    def add_seq_description(self, data):
        self.description = data
        if self.state_play:
            self.state_reserve = True
        else:
            self._generate_sequence()

    # Sequence Control IF
    def start(self):
        self.state_play = True
        self.ptgen.start()

    # Sequence Control IF
    def return_to_top(self, tick_for_one_measure):
        # Phrase sequence return to top during playing 
        part_tick = 0
        if self.state_reserve:
            self._generate_sequence()
            self.state_reserve = False
        part_tick = self.ptgen.return_to_top()
        return part_tick

    # Sequence Control IF
    def generate_event(self, tick):
        return self.ptgen.generate_event(tick)

    # Sequence Control IF
    def stop(self):
        all_ntof = copy.deepcopy(self.retained_note)
        for nt in all_ntof:
            self._send_midi_note(nt, 0)
        self.state_play = False
        self.ptgen.stop()

