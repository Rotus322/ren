import streamlit as st
import matplotlib.pyplot as plt

st.title("1日の予定")

st.markdown("予定を入力してください（例：9〜10時は起床）")

# 入力用の予定リスト
schedule = []
num_tasks = st.number_input("予定の数", min_value=1, max_value=10, value=5)

for i in range(num_tasks):
    col1, col2, col3 = st.columns(3)
    with col1:
        label = st.text_input(f"{i+1}件目の予定", key=f"label{i}")
    with col2:
        start = st.number_input("開始時刻", min_value=0.0, max_value=24.0, step=0.5, key=f"start{i}")
    with col3:
        end = st.number_input("終了時刻", min_value=0.0, max_value=24.0, step=0.5, key=f"end{i}")

    if label and end > start:
        schedule.append({"label": label, "start": start, "end": end})

# 円グラフを表示
if st.button("円グラフを作成"):
    if schedule:
        labels = [item["label"] for item in schedule]
        sizes = [item["end"] - item["start"] for item in schedule]

        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(aspect="equal"))
        ax.pie(sizes, labels=labels, startangle=90, counterclock=False)
        ax.set_title("あなたの1日（24時間円グラフ）")

        st.pyplot(fig)

        # 保存機能
        fig.savefig("today_schedule.png")
        st.success("グラフを today_schedule.png に保存しました。")
    else:
        st.warning("予定が入力されていません。")