# -*- coding: utf-8 -*-
import pygame
from pygame.locals import *     # 定数を読み込む
import sys
import datetime
import namiconf as ncf

class Loop:
    running = True

class NamiGui:

    SURFACE_X_SZ = 880  #   Window Size
    SURFACE_Y_SZ = 120  #   Window Size

    LINE1_Y = 10
    LINE2_Y = 50
    LINE3_Y = 90
    POINT_OFS = 10

    COLUMN1_X = 10
    COLUMN12_X = 150

    COLUMN2_X = 300
    COLUMN21_X = 330
    COLUMN22_X = 360
    LAMP_INTERVAL = 40

    COLUMN3_X = 594     # Part Number
    COLUMN31_X = 600    # Part Sound Indicator
    PART_INTERVAL = 40

    def __init__(self):
        super(NamiGui, self).__init__()
        pygame.init()
        self.SURFACE = pygame.display.set_mode((self.SURFACE_X_SZ, self.SURFACE_Y_SZ))
        pygame.display.set_caption("namihey")    # タイトル文字を指定
        self.font = pygame.font.Font(None, 28)   # フォントの設定

    def _display_time(self):
        date = self.font.render(str(datetime.date.today()), True, 'magenta')
        time = self.font.render(datetime.datetime.now().strftime("%H:%M:%S"), True, 'lightblue')
        self.SURFACE.blit(date, [self.COLUMN1_X, self.LINE1_Y])   # 文字列の位置を指定
        self.SURFACE.blit(time, [self.COLUMN12_X, self.LINE1_Y])  # 文字列の位置を指定

    def _display_beat(self, seq):
        bpm_str = self.font.render('bpm : ' + str(seq.current_bk.bpm), True, 'lightblue')
        self.SURFACE.blit(bpm_str, [self.COLUMN2_X, self.LINE1_Y])   # 文字列の位置を指定
        beat, tick, count = seq.get_tick()
        beat_str = self.font.render(str(beat+1) + ' : ' + str(tick), True, 'magenta')
        self.SURFACE.blit(beat_str, [self.COLUMN21_X, self.LINE2_Y])   # 文字列の位置を指定
        for i in range(count):
            color_str = 'lightblue'
            if i==beat:
                color_str = 'magenta'
            pygame.draw.circle(self.SURFACE,color_str, \
                (self.COLUMN2_X+i*self.LAMP_INTERVAL, self.LINE3_Y+self.POINT_OFS), 5)

    def _display_part(self, seq):
        for num in range(ncf.MAX_PART_COUNT):
            self.SURFACE.blit(self.font.render(str(num+1), True, 'lightblue'), \
                [self.COLUMN3_X+num*self.PART_INTERVAL, self.LINE1_Y])
            color_str = 'lightblue'
            pt = seq.current_bk.part(num)
            if len(pt.retained_note) > 0:
                color_str = 'magenta'
            pygame.draw.circle(self.SURFACE, color_str, \
                (self.COLUMN31_X+num*self.PART_INTERVAL, self.LINE2_Y+self.POINT_OFS), 5)
            self.SURFACE.blit(self.font.render(str(pt.keynote-60), True, 'lightblue'), \
                [self.COLUMN3_X+num*self.PART_INTERVAL, self.LINE3_Y])

    def _debug_support(self, seq):
        value = seq.latest_clear_time      # 見たい変数を記載する
        debug = self.font.render(str(value), True, 'lightblue')
        #self.SURFACE.blit(debug, [10, 250])   # 文字列の位置を指定

    def main_loop(self, loop, seq):
        while True:
            self.SURFACE.fill((0,0,100))
            self._display_time()
            self._display_beat(seq)
            self._display_part(seq)
            self._debug_support(seq)
            pygame.display.update()

            # イベントを処理
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()   # Pygameの終了（画面を閉じる）
                    return
            if not loop.running:
                pygame.quit()       # Pygameの終了（画面を閉じる）
                return


