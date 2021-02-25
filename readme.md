
namihey Alpha-version(0.210224)
=================================

about namihey
--------------

"namihey" is a music description language being developed mainly for use in Live Coding.
The main feature of namihey is the ability to specify tones by a gradation with a movable-do.
It is written in python and output to MIDI by the mido library.



namihey とは
------------

namihey は、Live Coding などで使うために開発しているテキストベースの音楽記述言語です。
音の指定を、移動ドによる階名で指定することを大きな特徴とします。
python によって記述され、mido というライブラリにより、MIDI出力します。



記述の基本ルール
--------------

- 起動
    - 'python namihey.py'  : 通常の python スクリプトと同じ
- 入力
    - '[1][1]~~> ' : nami prompt
        - [1][1]は、block 1/part 1の入力状態であることを示す
        - このプロンプトの後に、コマンドやフレーズを書き込む
    - カーソルによる過去入力のヒストリー呼び出しが可能
- 終了
    - 'quit' 'exit' : 終了


音を出す方法
----------

- MIDI 音源を繋ぐ
- Logic などマルチパートで MIDI受信するアプリを同時に起動する


再生コントロール
--------------

- 'play' 'start' : シーケンス開始
- 'mute 2,3' : part2 と part3 をミュートする        【未実装】
- 'mutecancel' : ミュートしていたパートのミュート解除する    【未実装】
- 'fine' : ブロックの最後でシーケンス終了
- 'stop' : 直ちにシーケンス終了



フレーズ追加
-------------

- [*note*][*duration*][*velocity*] : フレーズ追加の基本形式
    - *note*: 階名
    - *duration*: 音価
    - *velocity*: 音量
    - [*duration*] と [*velocity*] は省略可能
        - 階名と音価と音量の全体の数が合わないとき、階名の内容で数を合わせる。
        - 音価と音量は、足りない時は最後の数値がそのまま連続し、多い時は途中で打ち切られる。
        - 音価を省略した場合全て四分音符とみなし、音量を省略した場合100(mf)とみなす。
    - [] : 全データ削除

- 階名表現
    - d,r,m,f,s,l,t: ド、レ、ミ、ファ、ソ、ラ、シ
    - di,ri,fi,si,li: ド#、レ#、ファ#、ソ#、ラ#
    - ra,ma,sa,lo,ta: レb、ミb、ソb、ラb、シb
    - -d : 1オクターブ下のド、 +d : 1オクターブ上のド
    - ',' '|' : カンマ、縦棒、どちらで区切っても良い
    - x: 休符
    - d=m=s, : 同時演奏
    - |:d,r,m:3| : ドレミを３回繰り返し、合計４回演奏（数字がなければ1回繰り返し）
    - <d,r,m>*4 : ドレミを４回演奏
    - d*4 : ドを４回連続して発音

- 音価表現
    - [8:] , [:8] は基準音価が 8 であることを示す
        - 基準音価は任意の数値が指定可能で、全音符の長さの何分の1かを示す数値となる
        - 基準音価(:n, n:)を省略した場合、全て四分音符とみなす
    - [1,1,1,1:8] : 八分音符を４回
        - :n と基準音価を書く場合、各音の音価指定の後ろに書く
        - [8:1,1,1,1] : n: と書く場合、各音の音価指定の前に書く
        - [2,1,2,1,3:12] : 一拍3連(12分音符)で、タータタータター
        - [1:2] のように書くと、どちらが基準音価か分からないので、値の大きい方を基準音価とみなす
    - [<2,1>:12] : とすると、この後もずっと 2,1 のパターンの長さを繰り返す
        - <2,1>*2 のように階名と同じように繰り返し回数の指定ができる
        - 繰り返し記号の終わりが音価表現全体の最後の場合、繰り返しパターンを何度も繰り返すが、最後でないと回数指定分しか繰り返さない。
    - [:8(80%)] 音価指定の後に (nn%) とすると、実際の発音時間がそのパーセントの短さになる
        - (stacc.) と書くと 50% になる

- 音量表現
    - 省略した場合、全て velocity=100 とみなす
    - [127,127,127,127] : MIDI velocity=127 を４回
    - [ff,f,mf,mp,p,pp] : ff-pp で音量を表現できる
    - [<f,p,mf,p>] : とすると、この後もずっと f,p,mf,p のパターンを繰り返す
        - <f,mp>*2 のように階名と同じように繰り返し回数の指定ができる
        - 繰り返し記号の終わりが音量表現全体の最後の場合、繰り返しパターンを何度も繰り返すが、最後でないと回数指定分しか繰り返さない。


ランダムパターン追加
----------------------------

- {rnd(*prm*):*chord*}{*length*}{*velocity*} : ランダムパターンの基本形式
    - *prm*: ランダムのパラメータ
    - *chord*: ランダムのコード、カンマで区切って時系列で表現可能
    - *length*: パターンの小節数、カンマで区切って、上の対応するコードが持続する小節数を表現する
    - *velocity*: 音量、同様にカンマで区切って、対応するコードの音量を表現
    - {*length*} と {*velocity*} は省略可能
        - 長さを省略した場合全て１小節とみなし、音量を省略した場合100(mf)とみなす。
    - {} : 全データ削除

- ランダムパターン表現
    - パラメータ
        - (type=full, dur=8) : typeとdurの指定
        - 必ずデフォルト値を持ち、省略が可能
        - type
            - full : C4を中心とした２オクターブ分（デフォルト）
        - dur   : ランダム音の音価。数値は基準音価と同じ（デフォルトは 8)
    - コード名
        - 1 : d=m=s（Iの和音)
        - +1 : di=mi=si (数字の前に + を付けると半音高いコードになる）
        - 5 : s=t=r (Ⅴの和音)
        - 6m : l=d=m (m: minor)
        - -37 : ma=s=ta=ra (- を付けると半音低くなる。7: 7th)
        - 4M7 : f=l=d=m (M7: major7th)
        - 3m7-5 : m=s=ta=r (m7-5: minor7th -5th)
        - diatonic : d=r=m=f=s=l=t (Diatonic Scale)
        - lydian : d=r=m=fi=s=l=t (Lydian Scale)
        - all : 全ての音
    - 使用例
        - ex1)  {rnd(dur=8):all}{2}{mp}  : 全音域ランダム、２小節分、mpで
        - ex2)  {rnd:6m,4,5,1}{1,1,1,1}{mf} : 1小節ごとに指定した和音をランダムに、mfで



入力環境コマンド
----------------

- 'copyto 2' : 入力中のpartのフレーズを part2 にコピー
- 'input 1' : part 1への入力切り替え（1〜16)
- 'input b1' : block 1への入力切り替え (1〜?)     【未実装】
- 'show' : 現在のフレーズ情報を、階名(N)、音価(D)、音量(V)を nami prompt と一緒に、それぞれ一行ずつにして表示


設定コマンド
-----------

- 'set bpm=100' : BPM（テンポ）=100 にセット
- 'set beat=4/4' : 拍子を 4/4 にセット
- 'set key=C4' : key を C4 にセット
    - namihey にとって key とは [d] と指示されたときの音名を表す
    - デフォルト値は C4
    - 最後に all をつけると、全 part に効果、付けなければ入力中の part に対してのみ効果
- 再生中でも設定可能。再生中の場合、次のループから反映される

