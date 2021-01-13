# -*- coding: utf-8 -*-
import namiphrase as nph



class Part:
    #   Part 単位で、演奏情報を保持
    #   演奏時に、適切なタイミングで MIDI データを出力
    def __init__(self, blk, partNum):
        self.noteData = [None for _ in range(3)]
        self.playData = []
        self.stockNoteOn = []
        self.playDataCnt = 0
        self.parentBlk = blk

        self.number = partNum
        self.wholeTick = 0          # a length of whole tick that needs to play
        self.statePlay = False      # during Playing
        self.stateRsrv = False      # Change Phrase at next loop top 

        self.keynote = 60


    def changeKeynote(self, nt):
        self.keynote = nt
        if self.statePlay == True:
            self.stateRsrv = True
        else:
            pg = nph.PhraseGenerator(self.noteData, nt)
            self.wholeTick, self.playData = pg.convertToMIDILikeFormat()


    def clearDescription(self):
        self.noteData= [None for _ in range(4)]


    def __generateSequence(self):
        seqType = self.noteData[0]
        if seqType == 'phrase':
            pg = nph.PhraseGenerator(self.noteData[1:], self.keynote)
            self.wholeTick, self.playData = pg.convertToMIDILikeFormat()
        elif seqType == 'pattern':
            pass


    def addSeqDescription(self, data):
        self.noteData = data
        if self.statePlay == True:
            self.stateRsrv = True
        else:
            self.__generateSequence()
        return self.wholeTick


    def stockNoteOn_duringPlay(self, note, vel):
        # stop 時に直ちに Note Off を出すため、現在 Note On 中の音を保持しておく
        if vel != 0:
            self.stockNoteOn.append(note)
        else:
            self.stockNoteOn.remove(note)


    def play(self):
        # 再生開始
        self.statePlay = True
        return self.generateEv(0)


    def returnToTop(self):
        # Phrase sequence return to top during playing 
        if self.stateRsrv == True:
            self.__generateSequence()
        self.playDataCnt = 0
        return self.wholeTick


    def generateEv(self, evTick):
        maxEv = len(self.playData)
        if maxEv == 0:
            # データを持っていない
            return self.parentBlk.getWholeTick()

        if evTick == 0:
            self.playDataCnt = 0

        trace = self.playDataCnt
        nextTick = 0
        while True:
            if maxEv <= trace:
                # Return Max Value
                nextTick = self.parentBlk.getWholeTick()
                break
            nextTick = self.playData[trace][0]
            if nextTick < evTick:
                nt = self.playData[trace][1]
                vel = self.playData[trace][2]
                ch = self.number
                self.parentBlk.sendMidiNote(ch, nt, vel)
                self.stockNoteOn_duringPlay(nt, vel)
            else:
                break
            trace += 1
            
        self.playDataCnt = trace
        return nextTick


    def stop(self):
        # 再生停止
        for nt in self.stockNoteOn:
            self.parentBlk.sendMidiNote(self.number, nt, 0)
        self.statePlay = False
