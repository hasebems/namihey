# -*- coding: utf-8 -*-
import namipart as npt
import namilib as nlib

STOP_PLAYING = -1

class PartOperator:
    #   各 Part が独立してループするために、Block 内部に Part の時間計測のための
    #   Class を持ち、そこから Part のメソドを呼び出す
    def __init__(self, blk, num):
        self.part = npt.Part(blk, num)
        self.part_num = num
        self.max_msr = 1                # データが無くても 1、whole_tick より大きい小節数
        self.loop_next_tick = 0         # 次回 event の tick
        self.wait_for_looptop = False   # 次回 event が loop に戻るか
        self.whole_tick = 0             # Phrase Data の総 tick 数
        self.looptop_msr = 0            # Loop start 時の絶対小節数(Measureにて計測)
        self.msr_counter = 0
        self.one_msr_tick = 0

    def reset(self):
        self.max_msr = 1
        self.loop_next_tick = 0
        self.wait_for_looptop = False
        self.whole_tick = 0
        self.msr_counter = 0

    #def is_same_measure(self, tt):
    #    return self.looptop_msr == tt.crnt_msr

    def msrtop(self):
        self.msr_counter += 1

    def return_to_looptop(self, one_msr_tick, cl=None):
        # 最大tick/小節数を算出する
        self.looptop_msr += 1
        self.one_msr_tick = one_msr_tick
        self.whole_tick = self.part.return_to_top(one_msr_tick, cl)
        self.wait_for_looptop = False
        self.loop_next_tick = 0
        self.msr_counter = 0
        nlib.log.record(str(self.part_num)+': looptop')  # DEBUG
        # loop の小節数の算出
        self.max_msr = 1
        while self.whole_tick > one_msr_tick*self.max_msr:
            self.max_msr += 1

    def _calc_elapsed_msr_tick(self):
        return self.one_msr_tick*self.msr_counter

    def next_tick_inmsr(self):
        return self.loop_next_tick - self._calc_elapsed_msr_tick()

    def generate_event_for_one_part(self, tick_inmsr):
        def nothing_todo():
            self.wait_for_looptop = True
            self.loop_next_tick = self.one_msr_tick

        elapsed_tick = tick_inmsr + self._calc_elapsed_msr_tick()
        if self.whole_tick == 0:    # データが存在しない
            nothing_todo()
            return self.one_msr_tick

        # 今回の tick に対応する Event 出力と、次回 tick の算出
        if elapsed_tick >= self.loop_next_tick and self.wait_for_looptop is False:
            self.loop_next_tick = self.part.generate_event(elapsed_tick) # <<Part>>
            nlib.log.record(str(elapsed_tick)+'=>'+str(self.loop_next_tick))  # DEBUG
            if self.loop_next_tick is nlib.END_OF_DATA:
                self.loop_next_tick = self.max_msr*self.one_msr_tick # 最大値にしておく
                self.wait_for_looptop = True
                return self.one_msr_tick
            else:
                return self.next_tick_inmsr()
        else:
            nlib.log.record(str(elapsed_tick)+'xx'+str(self.loop_next_tick))  # DEBUG
            nothing_todo()
            return self.one_msr_tick


class Block:
    #   シーケンスの断片を Block という単位で扱う
    #   本クラスは Block の IF を表す抽象クラス

    def __init__(self, md):
        self.md = md
        self.part_operator = [PartOperator(self,i) for i in range(nlib.MAX_PART_COUNT)]
        self.wait_for_fine = False
        self.__stock_beat_info = [nlib.DEFAULT_TICK_FOR_ONE_MEASURE,4,4]
        self.beat_info = self.__stock_beat_info
        self.tick_inmsr = 0
        self.abs_tick_of_msrtop = 0
        self.abs_msr_counter = 0
        for i in range(5):
            self.md.send_control(i, 7, 7)

    def stock_beat_info(self, beat_list):
        self.__stock_beat_info = beat_list

    def get_beat_info(self):
        return self.beat_info

    def part(self, num):
        return self.part_operator[num].part

    def midi(self):
        return self.md

    def change_beat(self):
        # 拍子が変わったとき
        self.beat_info = self.__stock_beat_info

    def no_running(self):
        # beat_info に更新がないかチェック
        if self.beat_info != self.__stock_beat_info:
            self.change_beat()

    # Main IF : Start Sequencer
    def start(self):
        # block の初期化
        self.wait_for_fine = False
        self.tick_inmsr = 0
        self.abs_tick_of_msrtop = 0
        self.abs_msr_counter = 0
        for op in self.part_operator:
            op.reset()
            op.return_to_looptop(self.beat_info[0])
            op.part.start() # <<Part>>

    # Main IF : Periodic
    def generate_event(self, ev_tick, cl):
        # 小節先頭チェック
        next_msrtop = self.beat_info[0] + self.abs_tick_of_msrtop
        if ev_tick > next_msrtop:
            if self.wait_for_fine:
                # Fine で終了
                self.wait_for_fine = False
                self.stop()
                return STOP_PLAYING

            # 小節先頭処理
            self.abs_tick_of_msrtop += self.beat_info[0]

            # beat_info に更新がないかチェック
            if self.beat_info != self.__stock_beat_info:
                self.change_beat()

            # 小節カウンタの更新
            self.abs_msr_counter += 1
            for op in self.part_operator:
                op.msrtop()

        # 全パートに対して、現在の tick を超えたイベントを出力
        # また、次のイベントの tick を調べ、一番最近のものを return とする
        # next_tick: とりあえず最大値を２小節分にしておく
        next_tick = self.beat_info[0]*2
        self.tick_inmsr = ev_tick - self.abs_tick_of_msrtop
        for op in self.part_operator:
            pt_next_tick = op.next_tick_inmsr()
            if self.tick_inmsr > pt_next_tick:
                if op.wait_for_looptop:
                    # loop 先頭に戻る
                    op.return_to_looptop(self.beat_info[0], cl)
                # 一番近い将来のイベントがある時間算出
                pt_next_tick = op.generate_event_for_one_part(self.tick_inmsr)
            if next_tick > pt_next_tick:
                next_tick = pt_next_tick
        return next_tick + self.abs_tick_of_msrtop # 絶対 tick を返す

    # Main IF : Stop Sequencer
    def stop(self):
        # 演奏強制終了
        for op in self.part_operator:
            op.part.stop()  # <<Part>>

    # Main IF : Stop like music
    def fine(self):
        # Blockの最後で演奏終了
        self.wait_for_fine = True
