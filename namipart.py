# -*- coding: utf-8 -*-
import namirandom as nrnd
import namiptgen as nptgen


DEFAULT_NOTE_NUMBER = 60


class Part:
    #   Part 単位で、演奏情報を保持
    #   演奏時に、適切なタイミングで MIDI データを出力
    def __init__(self, blk, partNum):
        self.description = [None for _ in range(4)]
        self.retained_note = []
        self.parent_block = blk
        self.midich = partNum
        self.whole_tick = 0             # a length of whole tick that needs to play
        self.state_play = False         # during Playing
        self.state_reserv = False       # Change Phrase at next loop top 
        self.keynote = DEFAULT_NOTE_NUMBER
        self.is_onebyone = False
        self.rnd = nrnd.RandomGenerator(DEFAULT_NOTE_NUMBER, self._send_midi_note)
        self.ptgen = nptgen.PartGenPlay(self._send_midi_note)

    def _send_midi_note(self, nt, vel):
        if nt > 127 or vel > 127: return
        self.parent_block.sendMidiNote(self.midich, nt, vel)
        # stop 時に直ちに Note Off を出すため、現在 Note On 中の音を保持しておく
        if vel != 0:
            self.retained_note.append(nt)
        elif nt in self.retained_note:
            self.retained_note.remove(nt)

    def _generate_sequence(self):
        seqType = self.description[0]
        if seqType == 'phrase':
            self.whole_tick = self.ptgen.set_phrase(self.description[1:], self.keynote)
            self.is_onebyone = False
        elif seqType == 'random':
            self.whole_tick = self.rnd.set_random(self.description[1:], self.keynote)
            self.is_onebyone = True

    # Settings IF
    def changeKeynote(self, nt):
        self.keynote = nt
        if self.state_play == True:
            self.state_reserv = True
        else:
            self._generate_sequence()

    # Data Input IF
    def clear_description(self):
        for nt in self.retained_note:
            self._send_midi_note(nt, 0)
        if self.is_onebyone:
            self.rnd.stop()
        self.description= [None for _ in range(4)]

    # Data Input IF
    def add_seq_description(self, data):
        self.description = data
        if self.state_play == True:
            self.state_reserv = True
        else:
            self._generate_sequence()
        return self.whole_tick

    # Sequence Control IF
    def start(self):
        self.state_play = True
        if not self.is_onebyone:
            self.ptgen.start()
        else:
            self.rnd.start()

    # Sequence Control IF
    def return_to_top(self, tick_for_one_measure):        # Phrase sequence return to top during playing 
        if self.state_reserv == True:
            self._generate_sequence()
            self.state_reserv = False
        if not self.is_onebyone:
            return self.ptgen.return_to_top()
        else:
            return self.rnd.return_to_top(tick_for_one_measure)

    # Sequence Control IF
    def generate_event(self, tick):
        if not self.is_onebyone:
            return self.ptgen.generate_event(tick)
        else:
            return self.rnd.generate_random(tick)

    # Sequence Control IF
    def stop(self):
        for nt in self.retained_note:
            self._send_midi_note(nt, 0)
        self.state_play = False
        if not self.is_onebyone:
            self.ptgen.stop()
        else:
            self.rnd.stop()
