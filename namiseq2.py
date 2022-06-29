# -*- coding: utf-8 -*-
import time
import namilib as nlib
import namiseqpart as sqp

####
# Tempo 生成の考え方
#   1. Tempo 変化時の絶対時間とその時点の tick を記録
#   2. 次に Tempo が変わるまで、その時間との差から、現在の tick を算出する
#   また、本 class 内に rit. 機構を持つ
#
class Seq2:
    #   開始時に生成され、periodic() がコマンド入力とは別スレッドで、定期的に呼ばれる。
    #   そのため、change_tempo, play, stop 受信時はフラグのみを立て、periodic()
    #   で実処理を行う。
    def __init__(self, md):
        self.origin_time = 0        # start 時の絶対時間
        self.bpm_start_time = 0     # tempo/beat が変わった時点の絶対時間、tick 計測の開始時間
        self.bpm_start_tick = 0     # tempo が変わった時点の tick, beat が変わったとき0clear
        self.beat_start_msr = 0     # beat が変わった時点の経過小節数
        self.elapsed_time = 0       # start からの経過時間
        self.crnt_measure = -1      # start からの小節数（最初の小節からイベントを出すため、-1初期化)
        self.crnt_tick_inmsr = 0    # 現在の小節内の tick 数

        self.tempo = 120
        self.beat = [4,4]
        self.tick_for_onemsr = nlib.DEFAULT_TICK_FOR_ONE_MEASURE # 1920
        self.stock_tick_for_onemsr = [nlib.DEFAULT_TICK_FOR_ONE_MEASURE,4,4]

        self.during_play = False
        self.play_for_periodic = False
        self.stop_for_periodic = False
        self.fine_for_periodic = False

        self.md = md
        self.sqobjs = []
        for i in range(nlib.MAX_PART_COUNT):
            obj = sqp.SeqPart(self,md,i)
            self.sqobjs.append(obj)

    def add_sqobj(self, obj):
        self.sqobjs.append(obj)
        #print(len(self.sqobjs))

    def get_tick_for_onemsr(self):
        return self.tick_for_onemsr

    def get_part(self, number):
        if number < nlib.MAX_PART_COUNT:
            return self.sqobjs[number]
        else:
            return None

    def get_note(self, part_num):
        nt = []
        for obj in self.sqobjs:
            if obj.type == 'Note' and obj.midi_ch == part_num:
                nt.append(obj)
        return nt

#    def file_auto_play(self, pas):
#        if self.fl.auto_stop:   # check end of chain loading
#            self.fl.auto_stop = False
#            #pas.print_dialogue("The End!")
#            pas.return_to_normal()

    def get_tick(self): # for GUI
        tick_for_beat = nlib.DEFAULT_TICK_FOR_ONE_MEASURE/self.beat[1]  # 一拍のtick数
        tick_inmsr = self.crnt_tick_inmsr
        count = self.tick_for_onemsr//tick_for_beat
        beat = tick_inmsr//tick_for_beat
        tick = tick_inmsr%tick_for_beat
        return self.crnt_measure+1,int(beat),int(tick),int(count)

    def _calc_current_tick(self, crnt_time):
        diff_time = crnt_time - self.bpm_start_time
        one_tick = 60/(480*self.tempo)
        return diff_time/one_tick + self.bpm_start_tick

    def _play(self):
        self.bpm_start_time = self.origin_time = time.time()  # Get current time
        self.bpm_start_tick = 0
        self.beat_start_msr = 0
        self.elapsed_time = 0

    def _destroy_ended_obj(self):
        maxsq = len(self.sqobjs)
        removed_num = -1
        while removed_num < maxsq:
            removed_num = -1
            for i in range(maxsq):
                if self.sqobjs[i].destroy_me():
                    self.sqobjs.pop(i)
                    removed_num = i
                    break
            if removed_num == -1: break
            maxsq = len(self.sqobjs)
            #print('Destroyed!')

    def periodic(self):     # seqplay thread
        ## check flags
        if self.play_for_periodic and not self.during_play:
            self.play_for_periodic = False
            self._play()
            self.during_play = True
            for sqobj in self.sqobjs:
                sqobj.start()

        if self.stop_for_periodic:
            self.stop_for_periodic = False
            self.during_play = False
            for sqobj in self.sqobjs:
                sqobj.stop()
            self._destroy_ended_obj()

        if not self.during_play:
            #self.block.no_running()
            return

        ## detect tick and measure
        current_time = time.time()
        tick_beat_starts = self._calc_current_tick(current_time)
        self.elapsed_time = current_time - self.origin_time
        former_msr = self.crnt_measure
        self.crnt_measure = int(tick_beat_starts//self.tick_for_onemsr + self.beat_start_msr)
        self.crnt_tick_inmsr = int(tick_beat_starts%self.tick_for_onemsr)

        ## new measure or not
        if former_msr is not self.crnt_measure:
            # 小節を跨いだ場合
            if self.stock_tick_for_onemsr[0] is not self.tick_for_onemsr:
                # change beat event があった
                self.beat_start_msr = self.crnt_measure
                self.bpm_start_time = current_time
                self.bpm_start_tick = 0
                self.tick_for_onemsr = self.stock_tick_for_onemsr[0]
                self.beat = self.stock_tick_for_onemsr[1:3]

            if self.fine_for_periodic:
                # fine event
                self.fine_for_periodic = False
                self.during_play = False
                for sqobj in self.sqobjs:
                    sqobj.fine()
                self._destroy_ended_obj()
                return

            ## new measure
            for sqobj in self.sqobjs:
                sqobj.msrtop(self.crnt_measure)

        ## play seqplay_object
        for sqobj in self.sqobjs:
            sqobj.periodic(self.crnt_measure, self.crnt_tick_inmsr)

        ## remove ended obj
        self._destroy_ended_obj()


    def change_tempo(self, tempo):     # command thread
        current_time = time.time()
        self.bpm_start_tick = self._calc_current_tick(current_time)
        self.bpm_start_time = current_time  # Get current time
        self.tempo = tempo

    def change_beat(self, beat):    # beat: number of ticks of one measure
        self.stock_tick_for_onemsr = beat

    def start(self):     # command thread
        self.play_for_periodic = True
        if self.during_play is False:
            return True
        else:
            return False

    def stop(self):     # command thread
        self.stop_for_periodic = True

    def fine(self):     # command thread
        self.fine_for_periodic = True
