#!/usr/bin/env python3
# Part 1 of the 2026-09-25 Friday pre-open refresh of data/market.json.
import json

with open('data/market.json') as f:
    d = json.load(f)

d['as_of'] = '2026-09-24'
d['generated'] = '2026-09-25T04:55:00-07:00'
d['mode'] = 'weekday'

# ---------------- strip ----------------
d['strip']['spx'].update({
    'value': '7,704.13',
    'change_en': 'flat yesterday — it finished 1.90 points lower after a full round trip: down about half a percent in the morning as bond rates and oil climbed, then back by the close on a report that the United States and Iran are discussing reopening the oil shipping strait',
    'change_ko': '어제 제자리 — 1.90포인트 낮게 마쳤지만 하루는 왕복이었습니다. 채권 금리와 유가가 오르며 아침에 0.5%쯤 밀렸다가, 미국과 이란이 원유 수송로를 다시 여는 방안을 논의 중이라는 보도에 마감까지 되돌아왔습니다',
    'dir': 'fl',
})
d['strip']['ndx'].update({
    'value': '26,939.37',
    'change_en': 'flat yesterday — 3.34 points higher, after clawing back a morning fall of about 1%. Chip shares were down more than 2% early and ended a hair higher',
    'change_ko': '어제 제자리 — 3.34포인트 올랐습니다. 1%쯤 밀렸던 아침 하락을 되찾은 결과입니다. 반도체는 장 초반 2% 넘게 내렸다가 살짝 오른 채 마쳤습니다',
    'dir': 'fl',
})
d['strip']['dow'].update({
    'value': '51,349.98',
    'change_en': '▼ down 0.3% yesterday — 161.61 points, a third straight fall, as bond rates rose again',
    'change_ko': '▼ 어제 0.3% 하락 — 161.61포인트로 사흘 연속 하락입니다. 채권 금리가 다시 오른 날이었습니다',
    'dir': 'dn',
})
d['strip']['vix'].update({
    'value': '15.67',
    'change_en': '▲ up to 15.67 from 15.18 — a second daily rise as bond rates keep climbing, though this is still a low reading for the year',
    'change_ko': '▲ 15.18에서 15.67로 상승 — 채권 금리가 계속 오르며 이틀째 올랐지만, 올해 기준으로는 여전히 낮은 수준입니다',
    'dir': 'up',
})
d['strip']['us10y'].update({
    'value': '≈ 5.18%',
    'change_en': '▲ up again to about 5.18% — a second straight highest close since 2007. Even a calm day for shares did not stop lenders asking for more',
    'change_ko': '▲ 다시 올라 약 5.18% — 이틀 연속 2007년 이후 최고 종가입니다. 주가가 차분했던 날에도 빌려주는 쪽은 더 요구했습니다',
    'dir': 'up',
})
d['strip']['us30y'].update({
    'value': '≈ 5.47%',
    'change_en': '▲ up to 5.47% from 5.40% — reported during the day as the long rate’s highest since 2004, with oil rising a second day',
    'change_ko': '▲ 5.40%에서 5.47%로 상승 — 장중에는 2004년 이후 최고로 보도됐습니다. 유가가 이틀째 오른 날입니다',
    'dir': 'up',
})

with open('data/market.json', 'w') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
    f.write('\n')
print('part 1 done: as_of/generated/strip')
