# -*- coding: utf-8 -*-
import re
import namilib as nlib

REPEAT_START = -1
NO_REPEAT = 0
REPEAT_END = 1 # 1,2,3 の数値はリピート回数

class PhraseGenerator():
    #   文字情報を MIDI で使う数値に変換
    #   変換の際、一回生成されるだけ

    def __init__(self, phraseData, key):
        self.baseNote = 4               # base note type
        self.durPer = 100               # 100%
        self.playData = []
        self.noteData = phraseData
        self.keynote = key

    def __addNote(self, tick, notes, duration, velocity=100):
        for note in notes:
            if note != nlib.REST:
                self.playData.append([tick,note,velocity])
        for note in notes:
            if note != nlib.REST:
                realDur = int(duration*self.durPer*480*4/(100*self.baseNote))
                offTick = tick + realDur - 1
                self.playData.append([offTick,note,0])

    def __fillOmittedNoteData(self):
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

    def __fillOmittedDurData(self, durText, ntNum):
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

    def __fillOmittedVelData(self, velText, ntNum):
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

    def __changeBasicNoteValue(self, durText):
        # コロンで設定されている基本音価の調査し、変更があれば差し替え
        if ':' in durText:
            spTxt = durText.split(':')
            baseNoteTxt = '4'
            # 基本音価はコロンの前か後か？
            if (',' in spTxt[0]) or ('(' and ')' in spTxt[1]):
                durText = spTxt[0]
                baseNoteText = spTxt[1]
            elif (',' in spTxt[1]) or ('(' and ')' in spTxt[0]):
                baseNoteText = spTxt[0]
                durText = spTxt[1]
            elif spTxt[0] == '':
                durText = '1'
                baseNoteText = spTxt[1]
            elif spTxt[0].isdecimal() and spTxt[1].isdecimal() and int(spTxt[0]) < int(spTxt[1]):
                durText = spTxt[0]
                baseNoteText = spTxt[1]
            else:
                baseNoteText = spTxt[0]
                durText = spTxt[1]

            if '(' and ')' in baseNoteText:
                percent = re.findall("(?<=\().+?(?=\))", baseNoteText)
                if '%' in percent[0]:
                    per = percent[0].strip('%')
                    if per.isdecimal() == True and int(per) <= 100:
                        self.durPer = int(per)                  # % の数値
                elif percent[0] == 'stacc.':
                    self.durPer = 50
            durLen = re.sub("\(.+?\)", "", baseNoteText)
            if durLen.isdecimal() == True:
                self.baseNote = int(durLen)
            else:
                self.baseNote = 4
        return durText

    def __fillOmittedData(self):
        ### Note
        noteFlow, ntNum = self.__fillOmittedNoteData()

        ### Duration
        durText = self.__changeBasicNoteValue(self.noteData[1])
        durFlow = self.__fillOmittedDurData(durText, ntNum)

        ### Velocity
        velFlow = self.__fillOmittedVelData(self.noteData[2], ntNum)

        return noteFlow, durFlow, velFlow, ntNum

    def __cnvNoteToPitch(self, noteText):
        nlists = noteText.replace(' ','').split('=')    # 和音検出
        bpchs = []
        for nx in nlists:
            basePitch = self.keynote + nlib.convert_doremi(nx)
            bpchs.append(basePitch)
        return bpchs

    def __cnvDuration(self, durText):
        if durText.isdecimal() == True:
            return int(durText)
        else:
            return 1

    def convertToMIDILikeFormat(self):
        if self.noteData[0] == None or len(self.noteData[0]) == 0:
            return 0, self.playData

        noteFlow, durFlow, velFlow, ntNum = self.__fillOmittedData()
        tick = 0
        readPtr = 0
        while readPtr < ntNum:
            cnts = self.__cnvNoteToPitch(noteFlow[readPtr])
            dur = self.__cnvDuration(durFlow[readPtr])
            vel = nlib.convert_exp2vel(velFlow[readPtr])
            self.__addNote(tick,cnts,dur,vel)
            tick += dur*480*4/self.baseNote
            readPtr += 1    # out from repeat

        return tick, self.playData
