# -*- coding: utf-8 -*-
import re

REPEAT_START = -1
NO_REPEAT = 0
REPEAT_END = 1 # 1,2,3 の数値はリピート回数
REST = 1000

class PhraseGenerator():
    #   文字情報を MIDI で使う数値に変換
    #   変換の際、一回生成されるだけ

    def __init__(self, phraseData, base):
        self.onpu = 4                   # base note type
        self.playData = []
        self.noteData = phraseData
        self.baseNote = base

    def addNote(self, tick, notes, duration, velocity=100):
        for note in notes:
            if note != REST:
                self.playData.append([tick,note,velocity])
        for note in notes:
            if note != REST:
                offTick = tick + duration*480*4/self.onpu - 1
                self.playData.append([offTick,note,0])

    def fillOmittedData(self):
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

    def cnvNoteToPitch(self, noteText):
        repeat = NO_REPEAT
        if ':' in noteText:       # repeat
            num = noteText.find(':')
            if num == 0:
                noteText = noteText[1:]
                repeat = REPEAT_START
            else:
                num = noteText.rfind(':') - len(noteText)
                if num == -1:
                    repeat = REPEAT_END
                else:
                    repeat = int(noteText[num+1:]) if noteText[num+1:].isdecimal() == True else REPEAT_END
                noteText = noteText[0:num]

        nlists = noteText.replace(' ','').split('=')    # 和音検出
        bpchs = []
        for nx in nlists:
            basePitch = self.baseNote
            first = nx[0]

            if first == '+':    # octave up
                nx = nx[1:]
                basePitch += 12
            elif first == '-':  # octave down
                nx = nx[1:]
                basePitch -= 12

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

    def cnvDuration(self, durText):
        if durText.isdecimal() == True:
            return int(durText)
        else:
            return 1

    def cnvExpToVel(self, expText):
        vel = 100
        if expText.isdecimal() == False:
            if   expText == 'ff':   vel = 127
            elif expText == 'f':    vel = 114
            elif expText == 'mf':   vel = 100
            elif expText == 'mp':   vel = 84
            elif expText == 'p':    vel = 64
            elif expText == 'pp':   vel = 48
            elif expText == 'ppp':  vel = 24
        else:
            vel = int(expText)
        return vel

    def convertToMIDILikeFormat(self):
        if len(self.noteData[0]) == 0:
            return 0, self.playData

        noteFlow, durFlow, velFlow, ntNum = self.fillOmittedData()
        tick = 0
        readPtr = 0
        repeatPoint = 0     # リピートして戻る場所
        repeatCnt = 0       # リピート回数のカウント
        while readPtr < ntNum:
            cnts, repeatValue = self.cnvNoteToPitch(noteFlow[readPtr])
            dur = self.cnvDuration(durFlow[readPtr])
            vel = self.cnvExpToVel(velFlow[readPtr])
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

        return tick, self.playData
