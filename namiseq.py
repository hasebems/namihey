# -*- coding: utf-8 -*-
import  time
import  mido
import  namiconf
import  namipart as npt

MAX_PART_COUNT = 16

class Block:
    #   シーケンスの断片を Block という単位で扱う
    #   Block 内に最大 MAX_PART_COUNT part持つことができる
    #   CUI からの情報を取得後、 Part に渡し、generateEv() で MIDI OUT する
    def __init__(self, midiport):
        self.part = [npt.Part(self,i) for i in range(MAX_PART_COUNT)]
        self.bpm = 100
        self.maxMeasure = 1
        self.tickForOneMeasure = 1920
        self.port = midiport
        self.inputPart = 0

        self.nextLoopStartTime = 0
        self.currentLoopStartTime = 0

        self.stockBpm = self.bpm
        self.stockTickForOneMeasure = self.tickForOneMeasure

    def getWholeTick(self):
        return self.tickForOneMeasure*self.maxMeasure

    def clearPhrase(self):
        self.part[self.inputPart].clearPhrase()

    def addPhrase(self,data):
        self.maxMeasure = 0
        pt = self.inputPart
        tick = self.part[pt].addPhrase(data)
        while tick > self.getWholeTick():
            self.maxMeasure += 1

    def sendMidiNote(self, ch, nt, vel):
        if vel != 0:
            msg = mido.Message('note_on', channel=ch, note=nt, velocity=vel)
        else:
            msg = mido.Message('note_off', channel=ch, note=nt)
        self.port.send(msg)

    def play(self):
        # 演奏開始
        self.bpm = self.stockBpm
        if self.tickForOneMeasure != self.stockTickForOneMeasure:
            # beat が設定された場合
            self.tickForOneMeasure = self.stockTickForOneMeasure

            # 最大小節数の再計算
            self.maxMeasure = 0
            tick = 0
            for pt in range(MAX_PART_COUNT):
                ptTick = self.part[pt].wholeTick
                if ptTick > tick:
                    tick = ptTick
            while tick > self.getWholeTick():
                self.maxMeasure += 1

        self.currentLoopStartTime = 0
        self.nextLoopStartTime = self.getWholeTick()/(self.bpm*8)
        for pt in range(MAX_PART_COUNT):
            self.part[pt].play()

    def generateEv(self, evTime):
        # 演奏データの生成
        if evTime > self.nextLoopStartTime:
            # loop して先頭に戻った時
            self.bpm = self.stockBpm
            self.tickForOneMeasure = self.stockTickForOneMeasure

            # 最大小節数の再計算
            self.maxMeasure = 0
            tick = 0
            for pt in range(MAX_PART_COUNT):
                ptTick = self.part[pt].returnToTop()
                if ptTick > tick:
                    tick = ptTick
            while tick > self.getWholeTick():
                self.maxMeasure += 1

            self.currentLoopStartTime = self.nextLoopStartTime
            self.nextLoopStartTime += self.getWholeTick()/(self.bpm*8)

        currentTick = (evTime - self.currentLoopStartTime)*self.bpm*8
        nextTick = self.getWholeTick()
        for pt in range(MAX_PART_COUNT):
            ptNextTick = self.part[pt].generateEv(currentTick)
            if nextTick > ptNextTick:
                nextTick = ptNextTick

        return self.currentLoopStartTime + nextTick/(self.bpm*8)

    def stop(self):
        # 演奏終了
        for pt in range(MAX_PART_COUNT):
            self.part[pt].stop()


class Seq:
    #   MIDI シーケンスを再生する全体のまとめ処理
    #   開始時に生成され、playSeq() がコマンド入力とは別スレッドで、定期的に呼ばれる
    #   その他の機能： mido の生成、CUIに情報を送る
    def __init__(self):
        self.startTime = time.time()
        self.duringPlay = False
        self.bk = []
        allPort = mido.get_output_names()
        print("MIDI OUT: " + allPort[-1])
        self.midiport = mido.open_output(allPort[-1])
        self.bk.append(Block(self.midiport))
        self.currentBk = self.bk[0]

    def playSeq(self):
        if self.duringPlay == False:
            return
        currentTime = time.time() - self.startTime
        if currentTime > self.nextTime:
            self.nextTime = self.currentBk.generateEv(currentTime)

    def get_block(self, block=1):
        return self.bk[block-1]

    def play(self, block=1, repeat='on'):
        self.duringPlay = True
        self.startTime = time.time()
        self.nextTime = 0
        self.currentBk = self.bk[block-1]
        self.currentBk.play()

    def stop(self):
        self.currentBk.stop()
        self.duringPlay = False

