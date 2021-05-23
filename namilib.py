# -*- coding: utf-8 -*-
import datetime

REST = 1000
NONE = 1000
DEFAULT_TICK_FOR_ONE_MEASURE = 1920  # 480 * 4
END_OF_DATA = -1

CHORD_SCALE = {  # ±2オクターブ分
    'all': [-24, -23, -22, -21, -20, -19, -18, -17, -16, -15, -14, -13, -12, -11, -10, -9, -8, -7, -6, -5, -4, -3, -2,
            -1,
            0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24],
    '_': [-24, -20, -17, -12, -8, -5, 0, 4, 7, 12, 16, 19, 24],
    '_m': [-24, -21, -17, -12, -9, -5, 0, 3, 7, 12, 15, 19, 24],
    '_7': [-24, -20, -17, -14, -12, -8, -5, -2, 0, 4, 7, 10, 12, 16, 19, 22, 24],
    '_6': [-24, -20, -17, -15, -12, -8, -5, -3, 0, 4, 7, 9, 12, 16, 19, 21, 24],
    '_m7': [-24, -21, -17, -14, -12, -9, -5, -2, 0, 3, 7, 10, 12, 15, 19, 22, 24],
    '_M7': [-24, -20, -17, -13, -12, -8, -5, -1, 0, 4, 7, 11, 12, 16, 19, 23, 24],
    '_maj7': [-24, -20, -17, -13, -12, -8, -5, -1, 0, 4, 7, 11, 12, 16, 19, 23, 24],
    '_9': [-24, -22, -20, -17, -14, -12, -10, -8, -5, -2, 0, 2, 4, 7, 10, 12, 14, 19, 22, 24],
    '_m9': [-24, -22, -21, -17, -14, -12, -10, -9, -5, -2, 0, 2, 3, 7, 10, 12, 14, 15, 19, 22, 24],
    '_M9': [-24, -22, -20, -17, -13, -12, -10, -8, -5, -1, 0, 2, 4, 7, 11, 12, 14, 19, 23, 24],
    '_maj9': [-24, -22, -20, -17, -13, -12, -10, -8, -5, -1, 0, 2, 4, 7, 11, 12, 14, 19, 23, 24],
    '_+5': [-24, -20, -16, -12, -8, -4, 0, 4, 8, 12, 16, 20, 24],
    '_aug': [-24, -20, -16, -12, -8, -4, 0, 4, 8, 12, 16, 20, 24],
    '_7+5': [-24, -20, -16, -14, -12, -8, -4, -2, 0, 4, 8, 10, 12, 16, 20, 22, 24],
    '_aug7': [-24, -20, -16, -14, -12, -8, -4, -2, 0, 4, 8, 10, 12, 16, 20, 22, 24],
    '_7-9': [-24, -23, -20, -17, -14, -12, -11, -8, -5, -2, 0, 1, 4, 7, 10, 12, 13, 16, 19, 22, 24],
    '_7+9': [-24, -21, -20, -17, -14, -12, -9, -8, -5, -2, 0, 3, 4, 7, 10, 12, 15, 16, 19, 22, 24],
    '_dim': [-24, -21, -18, -15, -12, -9, -6, -3, 0, 3, 6, 9, 12, 15, 18, 21, 24],
    '_m7-5': [-24, -21, -18, -14, -12, -9, -6, -2, 0, 3, 6, 10, 12, 15, 18, 20, 24],
    'diatonic': [-24, -22, -20, -19, -17, -15, -13, -12, -10, -8, -7, -5, -3, -1,
                 0, 2, 4, 5, 7, 9, 11, 12, 14, 16, 17, 19, 21, 23, 24],
    'dorian': [-24, -22, -21, -19, -17, -15, -14, -12, -10, -9, -7, -5, -3, -2,
               0, 2, 3, 5, 7, 9, 10, 12, 14, 15, 17, 19, 21, 22, 24],
    'lydian': [-24, -22, -20, -18, -17, -15, -13, -12, -10, -8, -6, -5, -3, -1,
               0, 2, 4, 6, 7, 9, 11, 12, 14, 16, 18, 19, 21, 23, 24],
    'mixolydian': [-24, -22, -20, -19, -17, -15, -14, -12, -10, -8, -7, -5, -3, -2,
                   0, 2, 4, 5, 7, 9, 10, 12, 14, 16, 17, 19, 21, 22, 24],
    'aeolian': [-24, -22, -21, -19, -17, -16, -14, -12, -10, -9, -7, -5, -4, -2,
                0, 2, 3, 5, 7, 8, 10, 12, 14, 15, 17, 19, 20, 22, 24],
    'comdim': [-24, -22, -21, -19, -18, -16, -15, -13, -12, -10, -9, -7, -6, -4, -3, -1,
               0, 2, 3, 5, 6, 8, 9, 11, 12, 14, 15, 17, 18, 20, 21, 24],
    'pentatonic': [-24, -22, -20, -17, -15, -12, -10, -8, -5, -3,
                   0, 2, 4, 7, 9, 12, 14, 16, 19, 21, 24],
    'none': [1000, 1001]  # if more than 127, no sound by limit
}


def convert_exp2vel(exp_text):
    vel = 100
    if not exp_text.isdecimal():
        if exp_text == 'ff':
            vel = 127
        elif exp_text == 'f':
            vel = 114
        elif exp_text == 'mf':
            vel = 100
        elif exp_text == 'mp':
            vel = 84
        elif exp_text == 'p':
            vel = 64
        elif exp_text == 'pp':
            vel = 48
        elif exp_text == 'ppp':
            vel = 24
        elif exp_text == 'pppp':
            vel = 12
        elif exp_text == 'ppppp':
            vel = 1
    else:
        vel = int(exp_text)
        if vel > 127:
            vel = 127
    return vel


def convert_doremi(doremi_str):
    # 最初に +/- がある場合、オクターブ(+12/-12)とみなす
    # +/- を抜いた文字列の最初の一文字、あるいは二文字が移動ドなら、その音程を返す
    base_pitch = 0
    pm_sign = doremi_str[0]
    nx = doremi_str
    if pm_sign == '+':  # octave up
        nx = doremi_str[1:]
        base_pitch += 12
    elif pm_sign == '-':  # octave down
        nx = doremi_str[1:]
        base_pitch -= 12

    if len(nx) > 1:
        l2 = nx[1]
    else:
        l2 = None
    if l2 is None or (l2 != 'i' and l2 != 'a' and l2 != 'o'):
        l1 = nx[0]
        if l1 == 'x':
            base_pitch = REST
        elif l1 == 'd':
            base_pitch += 0
        elif l1 == 'r':
            base_pitch += 2
        elif l1 == 'm':
            base_pitch += 4
        elif l1 == 'f':
            base_pitch += 5
        elif l1 == 's':
            base_pitch += 7
        elif l1 == 'l':
            base_pitch += 9
        elif l1 == 't':
            base_pitch += 11
    else:
        l12 = nx[0:2]
        if l12 == 'di' or l12 == 'ra':
            base_pitch += 1
        elif l12 == 'ri' or l12 == 'ma':
            base_pitch += 3
        elif l12 == 'fi' or l12 == 'sa':
            base_pitch += 6
        elif l12 == 'si' or l12 == 'lo':
            base_pitch += 8
        elif l12 == 'li' or l12 == 'ta':
            base_pitch += 10

    return base_pitch


def limit(num, min_value, max_value):
    if num > max_value:
        num = max_value
    elif num < min_value:
        num = min_value
    return num


def note_limit(num, min_value, max_value):
    while num > max_value:
        num -= 12
    while num < min_value:
        num += 12
    return num


class Log:

    def __init__(self):
        self.log_text = ['Start Log\n']

    def record(self, log_str):
        date = datetime.datetime.now()
        add_str = str(date) + ' : ' + log_str + '\n'
        self.log_text.append(add_str)
        while len(self.log_text) > 200:
            del self.log_text[0]

    def save_file(self):
        self.log_text.append('End Log')
        with open("log.txt", mode='w') as lf:
            for lstr in self.log_text:
                lf.write(lstr)

log = Log()