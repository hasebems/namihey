# -*- coding: utf-8 -*-
import  time
import  mido
import  namiconf
import  namipart as npt
import  namilib as nlib


MAX_PART_COUNT = 16
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
        self.tick_for_one_measure = nlib.DEFAULT_TICK_FOR_ONE_MEASURE
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

    def _inputPhrase(self,data,pt):
        self.maxMeasure = 0
        tick = self.parts[pt].addPhrase(data)
        while tick > self.get_whole_tick():
            self.maxMeasure += 1

    def add_seq_description(self,data):
        self.parts[self.inputPart].add_seq_description(data)

    def clear_description(self):
        self.parts[self.inputPart].clear_description()

    def copyPhrase(self,pt):
        self._inputPhrase(self.parts[self.inputPart].noteData, pt)

    def addPhrase(self,data):
        self._inputPhrase(data, self.inputPart)

    def sendMidiNote(self, ch, nt, vel):
        if nt > 127 or vel > 127: return
        if vel != 0:
            msg = mido.Message('note_on', channel=ch, note=nt, velocity=vel)
        else:
            msg = mido.Message('note_off', channel=ch, note=nt)
        self.port.send(msg)

    def _calc_max_measure(self):
        # 最大小節数の再計算
        self.maxMeasure = 0
        tick = 0
        for pt in self.parts:
            ptTick = pt.return_to_top(self.tick_for_one_measure)
            if ptTick > tick:
                tick = ptTick
        while tick > self.get_whole_tick():
            self.maxMeasure += 1

    def _goes_to_loop_top(self):
        # loop して先頭に戻った時
        if self.waitForFine == True:
            self.waitForFine = False
            self.stop()
            return False
            
        self.bpm = self.__stock_bpm
        self.tick_for_one_measure = self.__stock_tick_for_one_measure
        self._calc_max_measure()
        self.currentLoopStartTime = self.nextLoopStartTime
        self.nextLoopStartTime += self.get_whole_tick()/(self.bpm*TICK_PER_SEC)
        return True

    # Main IF : Start Sequencer
    def start(self):
        self.bpm = self.__stock_bpm
        if self.tick_for_one_measure != self.__stock_tick_for_one_measure:
            # beat が設定された場合
            self.tick_for_one_measure = self.__stock_tick_for_one_measure

        self._calc_max_measure()
        self.currentLoopStartTime = 0
        self.nextLoopStartTime = self.get_whole_tick()/(self.bpm*TICK_PER_SEC)
        for pt in self.parts:
            pt.start()

    # Main IF : Generate Music Event
    def generate_event(self, evTime):
        if evTime > self.nextLoopStartTime:
            if self._goes_to_loop_top() == False:
                return 0

        current_tick = (evTime - self.currentLoopStartTime)*self.bpm*TICK_PER_SEC
        next_tick = self.get_whole_tick()
        for pt in self.parts:
            pt_next_tick = pt.generate_event(current_tick)
            if pt_next_tick != -1 and next_tick > pt_next_tick:
                next_tick = pt_next_tick

        return self.currentLoopStartTime + next_tick/(self.bpm*TICK_PER_SEC)

    # Main IF : Stop Sequencer
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
        self.start_time = time.time()
        self.during_play = False
        self.bk = []
        all_port = mido.get_output_names()
        print("MIDI OUT: " + all_port[-1])
        midiport = mido.open_output(all_port[-1])
        self.bk.append(Block(midiport))
        self.current_bk = self.bk[0]
        self.next_time = 0

    def getBlock(self, block=1):
        return self.bk[block-1]

    def periodic(self):
        if self.during_play == False:
            return
        currentTime = time.time() - self.start_time  # calculate elapsed time
        if currentTime > self.next_time:             # if time of next event come,
            self.next_time = self.current_bk.generate_event(currentTime)
            if self.next_time == 0:
                self.during_play = False             # Stop playing

    def play(self, block=1, repeat='on'):
        self.during_play = True
        self.start_time = time.time()                # Get current time
        self.next_time = 0
        self.current_bk = self.bk[block-1]
        self.current_bk.start()

    def stop(self):
        self.current_bk.stop()
        self.during_play = False

    def fine(self):
        print('Will be ended!')
        self.current_bk.fine()
