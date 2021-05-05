# -*- coding: utf-8 -*-
import time
#import mido
import pygame.midi as pmd
import namiconf as ncf
import namipart as npt
import namilib as nlib


TICK_PER_SEC = 8    # convert [bpm] to [tick per sec] := 480(tick)/60(sec)
STOP_PLAYING = -1


class Block:
    #   シーケンスの断片を Block という単位で扱う
    #   本クラスは Block の IF を表す抽象クラス
    def __init__(self, midiport):
        self.port = midiport
        self.__stock_bpm = ncf.DEFAULT_BPM
        self.__stock_tick_for_one_measure = [nlib.DEFAULT_TICK_FOR_ONE_MEASURE,4,4]
        self.su_one_measure_time = 0       # 1小節の時間の長さ

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
    def stock_tick_for_one_measure(self, beat_list):
        self.__stock_tick_for_one_measure = beat_list

    def send_midi_note(self, ch, nt, vel):
        if nt > 127 or vel > 127: return
        if vel != 0:
            self.port.note_on(nt, velocity=vel, channel=ch)
        else:
            self.port.note_off(nt, channel=ch)
        nlib.log.record(str(nt)+'-'+str(vel))

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
        self.parts = [npt.Part(self, i) for i in range(ncf.MAX_PART_COUNT)]
        self.bpm = ncf.DEFAULT_BPM
        self.tick_for_one_measure = [nlib.DEFAULT_TICK_FOR_ONE_MEASURE,4,4]
        self.max_measure = 0
        self.inputPart = 0      # 0origin
        self.waitForFine = False
        self.next_loop_start_time = 0      # 次回 loop 先頭の Start からの経過時間
        self.current_loop_start_time = 0   # 現 loop 先頭の Start からの経過時間

    def get_whole_tick(self):
        return self.tick_for_one_measure[0]*self.max_measure

    def _input_phrase(self, data, pt):
        self.max_measure = 0
        tick = self.parts[pt].add_seq_description(data)
        while tick > self.get_whole_tick():
            self.max_measure += 1

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

    def _return_to_loop_top(self, ev_time=0):
        # bpm/beat に変更があった場合
        if self.bpm is not self.stock_bpm or \
          self.tick_for_one_measure is not self.stock_tick_for_one_measure:
            self.bpm = self.stock_bpm
            self.tick_for_one_measure = self.stock_tick_for_one_measure
            self.su_one_measure_time = self.tick_for_one_measure[0]/(self.bpm*TICK_PER_SEC) # 1小節の長さ

        # loop 先頭に戻り、loop 小節数の再計算
        self.max_measure = 0
        largest_tick = 0    # 全パートの最大 tick を調べる
        for pt in self.parts:
            pt_tick = pt.return_to_top(self.tick_for_one_measure[0]) # <<Part>>
            if pt_tick > largest_tick:
                largest_tick = pt_tick
        while largest_tick > self.get_whole_tick():
            self.max_measure += 1

        # 今回の Loop Start と次回の Loop Start の時間を更新
        self.current_loop_start_time = self.next_loop_start_time
        self.next_loop_start_time += self.get_whole_tick()/(self.bpm*TICK_PER_SEC)

    # Main IF : Start Sequencer
    def start(self):
        self.next_loop_start_time = 0
        self.su_one_measure_time = self.tick_for_one_measure[0]/(self.bpm*TICK_PER_SEC) # 1小節の長さ
        self._return_to_loop_top()

        if self.get_whole_tick() == 0:
            return False

        for pt in self.parts:
            pt.start()  # <<Part>>
        return True

    # Main IF : Generate Music Event
    def generate_event(self, ev_time):
        clear_ev = False
        # Loop 先頭かどうかの判断
        if ev_time > self.next_loop_start_time:
            if self.waitForFine:
                # Fine で終了
                self.waitForFine = False
                self.stop()
                return STOP_PLAYING, True
            else:
                # loop 先頭に戻る
                clear_ev = True
                self._return_to_loop_top(ev_time)

        # Part ごとのイベント処理
        current_tick = (ev_time - self.current_loop_start_time)*self.bpm*TICK_PER_SEC
        next_tick = self.get_whole_tick() # 最大値で初期化
        for pt in self.parts:
            pt_next_tick = pt.generate_event(current_tick)  # <<Part>>
            if pt_next_tick != nlib.END_OF_DATA and next_tick > pt_next_tick:
                next_tick = pt_next_tick

        return self.current_loop_start_time + next_tick/(self.bpm*TICK_PER_SEC), clear_ev    # time(sec)

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
            self.max_measure = 1  # データが無くても、loop start time を更新するため、1にしておく
            self.next_tick = 0              # 次回 event の tick
            self.has_looped = False         # 次回 event が loop に戻るか
            self.current_loop_start_time = 0   # 現 loop 先頭の Start からの経過時間
            self.total_tick = 0             # Data の長さ
            self.next_time = 0              # 次回 event の時間

        def reset(self):
            self.max_measure = 1
            self.next_tick = 0
            self.has_looped = False
            self.current_loop_start_time = 0
            self.total_tick = 0
            self.next_time = 0

    #   BlockIndependentLoop は、Block を継承して、block の各 part が独立で loop する
    def __init__(self, midiport):
        super().__init__(midiport)
        self.part_operator = [self.PartOperator(self,i) for i in range(ncf.MAX_PART_COUNT)]
        self.bpm = ncf.DEFAULT_BPM
        self.tick_for_one_measure = [nlib.DEFAULT_TICK_FOR_ONE_MEASURE,4,4]
        self.inputPart = 0      # 0origin
        self.waitForFine = False
        self.su_reset_time = 0             # 最後のtempo/bpm変更時の絶対時間
        self.su_current_measure = 0        # 現在の通算小節数

    def get_whole_tick(self, op):
        return self.tick_for_one_measure[0]*op.max_measure

    def _input_phrase(self, data, pt):
        op = self.part_operator[pt]
        op.max_measure = 1
        tick = op.part.add_seq_description(data)
        while tick > self.get_whole_tick(op):
            op.max_measure += 1

    def add_seq_description(self, data):
        op = self.part_operator[self.inputPart]
        op.part.add_seq_description(data)

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

    def _return_to_loop_top(self, op, start_time=0):
        # Part の loop 先頭に戻り、loop 小節数の再計算
        #if op.current_loop_start_time+0.5 >= start_time:
        #    nlib.log.record('No Measure Count!')  # DEBUG
        op.current_loop_start_time = start_time
        op.max_measure = 1
        op.total_tick = op.part.return_to_top(self.tick_for_one_measure[0]) # <<Part>>
        while op.total_tick > self.get_whole_tick(op):
            op.max_measure += 1

    def _generate_event_for_one_part(self, op, current_tick):
        if op.total_tick == 0:
            op.has_looped = True
            return self.tick_for_one_measure[0]

        # 今回の tick に対応する Event 出力と、次回 tick の算出
        if current_tick >= op.next_tick:
            op.next_tick = op.part.generate_event(current_tick) # <<Part>>
            nlib.log.record(str(current_tick)+'=>'+str(op.next_tick))  # DEBUG
            if op.next_tick is not nlib.END_OF_DATA:
                return op.next_tick
            else:
                op.next_tick = 0
                op.has_looped = True
                return self.tick_for_one_measure[0]*op.max_measure
        else:
            nlib.log.record(str(current_tick)+'xx'+str(op.next_tick))  # DEBUG
            op.has_looped = True
            return self.tick_for_one_measure[0]*op.max_measure

    # Main IF : Start Sequencer
    def start(self):
        # block の初期化
        self.bpm = self.stock_bpm
        self.tick_for_one_measure = self.stock_tick_for_one_measure
        self.su_current_measure = 0
        self.su_reset_time = 0
        self.su_one_measure_time = self.tick_for_one_measure[0]/(self.bpm*TICK_PER_SEC) # 1小節の長さ

        for op in self.part_operator:
            op.reset()
            self._return_to_loop_top(op)
            op.current_loop_start_time = 0
            op.part.start() # <<Part>>
        return True

    # Main IF : Generate Music Event
    def generate_event(self, ev_time):
        clear_ev = False
        ev_timex = ev_time - self.su_reset_time    # ev_timex は、Tempo/beat が変わった以降の経過時間
        real_measure = int(ev_timex/self.su_one_measure_time)
        if real_measure > self.su_current_measure:
            # 小節先頭
            self.su_current_measure = real_measure
            clear_ev = True
            if self.waitForFine:
                # Fine で終了
                self.waitForFine = False
                self.stop()
                return STOP_PLAYING, True

            if self.bpm is not self.stock_bpm or \
              self.tick_for_one_measure is not self.stock_tick_for_one_measure:
                self.start()    # Tempo が変わったら、Start からやり直す
                self.su_reset_time = ev_time
                return 0, True

        next_time = (real_measure+100)*self.su_one_measure_time # 100小節先に初期値設定
        for op in self.part_operator:
            if ev_timex > op.next_time:
                if op.has_looped:
                    # loop 先頭に戻る
                    self._return_to_loop_top(op, real_measure*self.su_one_measure_time)
                    op.has_looped = False
                current_tick = (ev_timex - op.current_loop_start_time)*self.bpm*TICK_PER_SEC
                pt_next_tick = self._generate_event_for_one_part(op, current_tick)
                op.next_time = op.current_loop_start_time + pt_next_tick/(self.bpm*TICK_PER_SEC)
            # 一番近い将来のイベントがある時間算出
            if next_time > op.next_time:
                next_time = op.next_time
        return next_time, clear_ev

    # Main IF : Stop Sequencer
    def stop(self):
        # 演奏強制終了
        for op in self.part_operator:
            op.part.stop()  # <<Part>>

    def fine(self):
        # Blockの最後で演奏終了
        self.waitForFine = True


class Seq:
    #   MIDI シーケンスの制御
    #   開始時に生成され、periodic() がコマンド入力とは別スレッドで、定期的に呼ばれる
    #   その他の機能： mido の生成、CUIに情報を送る
    #   Block: 現状 [0] の一つだけ生成
    def __init__(self):
        # MIDI settings
        pmd.init()
        devnum = pmd.get_count()
        self.all_port = []
        lastid = 0
        self.port_name = ''
        for i in range(devnum):
            dev = pmd.get_device_info(i)
            if dev[3] == 1:
                self.all_port.append(dev[1].decode())
                lastid = i
                self.port_name = dev[1].decode()
        self.midi_port = pmd.Output(lastid)

        self.start_time = time.time()
        self.during_play = False
        self.bk = [BlockRegular(self.midi_port), BlockIndependentLoop(self.midi_port)]
        self.current_bk = self.bk[0]
        self.next_time = 0
        self.current_time = 0
        self.latest_clear_time = 0

    def get_midi_all_port(self):
        return self.all_port

    def get_tick(self):
        tm = 0
        one_beat = 1
        block_tick_info = self.current_bk.tick_for_one_measure
        tm = self.current_time - self.latest_clear_time
        one_beat = 60/(self.current_bk.bpm*(block_tick_info[2]/4)) # 1拍の時間
        while tm > one_beat*block_tick_info[1]:
            tm -= one_beat*block_tick_info[1]
        return int(tm//one_beat), int((tm%one_beat)*1000/one_beat), block_tick_info[1]

    def get_midi_port(self):
        return self.port_name

    def set_midi_port(self, idx):
        if idx < len(self.all_port):
            self.port_name = self.all_port[idx]
            return True
        else: return False

    def block(self):
        return self.current_bk

    def change_block(self, blk):
        self.current_bk = self.bk[blk]

    def periodic(self):     # 別スレッド
        if not self.during_play:
            return
        self.current_time = time.time() - self.start_time  # calculate elapsed time
        if self.current_time > self.next_time:             # if time of next event come,
            # Call Block
            self.next_time, clear_ev = self.current_bk.generate_event(self.current_time)
            if self.next_time == STOP_PLAYING:
                self.during_play = False             # Stop playing
            if clear_ev:
                self.latest_clear_time = self.current_time

    def play(self, repeat='on'):
        if self.during_play: return False
        self.during_play = True
        self.start_time = time.time()                # Get current time
        self.next_time = 0
        self.latest_clear_time = 0
        return self.current_bk.start()

    def stop(self):
        self.current_bk.stop()
        self.during_play = False

    def fine(self):
        self.current_bk.fine()
