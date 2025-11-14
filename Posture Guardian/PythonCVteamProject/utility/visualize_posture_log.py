# ===  자세 로그 시각화 (이벤트별 + 개별 그래프 포함) ===
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

def visualize_posture_log(csv_path=None):
    """
    posture_log.csv를 불러와:
      (1) 이벤트별 발생 빈도
      (2) 시간 흐름 누적 그래프
      (3) 자세별 개별 그래프
    를 자동 저장한다.
    """
    try:
        # 경로 설정
        if csv_path is None:
            csv_path = Path(__file__).parent.parent / "posture_log.csv"
        else:
            csv_path = Path(csv_path)

        # 1. 결과물 저장 폴더 정의 (PythonCVteamProject/visualize_results)
        output_dir = Path(__file__).parent.parent / "visualize_results"
        
        # 2. 폴더가 없으면 생성 (exist_ok=True: 이미 있어도 오류 안 냄)
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"📊 그래프를 '{output_dir}' 폴더에 저장합니다.")


        if not csv_path.exists():
            print(f"⚠️ 로그 파일이 없습니다: {csv_path}")
            return

        df = pd.read_csv(csv_path)
        if df.empty:
            print("⚠️ 로그 데이터가 비어있습니다. 그래프를 생성하지 않습니다.")
            return

        # timestamp 파싱
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.dropna(subset=["timestamp"]).sort_values("timestamp")
        if df.empty:
            print("⚠️ 유효한 timestamp가 없어 그래프를 생성할 수 없습니다.")
            return

        # ---------- (1) 이벤트별 발생 빈도 ----------
        counts = df["event_type"].value_counts()
        plt.figure(figsize=(8, 5))
        plt.bar(counts.index, counts.values, color="#6fa8dc")
        plt.title("Posture Warning Frequency")
        plt.xlabel("Event Type")
        plt.ylabel("Count")
        plt.grid(axis='y', linestyle='--', alpha=0.6)
        for i, v in enumerate(counts.values):
            plt.text(i, v + 0.1, str(v), ha='center', fontweight='bold')
        plt.tight_layout()
        plt.savefig("posture_stats_bar.png")
        plt.close()
        print("✅ posture_stats_bar.png 저장 완료")

        # ---------- (2) 시간 흐름 누적 그래프 ----------
        df["count"] = 1
        time_series = (
            df.set_index("timestamp")
              .resample("30S")
              .sum(numeric_only=True)
              .fillna(0)
        )
        time_series["cumulative"] = time_series["count"].cumsum()

        plt.figure(figsize=(8, 5))
        plt.plot(time_series.index, time_series["cumulative"], marker='o', color="#ff7f50")
        plt.title("Cumulative Posture Warnings Over Time")
        plt.xlabel("Time")
        plt.ylabel("Cumulative Count")
        ax = plt.gca()
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
        plt.xticks(rotation=45)
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        plt.savefig("posture_stats_line.png")
        plt.close()
        print("✅ posture_stats_line.png 저장 완료")

        # ---------- (3) 자세별 개별 그래프 ----------
        for event in df["event_type"].unique():
            sub = df[df["event_type"] == event]
            if sub.empty:
                continue

            plt.figure(figsize=(8, 4))
            plt.plot(sub["timestamp"], range(1, len(sub)+1),
                     marker='o', linestyle='-', label=event)
            plt.title(f"{event} Occurrences Over Time")
            plt.xlabel("Time")
            plt.ylabel("Count (incremental)")
            plt.grid(True, linestyle='--', alpha=0.6)
            plt.legend()
            ax = plt.gca()
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
            plt.xticks(rotation=45)
            plt.tight_layout()

            filename = f"{event}_timeline.png".replace(" ", "_")
            plt.savefig(filename)
            plt.close()
            print(f"✅ {filename} 저장 완료")

        print("📊 모든 그래프 생성 완료.")

    except Exception as e:
        print(f"🚨 시각화 중 오류 발생: {e}")

# === 프로그램 종료 후 자동 실행 ===
visualize_posture_log()
