# -*- coding: utf-8 -*-

REST = 1000

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
