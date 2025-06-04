import random
import math
import copy
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import numpy as np

class NurseScheduling:
    """看護師シフトスケジューリングシステム（焼きなまし法実装）"""
    
    def __init__(self):
        # 基本設定
        self.num_nurses = 10  # ナース総人数
        self.num_days = 31    # 1ヶ月の日数
        self.max_work_days = 20  # 1月の勤務日数上限
        
        # シフトパターン定義
        self.shift_types = {
            0: "休日",
            1: "日勤", 
            2: "夜勤",
            3: "夜勤明",
            4: "早出",
            5: "遅出"
        }
        
        # 曜日定義（0=月曜日, 6=日曜日）
        self.weekdays = list(range(7))
        
        # 必要人数設定
        self.required_staff = self._setup_required_staff()
        
        # ペナルティ重み
        self.penalty_weights = {
            "staff_shortage": 10,       # 人員不足
            "staff_excess": 5,          # 人員過多
            "max_work_days": 20,        # 勤務日数上限違反
            "night_shift_rule": 30,     # 夜勤明けルール違反
            "consecutive_work": 15,     # 連続勤務違反
            "fairness": 1               # 公平性
        }
        
        # 現在のスケジュール（nurses x days）
        self.schedule = np.zeros((self.num_nurses, self.num_days), dtype=int)
        
    def _setup_required_staff(self) -> Dict[str, Dict[int, int]]:
        """曜日別・シフト別必要人数設定"""
        required = {
            "weekday": {  # 平日（月～金）
                1: 6,  # 日勤: 6名
                2: 1,  # 夜勤: 1名
                3: 0,  # 夜勤明: 0名（必要人数ではなく制約）
                4: 0,  # 早出: 0名
                5: 0   # 遅出: 0名
            },
            "weekend": {  # 休日（土・日）
                1: 2,  # 日勤: 2名
                2: 1,  # 夜勤: 1名
                3: 0,  # 夜勤明: 0名
                4: 0,  # 早出: 0名
                5: 0   # 遅出: 0名
            }
        }
        return required
    
    def get_day_type(self, day: int) -> str:
        """日付から平日/休日を判定"""
        # 1日目を月曜日として仮定
        weekday = (day - 1) % 7
        day_type_mapping = {
            True: "weekend",    # 土日
            False: "weekday"    # 平日
        }
        return day_type_mapping[weekday >= 5]
    
    def generate_initial_solution(self) -> np.ndarray:
        """初期解生成"""
        schedule = np.zeros((self.num_nurses, self.num_days), dtype=int)
        
        for day in range(1, self.num_days + 1):
            day_type = self.get_day_type(day)
            required = self.required_staff[day_type]
            
            # 使用可能な看護師リスト
            available_nurses = list(range(self.num_nurses))
            random.shuffle(available_nurses)
            
            # 各シフトに必要な人数を割り当て
            nurse_idx = 0
            for shift_type, count in required.items():
                if count > 0:
                    for _ in range(count):
                        if nurse_idx < len(available_nurses):
                            nurse = available_nurses[nurse_idx]
                            schedule[nurse, day - 1] = shift_type
                            nurse_idx += 1
        
        # 夜勤明けルールを適用
        schedule = self._apply_night_shift_rule(schedule)
        
        self.schedule = schedule
        return schedule
    
    def _apply_night_shift_rule(self, schedule: np.ndarray) -> np.ndarray:
        """夜勤の翌日は必ず夜勤明けルールを適用"""
        for nurse in range(self.num_nurses):
            for day in range(self.num_days - 1):
                if schedule[nurse, day] == 2:  # 夜勤
                    schedule[nurse, day + 1] = 3  # 翌日は夜勤明け
        return schedule
    
    def calculate_penalty(self, schedule: np.ndarray) -> float:
        """ペナルティ計算"""
        total_penalty = 0.0
        
        # 1. 人員配置違反のペナルティ
        total_penalty += self._calculate_staff_penalty(schedule)
        
        # 2. 勤務日数上限違反のペナルティ
        total_penalty += self._calculate_work_days_penalty(schedule)
        
        # 3. 夜勤明けルール違反のペナルティ
        total_penalty += self._calculate_night_shift_penalty(schedule)
        
        # 4. 連続勤務違反のペナルティ
        total_penalty += self._calculate_consecutive_work_penalty(schedule)
        
        # 5. 公平性ペナルティ
        total_penalty += self._calculate_fairness_penalty(schedule)
        
        return total_penalty
    
    def _calculate_staff_penalty(self, schedule: np.ndarray) -> float:
        """人員配置違反のペナルティ計算"""
        penalty = 0.0
        
        for day in range(self.num_days):
            day_type = self.get_day_type(day + 1)
            required = self.required_staff[day_type]
            
            for shift_type, required_count in required.items():
                if required_count > 0:
                    actual_count = np.sum(schedule[:, day] == shift_type)
                    
                    shortage_penalty = {
                        True: self.penalty_weights["staff_shortage"] * (required_count - actual_count),
                        False: 0
                    }
                    excess_penalty = {
                        True: self.penalty_weights["staff_excess"] * (actual_count - required_count),
                        False: 0
                    }
                    
                    penalty += shortage_penalty[actual_count < required_count]
                    penalty += excess_penalty[actual_count > required_count]
        
        return penalty
    
    def _calculate_work_days_penalty(self, schedule: np.ndarray) -> float:
        """勤務日数上限違反のペナルティ計算"""
        penalty = 0.0
        
        for nurse in range(self.num_nurses):
            work_days = np.sum(schedule[nurse, :] != 0)  # 休日以外の日数
            excess_penalty = {
                True: self.penalty_weights["max_work_days"] * (work_days - self.max_work_days),
                False: 0
            }
            penalty += excess_penalty[work_days > self.max_work_days]
        
        return penalty
    
    def _calculate_night_shift_penalty(self, schedule: np.ndarray) -> float:
        """夜勤明けルール違反のペナルティ計算"""
        penalty = 0.0
        
        for nurse in range(self.num_nurses):
            for day in range(self.num_days - 1):
                if schedule[nurse, day] == 2:  # 夜勤
                    violation_penalty = {
                        True: 0,
                        False: self.penalty_weights["night_shift_rule"]
                    }
                    penalty += violation_penalty[schedule[nurse, day + 1] == 3]
        
        return penalty
    
    def _calculate_consecutive_work_penalty(self, schedule: np.ndarray) -> float:
        """連続勤務違反のペナルティ計算"""
        penalty = 0.0
        
        for nurse in range(self.num_nurses):
            consecutive_count = 0
            for day in range(self.num_days):
                if schedule[nurse, day] != 0:  # 勤務日
                    consecutive_count += 1
                else:
                    consecutive_count = 0
                
                # 5日以上連続勤務でペナルティ
                excess_penalty = {
                    True: self.penalty_weights["consecutive_work"] * (consecutive_count - 4),
                    False: 0
                }
                penalty += excess_penalty[consecutive_count > 4]
        
        return penalty
    
    def _calculate_fairness_penalty(self, schedule: np.ndarray) -> float:
        """公平性ペナルティ計算（各シフトの偏り）"""
        penalty = 0.0
        
        # 各シフトタイプの割り当て回数を計算
        for shift_type in [1, 2, 4, 5]:  # 日勤、夜勤、早出、遅出
            counts = []
            for nurse in range(self.num_nurses):
                count = np.sum(schedule[nurse, :] == shift_type)
                counts.append(count)
            
            # 標準偏差をペナルティとして使用
            if len(counts) > 0:
                std_dev = np.std(counts)
                penalty += self.penalty_weights["fairness"] * std_dev
        
        return penalty
    
    def generate_neighbor(self, schedule: np.ndarray) -> np.ndarray:
        """近傍解生成（勤務交換）"""
        new_schedule = copy.deepcopy(schedule)
        
        # 複数の近傍生成方法からランダムに選択
        neighbor_type = random.choice(['swap_shifts', 'change_shift', 'swap_days'])
        
        if neighbor_type == 'swap_shifts':
            # 2人の看護師の特定の日の勤務を交換
            nurse1, nurse2 = random.sample(range(self.num_nurses), 2)
            day = random.randint(0, self.num_days - 1)
            new_schedule[nurse1, day], new_schedule[nurse2, day] = \
                new_schedule[nurse2, day], new_schedule[nurse1, day]
                
        elif neighbor_type == 'change_shift':
            # 1人の看護師の1日の勤務を変更
            nurse = random.randint(0, self.num_nurses - 1)
            day = random.randint(0, self.num_days - 1)
            
            # 現在のシフトと異なるシフトをランダムに選択
            current_shift = new_schedule[nurse, day]
            possible_shifts = [s for s in range(6) if s != current_shift]
            new_shift = random.choice(possible_shifts)
            new_schedule[nurse, day] = new_shift
            
        else:  # swap_days
            # 1人の看護師の2日間の勤務を交換
            nurse = random.randint(0, self.num_nurses - 1)
            day1, day2 = random.sample(range(self.num_days), 2)
            new_schedule[nurse, day1], new_schedule[nurse, day2] = \
                new_schedule[nurse, day2], new_schedule[nurse, day1]
        
        # 夜勤明けルールを再適用
        new_schedule = self._apply_night_shift_rule(new_schedule)
        
        return new_schedule
    
    def simulated_annealing(self, initial_temp: float = 1000.0, 
                          final_temp: float = 1.0, 
                          cooling_rate: float = 0.98,
                          max_iterations: int = 5000) -> Tuple[np.ndarray, float]:
        """焼きなまし法実行"""
        print("焼きなまし法によるスケジュール最適化を開始します...")
        
        # 初期解生成
        current_schedule = self.generate_initial_solution()
        current_penalty = self.calculate_penalty(current_schedule)
        
        best_schedule = copy.deepcopy(current_schedule)
        best_penalty = current_penalty
        
        temperature = initial_temp
        iteration = 0
        
        print(f"初期ペナルティ: {current_penalty:.2f}")
        
        while temperature > final_temp and iteration < max_iterations:
            # 近傍解生成
            neighbor_schedule = self.generate_neighbor(current_schedule)
            neighbor_penalty = self.calculate_penalty(neighbor_schedule)
            
            # 解の受理判定
            delta = neighbor_penalty - current_penalty
            
            # オーバーフロー防止のための安全な受理確率計算
            should_accept = False
            
            if delta < 0:
                # より良い解は必ず受理
                should_accept = True
            else:
                # 悪い解も確率的に受理（オーバーフロー防止）
                exp_arg = -delta / temperature
                if exp_arg > -50:  # exp(-50) ≈ 2e-22（十分小さい値）
                    acceptance_prob = math.exp(exp_arg)
                    should_accept = random.random() < acceptance_prob
                else:
                    should_accept = False
            
            if should_accept:
                current_schedule = neighbor_schedule
                current_penalty = neighbor_penalty
                
                # 最良解更新
                if current_penalty < best_penalty:
                    best_schedule = copy.deepcopy(current_schedule)
                    best_penalty = current_penalty
                    print(f"反復 {iteration}: 新しい最良解発見 (ペナルティ: {best_penalty:.2f})")
            
            # 温度降下
            temperature *= cooling_rate
            iteration += 1
            
            # 進捗表示
            if iteration % 500 == 0:
                print(f"反復 {iteration}: 温度={temperature:.2f}, "
                      f"現在ペナルティ={current_penalty:.2f}, "
                      f"最良ペナルティ={best_penalty:.2f}")
        
        print(f"最適化完了: 最終ペナルティ = {best_penalty:.2f}")
        self.schedule = best_schedule
        return best_schedule, best_penalty
    
    def print_schedule(self, schedule: Optional[np.ndarray] = None):
        """スケジュール表示"""
        if schedule is None:
            schedule = self.schedule
        
        print("\n=== 看護師シフトスケジュール ===")
        print("看護師\\日", end="")
        for day in range(1, min(self.num_days + 1, 32)):
            print(f"{day:>4}", end="")
        print()
        
        for nurse in range(self.num_nurses):
            print(f"看護師{nurse+1:2d}", end="")
            for day in range(min(self.num_days, 31)):
                shift_code = schedule[nurse, day]
                shift_name = self.shift_types[shift_code]
                display_mapping = {
                    "休日": " 休",
                    "日勤": " 日", 
                    "夜勤": " 夜",
                    "夜勤明": "夜明",
                    "早出": " 早",
                    "遅出": " 遅"
                }
                print(f"{display_mapping[shift_name]:>4}", end="")
            print()
    
    def analyze_schedule(self, schedule: Optional[np.ndarray] = None):
        """スケジュール分析"""
        if schedule is None:
            schedule = self.schedule
        
        print("\n=== スケジュール分析 ===")
        
        # 各看護師の勤務日数
        print("各看護師の勤務日数:")
        for nurse in range(self.num_nurses):
            work_days = np.sum(schedule[nurse, :] != 0)
            print(f"看護師{nurse+1}: {work_days}日")
        
        # 各日の人員配置
        print("\n各日の人員配置:")
        for day in range(min(self.num_days, 31)):
            day_type = self.get_day_type(day + 1)
            print(f"{day+1}日 ({day_type}):")
            for shift_type in [1, 2, 3, 4, 5]:
                count = np.sum(schedule[:, day] == shift_type)
                shift_name = self.shift_types[shift_type]
                print(f"  {shift_name}: {count}人")
        
        # ペナルティ詳細
        total_penalty = self.calculate_penalty(schedule)
        print(f"\n総ペナルティ: {total_penalty:.2f}")

def main():
    """メイン実行関数"""
    print("看護師シフトスケジューリングシステム")
    print("=====================================")
    
    # スケジューラ初期化
    scheduler = NurseScheduling()
    
    # 焼きなまし法実行
    best_schedule, best_penalty = scheduler.simulated_annealing(
        initial_temp=1000.0,
        final_temp=1.0,
        cooling_rate=0.98,
        max_iterations=5000
    )
    
    # 結果表示
    scheduler.print_schedule()
    scheduler.analyze_schedule()

if __name__ == "__main__":
    main() 