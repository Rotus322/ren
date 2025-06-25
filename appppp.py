import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import streamlit as st

def plot_user_schedule(df, user_name, selected_date):
    from matplotlib.patches import ConnectionPatch

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
        time_points.extend([start, end])

        if start > current_time:
            labels.append("")
            raw_labels.append("（空き）")
            sizes.append(start - current_time)
            colors.append("lightgray")
            time_points.append(current_time)

        dur = end - start
        labels.append("")
        raw_labels.append(f'{row["内容"]} ({row["開始"]}-{row["終了"]})')
        sizes.append(dur)
        colors.append(color_palette[color_index % len(color_palette)])
        color_index += 1
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
    ax.set_title(f"{user_name} の予定（時間と内容付き）")

    total = sum(sizes)
    angle = 90
    radius = 1

    for i, wedge in enumerate(wedges):
        dur = sizes[i]
        label = raw_labels[i]

        theta = angle - (dur / 2 / total) * 360
        x = radius * 0.6 * np.cos(np.radians(theta))
        y = radius * 0.6 * np.sin(np.radians(theta))

        if not label or label == "（空き）":
            pass
        elif dur >= 1.0:
            ax.text(x, y, label, ha="center", va="center", fontsize=8, color="black")
        else:
            x0 = radius * 0.9 * np.cos(np.radians(theta))
            y0 = radius * 0.9 * np.sin(np.radians(theta))
            x1 = radius * 1.2 * np.cos(np.radians(theta))
            y1 = radius * 1.2 * np.sin(np.radians(theta))
            ax.plot([x0, x1], [y0, y1], color="black", linewidth=0.8)
            ax.text(x1, y1, label, ha="center", va="center", fontsize=7, color="black")

        angle -= dur / total * 360

    for h in sorted(set(time_points)):
        angle_h = 90 - (h / 24) * 360
        x = 1.35 * np.cos(np.radians(angle_h))
        y = 1.35 * np.sin(np.radians(angle_h))
        ax.text(x, y, f"{int(h):02d}:{int((h % 1)*60):02d}", ha="center", va="center", fontsize=6)

    st.pyplot(fig)
