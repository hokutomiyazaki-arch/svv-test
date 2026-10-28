#!/usr/bin/env python3
"""アプリが読み上げる文を、ElevenLabs で前もって音声にして voice/ に置く（2026-10-16。もとは fnt-camera-check/tools/voice_build.py）。

  python3 tools/voice_build.py          # 足りない分だけ作る
  python3 tools/voice_build.py --dry    # 一覧と字数だけ

- 読み上げる文は下の TEXTS に全部並べる（index.html の svvMsg・note・say に渡している文）
- 文 → 鍵（空白と「。」を抜いたもの）→ ファイル名 は voice/index.json。index.html の vkey() と同じ規則
- ファイル名は読ませる文の md5 なので、カメラでチェックに同じ文があればそれを写す（クレジットを使わない）
- 声と型は AI音読（skill ai-onodoku）で決めたもの：eleven_v3・リョウ。鍵は ~/.zshenv の ELEVENLABS_API_KEY（値は出さない）
"""
import hashlib, json, os, re, shutil, subprocess, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'voice'
SIB = ROOT.parent / 'fnt-camera-check' / 'voice'
API, MODEL, VOICE = 'https://api.elevenlabs.io', 'eleven_v3', '1cOJcfrlMmUCGpeJbXg9'   # リョウ

TEXTS = ['線をまっすぐ縦に。スマホを傾けて合わせ、止める。1回10秒', '次はまっすぐ横に。スマホを傾けて合わせ、止める。1回10秒',
         '記録しました', 'この端末では測れませんでした', 'スマホを縦に持ってください', '線を合わせたところを読み取れませんでした。もう一度どうぞ', 'スマホを顔に近づけて。画面で見える範囲がほぼ埋まるくらい',
         # 首の傾きチェック（2026-10-24。文は hanasaki-awase・カメラでチェックと同じにして、音声を写す）
         '楽にして。画面を見るだけ。スマホは縦にまっすぐ', 'スマホをまっすぐ縦に', '楽にしたまま。画面を見ていてください',
         '顔が見つかりませんでした。顔を画面に入れて、もう一度どうぞ', '顔が見えている時間が短すぎました。顔を画面に入れて、もう一度どうぞ']

def vkey(t): return re.sub(r'[\s。]', '', t)
def say_text(t): return t.replace('OK', 'オーケー').strip('。 ')

def tts(text, path):
    k = os.environ.get('ELEVENLABS_API_KEY') or sys.exit('ELEVENLABS_API_KEY が無い（~/.zshenv）')
    body = json.dumps({'text': text, 'model_id': MODEL, 'voice_settings': {'stability': 0.5, 'similarity_boost': 0.75}}).encode()
    req = urllib.request.Request(f'{API}/v1/text-to-speech/{VOICE}?output_format=mp3_22050_32', data=body, headers={'xi-api-key': k, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r: path.write_bytes(r.read())

def main():
    OUT.mkdir(exist_ok=True); idx, todo = {}, []
    for t in TEXTS:
        f = hashlib.md5(say_text(t).encode()).hexdigest()[:12] + '.mp3'; idx[vkey(t)] = f
        if (OUT / f).exists(): continue
        if (SIB / f).exists(): shutil.copy(SIB / f, OUT / f); print('写した', t); continue
        todo.append((t, f))
    n = sum(len(say_text(t)) for t, _ in todo)
    print(f'文 {len(TEXTS)}・作るもの {len(todo)}・{n}字（eleven_v3 は約 {n // 2} クレジット）')
    if '--dry' in sys.argv:
        for t, _ in todo: print('  ', t)
        return
    for t, f in todo: tts(say_text(t), OUT / f); print('作った', t)
    if not (OUT / 'unlock.mp3').exists():
        if (SIB / 'unlock.mp3').exists(): shutil.copy(SIB / 'unlock.mp3', OUT / 'unlock.mp3')
        else: subprocess.run(['ffmpeg', '-loglevel', 'error', '-f', 'lavfi', '-i', 'anullsrc=r=22050:cl=mono', '-t', '0.2', '-b:a', '32k', str(OUT / 'unlock.mp3')], check=True)
    (OUT / 'index.json').write_text(json.dumps(dict(sorted(idx.items())), ensure_ascii=False, indent=0))
    print('voice/index.json', len(idx))

main()
