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

    def fillOmittedNoteData(self):
        # スペース削除し、',' '|' 区切りでリスト化
        noteFlow = re.split('[,|]', self.noteData[0].replace(' ',''))
        while '' in noteFlow:
            noteFlow.remove('')

        # If find Repeat mark, expand all event.
        noRepeat = False
        while noRepeat == False:
            noRepeat = True
            repeatStart = 0
            for i, nt in enumerate(noteFlow):   # |: :n|
                if ':' in nt:
                    noRepeat = False
                    locate = nt.find(':')
                    if locate == 0:
                        noteFlow[i] = nt[1:]
                        repeatStart = i
                    else:
                        repeatCount = 0
                        num = nt.rfind(':') - len(nt)
                        noteFlow[i] = nt[0:num]
                        if num == -1:
                            repeatCount = 1
                        else:
                            if nt[num+1:].isdecimal() == True: repeatCount = int(nt[num+1:])
                        rptEndPtr = i+1
                        for j in range(repeatCount):
                            insPtr = rptEndPtr + j*(rptEndPtr-repeatStart)
                            noteFlow[insPtr:insPtr] = noteFlow[repeatStart:rptEndPtr]
                        break
            ## end of for

            repeatStart = 0
            firstBracket = False
            for i, nt in enumerate(noteFlow):   # <  >*n
                if '<' in nt:
                    noRepeat = False
                    locate = nt.find('<')
                    if locate == 0:
                        noteFlow[i] = nt[1:]
                        repeatStart = i
                        firstBracket = True
                elif '>' in nt:
                    repeatCount = 0
                    reCnt = nt.rfind('>')
                    noteFlow[i] = nt[0:reCnt]
                    if nt[reCnt+1:reCnt+2] == '*' and firstBracket == True:
                        if nt[reCnt+2:].isdecimal() == True: repeatCount = int(nt[reCnt+2:])
                        if repeatCount > 1:
                            rptEndPtr = i+1
                            for j in range(repeatCount-1):
                                insPtr = rptEndPtr + j*(rptEndPtr-repeatStart)
                                noteFlow[insPtr:insPtr] = noteFlow[repeatStart:rptEndPtr]
                    break
            ## end of for
        ## end of while

        # Same note repeat
        noRepeat = False
        while noRepeat == False:
            noRepeat = True
            for i, nt in enumerate(noteFlow):
                if '*' in nt:
                    noRepeat = False
                    locate = nt.find('*')
                    noteFlow[i] = nt[0:locate]
                    repeatCount = 0
                    if nt[locate+1:].isdecimal() == True: repeatCount = int(nt[locate+1:])
                    if repeatCount > 1:
                        for j in range(repeatCount-1):
                            noteFlow.insert(i+1, nt[0:locate])
                    break
            ## end of for
        ## end of while

        return noteFlow, len(noteFlow)

    def fillOmittedDurData(self, durText, ntNum):
        durFlow = []
        if ',' in durText:
            durFlow = re.split('[,|]', durText.replace(' ',''))
        else:
            # ','が無い場合、全体を一つの文字列にし、リストとして追加
            durFlow.append(durText)

        noRepeat = False
        while noRepeat == False:
            noRepeat = True
            repeatStart = 0
            firstBracket = False
            for i, dur in enumerate(durFlow):   # <  >*n
                if '<' in dur:
                    noRepeat = False
                    locate = dur.find('<')
                    if locate == 0:
                        durFlow[i] = dur[1:]
                        repeatStart = i
                        firstBracket = True
                elif '>' in dur:
                    reCnt = dur.rfind('>')
                    durFlow[i] = dur[0:reCnt]
                    if dur[reCnt+1:reCnt+2] == '*' and firstBracket == True:
                        repeatCount = 0
                        if dur[reCnt+2:].isdecimal() == True: repeatCount = int(dur[reCnt+2:])
                        if repeatCount > 1:
                            rptEndPtr = i+1
                            for j in range(repeatCount-1):
                                insPtr = rptEndPtr + j*(rptEndPtr-repeatStart)
                                durFlow[insPtr:insPtr] = durFlow[repeatStart:rptEndPtr]
                    elif i+1 == len(durFlow) and firstBracket == True:
                        cntr = 0
                        while True:
                            durFlow.append(durFlow[repeatStart+cntr])
                            cntr+=1
                            if ntNum <= len(durFlow): break
                    break
            ## end of for
        ## end of while

        durNum = len(durFlow)
        if durNum < ntNum:
            for _ in range(ntNum-durNum):
                durFlow.append(durFlow[durNum-1])   # 足りない要素を補填
        elif durNum > ntNum:
            del durFlow[ntNum:] # 多い要素を削除
        return durFlow

    def fillOmittedVelData(self, velText, ntNum):
        velFlow = []
        if ',' in velText:
            velFlow = re.split('[,|]', velText.replace(' ',''))
        else:
            # ','が無い場合、全体を一つの文字列にし、リストとして追加
            velFlow.append(velText)

        noRepeat = False
        while noRepeat == False:
            noRepeat = True
            repeatStart = 0
            firstBracket = False
            for i, vel in enumerate(velFlow):   # <  >*n
                if '<' in vel:
                    noRepeat = False
                    locate = vel.find('<')
                    if locate == 0:
                        velFlow[i] = vel[1:]
                        repeatStart = i
                        firstBracket = True
                elif '>' in vel:
                    reCnt = vel.rfind('>')
                    velFlow[i] = vel[0:reCnt]
                    if vel[reCnt+1:reCnt+2] == '*' and firstBracket == True:
                        repeatCount = 0
                        if vel[reCnt+2:].isdecimal() == True: repeatCount = int(vel[reCnt+2:])
                        if repeatCount > 1:
                            rptEndPtr = i+1
                            for j in range(repeatCount-1):
                                insPtr = rptEndPtr + j*(rptEndPtr-repeatStart)
                                velFlow[insPtr:insPtr] = velFlow[repeatStart:rptEndPtr]
                    elif i+1 == len(velFlow) and firstBracket == True:
                        cntr = 0
                        while True:
                            velFlow.append(velFlow[repeatStart+cntr])
                            cntr+=1
                            if ntNum <= len(velFlow): break
                    break
            ## end of for
        ## end of while

        velNum = len(velFlow)
        if velNum < ntNum:
            for _ in range(ntNum-velNum):
                velFlow.append(velFlow[velNum-1])   # 足りない要素を補填
        return velFlow

    def fillOmittedData(self):
        ### Note
        noteFlow, ntNum = self.fillOmittedNoteData()

        ### Duration
        # セミコロンの後で設定されている基本音価の調査
        durText = self.noteData[1]
        if ':' in durText:
            lastDurTxt = durText.split(':')
            if lastDurTxt[0] == '':
                durText = '1'
            else:
                durText = lastDurTxt[0]
            if lastDurTxt[1].isdecimal() == True:
                self.onpu = int(lastDurTxt[1])
            else:
                self.onpu = 4
        durFlow = self.fillOmittedDurData(durText, ntNum)

        ### Velocity
        velFlow = self.fillOmittedVelData(self.noteData[2], ntNum)

        return noteFlow, durFlow, velFlow, ntNum

    def cnvNoteToPitch(self, noteText):
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

        return bpchs

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
        if self.noteData[0] == None or len(self.noteData[0]) == 0:
            return 0, self.playData

        noteFlow, durFlow, velFlow, ntNum = self.fillOmittedData()
        tick = 0
        readPtr = 0
        while readPtr < ntNum:
            cnts = self.cnvNoteToPitch(noteFlow[readPtr])
            dur = self.cnvDuration(durFlow[readPtr])
            vel = self.cnvExpToVel(velFlow[readPtr])
            self.addNote(tick,cnts,dur,vel)
            tick += dur*480*4/self.onpu
            readPtr += 1    # out from repeat

        return tick, self.playData
