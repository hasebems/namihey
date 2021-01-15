# -*- coding: utf-8 -*-
import namiphrase as nph


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
        self.number = partNum
        self.whole_tick = 0          # a length of whole tick that needs to play
        self.state_play = False      # during Playing
        self.state_reserv = False      # Change Phrase at next loop top 
        self.keynote = DEFAULT_NOTE_NUMBER

    def __generate_sequence(self):
        seqType = self.description[0]
        if seqType == 'phrase':
            pg = nph.PhraseGenerator(self.description[1:], self.keynote)
            self.whole_tick, self.sqdata = pg.convertToMIDILikeFormat()
        elif seqType == 'pattern':
            pass

    def changeKeynote(self, nt):
        self.keynote = nt
        if self.state_play == True:
            self.state_reserv = True
        else:
            self.__generate_sequence()

    def clear_description(self):
        self.description= [None for _ in range(4)]

    def add_seq_description(self, data):
        self.description = data
        if self.state_play == True:
            self.state_reserv = True
        else:
            self.__generate_sequence()
        return self.whole_tick

    def __retain_note_during_play(self, note, vel):
        # stop 時に直ちに Note Off を出すため、現在 Note On 中の音を保持しておく
        if vel != 0:
            self.retained_note.append(note)
        else:
            self.retained_note.remove(note)

    def play(self):
        # 再生開始
        self.state_play = True
        return self.generate_event(0)

    def returnToTop(self):
        # Phrase sequence return to top during playing 
        if self.state_reserv == True:
            self.__generate_sequence()
        self.play_counter = 0
        return self.whole_tick

    def generate_event(self, evTick):
        maxEv = len(self.sqdata)
        if maxEv == 0:
            # データを持っていない
            return self.parent_block.getWholeTick()

        if evTick == 0:
            self.play_counter = 0

        trace = self.play_counter
        nextTick = 0
        while True:
            if maxEv <= trace:
                # Return Max Value
                nextTick = self.parent_block.getWholeTick()
                break
            nextTick = self.sqdata[trace][0]
            if nextTick < evTick:
                nt = self.sqdata[trace][1]
                vel = self.sqdata[trace][2]
                ch = self.number
                self.parent_block.sendMidiNote(ch, nt, vel)
                self.__retain_note_during_play(nt, vel)
            else:
                break
            trace += 1

        self.play_counter = trace
        return nextTick

    def stop(self):
        # 再生停止
        for nt in self.retained_note:
            self.parent_block.sendMidiNote(self.number, nt, 0)
        self.state_play = False
