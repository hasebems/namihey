# -*- coding: utf-8 -*-
import pygame
from pygame.locals import *     # 定数を読み込む
import sys
import datetime

class Loop:
    running = True

class NamiGui:

    def __init__(self):
        super(NamiGui, self).__init__()
        pygame.init()
        self.SURFACE = pygame.display.set_mode((300, 300))    # サイズを指定して画面を作成
        pygame.display.set_caption("namihey")    # タイトル文字を指定
        self.font = pygame.font.Font(None, 28)   # フォントの設定

    def display_time(self):
        date = self.font.render(str(datetime.date.today()), True, 'magenta')
        time = self.font.render(datetime.datetime.now().strftime("%H:%M:%S"), True, 'lightblue')
        self.SURFACE.blit(date, [10, 10])   # 文字列の位置を指定
        self.SURFACE.blit(time, [150, 10])  # 文字列の位置を指定

    LAMP_START_X = 50
    LAMP_START_Y = 100
    LAMP_INTERVAL = 40

    def display_beat(self, seq):
        beat, tick, count = seq.get_tick()
        beat_str = self.font.render(str(beat+1) + ' : ' + str(tick), True, 'magenta')
        self.SURFACE.blit(beat_str, [40, 50])   # 文字列の位置を指定
        for i in range(count):
            color_str = 'lightblue'
            if i==beat:
                color_str = 'magenta'
            pygame.draw.circle(self.SURFACE,color_str, \
                (self.LAMP_START_X+i*self.LAMP_INTERVAL, self.LAMP_START_Y), 5)

    def debug_support(self, seq):
        value = seq.latest_clear_time      # 見たい変数を記載する
        debug = self.font.render(str(value), True, 'lightblue')
        #self.SURFACE.blit(debug, [10, 250])   # 文字列の位置を指定

    def main_loop(self, loop, seq):
        while True:
            self.SURFACE.fill((0,0,100))
            self.display_time()
            self.display_beat(seq)
            self.debug_support(seq)
            pygame.display.update()

            # イベントを処理
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()   # Pygameの終了（画面を閉じる）
                    return
            if not loop.running:
                pygame.quit()       # Pygameの終了（画面を閉じる）
                return


