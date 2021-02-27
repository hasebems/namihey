# -*- coding: utf-8 -*-
import namiphrase as nph
import namirandom as nrnd


DEFAULT_NOTE_NUMBER = 60


class Part:
    #   Part 単位で、演奏情報を保持
    #   演奏時に、適切なタイミングで MIDI データを出力
    def __init__(self, blk, partNum):
        self.description = [None for _ in range(4)]
        self.sqdata = []
        self.retained_note = []
        self.play_counter = 0
        self.parent_block = blk
        self.midich = partNum
        self.whole_tick = 0          # a length of whole tick that needs to play
        self.state_play = False      # during Playing
        self.state_reserv = False      # Change Phrase at next loop top 
        self.keynote = DEFAULT_NOTE_NUMBER
        self.is_random = False
        self.rnd = nrnd.RandomGenerator(DEFAULT_NOTE_NUMBER, self._send_midi_note)

    def _send_midi_note(self, nt, vel):
        self.parent_block.sendMidiNote(self.midich, nt, vel)
        # stop 時に直ちに Note Off を出すため、現在 Note On 中の音を保持しておく
        if vel != 0:
            self.retained_note.append(nt)
        elif nt in self.retained_note:
            self.retained_note.remove(nt)

    def _generate_sequence(self):
        seqType = self.description[0]
        if seqType == 'phrase':
            pg = nph.PhraseGenerator(self.description[1:], self.keynote)
            self.whole_tick, self.sqdata = pg.convertToMIDILikeFormat()
            self.is_random = False
        elif seqType == 'random':
            self.rnd.set_random(self.description[1:], self.keynote)
            self.is_random = True

    def changeKeynote(self, nt):
        self.keynote = nt
        if self.state_play == True:
            self.state_reserv = True
        else:
            self._generate_sequence()

    def clear_description(self):
        for nt in self.retained_note:
            self._send_midi_note(nt, 0)
        if self.is_random:
            self.rnd.stop()
        self.description= [None for _ in range(4)]

    def add_seq_description(self, data):
        self.description = data
        if self.state_play == True:
            self.state_reserv = True
        else:
            self._generate_sequence()
        return self.whole_tick

    def _generate_event_sq(self, tick):
        maxEv = len(self.sqdata)
        if maxEv == 0:
            # データを持っていない
            return -1

        if tick == 0:
            self.play_counter = 0

        trace = self.play_counter
        nextTick = 0
        while True:
            if maxEv <= trace:
                nextTick = -1   # means sequence finished
                break
            nextTick = self.sqdata[trace][0]
            if nextTick < tick:
                nt = self.sqdata[trace][1]
                vel = self.sqdata[trace][2]
                self._send_midi_note(nt, vel)
            else:
                break
            trace += 1

        self.play_counter = trace
        return nextTick

    # Main IF
    def start(self):
        if not self.is_random:
            self.state_play = True
            self.play_counter = 0
            self._generate_event_sq(0)

        elif self.rnd != None:
            self.rnd.start()

    # Main IF
    def return_to_top(self, tick_for_one_measure):        # Phrase sequence return to top during playing 
        if not self.is_random:
            if self.state_reserv == True:
                self._generate_sequence()
            self.play_counter = 0
            return self.whole_tick

        elif self.rnd != None:
            return self.rnd.return_to_top(tick_for_one_measure)
        else: return 0

    # Main IF
    def generate_event(self, tick):
        if not self.is_random:
            return self._generate_event_sq(tick)

        elif self.rnd != None:
            return self.rnd.generate_random(tick)
        else: return 0

    # Main IF
    def stop(self):     # 再生停止
        for nt in self.retained_note:
            self._send_midi_note(nt, 0)
        if not self.is_random:
            self.state_play = False
        elif self.rnd != None:
            self.rnd.stop()


