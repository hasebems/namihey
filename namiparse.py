# -*- coding: utf-8 -*-

class Parsing:
    #   入力した文字列の解析
    #   一行単位で入力されるたびに生成される
    def __init__(self, seq):
        self.sq = seq

    def changeBeat(self, text):
        if '/' in text:
            beatList = text.strip().split('/')
            btnum = onpu = 0
            btnumStr = beatList[0].strip()
            if btnumStr.isdecimal() == True:
                btnum = int(btnumStr)
            onpuStr = beatList[1].strip()
            if onpuStr.isdecimal() == True:
                onpu = int(onpuStr)
            if btnum >= 1 and onpu >= 1:
                self.sq.get_block().stockTickForOneMeasure = (1920/onpu)*btnum

    def parseSetCommand(self, inputText):
        prmText = inputText.strip()
        if 'part' in prmText:
            pickedTxt = prmText[prmText.find('part')+4:]
            if '=' in pickedTxt:
                ptNumList = pickedTxt[pickedTxt.find('=')+1:].strip().split()
                #print(ptNumList[0])
        if 'block' in prmText:
            pass
        if 'key' in prmText:
            pass
        if 'beat' in prmText:
            pickedTxt = prmText[prmText.find('bpm')+3:]
            if '=' in pickedTxt:
                beatList = pickedTxt[pickedTxt.find('=')+1:].strip().split()
                self.changeBeat(beatList[0])
        if 'bpm' in prmText:
            pickedTxt = prmText[prmText.find('bpm')+3:]
            if '=' in pickedTxt:
                bpmNumList = pickedTxt[pickedTxt.find('=')+1:].strip().split()
                self.sq.get_block().stockBpm = int(bpmNumList[0])

    def letterP(self, inputText):
        if inputText[0:4] == 'play':
            arg = inputText.split()
            if len(arg) == 1:
                self.sq.play()

    def letterS(self, inputText):
        if inputText[0:4] == 'stop':
            self.sq.stop()
        elif inputText[0:3] == 'set':
            self.parseSetCommand(inputText[3:])

    def letterI(self, inputText):
        if inputText[0:5] == 'input':
            tx = inputText[5:].replace(' ', '').split('=')
            if tx[0] == 'part':
                part = int(tx[1])
                if part > 0 and part <= 16:
                    print("Changed current part to " + str(part) + ".")
                    blk = self.sq.get_block()
                    blk.inputPart = part-1

    def letterBracket(self, inputText):
        # [] のペアを抜き出し、中身を noteInfo に入れる
        noteInfo = []
        tx = inputText
        while True:
            num = tx.find(']')
            if num == -1:
                break
            noteInfo.append(tx[1:num])
            tx = tx[num+1:].strip()
            if len(tx) == 0:
                break
            if tx[0:1] != '[':
                break

        # [] の数が 1,2 の時は中身を補填
        brktNum = len(noteInfo)
        if brktNum == 1:
            noteInfo.append('1')    # set default value
            noteInfo.append('100')
        elif brktNum == 2:
            noteInfo.append('100')  # set default velocity value
        elif brktNum == 0 or brktNum > 3:
            # [] の数が 1〜3 以外ならエラー
            print("Error!")
            return

        print("set Phrase!")
        blk = self.sq.get_block()
        blk.clearPhrase()
        blk.addPhrase(noteInfo)

    def letterQm(inputText):
        pass

    def startParsing(self, inputText):
        firstLetter = inputText[0:1]
        if firstLetter == 'p':   self.letterP(inputText)
        elif firstLetter == '[': self.letterBracket(inputText)
        elif firstLetter == 's': self.letterS(inputText)
        elif firstLetter == 'b': self.letterP(inputText)
        elif firstLetter == 'i': self.letterI(inputText)
        elif firstLetter == 'o': self.letterP(inputText)
        elif firstLetter == 'k': self.letterP(inputText)
        elif firstLetter == '?': self.letterQm(inputText)


def parse(inputText, seq):
    ps = Parsing(seq)
    ps.startParsing(inputText)
