# -*- coding: utf-8 -*-

REST = 1000
DEFAULT_TICK_FOR_ONE_MEASURE = 1920     # 480 * 4
INVALID_TICK = -1

CHORD_SCALE = {
    'all':[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23],
    '_':[0,4,7,12,16,19],
    '_m':[0,3,7,12,15,19],
    '_7':[0,4,7,10,12,16,19,22],
    '_6':[0,4,7,9,12,16,19,21],
    '_m7':[0,3,7,10,12,15,19,22],
    '_M7':[0,4,7,11,12,16,19,23],
    '_maj7':[0,4,7,11,12,16,19,23],
    '_9':[0,2,4,7,10,12,14,19,22],
    '_m9':[0,2,3,7,10,12,14,15,19,22],
    '_M9':[0,2,4,7,11,12,14,19,23],
    '_maj9':[0,2,4,7,11,12,14,19,23],
    '_+5':[0,4,8,12,16,20],
    '_aug':[0,4,8,12,16,20],
    '_7+5':[0,4,8,10,12,16,20,22],
    '_aug7':[0,4,8,10,12,16,20,22],
    '_7-9':[0,1,4,7,10,12,13,16,19,22],
    '_7+9':[0,3,4,7,10,12,15,16,19,22],
    '_dim':[0,3,6,9,12,15,18,21],
    '_m7-5':[0,3,6,10,12,15,18,20],
    'diatonic':[0,2,4,5,7,9,11,12,14,16,17,19,21],
    'dorian':[0,2,3,5,7,9,10,12,14,15,17,19,21,22],
    'lydian':[0,2,4,6,7,9,11,12,14,16,18,19,21,23],
    'mixolydian':[0,2,4,5,7,9,10,12,14,16,17,19,21,22],
    'aeolian':[0,2,3,5,7,8,10,12,14,15,17,19,20,22],
    'comdim':[0,2,3,5,6,8,9,11,12,14,15,17,18,20,21],
    'none':[1000,1001]   # if more than 127, no sound by limit
}

def convert_exp2vel(expText):
    vel = 100
    if expText.isdecimal() == False:
        if   expText == 'ff':   vel = 127
        elif expText == 'f':    vel = 114
        elif expText == 'mf':   vel = 100
        elif expText == 'mp':   vel = 84
        elif expText == 'p':    vel = 64
        elif expText == 'pp':   vel = 48
        elif expText == 'ppp':  vel = 24
    else:
        vel = int(expText)
        if vel > 127: vel = 127
    return vel


def convert_doremi(doremi_str):
    basePitch = 0
    first = doremi_str[0]
    nx = doremi_str
    if first == '+':    # octave up
        nx = doremi_str[1:]
        basePitch += 12
    elif first == '-':  # octave down
        nx = doremi_str[1:]
        basePitch -= 12

    if nx == 'x':                   basePitch = REST
    elif nx == 'd':                 basePitch += 0
    elif nx == 'di' or nx == 'ra':  basePitch += 1
    elif nx == 'r':                 basePitch += 2
    elif nx == 'ri' or nx == 'ma':  basePitch += 3
    elif nx == 'm':                 basePitch += 4
    elif nx == 'f':                 basePitch += 5
    elif nx == 'fi' or nx == 'sa':  basePitch += 6
    elif nx == 's':                 basePitch += 7
    elif nx == 'si' or nx == 'lo':  basePitch += 8
    elif nx == 'l':                 basePitch += 9
    elif nx == 'li' or nx == 'ta':  basePitch += 10
    elif nx == 't':                 basePitch += 11
    return basePitch
