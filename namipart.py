# -*- coding: utf-8 -*-
import namiphrase as nph
import namipattern as npt


DEFAULT_NOTE_NUMBER = 60


class Part:
    #   Part 単位で、演奏情報を保持
    #   演奏時に、適切なタイミングで MIDI データを出力
    def __init__(self, blk, partNum):
        self.description = [None for _ in range(4)]
        self.sqdata = []
        self.__retained_note = []
        self.__play_counter = 0
        self.parent_block = blk
        self.__midich = partNum
        self.whole_tick = 0          # a length of whole tick that needs to play
        self.__state_play = False      # during Playing
        self.__state_reserv = False      # Change Phrase at next loop top 
        self.keynote = DEFAULT_NOTE_NUMBER
        self.__is_random = False
        self.__ptn = None

    def __send_midi_note(self, nt, vel):
        self.parent_block.sendMidiNote(self.__midich, nt, vel)
        # stop 時に直ちに Note Off を出すため、現在 Note On 中の音を保持しておく
        if vel != 0:
            self.__retained_note.append(nt)
        elif nt in self.__retained_note:
            self.__retained_note.remove(nt)

    def __generate_sequence(self):
        seqType = self.description[0]
        if seqType == 'phrase':
            pg = nph.PhraseGenerator(self.description[1:], self.keynote)
            self.whole_tick, self.sqdata = pg.convertToMIDILikeFormat()
            self.__is_random = False
        elif seqType == 'pattern':
            self.__ptn = npt.PatternGenerator(self.description[1:], self.keynote, self.__send_midi_note)
            self.__is_random = True

    def changeKeynote(self, nt):
        self.keynote = nt
        if self.__state_play == True:
            self.__state_reserv = True
        else:
            self.__generate_sequence()

    def clear_description(self):
        self.description= [None for _ in range(4)]

    def add_seq_description(self, data):
        self.description = data
        if self.__state_play == True:
            self.__state_reserv = True
        else:
            self.__generate_sequence()
        return self.whole_tick

    def __generate_event_sq(self, evTick):
        maxEv = len(self.sqdata)
        if maxEv == 0:
            # データを持っていない
            return self.parent_block.get_whole_tick()

        if evTick == 0:
            self.__play_counter = 0

        trace = self.__play_counter
        nextTick = 0
        while True:
            if maxEv <= trace:
                # Return Max Value
                nextTick = self.parent_block.get_whole_tick()
                break
            nextTick = self.sqdata[trace][0]
            if nextTick < evTick:
                nt = self.sqdata[trace][1]
                vel = self.sqdata[trace][2]
                self.__send_midi_note(nt, vel)
            else:
                break
            trace += 1

        self.__play_counter = trace
        return nextTick

    def play(self):     # 再生開始
        if not self.__is_random:
            self.__state_play = True
            self.__play_counter = 0
            self.__generate_event_sq(0)

        elif self.__ptn != None:
            self.__ptn.play()

    def return_to_top(self):        # Phrase sequence return to top during playing 
        if not self.__is_random:
            if self.__state_reserv == True:
                self.__generate_sequence()
            self.__play_counter = 0
            return self.whole_tick

        elif self.__ptn != None:
            return self.__ptn.return_to_top()
        else: return 0

    def generate_event(self, tick):
        if not self.__is_random:
            return self.__generate_event_sq(tick)

        elif self.__ptn != None:
            return self.__ptn.generate_random(tick)
        else: return 0

    def stop(self):     # 再生停止
        for nt in self.__retained_note:
            self.__send_midi_note(nt, 0)
        if not self.__is_random:
            self.__state_play = False
        elif self.__ptn != None:
            self.__ptn.stop()


