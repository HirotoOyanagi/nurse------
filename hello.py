from pulp import *
import calendar

# 問題の定義
prob = LpProblem("NurseScheduling", LpMinimize)

# パラメータの設定
NUM_NURSES = 10
SHIFTS = ['日勤', '夜勤', '夜勤明']  # シフトを3種類に制限
DAYS_IN_MONTH = 31
MAX_WORKING_DAYS = 20

# ナースの名前設定
NURSE_NAMES = {
    0: "佐藤 美咲",
    1: "鈴木 愛",
    2: "高橋 優子",
    3: "田中 真理",
    4: "渡辺 京子",
    5: "伊藤 陽子",
    6: "山本 恵美",
    7: "中村 直美",
    8: "小林 真由美",
    9: "加藤 美穂"
}

# 日付の設定
dates = range(1, DAYS_IN_MONTH + 1)

# 曜日の判定関数
def is_weekend(day):
    return day % 7 == 6 or day % 7 == 0  # 土日の場合

# 変数の定義
x = LpVariable.dicts("shift",
                    ((n, d, s) for n in range(NUM_NURSES) 
                               for d in dates 
                               for s in SHIFTS),
                    cat='Binary')

# 目的関数: シフトの公平性を最大化
prob += 0  # 目的関数を最小化（制約条件のみを考慮）

# 制約条件
# 1. 1日1シフトの制約
for n in range(NUM_NURSES):
    for d in dates:
        prob += lpSum(x[n, d, s] for s in SHIFTS) <= 1

# 2. 月間シフト数の上限
for n in range(NUM_NURSES):
    prob += lpSum(x[n, d, s] for d in dates for s in SHIFTS) <= MAX_WORKING_DAYS

# 3. 各シフトの必要人数
for d in dates:
    if is_weekend(d):  # 休日
        prob += lpSum(x[n, d, '日勤'] for n in range(NUM_NURSES)) == 2
        prob += lpSum(x[n, d, '夜勤'] for n in range(NUM_NURSES)) == 1
    else:  # 平日
        prob += lpSum(x[n, d, '日勤'] for n in range(NUM_NURSES)) == 6
        prob += lpSum(x[n, d, '夜勤'] for n in range(NUM_NURSES)) == 1

# 4. 夜勤の次の日は夜勤明
for n in range(NUM_NURSES):
    for d in range(1, DAYS_IN_MONTH):
        prob += x[n, d, '夜勤'] <= x[n, d+1, '夜勤明']

# 問題の求解
prob.solve()

# 結果の出力
if LpStatus[prob.status] == 'Optimal' or LpStatus[prob.status] == 'Infeasible':
    print("シフトスケジュール:")
    
    # カレンダー形式で出力
    for d in dates:
        print(f"\n{d}日目 ({'休日' if is_weekend(d) else '平日'}):")
        for s in SHIFTS:
            nurses = [NURSE_NAMES[n] for n in range(NUM_NURSES) if value(x[n, d, s]) == 1]
            if nurses:
                print(f"{s}: {', '.join(nurses)}")
    
    print("\n勤務統計:")
    for n in range(NUM_NURSES):
        total_days = sum(value(x[n, d, s]) for d in dates for s in SHIFTS)
        weekend_days = sum(value(x[n, d, s]) for d in dates for s in SHIFTS if is_weekend(d))
        print(f"{NURSE_NAMES[n]}: 総勤務日数={total_days}, 休日勤務={weekend_days}")
else:
    print(f"シフトが見つかりませんでした。ステータス: {LpStatus[prob.status]}") 