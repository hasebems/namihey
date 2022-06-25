# -*- coding: utf-8 -*-
import time
import namiblock as blk
import namilib as nlib

####
# Tempo 生成の考え方
#   1. Tempo 変化時の絶対時間とその時点の tick を記録
#   2. 次に Tempo が変わるまで、その時間との差から、現在の tick を算出する
#   また、本 class 内に rit. 機構を持つ
#
####
# Event 受信の考え方
#   - queue を利用して、スレッドを跨いだメッセージを送る
#   - フラグを利用して、スレッドを跨いだ bool 情報を送る
#
class Seq2:
    #   開始時に生成され、periodic() がコマンド入力とは別スレッドで、定期的に呼ばれる。
    #   そのため、change_tempo, play, stop 受信時はフラグのみを立て、periodic()
    #   で実処理を行う。
    def __init__(self):
        self.origin_time = 0        # start 時の絶対時間
        self.bpm_start_time = 0     # tempo/beat が変わった時点の絶対時間、tick 計測の開始時間
        self.bpm_start_tick = 0     # tempo が変わった時点の tick, beat が変わったとき0clear
        self.beat_start_msr = 0     # beat が変わった時点の経過小節数
        self.elapsed_time = 0       # start からの経過時間
        self.crnt_measure = 0       # start からの小節数
        self.crnt_tick_inmsr = 0    # 現在の小節内の tick 数

        self.tempo = 120
        self.beat = [4,4]
        self.tick_for_onemsr = nlib.DEFAULT_TICK_FOR_ONE_MEASURE # 1920
        self.stock_tick_for_onemsr = [nlib.DEFAULT_TICK_FOR_ONE_MEASURE,4,4]

        self.during_play = False
        self.play_for_periodic = False
        self.stop_for_periodic = False
        self.fine_for_periodic = False

#    def file_auto_play(self, pas):
#        if self.fl.auto_stop:   # check end of chain loading
#            self.fl.auto_stop = False
#            #pas.print_dialogue("The End!")
#            pas.return_to_normal()

    def get_tick(self): # for GUI
        tick_for_beat = nlib.DEFAULT_TICK_FOR_ONE_MEASURE/self.beat[1]
        tick_inmsr = self.crnt_tick_inmsr
        count = self.tick_for_onemsr//tick_for_beat
        beat = tick_inmsr//tick_for_beat
        tick = tick_inmsr%tick_for_beat
        return self.crnt_measure+1,int(beat),int(tick),int(count)

    def _calc_current_tick(self, crnt_time):
        diff_time = crnt_time - self.bpm_start_time
        one_tick = 60/(480*self.tempo)
        return diff_time/one_tick + self.bpm_start_tick

    def start(self):
        self.bpm_start_time = self.origin_time = time.time()  # Get current time
        self.bpm_start_tick = 0
        self.beat_start_msr = 0
        self.elapsed_time = 0

    def periodic(self):     # seqplay thread
        ## check flags
        if self.play_for_periodic and not self.during_play:
            self.play_for_periodic = False
            self.start()
            self.during_play = True

        if self.stop_for_periodic:
            self.stop_for_periodic = False
            #self.block.stop()
            self.during_play = False

        if self.fine_for_periodic:
            self.fine_for_periodic = False
            #self.block.fine()

        if not self.during_play:
            #self.block.no_running()
            return

        ## detect tick and measure
        current_time = time.time()
        tick_beat_starts = self._calc_current_tick(current_time)
        self.elapsed_time = current_time - self.origin_time
        former_msr = self.crnt_measure
        self.crnt_measure = int(tick_beat_starts//self.tick_for_onemsr + self.beat_start_msr)
        self.crnt_tick_inmsr = tick_beat_starts%self.tick_for_onemsr

        if former_msr is not self.crnt_measure:
            # 小節を跨いだ
            if self.stock_tick_for_onemsr[0] is not self.tick_for_onemsr:
                # change beat event があった
                self.beat_start_msr = self.crnt_measure
                self.bpm_start_time = current_time
                self.bpm_start_tick = 0
                self.tick_for_onemsr = self.stock_tick_for_onemsr[0]
                self.beat = self.stock_tick_for_onemsr[1:3]

        ## play seqplay_object




    def change_tempo(self, tempo):     # command thread
        current_time = time.time()
        self.bpm_start_tick = self._calc_current_tick(current_time)
        self.bpm_start_time = current_time  # Get current time
        self.tempo = tempo

    def change_beat(self, beat):    # beat: number of ticks of one measure
        self.stock_tick_for_onemsr = beat

    def play(self):     # command thread
        self.play_for_periodic = True
        if self.during_play is False:
            return True
        else:
            return False

    def stop(self):     # command thread
        self.stop_for_periodic = True

    def fine(self):     # command thread
        self.fine_for_periodic = True
