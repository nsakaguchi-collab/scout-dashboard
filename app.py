import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="企業別 スカウトCVR分析ダッシュボード", layout="wide")
st.title("企業別 スカウトCVR分析ダッシュボード")

# ① スプレッドシート①のWeb公開URL（配信企業数算出用）
sheet_url_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTPfITrufiiyG9YiQcAARjSMjeMTHKDAfzcurgNOq8b3_FCbtM80NqhEBzT2Sd8sqv3d_a2PWxvZpoq/pub?gid=2141548826&single=true&output=csv"

# ② スプレッドシート②のWeb公開URL（スカウト送信数・エントリー数・CVR集計用）
sheet_url_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWice_bz5atOTDo_RUl5xQxsLT5FS8urptp-yG_WwWPNkCbstkDGtrqdRtv6MolH_V2sjdP_RR7dtA/pub?gid=196825834&single=true&output=csv"

try:
    # 共通の数値クリーンアップ用関数（カンマや%を除去して数値化）
    def clean_num(s):
        return pd.to_numeric(
            s.astype(str).str.replace(",", "").str.replace("%", "").str.strip(), 
            errors="coerce"
        ).fillna(0)

    # 共通の除外キーワードパターン
    ng_pattern = "企業取引先名|送信数|エントリー数|cvr|CVR|累計|目標|実績|当日|合計|達成率|オファー|nan|None"

    # ==========================================
    # 1. スプレッドシート①から「配信企業数」を計算
    # ==========================================
    raw_1 = pd.read_csv(sheet_url_1, header=None)
    
    # E列（4列目）から有効な取引先名を抽出
    e_column_data = raw_1[4].astype(str).str.strip()
    clean_e_names = e_column_data[
        (~e_column_data.str.contains(ng_pattern, case=False, na=False)) & 
        (e_column_data != "")
    ]
    delivered_company_count = clean_e_names.nunique()  # 重複を除いた企業数

    # ==========================================
    # 2. スプレッドシート②から送信数・エントリー数・CVRを集計
    # ==========================================
    raw_2 = pd.read_csv(sheet_url_2, header=None)

    # A列(0), E列(4), F列(5) をピンポイント抽出
    work_df_2 = pd.DataFrame({
        "企業取引先名": raw_2[0].astype(str).str.strip(), # A列
        "送信数": clean_num(raw_2[4]),                    # E列
        "エントリー数": clean_num(raw_2[5])               # F列
    })

    filtered_df_2 = work_df_2[
        (~work_df_2["企業取引先名"].str.contains(ng_pattern, case=False, na=False)) & 
        (work_df_2["企業取引先名"] != "")
    ].copy()

    # A列（企業取引先名）ごとに E列（送信数）と F列（エントリー数）を合計集計
    df_grouped = filtered_df_2.groupby("企業取引先名", as_index=False)[["送信数", "エントリー数"]].sum()

    # 送信数が1件以上ある企業のみ抽出
    df_grouped = df_grouped[df_grouped["送信数"] > 0].copy()

    # 合計された送信数とエントリー数から正しく CVR (%) を計算
    df_grouped["CVR (%)"] = (df_grouped["エントリー数"] / df_grouped["送信数"] * 100).round(2)

    # CVR が高い順（降順）にソート
    df_final = df_grouped.sort_values(by="CVR (%)", ascending=False)

    # ==========================================
    # 3. KPI表示（①の「配信企業数」＋ ②の集計値）
    # ==========================================
    total_scout = int(df_final["送信数"].sum())
    total_entry = int(df_final["エントリー数"].sum())
    entry_rate = (total_entry / total_scout * 100) if total_scout > 0 else 0

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("配信企業数 ", f"{delivered_company_count:,} 社")
    col2.metric("総送信数 ", f"{total_scout:,} 件")
    col3.metric("総エントリー数", f"{total_entry:,} 件")
    col4.metric("全体平均 CVR", f"{entry_rate:.2f} %")
    col5.metric("分析対象 企業数", f"{len(df_final)} 社")

    st.markdown("---")

    # CVRランキンググラフ
    st.subheader("企業別 CVRランキング ")
    fig = px.bar(
        df_final,
        x="CVR (%)",
        y="企業取引先名",
        orientation="h",
        text="CVR (%)",
        color="CVR (%)",
        color_continuous_scale="Viridis"
    )
    fig.update_layout(
        yaxis={"categoryorder": "total ascending"},
        height=max(400, len(df_final) * 35)
    )
    st.plotly_chart(fig, use_container_width=True)

    # データ一覧（CVR順）
    st.subheader("企業別データ一覧 (CVRが高い順)")
    st.dataframe(df_final, use_container_width=True)

except Exception as e:
    st.error(f"読み込みエラーが発生しました: {e}")