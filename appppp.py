import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, time, date
import matplotlib_fontja
import numpy as np
from matplotlib.patches import ConnectionPatch
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json



SPREADSHEET_ID = "1T-7Ue8nHolwx9KrK0vdsqMYINxdbj830NnQ1TVoka8M"  # ←変更必須！

def get_worksheet():
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    creds_dict = json.loads(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID)
    return sheet.sheet1

def load_schedules_from_gsheet():
    worksheet = get_worksheet()
    records = worksheet.get_all_records()
    df = pd.DataFrame(records)
    return df
    
def append_schedule_to_gsheet(entries):
    worksheet = get_worksheet()
    for e in entries:
        worksheet.append_row([
            e["日時"], e["名前"], e["日付"],
            e["開始"], e["終了"], e["内容"]
        ])






st.set_page_config(page_title="予定アプリ", layout="centered")
st.title("\U0001F4C5 予定アプリ")

if "schedule_count" not in st.session_state:
    st.session_state.schedule_count = 1

def add_schedule():
    st.session_state.schedule_count += 1

st.header("\U0001F4E9 予定を提出")

name = st.selectbox("名前を選んでください", ["れん", "ゆみ"])
selected_date = st.date_input("予定の日付", value=date.today())

st.write("\U0001F4DD 時間と内容を指定してください")

schedule_data = []

for i in range(st.session_state.schedule_count):
    st.subheader(f"予定 {i + 1}")
    col1, col2 = st.columns(2)
    with col1:
        hour = st.selectbox("開始時", list(range(0, 24)), key=f"sh_{i}")
        minute = st.selectbox("開始分", list(range(0, 60, 5)), key=f"sm_{i}")
        start_time = time(hour, minute)
    with col2:
        hour_e = st.selectbox("終了時", list(range(0, 25)), key=f"eh_{i}")
        minute_e = st.selectbox("終了分", list(range(0, 60, 5)), key=f"em_{i}")
        if hour_e == 24:
            end_time = time(23, 59)
        else:
            end_time = time(hour_e, minute_e)

    content = st.text_input("内容（例：朝ご飯・勉強など）", key=f"content_{i}")
    schedule_data.append((start_time, end_time, content))

st.button("➕ 予定を追加", on_click=add_schedule)

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
        append_schedule_to_gsheet(new_entries)
        st.success(f"✅ {len(new_entries)} 件の予定を Google Sheets に保存しました！")
    else:
        st.warning("有効な予定が入力されていません。")

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

    def to_hour(tstr):
        if tstr == "23:59":
            return 24.0
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
        x = radius * 0.6 * np.cos(np.radians(theta))
        y = radius * 0.6 * np.sin(np.radians(theta))

        if dur >= 1.0:
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

st.header("\U0001F4CA 円グラフで予定を比較")
view_date = st.date_input("表示する日付を選択", value=date.today(), key="view_date")

try:
    df = load_schedules_from_gsheet()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🧑 れん")
        plot_user_schedule(df, "れん", view_date)
    with col2:
        st.subheader("👩 ゆみ")
        plot_user_schedule(df, "ゆみ", view_date)

except Exception as e:
    st.error(f"読み込み中にエラーが発生しました: {e}")

st.header("🗑️ 予定の削除")

def delete_schedule_from_gsheet(target_row_index):
    worksheet = get_worksheet()
    worksheet.delete_rows(target_row_index + 2)  # 1行目はヘッダーなので+2

try:
    df = load_schedules_from_gsheet()
    del_date = st.date_input("削除したい日付を選んでください", value=date.today(), key="delete_date")

    df_filtered = df[df["日付"] == del_date.strftime("%Y-%m-%d")]

    if df_filtered.empty:
        st.info("この日には削除できる予定がありません。")
    else:
        for i, row in df_filtered.iterrows():
            delete_label = f'{row["名前"]} / {row["内容"]} ({row["開始"]}-{row["終了"]})'
            if st.button(f"🗑️ 削除：{delete_label}", key=f"delete_{i}"):
                # 元の df の index を取得
                original_index = int(df[df.eq(row).all(axis=1)].index[0])

                delete_schedule_from_gsheet(original_index)
                st.success("✅ 削除しました！ページを更新してください。")
                st.stop()

except Exception as e:
    st.error(f"削除中にエラーが発生しました: {e}")
    
