
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, date
import os

# CSVファイル名
CSV_FILE = "schedule.csv"

# 初期データフレーム作成
def load_data():
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE)
    else:
        return pd.DataFrame(columns=["名前", "日付", "開始", "終了", "内容"])

# 時刻文字列 → float時間（24:00対応）
def time_str_to_float(tstr):
    return 24.0 if tstr == "24:00" else int(tstr[:2]) + int(tstr[3:]) / 60

# 表示用：24:00 → 00:00
def time_display_label(tstr):
    return "00:00" if tstr == "24:00" else tstr

# 時刻オプション（30分刻み）
time_options = [f"{h:02d}:{m:02d}" for h in range(24) for m in (0, 30)] + ["24:00"]

# 円グラフ描画関数
def plot_user_schedule(df, user_name, selected_date):
    df_user = df[(df["名前"] == user_name) & (df["日付"] == selected_date.strftime("%Y-%m-%d"))]
    if df_user.empty:
        st.warning(f"{user_name} の予定が見つかりませんでした。")
        return

    df_user_sorted = df_user.sort_values(by="開始")

    labels = []
    sizes = []
    colors = []
    raw_labels = []
    time_points = []

    current_time = 0.0
    color_palette = [
        "#FF9999", "#FFCC99", "#99CCFF", "#99FF99", "#FFB3E6",
        "#CCCCFF", "#FFFF99", "#FF6666", "#66CCCC", "#FF9966"
    ]
    color_index = 0

    for _, row in df_user_sorted.iterrows():
        start = time_str_to_float(row["開始"])
        end = time_str_to_float(row["終了"])

        if start > current_time:
            labels.append("")
            raw_labels.append("（空き）")
            sizes.append(start - current_time)
            colors.append("lightgray")
            time_points.append(current_time)
            time_points.append(start)

        dur = end - start
        labels.append("")
        raw_labels.append(f'{row["内容"]}')
        sizes.append(dur)
        colors.append(color_palette[color_index % len(color_palette)])
        color_index += 1
        time_points.append(start)
        time_points.append(end)

        current_time = end

    if current_time < 24.0:
        labels.append("")
        raw_labels.append("（空き）")
        sizes.append(24.0 - current_time)
        colors.append("lightgray")
        time_points.append(current_time)
        time_points.append(24.0)

    fig, ax = plt.subplots(figsize=(6, 6))
    wedges, _ = ax.pie(sizes, startangle=90, counterclock=False, colors=colors)
    ax.set_title(f"{user_name} の予定")

    total = sum(sizes)
    angle = 90
    radius = 1

    for i, wedge in enumerate(wedges):
        dur = sizes[i]
        label = raw_labels[i]

        if not label or label == "（空き）":
            angle -= dur / total * 360
            continue

        theta = angle - (dur / 2 / total) * 360
        if dur >= 1.0:
            x = radius * 0.6 * np.cos(np.radians(theta))
            y = radius * 0.6 * np.sin(np.radians(theta))
            ax.text(x, y, label, ha="center", va="center", fontsize=8, color="black")
        else:
            x0 = radius * 0.8 * np.cos(np.radians(theta))
            y0 = radius * 0.8 * np.sin(np.radians(theta))
            x1 = radius * 1.2 * np.cos(np.radians(theta))
            y1 = radius * 1.2 * np.sin(np.radians(theta))
            ax.plot([x0, x1], [y0, y1], color="black", linewidth=0.8)
            ax.text(x1, y1, label, ha="center", va="center", fontsize=8, color="black")

        angle -= dur / total * 360

    for h in sorted(set(time_points)):
        h_rounded = round(h, 4)
        if abs(h_rounded - 24.0) < 1e-2:
            h_rounded = 0.0

        angle_h = 90 - (h_rounded / 24) * 360
        x = 1.05 * np.cos(np.radians(angle_h))
        y = 1.05 * np.sin(np.radians(angle_h))
        hour = int(h_rounded)
        minute = int(round((h_rounded % 1) * 60))
        label = f"{hour:02d}:{minute:02d}"
        ax.text(x, y, label, ha="center", va="center", fontsize=6)

    st.pyplot(fig)

# Streamlit アプリ本体
st.title("🕒 円グラフ予定提出アプリ")

data = load_data()
name = st.selectbox("名前を選んでください", ["郡司島", "ゆみ"])
selected_date = st.date_input("日付を選んでください", date.today())

st.subheader("予定を追加")
content = st.text_input("予定の内容")
col1, col2 = st.columns(2)
with col1:
    start_time_str = st.selectbox("開始時間", time_options, key="start")
with col2:
    end_time_str = st.selectbox("終了時間", time_options, index=len(time_options)-1, key="end")

if st.button("予定を追加"):
    display_start = time_display_label(start_time_str)
    display_end = time_display_label(end_time_str)
    new_row = {
        "名前": name,
        "日付": selected_date.strftime("%Y-%m-%d"),
        "開始": display_start,
        "終了": display_end,
        "内容": content
    }
    data = pd.concat([data, pd.DataFrame([new_row])], ignore_index=True)
    data.to_csv(CSV_FILE, index=False)
    st.success("予定を追加しました！")

st.subheader("予定の表示")
plot_user_schedule(data, name, selected_date)

st.subheader("予定の削除")
df_filtered = data[(data["名前"] == name) & (data["日付"] == selected_date.strftime("%Y-%m-%d"))]
if not df_filtered.empty:
    for i, row in df_filtered.iterrows():
        row_str = f'{row["開始"]}〜{row["終了"]} {row["内容"]}'
        if st.button(f"削除: {row_str}", key=f"delete_{i}"):
            data = data.drop(i).reset_index(drop=True)
            data.to_csv(CSV_FILE, index=False)
            st.success("予定を削除しました！")
            st.experimental_rerun()
else:
    st.info("この日の予定はありません。")
