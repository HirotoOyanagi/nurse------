from pulp import *

# 問題の定義
prob = LpProblem("NurseScheduling", LpMinimize)

# パラメータの設定
NUM_NURSES = 10
SHIFTS = ['日勤', '夜勤', '夜勤明', '早出', '遅出']
DAYS_IN_MONTH = 31  # 1月は31日
MAX_WORKING_DAYS = 20

# 日付の設定
dates = range(1, DAYS_IN_MONTH + 1)

# 変数の定義
# x[nurse][date][shift] = 1 if nurse n works shift s on date d, 0 otherwise
x = LpVariable.dicts("shift",
                    ((n, d, s) for n in range(NUM_NURSES) 
                               for d in dates 
                               for s in SHIFTS),
                    cat='Binary')

# 目的関数: シフトの公平性を最大化
prob += lpSum(x[n, d, s] for n in range(NUM_NURSES) 
                            for d in dates 
                            for s in SHIFTS)

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
    prob += lpSum(x[n, d, '日勤'] for n in range(NUM_NURSES)) == 6
    prob += lpSum(x[n, d, '夜勤'] for n in range(NUM_NURSES)) == 1
    prob += lpSum(x[n, d, '夜勤明'] for n in range(NUM_NURSES)) == 1

# 4. 夜勤の次の日は夜勤明
for n in range(NUM_NURSES):
    for d in range(1, DAYS_IN_MONTH):
        prob += x[n, d, '夜勤'] <= x[n, d+1, '夜勤明']

# 問題の求解
prob.solve()

# 結果の出力
if LpStatus[prob.status] == 'Optimal':
    print("最適解が見つかりました！")
    print("\nナーススケジュール:")
    
    # カレンダー形式で出力
    for d in dates:
        print(f"\n{d}日目:")
        for s in SHIFTS:
            nurses = [n for n in range(NUM_NURSES) if value(x[n, d, s]) == 1]
            if nurses:
                print(f"{s}: ナース {nurses}")
else:
    print("最適解が見つかりませんでした。") 