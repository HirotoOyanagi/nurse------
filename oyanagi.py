import random
import math
import copy
import pandas as pd
import os
import datetime
import time
import pathlib
import platform

# 定数
NUM_NURSES = 10
SHIFTS_EN = ['R', 'D', 'N', 'A', 'E', 'L']  # 休み, 日勤, 夜勤, 夜勤明, 早出, 遅出 (英語表記)
SHIFTS_JP = ['休み', '日勤', '夜勤', '夜勤明', '早出', '遅出'] # 日本語表記
SHIFT_MAP_EN_TO_JP = dict(zip(SHIFTS_EN, SHIFTS_JP))
SHIFT_MAP_JP_TO_EN = dict(zip(SHIFTS_JP, SHIFTS_EN))

DAYS_IN_MONTH = 31 # 1ヶ月の日数
MAX_WORK_DAYS = 20 # 月間勤務日数上限

# シフトの必要人数 (月～金)
REQUIRED_SHIFTS_WEEKDAY = {'日勤': 6, '夜勤': 1, '休み': 0, '夜勤明': 0, '早出': 0, '遅出': 0}
# シフトの必要人数 (土、日)
REQUIRED_SHIFTS_WEEKEND = {'日勤': 2, '夜勤': 1, '休み': 0, '夜勤明': 0, '早出': 0, '遅出': 0}

# シフト間の制約
# 夜勤の次の日は夜勤明 (夜勤 -> 夜勤明)
# 夜勤以外の次の日に夜勤明は入らない (日勤/早出/遅出/休み -> 夜勤明 は不可)
FORBIDDEN_FOLLOW_SHIFTS = {
    '夜勤': [], # 夜勤の次には夜勤明が望ましいが、それ以外は強くペナルティ
    '日勤': ['夜勤明'],
    '早出': ['夜勤明'],
    '遅出': ['夜勤明'],
    '休み': ['夜勤明'],
    '夜勤明': [] # 夜勤明の次のシフトに制約はない
}

def is_weekend(day):
    """
    指定された日が週末かどうかを判定する (0:月, ..., 6:日)
    ここでは簡易的にday % 7 が 5または6を週末とする (0-indexed)
    例: 1日(月)の場合、0%7=0。6日(土)の場合、5%7=5。7日(日)の場合、6%7=6。
    """
    return (day % 7 == 5) or (day % 7 == 6)

def generate_initial_solution():
    """
    初期解を生成する
    各ナースの各日のシフトをランダムに割り当てる
    """
    solution = []
    for _ in range(NUM_NURSES):
        nurse_schedule = []
        for day in range(DAYS_IN_MONTH):
            # 初期解生成時に夜勤明の制約は考慮しない (評価関数でペナルティを与える)
            # '夜勤明' は単独で割り当てない
            nurse_schedule.append(random.choice([s for s in SHIFTS_JP if s != '夜勤明'])) 
        solution.append(nurse_schedule)
    return solution

def calculate_cost(solution):
    """
    現在のシフト割り当てのコストを計算する (評価関数)
    制約違反が多いほどコストが高くなる
    """
    cost = 0

    # 1. 各日のシフト必要人数に関する制約
    for day in range(DAYS_IN_MONTH):
        daily_shifts = {shift_type: 0 for shift_type in SHIFTS_JP}
        for nurse_id in range(NUM_NURSES):
            daily_shifts[solution[nurse_id][day]] += 1
        
        required_shifts = REQUIRED_SHIFTS_WEEKEND if is_weekend(day) else REQUIRED_SHIFTS_WEEKDAY

        for shift_type, required_count in required_shifts.items():
            cost += abs(daily_shifts[shift_type] - required_count) * 50 # 違反が大きいほどペナルティも大きく

    # 2. シフト間の連続制約
    for nurse_id in range(NUM_NURSES):
        for day in range(DAYS_IN_MONTH - 1):
            current_shift = solution[nurse_id][day]
            next_shift = solution[nurse_id][day+1]

            # 夜勤の次の日は夜勤明 (N -> A) 制約
            if current_shift == '夜勤' and next_shift != '夜勤明':
                cost += 100 # 強い制約違反として大きなペナルティ

            # 夜勤以外の次の日に夜勤明は入らない制約
            if current_shift in FORBIDDEN_FOLLOW_SHIFTS and next_shift in FORBIDDEN_FOLLOW_SHIFTS[current_shift]:
                 cost += 100 # 強い制約違反として大きなペナルティ
            
    # 3. 月間勤務日数上限 (20日)
    for nurse_id in range(NUM_NURSES):
        work_days = 0
        for day in range(DAYS_IN_MONTH):
            if solution[nurse_id][day] not in ['休み', '夜勤明']: # 休みと夜勤明は勤務日数にカウントしない
                work_days += 1
        if work_days > MAX_WORK_DAYS:
            cost += (work_days - MAX_WORK_DAYS) * 20 # 超過日数に応じてペナルティ

   

    return cost

def generate_neighbor(solution):
    """
    現在の解から近傍解を生成する
    ランダムに1人のナースの1日のシフトを変更する
    """
    new_solution = copy.deepcopy(solution)
    
    nurse_idx = random.randint(0, NUM_NURSES - 1)
    day_idx = random.randint(0, DAYS_IN_MONTH - 1)
    
    # 新しいシフトを選択 ('夜勤明'は単独で割り当てないように、ただし夜勤後の割り当ては可能)
    # 評価関数で制御するため、ここではランダムに選ぶ
    new_shift = random.choice(SHIFTS_JP)
    
    new_solution[nurse_idx][day_idx] = new_shift
    
    return new_solution

def simulated_annealing(initial_temperature, cooling_rate, iterations):
    """
    焼きなまし法を実行する
    """
    current_solution = generate_initial_solution()
    current_cost = calculate_cost(current_solution)
    
    best_solution = copy.deepcopy(current_solution)
    best_cost = current_cost
    
    temperature = initial_temperature
    
    print(f"焼きなまし法を開始します。初期温度: {initial_temperature:.2f}, 冷却率: {cooling_rate}, 繰り返し回数: {iterations}")

    for i in range(iterations):
        neighbor_solution = generate_neighbor(current_solution)
        neighbor_cost = calculate_cost(neighbor_solution)
        
        delta_E = neighbor_cost - current_cost
        
        if delta_E < 0: # 改善した場合
            current_solution = neighbor_solution
            current_cost = neighbor_cost
        else: # 悪化した場合でも確率的に採択
            acceptance_probability = math.exp(-delta_E / temperature)
            if random.random() < acceptance_probability:
                current_solution = neighbor_solution
                current_cost = neighbor_cost
        
        if current_cost < best_cost:
            best_solution = copy.deepcopy(current_solution)
            best_cost = current_cost
            
        temperature *= cooling_rate
        
        if i % 5000 == 0: # 進行状況を1000回ごとに表示
            print(f"  Iteration {i:06d}, Current Cost: {current_cost:04d}, Best Cost: {best_cost:04d}, Temp: {temperature:.2f}")
        
        if best_cost == 0: # コストが0になったら早期終了
            print(f"  Iteration {i:06d}, Optimal solution found (Cost: 0). Early exit.")
            break

    return best_solution, best_cost

def print_schedule(schedule):
    """
    生成されたスケジュールを整形してコンソールに出力する
    """
    print("\n--- ナースシフトスケジュール ---")
    header = "  " + "".join([f"{d:3d}" for d in range(1, DAYS_IN_MONTH + 1)])
    print(header)
    print("-" * (len(header) + 2))
    for i, nurse_schedule in enumerate(schedule):
        print(f"N{i+1:<2} " + "".join([f"{s:3s}" for s in nurse_schedule]))
    print("-" * (len(header) + 2))

    # 各ナースの勤務日数
    print("\n--- 各ナースの勤務日数 ---")
    for i, nurse_schedule in enumerate(schedule):
        work_days = sum(1 for s in nurse_schedule if s not in ['休み', '夜勤明'])
        off_days_and_after_night_shift = sum(1 for s in nurse_schedule if s in ['休み', '夜勤明'])
        print(f"N{i+1}: 勤務 {work_days}日, 休み/夜勤明 {off_days_and_after_night_shift}日")

def save_schedule_to_csv(schedule, filename="nurse_schedule.csv"):
    """
    生成されたスケジュールをCSVファイルに保存する
    """
    nurse_ids = [f"N{i+1}" for i in range(NUM_NURSES)]
    day_columns = [f"{d}日" for d in range(1, DAYS_IN_MONTH + 1)]
    
    df = pd.DataFrame(schedule, index=nurse_ids, columns=day_columns)
    
    try:
        df.to_csv(filename, encoding='utf-8-sig') # Excelで開けるようにutf-8-sig
        print(f"\nシフトスケジュールを '{filename}' に保存しました。")
    except Exception as e:
        print(f"\nCSVファイルの保存中にエラーが発生しました: {e}")

def fix_consecutive_night_shift_off(schedule):
    """
    夜勤明けが同じ人で二回連続になった場合、2回目の夜勤明けを休みに変更する
    """
    modified_count = 0
    
    for nurse_id in range(NUM_NURSES):
        for day in range(DAYS_IN_MONTH - 1):
            current_shift = schedule[nurse_id][day]
            next_shift = schedule[nurse_id][day + 1]
            
            # 夜勤明けが2日連続の場合
            if current_shift == '夜勤明' and next_shift == '夜勤明':
                schedule[nurse_id][day + 1] = '休み'
                modified_count += 1
                print(f"  N{nurse_id + 1}の{day + 2}日目: 夜勤明 → 休み に変更")
    
    if modified_count > 0:
        print(f"\n夜勤明け連続の修正を{modified_count}箇所実施しました。")
    else:
        print("\n夜勤明け連続は検出されませんでした。")
    
    return schedule

if __name__ == "__main__":
    # 焼きなまし法のパラメータ
    initial_temp = 2000.0  # 初期温度 (高めに設定)
    cooling_rate = 0.998 # 冷却率 (ゆっくり冷却)
    iterations = 200000 # 繰り返し回数 (多めに設定)

    final_schedule_jp, final_cost = simulated_annealing(initial_temp, cooling_rate, iterations)

    print("\n--- 焼きなまし法終了 ---")
    print(f"最終コスト: {final_cost}")

    if final_cost == 0:
        print("おめでとうございます！すべての制約を満たす解が見つかりました！")
    else:
        print("残念ながら、すべての制約を満たす解は見つかりませんでした。")
        print("ただし、これが現在の探索における最適な近似解です。")
        print("コストの内訳を分析し、制約の緩和やパラメータ調整を検討してください。")

    # 夜勤明け連続の修正処理
    print("\n--- 夜勤明け連続チェック・修正 ---")
    final_schedule_jp = fix_consecutive_night_shift_off(final_schedule_jp)

    print_schedule(final_schedule_jp)
    save_schedule_to_csv(final_schedule_jp, "nurse_schedule.csv")
