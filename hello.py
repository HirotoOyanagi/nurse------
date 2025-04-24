from pulp import *
import datetime
import calendar
import csv
from collections import defaultdict

# 定数の定義
NURSES = 10  # ナースの人数
DAYS = 31    # 1月の日数
SHIFTS = ['日勤', '夜勤']  # 夜勤明けはシフトとして扱わない

# 問題の定義
prob = LpProblem("Nurse_Scheduling", LpMinimize)

# 変数の定義
# x[n][d][s] = 1 if nurse n works shift s on day d, 0 otherwise
x = LpVariable.dicts("shift",
                     ((n, d, s) for n in range(NURSES) 
                      for d in range(DAYS) 
                      for s in SHIFTS),
                     cat='Binary')

# 目的関数（最小化したい変数がない場合は0を設定）
prob += 0

# 制約条件
# 1. 各ナースは1日に1つのシフトのみ
for n in range(NURSES):
    for d in range(DAYS):
        prob += lpSum(x[n, d, s] for s in SHIFTS) <= 1

# 2. 平日のシフト制約（月～金）
for d in range(DAYS):
    weekday = (d + 1) % 7  # 1月1日が水曜日の場合の調整
    if weekday < 5:  # 月～金
        prob += lpSum(x[n, d, '日勤'] for n in range(NURSES)) == 6
        prob += lpSum(x[n, d, '夜勤'] for n in range(NURSES)) == 1

# 3. 休日のシフト制約（土日）
for d in range(DAYS):
    weekday = (d + 1) % 7
    if weekday >= 5:  # 土日
        prob += lpSum(x[n, d, '日勤'] for n in range(NURSES)) == 2
        prob += lpSum(x[n, d, '夜勤'] for n in range(NURSES)) == 1

# 4. 夜勤の次の日は必ず休み（夜勤明け）
for n in range(NURSES):
    for d in range(DAYS-1):
        prob += x[n, d, '夜勤'] + lpSum(x[n, d+1, s] for s in SHIFTS) <= 1

# 5. 1人あたりの月間勤務日数上限
for n in range(NURSES):
    prob += lpSum(x[n, d, s] for d in range(DAYS) for s in SHIFTS) <= 20

# 問題を解く
prob.solve()

# 結果の出力
if LpStatus[prob.status] == 'Optimal':
    # 勤務統計の計算
    stats = defaultdict(lambda: defaultdict(int))
    
    # 結果をCSVファイルに出力
    with open('nurse_schedule.csv', 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        # ヘッダー行
        header = ['日付', '曜日'] + [f'看護師{i+1}' for i in range(NURSES)]
        writer.writerow(header)
        
        # データ行
        weekdays = ['月', '火', '水', '木', '金', '土', '日']
        for d in range(DAYS):
            weekday = weekdays[(d + 1) % 7]  # 1月1日が水曜日の場合の調整
            row = [f'2025-01-{d+1:02d}', weekday]
            for n in range(NURSES):
                shift = ''
                for s in SHIFTS:
                    if value(x[n, d, s]) == 1:
                        shift = s
                        stats[n][s] += 1
                        break
                # 前日に夜勤だった場合は夜勤明けと表示
                if d > 0 and value(x[n, d-1, '夜勤']) == 1 and shift == '':
                    shift = '夜勤明け'
                row.append(shift)
            writer.writerow(row)
        
        # 統計情報の追加
        writer.writerow([])  # 空行
        writer.writerow(['勤務統計'])
        writer.writerow(['看護師', '日勤回数', '夜勤回数', '合計勤務日数'])
        for n in range(NURSES):
            total = sum(stats[n].values())
            writer.writerow([
                f'看護師{n+1}',
                stats[n]['日勤'],
                stats[n]['夜勤'],
                total
            ])
    
    print("スケジュールが正常に生成され、nurse_schedule.csvに保存されました。")
else:
    print("最適解が見つかりませんでした。")
