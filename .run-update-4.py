#!/usr/bin/env python3
# Part 4: COST panel (results settled), lede, events, next_session, today block, pancho.
import json

with open('data/market.json') as f:
    d = json.load(f)

p = d['positions']['cost']
p.update({
    'price': '$896.48',
    'day_arrow': '▼', 'day_en': '−0.91% yesterday', 'day_ko': '어제 −0.91%', 'day_dir': 'dn',
    'week_arrow': '▲', 'week_en': '≈ +0.3% past five days', 'week_ko': '최근 5거래일 ≈ +0.3%', 'week_dir': 'up',
    'month_arrow': '▼', 'month_en': '≈ −5.0% so far in September', 'month_ko': '9월 들어 ≈ −5.0%', 'month_dir': 'dn',
    'drawdown_arrow': '▼', 'drawdown': '≈ 18.3%', 'drawdown_dir': 'dn',
    'drawdown_fact_en': '≈ 18.3%', 'drawdown_fact_ko': '≈ 18.3%',
    'take_en': 'Solid results, calm reaction', 'take_ko': '실적 탄탄, 반응은 차분', 'take_tone': 'c-neu',
    'week_fact_en': 'up ≈ 0.3%', 'week_fact_ko': '≈ 0.3% 상승',
})
p['base']['eps_at'] = [896.48, 43.18]
p['note_en'] = '<b>The wait ended last night, and the answer was: solid.</b> During the day the shares slipped 0.91% to $896.48 — handing back Wednesday’s safety-day gain hours before the report — and after the close Costco published its full results. The quarter beat expectations on both counts: profits of <b>$6.75</b> a share against about $6.53 expected — up 15% on a year earlier, including a one-time <b>15-cent</b> benefit from tariff refunds, about 12% without it — and revenue of <b>$95.7 billion</b> against about $94.9 billion expected. Sales at year-old stores grew <b>9.4%</b>, and <b>6.7%</b> with petrol and currency swings stripped out; online sales grew <b>19.5%</b>. The profit margin — the number this page said the price was resting on — held: profits grew faster than sales. The <b>membership renewal rate came in at 89.8%</b> worldwide, across <b>150.4 million</b> cardholders, and membership fees — the heart of the business — rose <b>7.3%</b>. The market’s verdict was a shrug: options traders had braced for a move of about 3.5% either way, and the shares finished the evening session almost exactly flat. The full financial year closed at <b>$297.2 billion</b> of sales, up 10.1%, with profits of <b>$20.76</b> a share, up 14% — which brings the price down to about <b>43 times</b> profits. The shares sit about <b>18.3%</b> below their peak, still the widest gap of your five.'
p['note_ko'] = '<b>기다림은 어젯밤 끝났고, 답은 "탄탄하다"였습니다.</b> 낮 동안 주가는 0.91% 내린 896.48달러로, 실적 발표 몇 시간 전에 수요일의 안전-자산 상승분을 도로 내놓았습니다. 그리고 장 마감 뒤 코스트코가 전체 실적을 내놓았습니다. 분기는 양쪽 모두 예상을 넘었습니다. 주당 이익 <b>6.75달러</b> 대 예상 약 6.53달러 — 1년 전보다 15% 늘었고, 일회성 관세 환급 <b>15센트</b>를 빼면 12%쯤입니다 — 그리고 매출 <b>957억 달러</b> 대 예상 약 949억 달러였습니다. 1년 넘은 매장의 매출은 <b>9.4%</b>, 휘발유와 환율 변동을 빼면 <b>6.7%</b> 늘었고, 온라인 매출은 <b>19.5%</b> 늘었습니다. 이 페이지가 주가가 기대고 있다고 말해 온 숫자 — 이익률 — 는 지켜졌습니다. 이익이 매출보다 빨리 늘었습니다. <b>회원 갱신율은 전 세계 89.8%</b>였고, 카드 소지자는 <b>1억 5,040만 명</b>이며, 이 사업의 심장인 회비 수입은 <b>7.3%</b> 늘었습니다. 시장의 평결은 어깨 한번 으쓱이었습니다. 옵션 시장은 어느 쪽으로든 3.5%쯤의 움직임을 대비했는데, 주가는 저녁 거래를 거의 정확히 제자리로 마쳤습니다. 회계연도 전체로는 매출 <b>2,972억 달러</b>로 10.1% 늘었고, 주당 이익은 14% 늘어난 <b>20.76달러</b>였습니다. 그 덕에 이익 대비 주가는 약 <b>43배</b>로 내려왔습니다. 주가는 최고가보다 약 <b>18.3%</b> 아래로, 여전히 다섯 중 가장 큰 격차입니다.'
p['news_en'] = [
    {'dt': 'Sep 24', 'tx': '<b>Fell 0.91% to $896.48 during the day, then delivered after the close: profits of $6.75 a share and revenue of $95.7 billion, both ahead of expectations.</b> Sales at year-old stores grew <b>9.4%</b>, online <b>19.5%</b>; the worldwide <b>membership renewal rate was 89.8%</b>. Options traders had braced for a 3.5% move; the shares finished the evening almost exactly flat. Full-year profits: <b>$20.76</b> a share, up 14%.'},
    p['news_en'][0], p['news_en'][1], p['news_en'][2],
]
p['news_ko'] = [
    {'dt': '9월 24일', 'tx': '<b>낮에는 0.91% 내린 896.48달러, 장 마감 뒤에는 약속을 지켰습니다. 주당 이익 6.75달러, 매출 957억 달러로 둘 다 예상을 넘었습니다.</b> 1년 넘은 매장 매출은 <b>9.4%</b>, 온라인은 <b>19.5%</b> 늘었고, 전 세계 <b>회원 갱신율은 89.8%</b>였습니다. 옵션 시장은 3.5% 움직임을 대비했지만, 주가는 저녁 거래를 거의 제자리로 마쳤습니다. 연간 주당 이익은 14% 늘어난 <b>20.76달러</b>입니다.'},
    p['news_ko'][0], p['news_ko'][1], p['news_ko'][2],
]
p['verdict_en'] = '<b>What I’d watch: Tuesday, September 29 — the American ban on a list of Canadian foods takes effect, landing straight on a grocer’s shelves.</b> Certain cheeses and whey are barred entirely and other items carry a 50% tax; no reporting has yet put a number on what it costs this company, so the first evidence will be prices on the shelf. Second, <b>the bond comparison, which is still getting harder</b>: this share pays about <b>0.6%</b> a year in dividends against a thirty-year government rate now at <b>5.47%</b>, and that arithmetic — not the results, which were solid — is most of why the shares sit about <b>18.3%</b> below their peak. Third, <b>fuel</b>: oil has risen two days in a row and diesel remains near record prices — a real cost for a business built on lorries and petrol stations — while the diesel-export argument in Washington stays unresolved. Fourth, the routine that never stops: <b>September’s monthly sales figures land in about two weeks</b>, the first month of the new financial year and the first read on whether the quarter’s pace carried over.'
p['verdict_ko'] = '<b>지켜볼 것: 9월 29일 화요일 — 일부 캐나다산 식품에 대한 미국의 수입 금지가 시행돼 식료품 진열대에 곧바로 닿습니다.</b> 일부 치즈와 유청은 아예 막히고 다른 품목에는 50% 관세가 붙습니다. 이 회사에 얼마짜리인지 숫자를 낸 보도는 아직 없으니, 첫 증거는 진열대 위의 가격일 것입니다. 둘째, <b>여전히 어려워지고 있는 국채와의 비교</b>입니다. 이 주식의 배당은 연 <b>0.6%</b>쯤인데 30년물 국채 금리는 이제 <b>5.47%</b>이고, 주가가 최고가보다 약 <b>18.3%</b> 아래에 있는 이유의 대부분은 탄탄했던 실적이 아니라 이 산수입니다. 셋째, <b>연료</b>입니다. 유가는 이틀 연속 올랐고 경유는 사상 최고 부근입니다. 트럭과 주유소 위에 세워진 사업에 실제 비용이고, 워싱턴의 경유 수출 논쟁은 결론이 나지 않은 채입니다. 넷째, 멈추지 않는 일상입니다. <b>9월 월간 매출이 2주쯤 뒤에 나옵니다.</b> 새 회계연도의 첫 달이고, 분기의 속도가 이어졌는지를 보는 첫 자료입니다.'
p['facts'][4] = {'en': 'Latest results', 'ko': '최근 실적', 'v_en': 'Sep 24 — profits and sales both beat', 'v_ko': '9월 24일 — 이익·매출 모두 예상 상회'}
p['plain_en'] = 'The warehouse retailer — and last night, the one of your five that reported. <b>The results were solid: profits of $6.75 a share and revenue of $95.7 billion, both ahead of expectations, with sales at year-old stores up 9.4% and online sales up 19.5%.</b> The membership renewal rate — the number analysts check first — was <b>89.8%</b> worldwide. The market’s reaction was a shrug: the shares barely moved in evening trading, after slipping 0.91% to $896.48 during the day. A full year is now on the books: <b>$297.2 billion</b> of sales and profits up 14%, which brings the price to about <b>43 times</b> profits. The shares still sit about <b>18.3%</b> below their peak — not because the business stumbled, but because they compete with government bonds that now pay the most in about two decades.'
p['plain_ko'] = '창고형 매장을 운영하는 회사이고, 어젯밤 보유 다섯 중 유일하게 실적을 낸 곳입니다. <b>결과는 탄탄했습니다. 주당 이익 6.75달러, 매출 957억 달러로 둘 다 예상을 넘었고, 1년 넘은 매장 매출은 9.4%, 온라인 매출은 19.5% 늘었습니다.</b> 분석가들이 가장 먼저 보는 숫자인 회원 갱신율은 전 세계 <b>89.8%</b>였습니다. 시장의 반응은 어깨 한번 으쓱이었습니다. 낮에 0.91% 내린 896.48달러가 된 주가는 저녁 거래에서 거의 움직이지 않았습니다. 이제 한 해 전체가 장부에 올랐습니다. 매출 <b>2,972억 달러</b>, 이익은 14% 증가, 그 덕에 이익 대비 주가는 약 <b>43배</b>입니다. 주가는 여전히 최고가보다 약 <b>18.3%</b> 아래에 있습니다. 사업이 휘청여서가 아니라, 20년 만에 가장 많이 주는 국채와 경쟁하고 있기 때문입니다.'
p['bull_en'] = '<b>The question this page has asked for a month — did the margin hold? — was answered last night: yes.</b> Profits grew faster than sales; the quarter beat on both lines; the full year closed at <b>$297.2 billion</b>, up 10.1%, with profits up 14%; online sales grew <b>19.5%</b>; and <b>150.4 million</b> cardholders renewed at <b>89.8%</b> worldwide. The business is doing everything a shareholder could ask, and the new profits bring the price down to about <b>43 times</b> — its least expensive of the year. The gap below the peak is about the bond market, not the company — so any relief in rates falls onto a share whose own numbers just passed inspection. And the safety pattern still holds: on the frightened days of the past fortnight, this was the share the shelter money bought.'
p['bull_ko'] = '<b>이 페이지가 한 달 동안 물어 온 질문 — 이익률이 지켜졌는가? — 은 어젯밤 답을 받았습니다. 그렇다, 입니다.</b> 이익이 매출보다 빨리 늘었고, 분기는 두 줄 모두 예상을 넘었으며, 회계연도는 10.1% 늘어난 <b>2,972억 달러</b> 매출과 14% 늘어난 이익으로 마감했습니다. 온라인 매출은 <b>19.5%</b> 늘었고, <b>1억 5,040만</b> 카드 소지자의 전 세계 갱신율은 <b>89.8%</b>였습니다. 사업은 주주가 바랄 수 있는 모든 것을 하고 있고, 새 이익 덕에 값은 약 <b>43배</b> — 올해 가장 싼 수준 — 로 내려왔습니다. 최고가와의 격차는 회사가 아니라 채권시장의 문제입니다. 그러니 금리가 조금이라도 숨을 돌리면, 방금 검사를 통과한 숫자를 가진 이 주식 위로 떨어집니다. 그리고 안전 패턴은 그대로입니다. 지난 2주의 겁먹은 날들마다, 피난처를 찾는 돈이 산 것은 이 주식이었습니다.'
p['bear_en'] = '<b>The report was good, and the shares did not rise — that is the bear case in one sentence.</b> At about <b>43 times</b> profits, a beat helped by a one-time tariff refund was already in the price, and the buyer’s alternative keeps improving: the thirty-year government rate closed at <b>5.47%</b> against a dividend of about 0.6%, with the Fed expected to raise again in October. Tuesday’s Canadian food ban lands directly on these shelves, and nobody has priced its cost yet. Oil has turned back up, and diesel near record prices sits inside everything a warehouse sells. And the shares are down about <b>5.0%</b> in September while the rest of your five rose — the market has been choosing bonds over this stock for a month, and last night’s solid report did not change its mind.'
p['bear_ko'] = '<b>실적은 좋았는데 주가는 오르지 않았다 — 이것이 한 문장으로 줄인 비관론입니다.</b> 이익의 약 <b>43배</b>에서는 일회성 관세 환급의 도움을 받은 예상 상회가 이미 값에 들어 있었고, 사는 쪽의 대안은 계속 좋아지고 있습니다. 30년물 국채 금리가 <b>5.47%</b>로 마감한 반면 이 주식의 배당은 0.6%쯤이고, 연준은 10월에 또 올릴 것으로 예상됩니다. 화요일의 캐나다산 식품 금지는 바로 이 진열대에 떨어지는데, 그 비용을 계산한 사람은 아직 없습니다. 유가는 도로 올랐고, 사상 최고 부근의 경유 값은 창고형 매장이 파는 모든 것 안에 들어 있습니다. 그리고 보유 다섯 중 나머지가 오르는 동안 이 주식은 9월 들어 약 <b>5.0%</b> 내렸습니다. 시장은 한 달째 이 주식 대신 채권을 고르고 있고, 어젯밤의 탄탄한 실적도 그 마음을 바꾸지 못했습니다.'

# ---------------- lede ----------------
d['lede'] = [
    {'cls': 'first',
     'en': '<b>Yesterday the market was hit twice and finished where it started.</b> In the morning shares fell: the ten-year borrowing rate was climbing toward another record-since-2007 close, and oil jumped after missiles were fired at Saudi Arabia. By afternoon a report that the United States and Iran are discussing a step-by-step reopening of the <b>Strait of Hormuz</b> had pulled everything back. The S&amp;P 500 closed <b>essentially flat</b>, the Nasdaq the same, the Dow down 0.3%. Of your five: <b>SOXL +0.05%</b> after being down more than 6% in the first hour, <b>QQQ flat</b>, <b>SPX flat</b>, <b>NVDA −0.41%</b> — and <b>COST −0.91%</b>, handing back its safety-day gain hours before its own results. Those results, after the close, <b>beat expectations on profits and revenue</b>, and the shares barely moved.',
     'ko': '<b>어제 시장은 두 번 얻어맞고 출발한 자리에서 끝났습니다.</b> 아침에는 주가가 밀렸습니다. 10년물 차입 금리가 또 한 번 2007년 이후 최고 종가를 향해 오르고 있었고, 사우디아라비아에 미사일이 날아든 뒤 유가가 뛰었습니다. 오후에는 미국과 이란이 <b>호르무즈 해협</b>을 단계적으로 다시 여는 방안을 논의 중이라는 보도가 모든 것을 되돌렸습니다. S&amp;P 500은 <b>사실상 제자리</b>, 나스닥도 마찬가지, 다우존스는 0.3% 하락으로 마쳤습니다. 보유 다섯은 이렇습니다. 첫 한 시간에 6% 넘게 내렸다가 되오른 <b>SOXL +0.05%</b>, <b>QQQ 제자리</b>, <b>SPX 제자리</b>, <b>NVDA −0.41%</b> — 그리고 자기 실적 발표 몇 시간 전에 안전-자산 상승분을 도로 내놓은 <b>COST −0.91%</b>. 그 실적은 장 마감 뒤 <b>이익과 매출 모두 예상을 넘었고</b>, 주가는 거의 움직이지 않았습니다.'},
    {'cls': '',
     'en': '<b>The month’s two set-piece events have now both passed, and neither drew blood.</b> The White House summit ended with a state dinner — technology chiefs at the head table, warm toasts, a bald-eagle statue as a gift — and <b>no announcement about chips, exports or trade in either direction</b>; the tariff truce had already been extended to <b>January 10</b> the evening before. Costco’s results were solid and calmly received. What has not passed is the bond market: the ten-year rate closed at about <b>5.18%</b>, a second straight highest finish since 2007, the thirty-year was reported at its highest since 2004, and most Fed officials still expect another rise, with the next decision on <b>October 28</b>. Shares being pushed this hard by rates and refusing to fall is the month’s real story — and nobody can tell you which side gives first.',
     'ko': '<b>이번 달의 두 개의 큰 행사가 이제 모두 지나갔고, 어느 쪽도 상처를 내지 못했습니다.</b> 백악관 정상회담은 국빈 만찬으로 끝났습니다. 헤드테이블의 기술 기업 대표들, 따뜻한 건배사, 선물로 준 흰머리수리 조각상 — 그리고 <b>반도체든 수출이든 무역이든 어느 방향으로도 발표는 없었습니다.</b> 관세 휴전은 이미 그 전날 저녁 <b>1월 10일까지</b> 연장돼 있었습니다. 코스트코 실적은 탄탄했고 차분하게 받아들여졌습니다. 지나가지 않은 것은 채권시장입니다. 10년물 금리는 약 <b>5.18%</b>로 이틀 연속 2007년 이후 최고 종가를 썼고, 30년물은 장중 2004년 이후 최고로 보도됐으며, 연준 위원 대부분은 여전히 추가 인상을 예상합니다. 다음 결정은 <b>10월 28일</b>입니다. 금리가 이렇게 세게 미는데도 주가가 넘어지지 않는 것 — 이것이 이번 달의 진짜 이야기이고, 어느 쪽이 먼저 무너질지는 아무도 말해 줄 수 없습니다.'},
    {'cls': '',
     'en': '<b>The week ends quietly; the next one does not.</b> Today brings a factory-orders report before the open, a consumer-mood reading just after it, and Federal Reserve officials speaking through the day. Then Tuesday the ban on some Canadian foods lands on Costco’s shelves; Wednesday brings both the <b>August inflation figure</b> the Fed watches most and <b>Micron’s results</b> — the memory maker whose story led the chip rise, reaching four of your five; and next Friday is the <b>September jobs report</b>. The standing warning matters as much as ever: four of your five are the same chip bet, and <b>SOXL</b> triples whatever chips decide those days are worth — yesterday it visited −6% and came all the way back before lunch.',
     'ko': '<b>이번 주는 조용히 끝나지만, 다음 주는 그렇지 않습니다.</b> 오늘은 개장 전의 내구재 주문 보고서, 개장 직후의 소비자 심리 수치, 그리고 하루에 걸친 연준 인사들의 발언이 있습니다. 그리고 화요일에는 일부 캐나다산 식품 금지가 코스트코 진열대에 닿고, 수요일에는 연준이 가장 눈여겨보는 <b>8월 물가 수치</b>와 <b>마이크론 실적</b> — 반도체 상승을 이끈 메모리 회사이고, 보유 다섯 중 넷에 닿습니다 — 이 함께 나오며, 다음 주 금요일은 <b>9월 고용 보고서</b>입니다. 늘 붙는 경고는 여느 때만큼 중요합니다. 보유 다섯 중 넷이 같은 반도체 베팅이고, <b>SOXL</b>은 반도체가 그 날들을 얼마짜리로 정하든 그 세 배를 합니다. 어제는 −6%까지 갔다가 점심 전에 전부 되올라왔습니다.'},
]

# ---------------- events ----------------
d['events'] = [
    {'hot': False,
     'when_en': 'Tue Sep 29', 'when_ko': '9월 29일(화)',
     'what_en': 'Canadian food ban takes effect', 'what_ko': '캐나다산 식품 수입 금지 시행',
     'note_en': "Some Canadian foods and drinks — certain cheeses and whey among them — are barred from entering the United States at all, with a 50% tax on others. It lands five days after Costco's solid results and reaches a grocer's shelves directly. No reporting has yet put a number on what it costs",
     'note_ko': '일부 캐나다산 식음료가 미국에 아예 들어오지 못하게 되고, 나머지에는 50% 관세가 붙습니다. 치즈 일부와 유청이 포함됩니다. 코스트코의 탄탄한 실적 발표 닷새 뒤에 시행되며, 식료품 매장 진열대에 곧바로 닿습니다. 비용이 얼마인지 숫자를 낸 보도는 아직 없습니다'},
    {'hot': True,
     'when_en': 'Wed Sep 30', 'when_ko': '9월 30일(수)',
     'what_en': 'August inflation figure — the one the Fed aims at', 'what_ko': '8월 물가 수치 — 연준이 목표로 삼는 지표',
     'note_en': "At 5:30 in the morning Pacific time, confirmed on the government statisticians' own schedule. This is the measure the Fed says it targets. The Fed raised its rate on September 16, most of its officials expect to raise again, and the ten-year borrowing rate has just set two straight highest closes since 2007 — this is the figure that whole argument turns on. It lands the same day as Micron's results, making Wednesday the heaviest day of next week",
     'note_ko': '서부 시각 오전 5시 30분이고, 통계기관이 공개한 일정표로 확인했습니다. 연준이 목표로 삼는다고 말하는 지표입니다. 연준은 9월 16일에 금리를 올렸고 위원 대부분이 또 올릴 것으로 보며, 10년물 차입 금리는 방금 이틀 연속 2007년 이후 최고 종가를 썼습니다. 그 논쟁 전체가 이 숫자에 걸려 있습니다. 마이크론 실적과 같은 날 나와, 수요일이 다음 주 가장 무거운 날입니다'},
    {'hot': True,
     'when_en': 'Wed Sep 30', 'when_ko': '9월 30일(수)',
     'what_en': 'Micron results', 'what_ko': '마이크론 실적',
     'note_en': "At 1:30 in the afternoon Pacific time, a date the company has set itself. Micron makes memory chips, and memory is where the chip strength keeps coming from — the shares have almost quadrupled this year. This report is the first hard set of figures behind that story, and it reaches four of your five",
     'note_ko': '서부 시각 오후 1시 30분이고, 회사가 직접 정한 날짜입니다. 마이크론은 메모리 반도체를 만들고, 최근 반도체의 힘이 계속 나오는 곳이 메모리입니다. 주가는 올해 네 배 가까이 올랐습니다. 이번 실적은 그 이야기 뒤에 있는 첫 확실한 숫자이고, 보유 다섯 중 넷에 닿습니다'},
    {'hot': False,
     'when_en': 'Fri Oct 2', 'when_ko': '10월 2일(금)',
     'what_en': 'September jobs report', 'what_ko': '9월 고용 보고서',
     'note_en': 'At 5:30 in the morning Pacific time. The first full read on the job market since the Fed started raising, and one of the two figures it says it is watching most closely',
     'note_ko': '서부 시각 오전 5시 30분에 나옵니다. 연준이 금리를 올리기 시작한 뒤 고용을 처음으로 온전히 보는 자료이고, 연준이 가장 눈여겨본다고 말하는 두 숫자 가운데 하나입니다'},
    {'hot': True,
     'when_en': 'Wed Oct 28', 'when_ko': '10월 28일(수)',
     'what_en': 'Next Federal Reserve decision', 'what_ko': '다음 연준 금리 결정',
     'note_en': 'At 11 in the morning Pacific time. On September 16 the Fed raised to a range of 3.75% to 4% and published forecasts showing 16 of its 18 officials expecting another rise before the year is out, four of them expecting two. This is the next chance to find out. Nobody can tell you what it will do',
     'note_ko': '서부 시각 오전 11시입니다. 9월 16일에 연준은 3.75%~4% 구간으로 올렸고, 함께 내놓은 전망에서 18명 중 16명이 올해가 가기 전 한 번 더 올릴 것으로 봤으며 그중 넷은 두 번을 봤습니다. 그것을 확인할 다음 기회가 이날입니다. 연준이 무엇을 할지는 아무도 말해 줄 수 없습니다'},
    {'hot': False,
     'when_en': 'Sun Jan 10', 'when_ko': '1월 10일(일)',
     'what_en': 'The tariff truce with China runs out', 'what_ko': '중국과의 관세 휴전 만료',
     'note_en': "The two-month extension announced on the eve of this week's summit runs to January 10. The summit itself ended with no agreement on chips or export rules, so those questions — the ones that reach four of your five — carry forward into the new deadline",
     'note_ko': '이번 주 정상회담 전야에 발표된 두 달 연장은 1월 10일까지입니다. 정상회담 자체는 반도체와 수출 규정에 대한 합의 없이 끝났으니, 보유 다섯 중 넷에 닿는 그 질문들은 새 시한으로 넘어갑니다'},
]

# ---------------- next session / today / pancho ----------------
d['next_session_en'] = 'Trading restarts this morning at 6:30 Pacific — the board shows Thursday’s closing prices'
d['next_session_ko'] = '오늘 아침 서부 시각 6시 30분에 거래가 다시 시작됩니다 — 표의 숫자는 목요일 종가입니다'
d['next_session_en_html'] = 'Trading restarts <b>this morning at 6:30 Pacific</b> &mdash; the board shows <b>Thursday&rsquo;s closing prices</b>'
d['next_session_ko_html'] = '<b>오늘 아침 서부 시각 6시 30분</b>에 거래가 다시 시작됩니다 &mdash; 표의 숫자는 <b>목요일 종가</b>입니다'

d['today_en'] = '<b>The morning points modestly higher, with chip shares leading.</b> Stock index futures are up a little, the Nasdaq contract ahead of the rest, and chipmakers — AMD, Intel and the memory companies — are higher in early trading on fresh optimism about demand for AI computing; <b>SOXL</b> will feel whatever chips do at three times the size. <b>Costco</b> is a touch lower before the open after last night’s solid, calmly received results. The bond market has not gone away — the ten-year rate is near <b>5.2%</b> this morning, its highest in about nineteen years — and oil has eased a little on the US-Iran talks. Today’s calendar is light: a factory-orders report just before the open, a consumer-mood reading just after it, and Federal Reserve officials speaking through the day. The heavier tests — the Fed’s inflation figure and <b>Micron’s results</b> — come next Wednesday.'
d['today_ko'] = '<b>오늘 아침은 완만한 상승 쪽을 가리키고 있고, 반도체가 앞장서고 있습니다.</b> 주가지수 선물은 소폭 올라 있고 나스닥 쪽이 가장 앞서 있으며, AMD·인텔·메모리 회사들 같은 반도체주는 AI 컴퓨팅 수요에 대한 새 낙관에 이른 거래에서 오르고 있습니다. <b>SOXL</b>은 반도체가 하는 일을 세 배 크기로 느낄 것입니다. <b>코스트코</b>는 어젯밤의 탄탄하고 차분하게 받아들여진 실적 뒤에 개장 전 살짝 내려 있습니다. 채권시장은 사라지지 않았습니다. 10년물 금리는 오늘 아침 <b>5.2%</b> 부근으로 약 19년 만에 가장 높고, 유가는 미국-이란 협상 소식에 조금 누그러졌습니다. 오늘 일정은 가볍습니다. 개장 직전의 내구재 주문 보고서, 개장 직후의 소비자 심리 수치, 그리고 하루에 걸친 연준 인사들의 발언입니다. 더 무거운 시험 — 연준 물가 수치와 <b>마이크론 실적</b> — 은 다음 주 수요일에 옵니다.'
d['today_date'] = '2026-09-25'

d['pancho_am'] = {
    'date': '2026-09-25', 'pos': 'cost',
    'en': "Costco passed its big test last night, and the market just nodded. Quiet can be good news.",
    'ko': '코스트코가 어젯밤 시험을 통과했는데 시장은 끄덕이고 말았어요. 조용한 게 좋은 소식일 때도 있죠.',
}
# pancho_pm deliberately left dated 2026-09-24 so no afternoon line renders pre-open.

with open('data/market.json', 'w') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
    f.write('\n')
print('part 4 done: cost + lede + events + today + pancho')
