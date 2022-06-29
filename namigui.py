# -*- coding: utf-8 -*-
import pygame
from pygame.locals import *     # 定数を読み込む
import datetime
import namilib as nlib

BACK_COLOR = ((100,0,0),(0,100,0),(0,0,100))

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

    COLUMN2_X = 380
    COLUMN21_X = 410
    COLUMN22_X = 440
    LAMP_INTERVAL = 40

    COLUMN3_X = 594     # Part Number
    COLUMN31_X = 600    # Part Sound Indicator
    PART_INTERVAL = 40

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((self.SURFACE_X_SZ, self.SURFACE_Y_SZ))
        pygame.display.set_caption("Namihey Indicator")    # タイトル文字を指定
        self.font = pygame.font.Font(None, 28)   # フォントの設定

    def _display_time(self):
        title = self.font.render('[Namihey]~~> Text MIDI Sequencer', True, 'lightblue')
        date = self.font.render(str(datetime.date.today()), True, 'magenta')
        time = self.font.render(datetime.datetime.now().strftime("%H:%M:%S"), True, 'lightblue')
        self.screen.blit(title, [NamiGui.COLUMN1_X, NamiGui.LINE1_Y])  # 文字列の位置を指定
        self.screen.blit(date, [NamiGui.COLUMN1_X, NamiGui.LINE2_Y])   # 文字列の位置を指定
        self.screen.blit(time, [NamiGui.COLUMN12_X, NamiGui.LINE2_Y])  # 文字列の位置を指定

    def _display_song(self, nfl, seq):
        if nfl.loaded_file is None or \
           nfl.chain_loading_state is False or \
           seq.during_play is False:
            return
        title = self.font.render(nfl.loaded_file, True, 'magenta')
        self.screen.blit(title, [NamiGui.COLUMN1_X, NamiGui.LINE3_Y])   # 文字列の位置を指定
    
    def _display_beat(self, seq):
        bpm_str = self.font.render('bpm : ' + str(seq.tempo), True, 'lightblue')
        self.screen.blit(bpm_str, [NamiGui.COLUMN2_X, NamiGui.LINE1_Y])   # 文字列の位置を指定
        msr, beat, tick, count = seq.get_tick()
        beat_str = self.font.render(str(msr) + ' : ' + str(beat+1) + ' : ' + str(tick), True, 'magenta')
        self.screen.blit(beat_str, [NamiGui.COLUMN2_X, NamiGui.LINE2_Y])   # 文字列の位置を指定
        for i in range(count):
            color_str = 'lightblue'
            if i==beat:
                color_str = 'magenta'
            pygame.draw.circle(self.screen,color_str, \
                (NamiGui.COLUMN2_X+i*NamiGui.LAMP_INTERVAL, NamiGui.LINE3_Y+NamiGui.LAMP_OFS), 5)

    def _display_part(self, seq):
        for num in range(nlib.MAX_PART_COUNT):
            self.screen.blit(self.font.render(str(num+1), True, 'lightblue'), \
                [NamiGui.COLUMN3_X+num*NamiGui.PART_INTERVAL, NamiGui.LINE1_Y])
            color_str = 'lightblue'
            if len(seq.get_note(num)) > 0:
                color_str = 'magenta'
            pygame.draw.circle(self.screen, color_str, \
                (NamiGui.COLUMN31_X+num*NamiGui.PART_INTERVAL, NamiGui.LINE2_Y+NamiGui.LAMP_OFS), 5)
            self.screen.blit(self.font.render(str(seq.get_part(num).keynote-60), True, 'lightblue'), \
                [NamiGui.COLUMN3_X+num*NamiGui.PART_INTERVAL, NamiGui.LINE3_Y])

    def _debug_support(self, seq):
        value = len(seq.sqobjs) # value に見たい変数値を代入する(seqから辿れるもの)
        debug = self.font.render('Sqobj. Num: '+str(value), True, 'lightblue')
        self.screen.blit(debug, [NamiGui.COLUMN1_X, NamiGui.LINE3_Y])

    def main_loop(self, loop, seq, pas, nfl):
        clock = pygame.time.Clock()
        while True:
            clock.tick(60)     # 60FPS
            self.screen.fill(BACK_COLOR[pas.back_color])
            self._display_time()
            self._display_song(nfl,seq)
            self._display_beat(seq)
            self._display_part(seq)
            self._debug_support(seq)
            # 画面更新
            pygame.display.update()

            # イベントを処理
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()   # Pygameの終了（画面を閉じる）
                    return
            if not loop.running:
                pygame.quit()       # Pygameの終了（画面を閉じる）
                return
