# -*- coding: utf-8 -*-
import time
import mido
import namiconf
import namipart as npt
import namilib as nlib


MAX_PART_COUNT = 16
DEFAULT_BPM = 100
TICK_PER_SEC = 8    # convert [bpm] to [tick per sec] := 480(tick)/60(sec)
STOP_PLAYING = 0


class Block:
    #   シーケンスの断片を Block という単位で扱う
    #   本クラスは Block の IF を表す抽象クラス
    def __init__(self, midiport):
        self.port = midiport

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

    def send_midi_note(self, ch, nt, vel):
        if nt > 127 or vel > 127: return
        if vel != 0:
            msg = mido.Message('note_on', channel=ch, note=nt, velocity=vel)
        else:
            msg = mido.Message('note_off', channel=ch, note=nt)
        self.port.send(msg)

    def part(self, num):
        return 0

    def max_part(self):
        return 0

    # Main IF : Stop Sequencer
    def start(self):
        pass

    # Main IF : Stop Sequencer
    def generate_event(self, ev_time):
        pass

    # Main IF : Stop Sequencer
    def stop(self):
        pass

    # Main IF : Stop Sequencer
    def fine(self):
        pass


class BlockRegular(Block):
    #   BlockRegular は、Block を継承して、block 全体で一つの loop の長さを持つデータを保持する
    #   Block 内に最大 MAX_PART_COUNT part持つことができる
    #   CUI からの情報を取得後、 Part に渡し、generate_event() で MIDI OUT する
    #
    #   tick は Block の長さ全体で管理（１小節単位ではなく）
    #   各 part への generate_event() では、loop 内の現在の tick を送る
    #   なお、その part の最大 tick を覚えておいて、それを超えた場合、
    #       現在tick - 最大tick
    #   の値を part に送り、loop 先頭から再度鳴らす
    def __init__(self, midiport):
        super().__init__(midiport)
        self.parts = [npt.Part(self, i) for i in range(MAX_PART_COUNT)]
        self.bpm = DEFAULT_BPM
        self.maxMeasure = 0
        self.tick_for_one_measure = nlib.DEFAULT_TICK_FOR_ONE_MEASURE
        self.inputPart = 0      # 0origin
        self.waitForFine = False
        self.nextLoopStartTime = 0      # 次回 loop 先頭の Start からの経過時間
        self.currentLoopStartTime = 0   # 現 loop 先頭の Start からの経過時間
        self.__stock_bpm = self.bpm
        self.__stock_tick_for_one_measure = self.tick_for_one_measure

    def get_whole_tick(self):
        return self.tick_for_one_measure*self.maxMeasure

    def _input_phrase(self, data, pt):
        self.maxMeasure = 0
        tick = self.parts[pt].add_seq_description(data)
        while tick > self.get_whole_tick():
            self.maxMeasure += 1

    def add_seq_description(self, data):
        self.parts[self.inputPart].add_seq_description(data)

    def clear_description(self):
        self.parts[self.inputPart].clear_description()

    def copy_phrase(self, pt):
        self._input_phrase(self.parts[self.inputPart].description, pt)

#    def add_phrase(self, data):
#        self._input_phrase(data, self.inputPart)

    def part(self, num):
        return self.parts[num]

    def max_part(self):
        return len(self.parts)

    def _return_to_loop_top(self):
        # 前回の loop 時に来た値を、loop 先頭で反映
        self.bpm = self.__stock_bpm
        self.tick_for_one_measure = self.__stock_tick_for_one_measure

        # loop 先頭に戻り、loop 小節数の再計算
        self.maxMeasure = 0
        largest_tick = 0    # 全パートの最大 tick を調べる
        for pt in self.parts:
            pt_tick = pt.return_to_top(self.tick_for_one_measure) # <<Part>>
            if pt_tick > largest_tick:
                largest_tick = pt_tick
        while largest_tick > self.get_whole_tick():
            self.maxMeasure += 1

        # 今回の Loop Start と次回の Loop Start の時間を更新
        self.currentLoopStartTime = self.nextLoopStartTime
        self.nextLoopStartTime += self.get_whole_tick()/(self.bpm*TICK_PER_SEC)

    # Main IF : Start Sequencer
    def start(self):
        self.nextLoopStartTime = 0
        self._return_to_loop_top()

        if self.get_whole_tick() == 0:
            return False

        for pt in self.parts:
            pt.start()  # <<Part>>
        return True

    # Main IF : Generate Music Event
    def generate_event(self, ev_time):
        if ev_time > self.nextLoopStartTime:
            if self.waitForFine:
                # Fine で終了
                self.waitForFine = False
                self.stop()
                return STOP_PLAYING
            else:
                # loop 先頭に戻る
                self._return_to_loop_top()

        current_tick = (ev_time - self.currentLoopStartTime)*self.bpm*TICK_PER_SEC
        next_tick = self.get_whole_tick() # 最大値で初期化
        for pt in self.parts:
            pt_next_tick = pt.generate_event(current_tick)  # <<Part>>
            if pt_next_tick != nlib.END_OF_DATA and next_tick > pt_next_tick:
                next_tick = pt_next_tick

        return self.currentLoopStartTime + next_tick/(self.bpm*TICK_PER_SEC)    # time(sec)

    # Main IF : Stop Sequencer
    def stop(self):
        # 演奏強制終了
        for pt in self.parts:
            pt.stop()  # <<Part>>

    def fine(self):
        # Blockの最後で演奏終了
        self.waitForFine = True


class BlockIndependentLoop(Block):

    class PartOperator:
        def __init__(self, blk, num):
            self.part = npt.Part(blk, num)
            self.part_num = num
            self.maxMeasure = 1  # データが無くても、loop start time を更新するため、1にしておく
            self.next_tick = 0
            self.nextLoopStartTime = 0      # 次回 loop 先頭の Start からの経過時間
            self.currentLoopStartTime = 0   # 現 loop 先頭の Start からの経過時間

        def reset(self):
            self.maxMeasure = 1
            self.next_tick = 0
            self.nextLoopStartTime = 0
            self.currentLoopStartTime = 0

    #   BlockIndependentLoop は、Block を継承して、block の各 part が独立で loop する
    def __init__(self, midiport):
        super().__init__(midiport)
        self.part_operator = [self.PartOperator(self,i) for i in range(MAX_PART_COUNT)]
        self.bpm = DEFAULT_BPM
        self.tick_for_one_measure = nlib.DEFAULT_TICK_FOR_ONE_MEASURE
        self.inputPart = 0      # 0origin
        self.waitForFine = False
        self.__stock_bpm = self.bpm
        self.__stock_tick_for_one_measure = self.tick_for_one_measure
        self.last_time = 0          # 前回の時間
        self.current_measure = 0    # 現在の通算小節数

    def get_whole_tick(self, op):
        return self.tick_for_one_measure*op.maxMeasure

    def _input_phrase(self, data, pt):
        op.maxMeasure = 1
        op = self.part_operator[pt]
        tick = op.part.add_seq_description(data)
        while tick > self.get_whole_tick(op):
            op.maxMeasure += 1

    def add_seq_description(self, data):
        self.part_operator[self.inputPart].part.add_seq_description(data)

    def clear_description(self):
        self.part_operator[self.inputPart].part.clear_description()

    def copy_phrase(self, pt):
        print('No Support!')
        #self._input_phrase(self.part_operator[self.inputPart].part.description, pt)

#    def add_phrase(self, data):
#        self._input_phrase(data, self.inputPart)

    def part(self, num):
        return self.part_operator[num].part

    def max_part(self):
        return len(self.part_operator)

    def _return_to_loop_top(self, op):
        # Part の loop 先頭に戻り、loop 小節数の再計算
        op.maxMeasure = 1
        total_tick = op.part.return_to_top(self.tick_for_one_measure) # <<Part>>
        while total_tick > self.get_whole_tick(op):
            op.maxMeasure += 1
        # Part の Loop Start Time, Next Loop Start Time を算出
        op.currentLoopStartTime = op.nextLoopStartTime
        op.nextLoopStartTime += self.get_whole_tick(op)/(self.bpm*TICK_PER_SEC)

    # Main IF : Start Sequencer
    def start(self):
        # block の初期化
        self.bpm = self.__stock_bpm
        self.tick_for_one_measure = self.__stock_tick_for_one_measure
        self.last_time = 0
        self.current_measure = 0

        for op in self.part_operator:
            op.reset()
            self._return_to_loop_top(op)

            if self.get_whole_tick(op) == 0:
                return False
            op.part.start() # <<Part>>
        return True

    # Main IF : Generate Music Event
    def generate_event(self, ev_time):
        one_measure_time = self.tick_for_one_measure/(self.bpm*TICK_PER_SEC) # 1小節の長さ
        next_time = ev_time + one_measure_time
        if int(self.last_time/one_measure_time) < int(ev_time/one_measure_time):
            # 小節先頭
            self.bpm = self.__stock_bpm
            self.tick_for_one_measure = self.__stock_tick_for_one_measure
            self.current_measure = int(ev_time/one_measure_time)

        for op in self.part_operator:
            if ev_time > op.nextLoopStartTime:
                # loop 先頭に戻る
                self._return_to_loop_top(op)

            pt_next_time = op.nextLoopStartTime
            current_tick = (ev_time - op.currentLoopStartTime)*self.bpm*TICK_PER_SEC
            if current_tick > op.next_tick:
                op.next_tick = op.part.generate_event(current_tick) # <<Part>>
                if op.next_tick != nlib.END_OF_DATA:
                    pt_next_time = op.currentLoopStartTime + op.next_tick/(self.bpm*TICK_PER_SEC)
                else:
                    op.next_tick = 0
            # 一番近い将来のイベントがある時間算出
            if next_time > pt_next_time:
                next_time = pt_next_time

        self.last_time = ev_time
        return next_time

    # Main IF : Stop Sequencer
    def stop(self):
        # 演奏強制終了
        for op in self.part_operator:
            op.part.stop()  # <<Part>>


class Seq:
    #   MIDI シーケンスの制御
    #   開始時に生成され、periodic() がコマンド入力とは別スレッドで、定期的に呼ばれる
    #   その他の機能： mido の生成、CUIに情報を送る
    #   Block: 現状 [0] の一つだけ生成
    def __init__(self):
        self.start_time = time.time()
        self.during_play = False
        self.bk = []
        self.all_port = mido.get_output_names()
        self.port_name = self.all_port[-1]
        midi_port = mido.open_output(self.port_name)
        self.bk.append(BlockIndependentLoop(midi_port))
        self.current_bk = self.bk[0]
        self.next_time = 0

    def get_midi_all_port(self):
        return self.all_port

    def get_midi_port(self):
        return self.port_name

    def set_midi_port(self, idx):
        if idx < len(self.all_port):
            self.port_name = self.all_port[idx]
            return True
        else: return False

    def block(self, block=1):
        return self.bk[block-1]

    def periodic(self):
        if not self.during_play:
            return
        current_time = time.time() - self.start_time  # calculate elapsed time
        if current_time > self.next_time:             # if time of next event come,
            self.next_time = self.current_bk.generate_event(current_time)
            if self.next_time == STOP_PLAYING:
                self.during_play = False             # Stop playing

    def play(self, block=1, repeat='on'):
        if self.during_play: return False
        self.during_play = True
        self.start_time = time.time()                # Get current time
        self.next_time = 0
        self.current_bk = self.bk[block-1]
        return self.current_bk.start()

    def stop(self):
        self.current_bk.stop()
        self.during_play = False

    def fine(self):
        self.current_bk.fine()
