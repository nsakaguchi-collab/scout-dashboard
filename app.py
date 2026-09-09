import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="企業別 スカウトCVR分析ダッシュボード", layout="wide")

# カスタムCSS（フォント・カード・丸バッジデザイン）
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&display=swap');
    
    html, body, [class*="css"], .stMarkdown, .stText {
        font-family: 'Noto Sans JP', 'Hiragino Sans', 'メイリオ', sans-serif !important;
    }
    
    .kpi-card {
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 20px 24px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        border: 1px solid #EAECF0;
        margin-bottom: 10px;
    }
    .kpi-title {
        font-size: 13px;
        color: #667085;
        font-weight: 700;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 32px;
        color: #101828;
        font-weight: 900;
        line-height: 1.2;
    }
    .kpi-sub {
        font-size: 12px;
        color: #98A2B3;
        margin-top: 4px;
        font-weight: 400;
    }

    /* 画像デザインの完全再現テーブル */
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
        background-color: #FFFFFF;
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #EAECF0;
    }
    .custom-table th {
        background-color: #F9FAFB;
        color: #475467;
        font-weight: 700;
        text-align: left;
        padding: 12px 16px;
        font-size: 13px;
        border-bottom: 1px solid #EAECF0;
    }
    .custom-table td {
        padding: 12px 16px;
        border-bottom: 1px solid #F2F4F7;
        color: #101828;
        font-size: 14px;
        vertical-align: middle;
    }
    
    /* 画像と全く同じ丸数字バッジ */
    .badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        font-weight: 700;
        font-size: 13px;
    }
    .badge-1 { background-color: #FFD000; color: #1D2939; } /* 1位: イエロー */
    .badge-2 { background-color: #C0C0C0; color: #1D2939; } /* 2位: シルバー */
    .badge-3 { background-color: #D97706; color: #FFFFFF; } /* 3位: ブロンズ */
    .badge-other { background-color: #E2E8F0; color: #475467; } /* 4位〜: ライトグレー */
</style>
""", unsafe_allow_html=True)

st.title("企業別 スカウトCVR分析ダッシュボード")

sheet_url_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTPfITrufiiyG9YiQcAARjSMjeMTHKDAfzcurgNOq8b3_FCbtM80NqhEBzT2Sd8sqv3d_a2PWxvZpoq/pub?gid=2141548826&single=true&output=csv"
sheet_url_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWice_bz5atOTDo_RUl5xQxsLT5FS8urptp-yG_WwWPNkCbstkDGtrqdRtv6MolH_V2sjdP_RR7dtA/pub?gid=196825834&single=true&output=csv"

try:
    def clean_num(s):
        return pd.to_numeric(
            s.astype(str).str.replace(",", "").str.replace("%", "").str.strip(), 
            errors="coerce"
        ).fillna(0)

    ng_pattern = "企業取引先名|送信数|エントリー数|cvr|CVR|累計|目標|実績|当日|合計|達成率|オファー|nan|None"

    # 1. 配信企業数
    raw_1 = pd.read_csv(sheet_url_1, header=None)
    e_column_data = raw_1[4].astype(str).str.strip()
    clean_e_names = e_column_data[
        (~e_column_data.str.contains(ng_pattern, case=False, na=False)) & 
        (e_column_data != "")
    ]
    delivered_company_count = clean_e_names.nunique()

    # 2. スカウト集計
    raw_2 = pd.read_csv(sheet_url_2, header=None)
    work_df_2 = pd.DataFrame({
        "企業取引先名": raw_2[0].astype(str).str.strip(),
        "送信予定日": pd.to_datetime(raw_2[2], errors="coerce", format="mixed"),
        "送信数": clean_num(raw_2[4]),
        "エントリー数": clean_num(raw_2[5])
    })

    filtered_df_2 = work_df_2[
        (~work_df_2["企業取引先名"].str.contains(ng_pattern, case=False, na=False)) & 
        (work_df_2["企業取引先名"] != "")
    ].copy()

    # 3. 期間フィルター
    st.sidebar.header("📅 期間フィルター")
    valid_dates = filtered_df_2["送信予定日"].dropna()

    if not valid_dates.empty:
        min_date = valid_dates.min().date()
        max_date = valid_dates.max().date()
        
        selected_range = st.sidebar.date_input(
            "送信予定日の期間を選択",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )

        if isinstance(selected_range, (list, tuple)):
            if len(selected_range) == 2:
                start_date, end_date = selected_range
                filtered_df_2 = filtered_df_2[
                    (filtered_df_2["送信予定日"].dt.date >= start_date) & 
                    (filtered_df_2["送信予定日"].dt.date <= end_date)
                ]
            elif len(selected_range) == 1:
                single_date = selected_range[0]
                filtered_df_2 = filtered_df_2[
                    filtered_df_2["送信予定日"].dt.date == single_date
                ]

    # 4. 集計・ソート
    df_grouped = filtered_df_2.groupby("企業取引先名", as_index=False)[["送信数", "エントリー数"]].sum()
    df_grouped = df_grouped[df_grouped["送信数"] > 0].copy()
    df_grouped["CVR (%)"] = (df_grouped["エントリー数"] / df_grouped["送信数"] * 100).round(2)
    df_final = df_grouped.sort_values(by="CVR (%)", ascending=False).reset_index(drop=True)

    # 5. KPI表示
    total_scout = int(df_final["送信数"].sum())
    total_entry = int(df_final["エントリー数"].sum())
    entry_rate = (total_entry / total_scout * 100) if total_scout > 0 else 0

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">配信企業数</div>
            <div class="kpi-value">{delivered_company_count:,}</div>
            <div class="kpi-sub">社</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">総送付数</div>
            <div class="kpi-value">{total_scout:,}</div>
            <div class="kpi-sub">{len(df_final)} 企業</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">総エントリー数</div>
            <div class="kpi-value">{total_entry:,}</div>
            <div class="kpi-sub">エントリー率 {entry_rate:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">平均エントリー率</div>
            <div class="kpi-value">{entry_rate:.2f}%</div>
            <div class="kpi-sub">全体平均</div>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">分析対象 企業数</div>
            <div class="kpi-value">{len(df_final)}</div>
            <div class="kpi-sub">対象企業</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 6. グラフ表示
    st.subheader("企業別 CVRランキング")
    if not df_final.empty:
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
            font=dict(family="Noto Sans JP, sans-serif"),
            yaxis={"categoryorder": "total ascending"},
            height=max(400, len(df_final) * 35)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("選択した期間に該当するデータがありません。")

    # 7. HTMLレンダリング専用機能 (st.html) を使用した丸数字バッジ表示
    st.subheader("企業別データ一覧 (CVRが高い順)")
    
    rows_html = ""
    for idx, row in df_final.iterrows():
        rank = idx + 1
        if rank == 1:
            badge_cls = "badge-1"
        elif rank == 2:
            badge_cls = "badge-2"
        elif rank == 3:
            badge_cls = "badge-3"
        else:
            badge_cls = "badge-other"
            
        rows_html += f"""
        <tr>
            <td style="text-align: center; width: 80px;"><span class="badge {badge_cls}">{rank}</span></td>
            <td>{row['企業取引先名']}</td>
            <td style="text-align: right;">{int(row['送信数']):,}</td>
            <td style="text-align: right;">{int(row['エントリー数']):,}</td>
            <td style="text-align: right; font-weight: 700;">{row['CVR (%)']:.2f}%</td>
        </tr>
        """

    full_table_html = f"""
    <table class="custom-table">
        <thead>
            <tr>
                <th style="width: 80px; text-align: center;">順位</th>
                <th>企業取引先名</th>
                <th style="text-align: right;">送信数</th>
                <th style="text-align: right;">エントリー数</th>
                <th style="text-align: right;">CVR (%)</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
    """
    
    # st.html() で文字化けせず確実にHTMLを描画
    st.html(full_table_html)

except Exception as e:
    st.error(f"読み込みエラーが発生しました: {e}")
