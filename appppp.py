import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, time, date

st.set_page_config(page_title="予定提出＆可視化アプリ", layout="centered")
st.title("🗓️ みんなの予定提出＆可視化アプリ")

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
    import numpy as np  # 時間ラベル用

    df_user = df[(df["名前"] == user_name) & (df["日付"] == selected_date.strftime("%Y-%m-%d"))]
    if df_user.empty:
        st.warning(f"{user_name} の予定が見つかりませんでした。")
        return

    df_user_sorted = df_user.sort_values(by="開始")

    labels = []
    sizes = []
    colors = []
    time_marks = []

    def to_hour(tstr):
        t = datetime.strptime(tstr, "%H:%M")
        return t.hour + t.minute / 60

    current_time = 0.0
    color_palette = [
        "#FF9999", "#FFCC99", "#99CCFF", "#99FF99", "#FFB3E6",
        "#CCCCFF", "#FFFF99", "#FF6666", "#66CCCC", "#FF9966"
    ]
    color_index = 0

    for _, row in df_user_sorted.iterrows():
        start = to_hour(row["開始"])
        end = to_hour(row["終了"])

        # 空き時間
        if start > current_time:
            labels.append("（空き時間）")
            sizes.append(start - current_time)
            colors.append("lightgray")
            time_marks.append(start)

        # 予定本体
        labels.append(f'{row["内容"]} ({row["開始"]}-{row["終了"]})')
        sizes.append(end - start)
        colors.append(color_palette[color_index % len(color_palette)])
        time_marks.append(end)

        color_index += 1
        current_time = end

    if current_time < 24.0:
        labels.append("（空き時間）")
        sizes.append(24.0 - current_time)
        colors.append("lightgray")
        time_marks.append(24.0)

    # --- グラフ描画 ---
    fig, ax = plt.subplots(figsize=(6, 6))
    wedges, _ = ax.pie(
        sizes,
        labels=labels,
        startangle=90,
        counterclock=False,
        colors=colors
    )
    ax.set_title(f"{user_name} の予定（24時間・区切り時間表示）")

    # --- 時間マークの表示 ---
    total = sum(sizes)
    angle = 90  # Start from 0:00 (top)

    for dur, mark in zip(sizes, time_marks):
        angle -= dur / total * 360
        x = 1.1 * np.cos(np.radians(angle))
        y = 1.1 * np.sin(np.radians(angle))
        label_time = f"{int(mark):02d}:{int((mark % 1) * 60):02d}"
        ax.text(x, y, label_time, ha="center", va="center", fontsize=9, color="black")

    st.pyplot(fig)
st.header("📊 円グラフで予定を比較")
view_date = st.date_input("表示する日付を選択", value=date.today(), key="view_date")

try:
    df = pd.read_csv("schedules.csv")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🧑 れん")
        plot_user_schedule(df, "れん", view_date)
    with col2:
        st.subheader("👩 ゆみ")
        plot_user_schedule(df, "ゆみ", view_date)

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

