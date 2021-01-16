# -*- coding: utf-8 -*-
import  time
import  mido
import  namiconf
import  namipart as npt


MAX_PART_COUNT = 16
DEFAULT_TICK_FOR_ONE_MEASURE = 1920     # 480 * 4
DEFAULT_BPM = 100
TICK_PER_SEC = 8    # convert [bpm] to [tick per sec] := 480(tick)/60(sec)


class Block:
    #   シーケンスの断片を Block という単位で扱う
    #   Block 内に最大 MAX_PART_COUNT part持つことができる
    #   CUI からの情報を取得後、 Part に渡し、generate_event() で MIDI OUT する
    def __init__(self, midiport):
        self.parts = [npt.Part(self,i) for i in range(MAX_PART_COUNT)]
        self.bpm = DEFAULT_BPM
        self.maxMeasure = 1
        self.tick_for_one_measure = DEFAULT_TICK_FOR_ONE_MEASURE
        self.port = midiport
        self.inputPart = 0      # 0origin
        self.waitForFine = False
        self.nextLoopStartTime = 0
        self.currentLoopStartTime = 0
        self.__stock_bpm = self.bpm
        self.__stock_tick_for_one_measure = self.tick_for_one_measure

    @property
    def stock_bpm(self):
        return self.__stock_bpm

    @stock_bpm.setter
    def stock_bpm(self, value):
        self.__stock_bpm = value

    @property
    def stock_tick_for_one_measure(self):
        return self.__stock_tick_for_one_measure

    @stock_tick_for_one_measure.setter
    def stock_tick_for_one_measure(self, value):
        self.__stock_tick_for_one_measure = value

    def get_whole_tick(self):
        return self.tick_for_one_measure*self.maxMeasure

    def __inputPhrase(self,data,pt):
        self.maxMeasure = 0
        tick = self.parts[pt].addPhrase(data)
        while tick > self.get_whole_tick():
            self.maxMeasure += 1

    def add_seq_description(self,data):
        self.parts[self.inputPart].add_seq_description(data)

    def clear_description(self):
        self.parts[self.inputPart].clear_description()

    def copyPhrase(self,pt):
        self.__inputPhrase(self.parts[self.inputPart].noteData, pt)

    def addPhrase(self,data):
        self.__inputPhrase(data, self.inputPart)

    def sendMidiNote(self, ch, nt, vel):
        if vel != 0:
            msg = mido.Message('note_on', channel=ch, note=nt, velocity=vel)
        else:
            msg = mido.Message('note_off', channel=ch, note=nt)
        self.port.send(msg)

    def __calc_max_measure(self):
        # 最大小節数の再計算
        self.maxMeasure = 0
        tick = 0
        for pt in self.parts:
            ptTick = pt.return_to_top()
            if ptTick > tick:
                tick = ptTick
        while tick > self.get_whole_tick():
            self.maxMeasure += 1

    def __goes_to_loop_top(self):
        # loop して先頭に戻った時
        if self.waitForFine == True:
            self.waitForFine = False
            self.stop()
            return False
            
        self.bpm = self.__stock_bpm
        self.tick_for_one_measure = self.__stock_tick_for_one_measure
        self.__calc_max_measure()
        self.currentLoopStartTime = self.nextLoopStartTime
        self.nextLoopStartTime += self.get_whole_tick()/(self.bpm*TICK_PER_SEC)
        return True

    def play(self):     # 演奏開始
        self.bpm = self.__stock_bpm
        if self.tick_for_one_measure != self.__stock_tick_for_one_measure:
            # beat が設定された場合
            self.tick_for_one_measure = self.__stock_tick_for_one_measure

        self.__calc_max_measure()
        self.currentLoopStartTime = 0
        self.nextLoopStartTime = self.get_whole_tick()/(self.bpm*TICK_PER_SEC)
        for pt in self.parts:
            pt.play()

    def generate_event(self, evTime):       # 演奏データの生成
        if evTime > self.nextLoopStartTime:
            if self.__goes_to_loop_top() == False:
                return 0

        current_tick = (evTime - self.currentLoopStartTime)*self.bpm*TICK_PER_SEC
        next_tick = self.get_whole_tick()
        for pt in self.parts:
            pt_next_tick = pt.generate_event(current_tick)
            if next_tick > pt_next_tick:
                next_tick = pt_next_tick

        return self.currentLoopStartTime + next_tick/(self.bpm*TICK_PER_SEC)

    def stop(self):
        # 演奏強制終了
        for pt in self.parts:
            pt.stop()

    def fine(self):
        # Blockの最後で演奏終了
        self.waitForFine = True



class Seq:
    #   MIDI シーケンスを再生する全体のまとめ処理
    #   開始時に生成され、periodic() がコマンド入力とは別スレッドで、定期的に呼ばれる
    #   その他の機能： mido の生成、CUIに情報を送る
    #   Block: 現状 [0] の一つだけ生成
    def __init__(self):
        self.startTime = time.time()
        self.duringPlay = False
        self.bk = []
        allPort = mido.get_output_names()
        print("MIDI OUT: " + allPort[-1])
        self.midiport = mido.open_output(allPort[-1])
        self.bk.append(Block(self.midiport))
        self.currentBk = self.bk[0]

    def getBlock(self, block=1):
        return self.bk[block-1]

    def periodic(self):
        if self.duringPlay == False:
            return
        currentTime = time.time() - self.startTime  # calculate elapsed time
        if currentTime > self.nextTime:             # if time of next event come,
            self.nextTime = self.currentBk.generate_event(currentTime)
            if self.nextTime == 0:
                self.duringPlay = False             # Stop playing

    def play(self, block=1, repeat='on'):
        self.duringPlay = True
        self.startTime = time.time()                # Get current time
        self.nextTime = 0
        self.currentBk = self.bk[block-1]
        self.currentBk.play()

    def stop(self):
        self.currentBk.stop()
        self.duringPlay = False

    def fine(self):
        print('Will be ended!')
        self.currentBk.fine()
