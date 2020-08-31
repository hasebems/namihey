# -*- coding: utf-8 -*-
import re

REST = 1000

REPEAT_START = -1
NO_REPEAT = 0
REPEAT_END = 1 # 1,2,3 の数値はリピート回数

class Part:
    #   Part 単位で、ノート情報を保持
    #   文字情報を MIDI で使う数値に変換
    #   演奏時に、適切なタイミングで MIDI データを出力
    def __init__(self, blk, partNum):
        self.noteData = [None for _ in range(3)]
        self.playData = []
        self.stockNoteOn = []
        self.playDataCnt = 0
        self.parentBlk = blk

        self.number = partNum
        self.onpu = 4               # base note type
        self.wholeTick = 0          # a length of whole tick that needs to play
        self.statePlay = False      # during Playing
        self.stateRsrv = False      # Change Phrase at next loop top 

        self.baseNote = 60

    def changeBaseNote(self, nt):
        self.baseNote = nt
        if self.statePlay == True:
            self.stateRsrv = True
        else:
            self.convertToMIDILikeFormat()

    def addNote(self, tick, notes, duration, velocity=100):
        for note in notes:
            if note != REST:
                self.playData.append([tick,note,velocity])
        for note in notes:
            if note != REST:
                offTick = tick + duration*480*4/self.onpu - 1
                self.playData.append([offTick,note,0])

    def clearPhrase(self):
        self.noteData= [None for _ in range(3)]

    def completeNoteData(self):
        # スペース削除し、',' '|' 区切りでリスト化
        # 内容が足りなければ補填
        ### Note
        noteFlow = re.split('[,|]', self.noteData[0].replace(' ',''))
        while '' in noteFlow:
            noteFlow.remove('')
        ntNum = len(noteFlow)

        ### Duration
        durFlow = []
        if ',' in self.noteData[1]:
            durFlow = re.split('[,|]', self.noteData[1].replace(' ',''))
        else:
            # ','が無い場合、全体を一つの文字列にし、リストとして追加
            durFlow.append(self.noteData[1])

        # セミコロンの後で設定されている基本音価の調査
        durNum = len(durFlow)
        if ':' in durFlow[durNum-1]:
            lastDurTxt = durFlow[durNum-1].replace(' ','').split(':')
            if lastDurTxt[0] == '':
                lastDurTxt[0] = '1'
            durFlow[durNum-1] = lastDurTxt[0]
            if lastDurTxt[1].isdecimal() == True:
                self.onpu = int(lastDurTxt[1])
            else:
                self.onpu = 4

        if durNum < ntNum:
            for _ in range(ntNum-durNum):
                durFlow.append(durFlow[durNum-1])   # 足りない要素を補填

        ### Velocity
        velFlow = []
        if ',' in self.noteData[2]:
            velFlow = re.split('[,|]', self.noteData[2].replace(' ',''))
        else:
            # ','が無い場合、全体を一つの文字列にし、リストとして追加
            velFlow.append(self.noteData[2])

        velNum = len(velFlow)
        if velNum < ntNum:
            for _ in range(ntNum-velNum):
                velFlow.append(velFlow[velNum-1])   # 足りない要素を補填
        return noteFlow, durFlow, velFlow, ntNum

    def cnvNote(self, noteText):
        nlists = noteText.replace(' ','').split('=')    # 和音検出
        bpchs = []
        repeat = NO_REPEAT
        for nx in nlists:
            basePitch = self.baseNote
            first = nx[0]

            if first == '+':    # octave up
                nx = nx[1:]
                basePitch += 12
            elif first == '-':  # octave down
                nx = nx[1:]
                basePitch -= 12

            if ':' in nx:       # repeat
                num = nx.find(':')
                if num == 0:
                    nx = nx[1:]
                    repeat = REPEAT_START
                else:
                    num = nx.rfind(':') - len(nx)
                    if num == -1:
                        repeat = REPEAT_END
                    else:
                        repeat = int(nx[num+1:]) if nx[num+1:].isdecimal() == True else REPEAT_END
                    nx = nx[0:num]

            if nx == 'x':                   basePitch = REST
            elif nx == 'd':                 basePitch += 0
            elif nx == 'di' or nx == 'ra':  basePitch += 1
            elif nx == 'r':                 basePitch += 2
            elif nx == 'ri' or nx == 'ma':  basePitch += 3
            elif nx == 'm':                 basePitch += 4
            elif nx == 'f':                 basePitch += 5
            elif nx == 'fi' or nx == 'sa':  basePitch += 6
            elif nx == 's':                 basePitch += 7
            elif nx == 'si' or nx == 'lo':  basePitch += 8
            elif nx == 'l':                 basePitch += 9
            elif nx == 'li' or nx == 'ta':  basePitch += 10
            elif nx == 't':                 basePitch += 11
            bpchs.append(basePitch)

        return bpchs, repeat

    def convertToMIDILikeFormat(self):
        self.onpu = 4
        self.playData = []
        if len(self.noteData[0]) == 0:
            return 0

        noteFlow, durFlow, velFlow, ntNum = self.completeNoteData()
        tick = 0
        readPtr = 0
        repeatPoint = 0     # リピートして戻る場所
        repeatCnt = 0       # リピート回数のカウント
        while readPtr < ntNum:
            cnts, repeatValue = self.cnvNote(noteFlow[readPtr])
            dur = int(durFlow[readPtr])
            vel = int(velFlow[readPtr])
            self.addNote(tick,cnts,dur,vel)
            tick += dur*480*4/self.onpu
            if repeatValue >= REPEAT_END:
                if repeatValue > repeatCnt:
                    readPtr = repeatPoint
                    repeatCnt += 1
                else:
                    readPtr += 1    # out from repeat
            else:
                if repeatValue == REPEAT_START:
                    repeatPoint = readPtr
                readPtr += 1

        self.wholeTick = tick
        return tick

    def addPhrase(self, data):
        self.noteData = data
        if self.statePlay == True:
            self.stateRsrv = True
            return self.wholeTick
        else:
            return self.convertToMIDILikeFormat()

    def stockNoteOn_duringPlay(self, note, vel):
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
        tick = self.wholeTick
        if self.stateRsrv == True:
            tick = self.convertToMIDILikeFormat()
        self.playDataCnt = 0
        return tick

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
