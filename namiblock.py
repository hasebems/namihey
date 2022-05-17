# -*- coding: utf-8 -*-
import namipart as npt
import namilib as nlib
import namifile as nfl

STOP_PLAYING = -1

class PartOperator:
    #   各 Part が独立でループ出来るように、Part の tick 管理を行う
    def __init__(self, blk, num):
        self.part = npt.Part(blk, num)
        self.part_num = num
        self.max_msr = 1                # データが無くても 1、whole_tick より大きい小節数
        self.loop_next_tick = 0         # 次回 event の tick
        self.wait_for_looptop = False   # 次回 event が loop に戻るか
        self.whole_tick = 0             # Phrase Data の総 tick 数
#        self.looptop_msr = 0            # Loop start 時の絶対小節数(Measureにて計測)
        self.msr_counter = 0            # Loop 内の経過小節数
        self.one_msr_tick = 0

    def reset(self):
        self.max_msr = 1
        self.loop_next_tick = 0
        self.wait_for_looptop = False
        self.whole_tick = 0
        self.msr_counter = 0

    def msrtop(self):
        self.msr_counter += 1

    def return_to_looptop(self, one_msr_tick):
#        self.looptop_msr += 1
        self.one_msr_tick = one_msr_tick

        # 最大tick/小節数を算出する
        self.whole_tick = self.part.return_to_top(one_msr_tick)
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

    # 再生時の Part の制御 
    def generate_event_for_one_part(self, tick_inmsr):
        def nothing_todo():
            self.wait_for_looptop = True
            self.loop_next_tick = self.one_msr_tick

        # データが存在しない場合
        if self.whole_tick == 0:
            nothing_todo()
            return self.one_msr_tick

        # Loop 内での経過 tick の算出
        elapsed_tick = tick_inmsr + self._calc_elapsed_msr_tick()

        # 今回の tick に対応する Event 出力と、次回 tick の算出
        if elapsed_tick >= self.loop_next_tick and self.wait_for_looptop is False:
            self.loop_next_tick = self.part.generate_event(elapsed_tick) # <<Part>>
            nlib.log.record(str(elapsed_tick)+'=>'+str(self.loop_next_tick))  # DEBUG
            if self.loop_next_tick is nlib.END_OF_DATA:
                # このループの最後のイベントのとき
                self.loop_next_tick = self.max_msr*self.one_msr_tick - 1 # 最大値にしておく
                self.wait_for_looptop = True
                return self.one_msr_tick
            else:
                # 通常の再生時の次のtickを返す
                return self.next_tick_inmsr()
        else:
            nlib.log.record(str(elapsed_tick)+'xx'+str(self.loop_next_tick))  # DEBUG
            nothing_todo()
            return self.one_msr_tick


class Block:
    #   シーケンスの断片を Block という単位で扱う
    #   Part は見た目の Part に対して、二つの Part を用意しておく
    def __init__(self, nfl, md):
        self.md = md
        self.fl = nfl
        self.part_op = [PartOperator(self,i) for i in range(nlib.MAX_PART_COUNT*2)]
        self.which_op = [True for _ in range(nlib.MAX_PART_COUNT)]
        self.lock_new_dscrpt = [False for _ in range(nlib.MAX_PART_COUNT)]
        self.new_dscrpt_ev = [False for _ in range(nlib.MAX_PART_COUNT)]
        self.during_play = False
        self.wait_for_fine = False
        self.__stock_beat_info = [nlib.DEFAULT_TICK_FOR_ONE_MEASURE,4,4]
        self.beat_info = self.__stock_beat_info
        self.abs_tick_of_msrtop = 0
        self.abs_msr_counter = 0
        for i in range(nlib.MAX_PART_COUNT*2):
            self.md.send_control(i, 7, 88)

    def stock_beat_info(self, beat_list):
        self.__stock_beat_info = beat_list

    def get_beat_info(self):
        return self.beat_info

    def send_midi_cc(self, num, cc_num, val):
        self.md.send_control(num*2, cc_num, val)
        self.md.send_control(num*2+1, cc_num, val)

    def send_midi_pgn(self, num, pgn):
        self.md.send_program(num*2, pgn)
        self.md.send_program(num*2+1, pgn)

    def part_direct(self, num, which=True):
        return self.part_op[num*2].part if which else self.part_op[num*2+1].part

    def part(self, num):
        if self.during_play:
            return self.available_op(num, True).part
        else:
            return self.part_op[num*2].part

    def part_in_advance(self, num):
        if self.during_play:
            self.new_dscrpt_ev[num] = True
            return self.available_op(num, False).part
        else:
            return self.part_op[num*2].part

    def available_op(self, num, which=True):
        if which:
            return self.part_op[num*2] if self.which_op[num] else self.part_op[num*2+1]
        else:
            return self.part_op[num*2+1] if self.which_op[num] else self.part_op[num*2]

    def midi(self):
        return self.md

    def change_beat(self):
        # 拍子が変わったとき
        self.beat_info = self.__stock_beat_info

    def no_running(self):
        # beat_info に更新がないかチェック
        if self.beat_info != self.__stock_beat_info:
            self.change_beat()

    def set_chain_loading(self):
        for usr_part in range(nlib.MAX_PART_COUNT):
            op1 = self.part_op[usr_part*2]
            op2 = self.part_op[usr_part*2+1]
            if not self.lock_new_dscrpt[usr_part] and \
              ((self.which_op[usr_part] and op1.wait_for_looptop) or \
               (not self.which_op[usr_part] and op2.wait_for_looptop)):
                # wait_for_looptop 期間中に次の Description をセットする
                ninfo = self.fl.read_next_chain_loading(self, usr_part)
                if ninfo != nfl.NO_NOTE:
                    self.lock_new_dscrpt[usr_part] = True

    # 小節の先頭処理
    # ただし、シビアな再生タイミングに関わる処理ではない
    def change_part_on_msrtop(self):
        for usr_part in range(nlib.MAX_PART_COUNT):
            if self.new_dscrpt_ev[usr_part]:
                # Description セット後、最初の小節先頭処理
                # which_op を入れ替え、次の Description セット時のパートを変える
                self.which_op[usr_part] = not self.which_op[usr_part]
                self.new_dscrpt_ev[usr_part] = False
                if self.fl.chain_loading_state:
                    # Chain loading 時は、データセットのロックを外す
                    self.lock_new_dscrpt[usr_part] = False
        for op in self.part_op:
            # Part Operator に小節先頭であることを知らせる
            op.msrtop()

    # 全パートの再生処理    tick_inmsr: 小節内 tick
    def generate_block_event(self, tick_inmsr):
        # 直近の次のイベントtickを探すため、まず２小節先の値にしておく
        next_tick = self.beat_info[0]*2
        for op in self.part_op:
            # 小節内の次のイベントがあるtick
            pt_next_tick = op.next_tick_inmsr()
            if tick_inmsr > pt_next_tick:
                if op.wait_for_looptop:
                    # loop 先頭に戻す
                    op.return_to_looptop(self.beat_info[0])
                # イベントの再生 & 一番近い将来のイベントがある tick
                pt_next_tick = op.generate_event_for_one_part(tick_inmsr)

            if next_tick > pt_next_tick:
                next_tick = pt_next_tick
        return next_tick + self.abs_tick_of_msrtop # 絶対 tick を返す

    ### Main IF : Start Sequencer
    def start(self):
        # for chain loading
        if self.fl.chain_loading_state:
            self.fl.read_first_chain_loading(self)

        # block の初期化
        self.which_op = [True for _ in range(nlib.MAX_PART_COUNT)]
        self.lock_new_dscrpt = [False for _ in range(nlib.MAX_PART_COUNT)]
        self.new_dscrpt_ev = [False for _ in range(nlib.MAX_PART_COUNT)]
        self.during_play = True
        self.wait_for_fine = False
        self.abs_tick_of_msrtop = 0
        self.abs_msr_counter = 0
        for op in self.part_op:
            op.reset()
            op.return_to_looptop(self.beat_info[0])
            op.part.start() # <<Part>>

    ### Main IF : Periodic
    def generate_event(self, ev_tick):
        # 小節先頭チェック
        next_msrtop = self.beat_info[0] + self.abs_tick_of_msrtop
        if ev_tick > next_msrtop:
            if self.wait_for_fine:
                # Fine で終了
                self.wait_for_fine = False
                self.stop()
                return STOP_PLAYING

            # beat_info に更新がないかチェック
            if self.beat_info != self.__stock_beat_info:
                self.change_beat()

            # 小節先頭処理
            self.abs_tick_of_msrtop += self.beat_info[0]
            next_msrtop += self.beat_info[0]
            self.abs_msr_counter += 1
            self.change_part_on_msrtop()

        # ev_tick を超えたノートを再生
        tick_inmsr = ev_tick - self.abs_tick_of_msrtop
        abs_tick = self.generate_block_event(tick_inmsr)
        if abs_tick > next_msrtop:
            abs_tick = next_msrtop  # 小節先頭イベントは必ず得る

        # Chain Loading
        if self.fl.chain_loading_state:
            self.set_chain_loading()

        return abs_tick     # 次回コール時の絶対 tick を返す

    ### Main IF : Stop Sequencer
    def stop(self):
        # 演奏強制終了
        for op in self.part_op:
            op.part.stop()  # <<Part>>
        self.during_play = False

    ### Main IF : Stop like music
    def fine(self):
        # Blockの最後で演奏終了
        self.wait_for_fine = True
