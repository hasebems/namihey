# -*- coding: utf-8 -*-
import pygame
from pygame.locals import *     # 定数を読み込む
import sys
import datetime
import namiconf as ncf

class Loop:
    running = True

class NamiGui:

    SURFACE_X_SZ = 890  #   Window Size
    SURFACE_Y_SZ = 120  #   Window Size

#====================================================================
#               COLUMN1             COLUMN2                 COLUMN3
#               COLUMN12        COLUMN21 COLUMN22       COLUMN31
#           +---------------+-----------------------+-------------
#   LINE1   |               |                       |           
#           +---------------+-----------------------+
#   LINE2   |               |
#           +---------------+--------
#   LINE3   |               |
#           +-----------------------------------------------------
#
#====================================================================

    # 縦の位置
    LINE1_Y = 10
    LINE2_Y = 50
    LINE3_Y = 90
    LAMP_OFS = 10

    # 横の位置
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
        pygame.display.set_caption("Namihey Indicator")    # タイトル文字を指定
        self.font = pygame.font.Font(None, 28)   # フォントの設定

    def _display_time(self):
        date = self.font.render(str(datetime.date.today()), True, 'magenta')
        time = self.font.render(datetime.datetime.now().strftime("%H:%M:%S"), True, 'lightblue')
        self.SURFACE.blit(date, [NamiGui.COLUMN1_X, NamiGui.LINE1_Y])   # 文字列の位置を指定
        self.SURFACE.blit(time, [NamiGui.COLUMN12_X, NamiGui.LINE1_Y])  # 文字列の位置を指定

    def _display_beat(self, seq):
        bpm_str = self.font.render('bpm : ' + str(seq.current_bk.bpm), True, 'lightblue')
        self.SURFACE.blit(bpm_str, [NamiGui.COLUMN2_X, NamiGui.LINE1_Y])   # 文字列の位置を指定
        beat, tick, count = seq.get_tick()
        beat_str = self.font.render(str(beat+1) + ' : ' + str(tick), True, 'magenta')
        self.SURFACE.blit(beat_str, [NamiGui.COLUMN21_X, NamiGui.LINE2_Y])   # 文字列の位置を指定
        for i in range(count):
            color_str = 'lightblue'
            if i==beat:
                color_str = 'magenta'
            pygame.draw.circle(self.SURFACE,color_str, \
                (NamiGui.COLUMN2_X+i*NamiGui.LAMP_INTERVAL, NamiGui.LINE3_Y+NamiGui.LAMP_OFS), 5)

    def _display_part(self, seq):
        for num in range(ncf.MAX_PART_COUNT):
            self.SURFACE.blit(self.font.render(str(num+1), True, 'lightblue'), \
                [NamiGui.COLUMN3_X+num*NamiGui.PART_INTERVAL, NamiGui.LINE1_Y])
            color_str = 'lightblue'
            pt = seq.current_bk.part(num)
            if len(pt.retained_note) > 0:
                color_str = 'magenta'
            pygame.draw.circle(self.SURFACE, color_str, \
                (NamiGui.COLUMN31_X+num*NamiGui.PART_INTERVAL, NamiGui.LINE2_Y+NamiGui.LAMP_OFS), 5)
            self.SURFACE.blit(self.font.render(str(pt.keynote-60), True, 'lightblue'), \
                [NamiGui.COLUMN3_X+num*NamiGui.PART_INTERVAL, NamiGui.LINE3_Y])

    def _debug_support(self, seq):
        value = '<Debug Space>'      # 見たい変数を記載する
        debug = self.font.render(str(value), True, 'lightblue')
        self.SURFACE.blit(debug, [NamiGui.COLUMN1_X, NamiGui.LINE3_Y])

    def main_loop(self, loop, seq):
        clock = pygame.time.Clock()
        while True:
            clock.tick(60)     # 60FPS
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
