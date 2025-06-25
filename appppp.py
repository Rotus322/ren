import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, time, date
import matplotlib_fontja
from matplotlib.patches import Wedge
import numpy as np

def plot_circular_schedule(df_user, user_name):
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={'aspect': 'equal'})
    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-1.1, 1.1)
    ax.axis('off')

    for _, row in df_user.iterrows():
        start = datetime.strptime(row["開始"], "%H:%M")
        end = datetime.strptime(row["終了"], "%H:%M")
        start_hour = start.hour + start.minute / 60
        end_hour = end.hour + end.minute / 60
        if end_hour < start_hour:
            end_hour += 24  # 深夜またぎ対応

        # 円グラフの角度（0時が真上）
        start_angle = (90 - (start_hour / 24) * 360) % 360
        end_angle = (90 - (end_hour / 24) * 360) % 360
        if end_angle > start_angle:
            end_angle -= 360

        # 内容空白なら白色、そうでなければ青系
        content = row["内容"]
        color = "white" if not content.strip() else "lightblue"

        wedge = Wedge((0, 0), 1.0, theta1=start_angle, theta2=end_angle,
                      facecolor=color, edgecolor='black', linewidth=1.2)
        ax.add_patch(wedge)

        # 内容が空でなければラベルも表示
        if content.strip():
            mid_angle = (start_angle + end_angle) / 2
            rad = np.radians(mid_angle)
            x = 0.65 * np.cos(rad)
            y = 0.65 * np.sin(rad)
            ax.text(x, y, content, ha='center', va='center', fontsize=8)

    # ⏱ 外周に24時間表記
    for h in range(24):
        angle = (90 - h / 24 * 360) % 360
        rad = np.radians(angle)
        x = 1.05 * np.cos(rad)
        y = 1.05 * np.sin(rad)
        label = f"{h}:00"
        ax.text(x, y, label, ha='center', va='center', fontsize=7.5, color='gray')

    ax.set_title(f"{user_name} の予定（0時が真上）", fontsize=12)
    st.pyplot(fig)

st.set_page_config(page_title="予定提出アプリ", layout="centered")
st.title("🗓️ 予定提出アプリ")

# --- 初期設定 ---
if "schedule_count" not in st.session_state:
    st.session_state.schedule_count = 1

def add_schedule():
    st.session_state.schedule_count += 1

# ---------- 提出フォーム ----------
st.header("📩 予定を提出")

name = st.selectbox("名前を選んでください", ["れん", "ゆみ"])
selected_date = st.date_input("予定の日付", value=date.today())

st.write("📝 時間と内容を指定してください")

schedule_data = []

for i in range(st.session_state.schedule_count):
    st.subheader(f"予定 {i + 1}")
    col1, col2 = st.columns(2)
    with col1:
        start_time = st.time_input("開始時間", key=f"start_{i}", value=time(9, 0))
    with col2:
        end_time = st.time_input("終了時間", key=f"end_{i}", value=time(10, 0))

    content = st.text_input("内容（例：朝ご飯・勉強など）", key=f"content_{i}")
    schedule_data.append((start_time, end_time, content))

# ➕ 予定追加ボタン
st.button("➕ 予定を追加", on_click=add_schedule)

# ✅ 提出ボタン
if st.button("提出"):
    new_entries = []
    for (start_time, end_time, content) in schedule_data:
        if not content.strip():
            continue
        if end_time <= start_time:
            st.warning(f"{content} の時間設定が無効です（開始 ≥ 終了）")
            continue

        new_entries.append({
            "日時": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "名前": name,
            "日付": selected_date.strftime("%Y-%m-%d"),
            "開始": start_time.strftime("%H:%M"),
            "終了": end_time.strftime("%H:%M"),
            "内容": content.strip()
        })

    if new_entries:
        new_df = pd.DataFrame(new_entries)
        try:
            existing = pd.read_csv("schedules.csv")
            all_data = pd.concat([existing, new_df], ignore_index=True)
        except FileNotFoundError:
            all_data = new_df

        all_data.to_csv("schedules.csv", index=False)
        st.success(f"✅ {len(new_entries)} 件の予定を登録しました！")
    else:
        st.warning("有効な予定が入力されていません。")

# ---------- グラフ表示 ----------
def plot_user_schedule(df, user_name, selected_date):
    df_user = df[(df["名前"] == user_name) & (df["日付"] == selected_date.strftime("%Y-%m-%d"))]
    if df_user.empty:
        st.warning(f"{user_name} の予定が見つかりませんでした。")
        return

    labels = []
    sizes = []

    for _, row in df_user.iterrows():
        start = datetime.strptime(row["開始"], "%H:%M")
        end = datetime.strptime(row["終了"], "%H:%M")
        duration = (end - start).seconds / 3600
        if duration <= 0:
            continue

        labels.append(f'{row["内容"]} ({row["開始"]}-{row["終了"]})')
        sizes.append(duration)

    fig, ax = plt.subplots(figsize=(5, 5))
    ax.pie(sizes, labels=labels, startangle=90, counterclock=False)
    ax.set_title(f"{user_name} の予定")
    st.pyplot(fig)

st.header("📊 円グラフ予定")
view_date = st.date_input("表示する日付を選択", value=date.today(), key="view_date")

try:
    df = pd.read_csv("schedules.csv")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🧑 れん")
        df_g = df[(df["名前"] == "れん") & (df["日付"] == view_date.strftime("%Y-%m-%d"))]
        plot_circular_schedule(df_g, "れん")
    with col2:
        st.subheader("👩 ゆみ")
        df_g = df[(df["名前"] == "ゆみ") & (df["日付"] == view_date.strftime("%Y-%m-%d"))]
        plot_circular_schedule(df_g, "ゆみ")

except FileNotFoundError:
    st.info("まだ誰も予定を提出していません。")

# ---------- 削除機能 ----------
st.header("🗑️ 予定の削除")

try:
    df = pd.read_csv("schedules.csv")
    del_date = st.date_input("削除したい日付を選んでください", value=date.today(), key="delete_date")

    df_filtered = df[df["日付"] == del_date.strftime("%Y-%m-%d")]

    if df_filtered.empty:
        st.info("この日には削除できる予定がありません。")
    else:
        for i, row in df_filtered.iterrows():
            delete_label = f'{row["名前"]} / {row["内容"]} ({row["開始"]}-{row["終了"]})'
            if st.button(f"🗑️ 削除：{delete_label}", key=f"delete_{i}"):
                df.drop(index=i, inplace=True)
                df.to_csv("schedules.csv", index=False)
                st.success("✅ 削除しました！ページを更新してください。")
                st.stop()

except FileNotFoundError:
    st.info("まだ予定は登録されていません。")

