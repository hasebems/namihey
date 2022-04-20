# -*- coding: utf-8 -*-
import namiconf as ncf
import namipart as npt
import namilib as nlib

STOP_PLAYING = -1


class TimeTick:

    def __init__(self):
        self.bpm = ncf.DEFAULT_BPM
        self.msr_info = [nlib.DEFAULT_TICK_FOR_ONE_MEASURE,4,4]
        self.crnt_msr = 0
        self.last_msr_time = 0
        self._calc_one_msr_time()

    def _calc_one_msr_time(self):
        self.one_msr_time = self.msr_info[0]/self.TICK_PER_SEC()

    def TICK_PER_SEC(self): # convert [bpm] to [tick per sec] := 480(tick)/60(sec)
        return 8*self.bpm

    def start(self, bpm, tick_for_one_measure):
        self.bpm = bpm
        self.msr_info = tick_for_one_measure
        self.crnt_msr = 0
        self.last_msr_time = 0
        self._calc_one_msr_time()

    def measure_top(self):
        self.crnt_msr += 1
        self.last_msr_time += self.one_msr_time

    def set_bpm(self, bpm):
        self.bpm = bpm
        self._calc_one_msr_time()

    def set_tick_for_one_measure(self, tick_for_one_measure):
        self.msr_info = tick_for_one_measure
        self._calc_one_msr_time()

    def get_one_msr_tick(self):
        return self.msr_info[0]

    def get_one_msr_time(self):  # 1小節の時間
        self._calc_one_msr_time()
        return self.one_msr_time


class Block:
    #   シーケンスの断片を Block という単位で扱う
    #   本クラスは Block の IF を表す抽象クラス

    def __init__(self, midiport):
        self.port = midiport
        self.__stock_bpm = ncf.DEFAULT_BPM
        self.__stock_tick_for_one_measure = [nlib.DEFAULT_TICK_FOR_ONE_MEASURE,4,4]
        self.tt = TimeTick()

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

    def get_tick_info(self):
        return self.tt.msr_info

    def send_midi_note(self, ch, nt, vel):
        if nt > 127 or vel > 127: return
        if vel != 0:
            self.port.note_on(nt, velocity=vel, channel=ch)
        else:
            self.port.note_off(nt, channel=ch)
        nlib.log.record(str(ch)+'-'+str(nt)+'-'+str(vel))

    def send_control(self, ch, cntnum, value):
        if ch < 16 and cntnum < 128 and value < 128:
            self.port.write_short(0xb0+ch, cntnum, value)

    def send_program(self, ch, pgn):
        if ch < 16 and pgn < 128:
            self.port.set_instrument(pgn, channel=ch)

    def part(self, num):
        return 0

    def max_part(self):
        return 0

    # Main IF : Start Sequencer
    def start(self):
        pass

    # Main IF : Periodic
    def generate_event(self, ev_time, cl):
        pass

    # Main IF : Stop Sequencer
    def stop(self):
        pass

    # Main IF : Stop like music
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
        self.max_measure = 0
        self.inputPart = 0      # 0origin
        self.waitForFine = False
        self.next_loop_start_time = 0      # 次回 loop 先頭の Start からの経過時間
        self.current_loop_start_time = 0   # 現 loop 先頭の Start からの経過時間

    def get_whole_tick(self):
        return self.tt.get_one_msr_tick()*self.max_measure

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

    def _return_to_loop_top(self, cl=None, ev_time=0):
        # bpm/beat に変更があった場合
        if self.tt.bpm is not self.stock_bpm:
            self.tt.set_bpm(self.stock_bpm)
        if self.tt.tick_for_one_measure is not self.stock_tick_for_one_measure:
            self.tt.set_tick_for_one_measure(self.stock_tick_for_one_measure)

        # loop 先頭に戻り、loop 小節数の再計算
        self.max_measure = 0
        largest_tick = 0    # 全パートの最大 tick を調べる
        tick_one = self.tt.get_one_msr_tick()
        for pt in self.parts:
            pt_tick = pt.return_to_top(tick_one, cl)
            if pt_tick > largest_tick:
                largest_tick = pt_tick
        while largest_tick > self.get_whole_tick():
            self.max_measure += 1

        # 今回の Loop Start と次回の Loop Start の時間を更新
        self.current_loop_start_time = self.next_loop_start_time
        self.next_loop_start_time += self.get_whole_tick()/self.tt.TICK_PER_SEC()

    # Main IF : Start Sequencer
    def start(self):
        self.next_loop_start_time = 0
        self._return_to_loop_top()

        if self.get_whole_tick() == 0:
            return False

        for pt in self.parts:
            pt.start()  # <<Part>>
        return True

    # Main IF : Generate Music Event
    def generate_event(self, ev_time, cl):
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
                self._return_to_loop_top(cl, ev_time)

        # Part ごとのイベント処理
        current_tick = (ev_time - self.current_loop_start_time)*self.tt.TICK_PER_SEC()
        next_tick = self.get_whole_tick() # 最大値で初期化
        for i, pt in enumerate(self.parts):
            pt_next_tick = pt.generate_event(current_tick)  # <<Part>>
            if pt_next_tick != nlib.END_OF_DATA and next_tick > pt_next_tick:
                next_tick = pt_next_tick

        return self.current_loop_start_time + next_tick/self.tt.TICK_PER_SEC(), \
               clear_ev    # time(sec)

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
            self.max_msr = 1    # データが無くても、loop start time を更新するため、1にしておく
            self.next_tick = 0              # 次回 event の tick
            self.wait_for_looptop = False   # 次回 event が loop に戻るか
            self.whole_tick = 0             # Phrase Data の総 tick 数
            self.looptop_msr = 0            # Loop start 時の絶対小節数(Measureにて計測)

        def reset(self):
            self.max_msr = 1
            self.next_tick = 0
            self.wait_for_looptop = False
            self.whole_tick = 0

        def is_same_measure(self, tt):
            return self.looptop_msr == tt.crnt_msr

        def return_to_looptop(self, tt, cl=None):
            # 最大tick/小節数を算出する
            self.looptop_msr = tt.crnt_msr
            one_msr_tick = tt.get_one_msr_tick()
            self.whole_tick = self.part.return_to_top(one_msr_tick, cl)
            self.wait_for_looptop = False
            self.next_tick = 0
            nlib.log.record(str(self.part_num)+': looptop')  # DEBUG
            self.max_msr = 1
            while self.whole_tick > one_msr_tick*self.max_msr:
                self.max_msr += 1

        def _calc_elapsed_msr_tick(self, tt):
            msr_diff = tt.crnt_msr - self.looptop_msr
            return tt.get_one_msr_tick()*msr_diff

        def next_tick_inmsr(self, tt):
            return self.next_tick - self._calc_elapsed_msr_tick(tt)

        def generate_event_for_one_part(self, tt, tick_inmsr):
            def nothing_todo(tt):
                self.wait_for_looptop = True
                self.next_tick = tt.get_one_msr_tick()
                return tt.get_one_msr_tick()

            elapsed_tick = tick_inmsr + self._calc_elapsed_msr_tick(tt)
            if self.whole_tick == 0:    # データが存在しない
                return nothing_todo(tt)

            # 今回の tick に対応する Event 出力と、次回 tick の算出
            if elapsed_tick >= self.next_tick and self.wait_for_looptop is False:
                self.next_tick = self.part.generate_event(elapsed_tick) # <<Part>>
                nlib.log.record(str(elapsed_tick)+'=>'+str(self.next_tick))  # DEBUG
                if self.next_tick is nlib.END_OF_DATA:
                    self.next_tick = self.max_msr*tt.get_one_msr_tick() # 最大値にしておく
                    self.wait_for_looptop = True
                    return tt.get_one_msr_tick()
                else:
                    return self.next_tick_inmsr(tt)
            else:
                nlib.log.record(str(elapsed_tick)+'xx'+str(self.next_tick))  # DEBUG
                return nothing_todo(tt)


    #   BlockIndependentLoop は、Block を継承して、block の各 part が独立で loop する
    def __init__(self, midiport):
        super().__init__(midiport)
        self.part_operator = [self.PartOperator(self,i) for i in range(ncf.MAX_PART_COUNT)]
        self.inputPart = 0      # 0origin
        self.waitForFine = False

    def get_whole_tick(self, op):
        return self.tt.get_one_msr_tick()*op.max_msr

    def _input_phrase(self, data, pt):
        op = self.part_operator[pt]
        op.max_msr = 1
        tick = op.part.add_seq_description(data)
        while tick > self.get_whole_tick(op):
            op.max_msr += 1

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

    # Main IF : Start Sequencer
    def start(self):
        # block の初期化
        self.tt.start(self.stock_bpm, self.stock_tick_for_one_measure)
        for op in self.part_operator:
            op.reset()
            op.return_to_looptop(self.tt)
            op.part.start() # <<Part>>
        return True

    # Main IF : Generate Music Event
    def generate_event(self, ev_time, cl):
        def in_msr(tt):
            ev_time_inmsr = ev_time - tt.last_msr_time          # この小節内の時間
            tick_inmsr = ev_time_inmsr * tt.TICK_PER_SEC()      # この小節内のtick
            return ev_time_inmsr, tick_inmsr

        tt = self.tt
        ev_time_inmsr, tick_inmsr = in_msr(tt)
        if ev_time_inmsr > tt.get_one_msr_time():
            # 小節先頭
            tt.measure_top()
            ev_time_inmsr, tick_inmsr = in_msr(tt)
            if self.waitForFine:
                # Fine で終了
                self.waitForFine = False
                self.stop()
                return STOP_PLAYING, True

            if tt.bpm is not self.stock_bpm:
                tt.set_bpm(self.stock_bpm)
                return ev_time, True # 現在時を返すので、すぐにまた呼ばれる
            if tt.get_one_msr_tick() is not self.stock_tick_for_one_measure[0]:
                tt.set_tick_for_one_measure(self.stock_tick_for_one_measure)
                return ev_time, True # 現在時を返すので、すぐにまた呼ばれる

        next_tick = tt.get_one_msr_tick()*2  # 最大値として2小節分のtick値
        for op in self.part_operator:
            pt_next_tick = op.next_tick_inmsr(tt)
            if tick_inmsr > pt_next_tick:
                if op.wait_for_looptop:
                    # loop 先頭に戻る
                    op.return_to_looptop(tt, cl)
                # 一番近い将来のイベントがある時間算出
                pt_next_tick = op.generate_event_for_one_part(tt, tick_inmsr)
            if next_tick > pt_next_tick:
                next_tick = pt_next_tick
        return tt.last_msr_time + next_tick/tt.TICK_PER_SEC(), False

    # Main IF : Stop Sequencer
    def stop(self):
        # 演奏強制終了
        for op in self.part_operator:
            op.part.stop()  # <<Part>>

    def fine(self):
        # Blockの最後で演奏終了
        self.waitForFine = True
