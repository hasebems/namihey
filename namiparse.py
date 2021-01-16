# -*- coding: utf-8 -*-


WHOLE_TONE_LENGTH = 1920


class Parsing:
    #   入力した文字列の解析
    #   一行単位で入力されるたびに生成される
    def __init__(self, seq):
        self.sq = seq
        self.inputPart = 1      # 1origin
        self.promptStr = '[1][1]~~> '

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
                self.sq.getBlock().stock_tick_for_one_measure = (WHOLE_TONE_LENGTH/onpu)*btnum

    def changeKey(self, keyText, all):
        key = 12
        firstLetter = keyText[0:1]
        if firstLetter == 'C':   key += 0
        elif firstLetter == 'D': key += 2
        elif firstLetter == 'E': key += 4
        elif firstLetter == 'F': key += 5
        elif firstLetter == 'G': key += 7
        elif firstLetter == 'A': key += 9
        elif firstLetter == 'B': key += 11
        else: return
        octaveLetter = keyText[1:2]
        if octaveLetter == '#':
            key += 1
            octaveLetter = keyText[2:3]
        elif octaveLetter == 'b':
            key -= 1
            octaveLetter = keyText[2:3]
        if octaveLetter.isdecimal() == True:
            key += int(octaveLetter)*12
            if all == True:
                for pt in self.sq.currentBk.parts:
                    pt.changeKeynote(key)
            else:
                pt = self.sq.currentBk.inputPart
                self.sq.currentBk.parts[pt].changeKeynote(key)

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
            pickedTxt = prmText[prmText.find('key')+3:]
            if '=' in pickedTxt:
                keyList = pickedTxt[pickedTxt.find('=')+1:].strip().split()
                if len(keyList) > 1 and 'all' == keyList[1]:
                    self.changeKey(keyList[0], True)
                else:
                    self.changeKey(keyList[0], False)
        if 'beat' in prmText:
            pickedTxt = prmText[prmText.find('beat')+4:]
            if '=' in pickedTxt:
                beatList = pickedTxt[pickedTxt.find('=')+1:].strip().split()
                self.changeBeat(beatList[0])
        if 'bpm' in prmText:
            pickedTxt = prmText[prmText.find('bpm')+3:]
            if '=' in pickedTxt:
                bpmNumList = pickedTxt[pickedTxt.find('=')+1:].strip().split()
                if bpmNumList[0].isdecimal() == True:
                    self.sq.getBlock().stockBpm = int(bpmNumList[0])

    def letterP(self, inputText):
        if inputText[0:4] == 'play':
            arg = inputText.split()
            if len(arg) == 1:
                print("Phrase has started!")
                self.sq.play()
        else: print("what?")

    def letterS(self, inputText):
        if inputText[0:5] == 'start':
            print("Phrase has started!")
            self.sq.play()            
        elif inputText[0:4] == 'stop':
            self.sq.stop()
            print("Stopped!")
        elif inputText[0:3] == 'set':
            self.parseSetCommand(inputText[3:])
        elif inputText[0:4] == 'show':
            blk = self.sq.getBlock()
            ele = blk.parts[blk.inputPart].description
            print('~~> N[' + str(ele[1]) + ']')
            print('~~> D[' + str(ele[2]) + ']')
            print('~~> V[' + str(ele[3]) + ']')
        else: print("what?")

    def letterI(self, inputText):
        if inputText[0:5] == 'input':
            tx = inputText[5:].replace(' ', '')
            if tx.isdecimal() == True:
                part = int(tx)
                if part > 0 and part <= 16:
                    print("Changed current part to " + str(part) + ".")
                    blk = self.sq.getBlock()
                    blk.inputPart = part-1
                    self.inputPart = part
                    self.promptStr = '[1][' + str(part) + ']~~> '
        else: print("what?")

    def letterBracket(self, inputText):
        # [] のセットを抜き出し、中身を noteInfo に入れる
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
        blk = self.sq.getBlock()
        blk.clear_description()
        noteInfo.insert(0,'phrase')
        blk.add_seq_description(noteInfo)

    def letterBrace(self, inputText):
        # {} のセットを抜き出し、中身を noteInfo に入れる
        noteInfo = []
        tx = inputText
        while True:
            num = tx.find('}')
            if num == -1:
                break
            noteInfo.append(tx[1:num])
            tx = tx[num+1:].strip()
            if len(tx) == 0:
                break
            if tx[0:1] != '{':
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

        print("set Pattern!")
        blk = self.sq.getBlock()
        blk.clear_description()
        noteInfo.insert(0,'pattern')
        blk.add_seq_description(noteInfo)

    def letterC(self, inputText):
        if inputText[0:6] == 'copyto':
            tx = inputText[7:].replace(' ', '')
            if tx.isdecimal() == True:
                part = int(tx)
                if part > 0 and part <= 16:
                    self.sq.currentBk.copyPhrase(part)
                    print("Phrase copied to part" + tx + ".")
        else: print("what?")

    def letterF(self, inputText):
        if inputText[0:4] == "fine":
            self.sq.fine()
        else: print("what?")

    def letterQm(self, inputText):
        print("what?")

    def startParsing(self, inputText):
        firstLetter = inputText[0:1]
        if firstLetter == '[': self.letterBracket(inputText)
        elif firstLetter == '{': self.letterBrace(inputText)
        elif firstLetter == 'b': self.letterP(inputText)
        elif firstLetter == 'c': self.letterC(inputText)
        elif firstLetter == 'f': self.letterF(inputText)
        elif firstLetter == 'i': self.letterI(inputText)
        elif firstLetter == 'k': self.letterP(inputText)
        elif firstLetter == 'o': self.letterP(inputText)
        elif firstLetter == 'p': self.letterP(inputText)
        elif firstLetter == 's': self.letterS(inputText)
        elif firstLetter == '?': self.letterQm(inputText)
        else: print("what?")

