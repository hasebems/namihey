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

    LETTER_L1_X = 10
    LETTER_L1_Y = 10

    LETTER_L2_START_X = 80 
    LETTER_L2_Y = 50

    LAMP_START_X = 50
    LAMP_START_Y = 100
    LAMP_INTERVAL = 40

    PTNUM_START_X = 294 # Part Number
    PART_START_X = 300  # Part Sound Indicator
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
        self.SURFACE.blit(date, [self.LETTER_L1_X, self.LETTER_L1_Y])   # 文字列の位置を指定
        self.SURFACE.blit(time, [150, self.LETTER_L1_Y])  # 文字列の位置を指定

    def _display_beat(self, seq):
        beat, tick, count = seq.get_tick()
        beat_str = self.font.render(str(beat+1) + ' : ' + str(tick), True, 'magenta')
        self.SURFACE.blit(beat_str, [self.LETTER_L2_START_X, self.LETTER_L2_Y])   # 文字列の位置を指定
        for i in range(count):
            color_str = 'lightblue'
            if i==beat:
                color_str = 'magenta'
            pygame.draw.circle(self.SURFACE,color_str, \
                (self.LAMP_START_X+i*self.LAMP_INTERVAL, self.LAMP_START_Y), 5)

    def _display_part(self, seq):
        for num, pt in enumerate(seq.current_bk.parts):
            self.SURFACE.blit(self.font.render(str(num+1), True, 'lightblue'), \
                [self.PTNUM_START_X+num*self.PART_INTERVAL, self.LETTER_L2_Y])
            color_str = 'lightblue'
            if len(pt.retained_note) > 0:
                color_str = 'magenta'
            pygame.draw.circle(self.SURFACE, color_str, \
                (self.PART_START_X+num*self.PART_INTERVAL, self.LAMP_START_Y), 5)

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


