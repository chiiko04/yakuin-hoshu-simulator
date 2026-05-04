import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time

st.set_page_config(
    page_title="役員報酬シミュレーター",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans JP', sans-serif; }
.main { background-color: #0f0f1a; }
h1 { color: #d4a853 !important; font-size: 1.4rem !important; }
h2 { color: #d4a853 !important; font-size: 1.1rem !important; }
h3 { color: #c8b8e0 !important; font-size: 1rem !important; }
.stNumberInput label, .stSlider label, .stSelectbox label { color: #c8b8e0 !important; }
.result-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border: 1px solid #d4a853; border-radius: 12px; padding: 20px; margin: 8px 0;
}
.result-main {
    background: linear-gradient(135deg, #2a1a0e 0%, #1e1a0e 100%);
    border: 2px solid #d4a853; border-radius: 16px; padding: 24px;
    text-align: center; margin: 12px 0;
}
.big-number { font-size: 2.2rem; font-weight: 700; color: #d4a853; }
.label-text { font-size: 0.85rem; color: #8888aa; margin-bottom: 4px; }
.value-text { font-size: 1.1rem; color: #e8e0f0; font-weight: 700; }
.detail-text { font-size: 0.72rem; color: #666688; line-height: 1.8; margin-top: 6px; }
.badge-yes {
    background: #1a3a1a; color: #4caf50; border: 1px solid #4caf50;
    border-radius: 20px; padding: 4px 16px; font-size: 0.9rem; font-weight: 700;
}
.badge-no {
    background: #3a1a1a; color: #ef5350; border: 1px solid #ef5350;
    border-radius: 20px; padding: 4px 16px; font-size: 0.9rem; font-weight: 700;
}
.section-divider { border-top: 1px solid #333355; margin: 16px 0; }
.note-text { font-size: 0.75rem; color: #666688; line-height: 1.6; }
.warn-text { font-size: 0.75rem; color: #d4a853; line-height: 1.6; }
.stTabs [data-baseweb="tab-list"] { background-color: #1a1a2e; border-radius: 8px; }
.stTabs [data-baseweb="tab"] { color: #8888aa !important; }
.stTabs [aria-selected="true"] { color: #d4a853 !important; background-color: #2a2a3e !important; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
#  定数・テーブル定義
# ══════════════════════════════════════════════════════════════

# 標準報酬月額等級表（協会けんぽ・2024年度）
# (等級, 標準報酬月額, 月収下限, 月収上限)
KENPO_GRADES = [
    (1, 58000, 0, 63000),
    (2, 68000, 63000, 73000),
    (3, 78000, 73000, 83000),
    (4, 88000, 83000, 93000),
    (5, 98000, 93000, 101000),
    (6, 104000, 101000, 107000),
    (7, 110000, 107000, 114000),
    (8, 118000, 114000, 122000),
    (9, 126000, 122000, 130000),
    (10, 134000, 130000, 138000),
    (11, 142000, 138000, 146000),
    (12, 150000, 146000, 155000),
    (13, 160000, 155000, 165000),
    (14, 170000, 165000, 175000),
    (15, 180000, 175000, 185000),
    (16, 190000, 185000, 195000),
    (17, 200000, 195000, 210000),
    (18, 220000, 210000, 230000),
    (19, 240000, 230000, 250000),
    (20, 260000, 250000, 270000),
    (21, 280000, 270000, 290000),
    (22, 300000, 290000, 310000),
    (23, 320000, 310000, 330000),
    (24, 340000, 330000, 350000),
    (25, 360000, 350000, 370000),
    (26, 380000, 370000, 395000),
    (27, 410000, 395000, 425000),
    (28, 440000, 425000, 455000),
    (29, 470000, 455000, 485000),
    (30, 500000, 485000, 515000),
    (31, 530000, 515000, 545000),
    (32, 560000, 545000, 575000),
    (33, 590000, 575000, 605000),
    (34, 620000, 605000, 635000),
    (35, 650000, 635000, 665000),
    (36, 680000, 665000, 695000),
    (37, 710000, 695000, 730000),
    (38, 750000, 730000, 770000),
    (39, 790000, 770000, 810000),
    (40, 830000, 810000, 855000),
    (41, 880000, 855000, 905000),
    (42, 930000, 905000, 955000),
    (43, 980000, 955000, 1005000),
    (44, 1040000, 1005000, 1090000),
    (45, 1090000, 1090000, 1150000),
    (46, 1150000, 1150000, 1210000),
    (47, 1210000, 1210000, 1270000),
    (48, 1270000, 1270000, 1330000),
    (49, 1330000, 1330000, 1390000),
    (50, 1390000, 1390000, float('inf')),
]

# 厚生年金は等級1〜32まで（上限: 650,000円）
NENKIN_GRADES = [g for g in KENPO_GRADES if g[0] <= 32]

# 所得税率テーブル（課税所得、税率、控除額）
INCOME_TAX_TABLE = [
    (1950000, 0.05, 0),
    (3300000, 0.10, 97500),
    (6950000, 0.20, 427500),
    (9000000, 0.23, 636000),
    (18000000, 0.33, 1536000),
    (40000000, 0.40, 2796000),
    (float('inf'), 0.45, 4796000),
]

# 給与所得控除テーブル
SALARY_DEDUCTION_TABLE = [
    (550000, lambda s: s),
    (1610000, lambda s: 550000),
    (1800000, lambda s: s * 0.4 - 100000),
    (3600000, lambda s: s * 0.3 + 80000),
    (6600000, lambda s: s * 0.2 + 440000),
    (8500000, lambda s: s * 0.1 + 1100000),
    (float('inf'), lambda s: 1950000),
]


# ══════════════════════════════════════════════════════════════
#  計算関数
# ══════════════════════════════════════════════════════════════

def get_hyojun_hoshu(monthly_salary, grades):
    """標準報酬月額を等級表から取得"""
    for grade, hyojun, lower, upper in grades:
        if monthly_salary < upper:
            return hyojun
    return grades[-1][1]

def calc_shakai_hoken(annual_salary, health_rate, pension_rate):
    """
    社会保険料を標準報酬月額等級表で計算
    戻り値: (健康保険料_年, 厚生年金_年, 合計_年, 標準報酬月額_健保, 標準報酬月額_厚年)
    """
    monthly = annual_salary / 12
    hyojun_kenpo = get_hyojun_hoshu(monthly, KENPO_GRADES)
    hyojun_nenkin = get_hyojun_hoshu(monthly, NENKIN_GRADES)

    health_monthly = hyojun_kenpo * health_rate
    pension_monthly = hyojun_nenkin * pension_rate

    health_annual = health_monthly * 12
    pension_annual = pension_monthly * 12

    return health_annual, pension_annual, health_annual + pension_annual, hyojun_kenpo, hyojun_nenkin

def get_salary_deduction(salary):
    """給与所得控除（6段階）"""
    for upper, func in SALARY_DEDUCTION_TABLE:
        if salary <= upper:
            return func(salary)
    return 1950000

def get_income_tax(taxable):
    """所得税（累進課税）＋復興特別所得税2.1%"""
    if taxable <= 0:
        return 0, 0
    base_tax = 0
    rate = 0
    deduction = 0
    for upper, r, d in INCOME_TAX_TABLE:
        if taxable <= upper:
            rate = r
            deduction = d
            break
    base_tax = taxable * rate - deduction
    fukko_tax = base_tax * 0.021  # 復興特別所得税
    return base_tax + fukko_tax, fukko_tax

def calc_net_detail(salary, health_rate, pension_rate, resident_rate):
    """
    個人の手取り計算（詳細内訳付き）
    戻り値: dict
    """
    if salary <= 0:
        return {
            'net': 0, 'health': 0, 'pension': 0, 'si_total': 0,
            'deduction': 0, 'taxable': 0, 'income_tax': 0, 'fukko_tax': 0,
            'resident_tax': 0, 'hyojun_kenpo': 0, 'hyojun_nenkin': 0
        }

    health, pension, si_total, hyojun_k, hyojun_n = calc_shakai_hoken(
        salary, health_rate, pension_rate
    )
    deduction = get_salary_deduction(salary)
    taxable = max(0, salary - deduction - si_total - 480000)  # 基礎控除48万
    income_tax, fukko_tax = get_income_tax(taxable)
    resident_tax = taxable * resident_rate
    net = salary - si_total - income_tax - resident_tax

    return {
        'net': net,
        'health': health,
        'pension': pension,
        'si_total': si_total,
        'deduction': deduction,
        'taxable': taxable,
        'income_tax': income_tax,
        'fukko_tax': fukko_tax,
        'resident_tax': resident_tax,
        'hyojun_kenpo': hyojun_k,
        'hyojun_nenkin': hyojun_n,
    }

def calc_corp_tax(profit):
    """法人税（800万の壁）"""
    if profit <= 0:
        return 0, 0
    if profit <= 8000000:
        tax = profit * 0.25
    else:
        tax = 2000000 + (profit - 8000000) * 0.34
    return tax, profit - tax

def run_simulation(sales, corp_expenses, pearl_profit, gaichuu_hi,
                   health_rate, pension_rate, resident_rate, step):
    """
    総当たりシミュレーション

    外注費（gaichuu_hi）の扱い：
    ・統合（役員化）の場合：外注費ゼロ。法人経費は corp_expenses のみ。
    ・非統合（現状）の場合：外注費が法人経費に加算され、
                           同額がちこむんの個人事業収入に加算される。
    """
    results = []

    for integrated in [True, False]:
        # 統合/非統合で経費と売上を切り替え
        if integrated:
            eff_corp_exp = corp_expenses          # 外注費なし
            chikomun_extra = 0                     # ちこむん追加収入なし
        else:
            eff_corp_exp = corp_expenses + gaichuu_hi  # 外注費を法人経費に加算
            chikomun_extra = gaichuu_hi            # 同額がちこむん収入に

        cur_sales = sales + (pearl_profit if integrated else 0)
        limit = cur_sales - eff_corp_exp
        if limit <= 0:
            continue

        # 非統合の場合はちこむん報酬ゼロ固定（s_cループ不要）
        s_c_range = range(0, 15000001, step) if integrated else [0]

        for s_a in range(3000000, min(50000001, int(limit) + 1), step):
            for s_c in s_c_range:
                cur_salary = s_a + s_c
                if cur_salary > limit:
                    break

                corp_profit = cur_sales - eff_corp_exp - cur_salary
                if corp_profit < 0:
                    continue

                c_tax, c_cash = calc_corp_tax(corp_profit)
                d_a = calc_net_detail(s_a, health_rate, pension_rate, resident_rate)

                if integrated:
                    d_c = calc_net_detail(s_c, health_rate, pension_rate, resident_rate)
                else:
                    # 非統合：パール利益＋外注費収入、青色控除65万・基礎控除48万
                    chikomun_income = pearl_profit + chikomun_extra
                    p_income = max(0, chikomun_income - 650000 - 480000)
                    i_tax, f_tax = get_income_tax(p_income)
                    r_tax = p_income * resident_rate
                    d_c = {
                        'net': chikomun_income - i_tax - r_tax,
                        'health': 0, 'pension': 0, 'si_total': 0,
                        'deduction': 650000, 'taxable': p_income,
                        'income_tax': i_tax, 'fukko_tax': f_tax,
                        'resident_tax': r_tax,
                        'hyojun_kenpo': 0, 'hyojun_nenkin': 0,
                    }

                total = d_a['net'] + d_c['net'] + c_cash
                results.append({
                    'あきたん報酬': s_a,
                    'ちこむん報酬': s_c,
                    '統合': integrated,
                    '世帯手残り': int(total),
                    '法人留保': int(c_cash),
                    'あきたん手取り': int(d_a['net']),
                    'ちこむん手取り': int(d_c['net']),
                    'ちこむん収入': int(s_c if integrated else pearl_profit + chikomun_extra),
                    'あきたん健保': int(d_a['health']),
                    'あきたん厚年': int(d_a['pension']),
                    'あきたん所得税': int(d_a['income_tax']),
                    'あきたん住民税': int(d_a['resident_tax']),
                    'あきたん復興税': int(d_a['fukko_tax']),
                    'ちこむん健保': int(d_c['health']),
                    'ちこむん厚年': int(d_c['pension']),
                    'ちこむん所得税': int(d_c['income_tax']),
                    'ちこむん住民税': int(d_c['resident_tax']),
                    'ちこむん復興税': int(d_c['fukko_tax']),
                    '法人税': int(c_tax),
                    '法人経費_実効': int(eff_corp_exp),
                    '外注費': int(gaichuu_hi if not integrated else 0),
                    'あきたん標準報酬_健保': d_a['hyojun_kenpo'],
                    'あきたん標準報酬_厚年': d_a['hyojun_nenkin'],
                })

    if not results:
        return None
    return pd.DataFrame(results)


# ══════════════════════════════════════════════════════════════
#  UI
# ══════════════════════════════════════════════════════════════

st.markdown("## 💎 役員報酬 最適化シミュレーター V3")
st.markdown('<p class="note-text">⚠️ 概算シミュレーションです。実際の税務処理は必ず税理士にご確認ください。</p>',
            unsafe_allow_html=True)

tab_main, tab_settings, tab_basis = st.tabs([
    "📊 シミュレーション", "⚙️ 税率設定", "📋 計算根拠・税率表"
])

# ── 税率設定タブ ──────────────────────────────────────────
with tab_settings:
    st.markdown("### 税率・保険料設定")
    st.markdown('<p class="note-text">デフォルト：大垣市・岐阜県 2026年度想定</p>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        health_pct = st.number_input(
            "健康保険料率（介護込・労使折半後 %）",
            value=5.79, min_value=1.0, max_value=15.0, step=0.01, key="health_pct",
            help="岐阜県 2026: (10.02% + 1.56%) ÷ 2 = 5.79%"
        )
        pension_pct = st.number_input(
            "厚生年金料率（労使折半後 %）",
            value=9.15, min_value=1.0, max_value=15.0, step=0.01, key="pension_pct",
            help="全国一律: 18.3% ÷ 2 = 9.15%"
        )
    with c2:
        resident_pct = st.number_input(
            "住民税率（%）",
            value=10.0, min_value=5.0, max_value=15.0, step=0.1, key="resident_pct",
            help="大垣市：市民税6% + 県民税4% = 10%"
        )
        city_name = st.text_input("市区町村名（表示用）", value="大垣市", key="city_name")

    st.markdown("#### 役員報酬の探索刻み幅（計算精度）")
    st.markdown('<p class="note-text">「何万円刻みで役員報酬の組み合わせを試すか」の設定です。<br>刻みが細かいほど最適解の精度が上がりますが、計算時間が長くなります。</p>', unsafe_allow_html=True)
    step_options = {
        "粗い：20万円刻み（計算時間 〜0.1秒）": 200000,
        "標準：10万円刻み（計算時間 〜数秒）": 100000,
        "精密：5万円刻み（計算時間 〜十数秒）": 50000,
        "高精度：1万円刻み（計算時間 〜数分）": 10000,
    }
    step_label = st.selectbox("刻み幅を選ぶ", list(step_options.keys()),
                               index=1, key="step_label")

# ── 計算根拠・税率表タブ ──────────────────────────────────
with tab_basis:
    st.markdown("### 所得税 累進課税テーブル（2026年度）")
    st.markdown('<p class="note-text">※ 復興特別所得税（基準所得税額×2.1%）を加算します（2013〜2037年）</p>',
                unsafe_allow_html=True)
    st.dataframe(pd.DataFrame([
        {"課税所得（以下）": "195万円", "税率": "5%", "控除額": "0円", "実効税率（復興税込）": "約5.1%"},
        {"課税所得（以下）": "330万円", "税率": "10%", "控除額": "97,500円", "実効税率（復興税込）": "約10.2%"},
        {"課税所得（以下）": "695万円", "税率": "20%", "控除額": "427,500円", "実効税率（復興税込）": "約20.4%"},
        {"課税所得（以下）": "900万円", "税率": "23%", "控除額": "636,000円", "実効税率（復興税込）": "約23.5%"},
        {"課税所得（以下）": "1,800万円", "税率": "33%", "控除額": "1,536,000円", "実効税率（復興税込）": "約33.7%"},
        {"課税所得（以下）": "4,000万円", "税率": "40%", "控除額": "2,796,000円", "実効税率（復興税込）": "約40.8%"},
        {"課税所得（以下）": "4,000万円超", "税率": "45%", "控除額": "4,796,000円", "実効税率（復興税込）": "約45.9%"},
    ]), use_container_width=True, hide_index=True)

    st.markdown("### 給与所得控除テーブル（2026年度）")
    st.dataframe(pd.DataFrame([
        {"給与収入（以下）": "55万円", "控除額": "給与収入の全額"},
        {"給与収入（以下）": "161万円", "控除額": "55万円（定額）"},
        {"給与収入（以下）": "180万円", "控除額": "収入×40% − 10万円"},
        {"給与収入（以下）": "360万円", "控除額": "収入×30% + 8万円"},
        {"給与収入（以下）": "660万円", "控除額": "収入×20% + 44万円"},
        {"給与収入（以下）": "850万円", "控除額": "収入×10% + 110万円"},
        {"給与収入（以下）": "850万円超", "控除額": "195万円（上限）"},
    ]), use_container_width=True, hide_index=True)

    st.markdown("### 社会保険料（協会けんぽ・岐阜県 2026年度）")
    col_h, col_p = st.columns(2)
    with col_h:
        st.markdown("**健康保険（介護保険込）**")
        st.markdown(f'<p class="note-text">料率：{st.session_state.get("health_pct", 5.79):.2f}%（折半後）<br>標準報酬月額等級表（50等級）を使用</p>',
                    unsafe_allow_html=True)
    with col_p:
        st.markdown("**厚生年金**")
        st.markdown(f'<p class="note-text">料率：{st.session_state.get("pension_pct", 9.15):.2f}%（折半後）<br>標準報酬月額等級表（32等級・上限65万円）を使用</p>',
                    unsafe_allow_html=True)

    st.markdown("### 標準報酬月額 等級表（抜粋）")
    grade_df = pd.DataFrame([
        {"等級": g[0], "標準報酬月額": f"{g[1]:,}円",
         "月収目安（以上〜未満）": f"{g[2]:,}円 〜 {int(g[3]):,}円" if g[3] != float('inf') else f"{g[2]:,}円 〜"}
        for g in KENPO_GRADES
    ])
    st.dataframe(grade_df, use_container_width=True, hide_index=True, height=300)

    st.markdown("### 法人税率")
    st.dataframe(pd.DataFrame([
        {"課税所得": "800万円以下", "税率": "25%（中小法人軽減税率）", "備考": "資本金1億円以下の法人"},
        {"課税所得": "800万円超", "税率": "34%", "備考": "800万円部分は25%、超過分は34%"},
    ]), use_container_width=True, hide_index=True)

    st.markdown("### 住民税")
    st.markdown(f'<p class="note-text">{st.session_state.get("city_name","大垣市")}：市民税6% + 県民税4% = 10%（均等割は別途）<br>本シミュレーターでは課税所得×10%で計算（均等割は含まない）</p>',
                unsafe_allow_html=True)

    st.markdown("### 💡 最適解のヒント（なぜその報酬額になるのか）")
    st.markdown("""
<div class="warn-text">
<strong>① 法人税800万の壁</strong><br>
法人利益が800万円を超えると法人税率が上がります（25%→34%）。<br>
そのため「法人利益がちょうど800万円以下になるよう役員報酬に回す」のが基本戦略です。<br>
<br>
<strong>② 社会保険料の等級の壁（2人の報酬を非対称にする理由）</strong><br>
社会保険料は月収に応じた「等級（階段）」で決まります。<br>
例：440万（月収36.7万）→ 等級25（標準報酬36万）<br>
　　455万（月収37.9万）→ 等級26（標準報酬38万）←社保が上がる<br>
　　470万（月収39.2万）→ 等級26（標準報酬38万）←455万と同じ等級のまま<br>
<br>
つまり「440万+470万」は「455万+455万」と法人利益が同じでも、<br>
440万側が1段下の等級になって社保が安くなる分だけ世帯手残りが多くなります。<br>
<br>
<strong>③ 夫婦で報酬額が違う結果が出た場合</strong><br>
逆の配分（あきたん高・ちこむん低 / ちこむん高・あきたん低）でも<br>
世帯合計手残りは同じになるケースがあります。<br>
どちらの配分にするかは税理士さんと相談してください。<br>
<br>
<strong>④ 端数処理について</strong><br>
実際の税務では課税所得の1,000円未満・所得税の100円未満の切り捨てがありますが、<br>
本プログラムでは省略しています。数千円程度の誤差が生じる場合があります。
</div>
""", unsafe_allow_html=True)

    st.markdown("### ⚠️ 本シミュレーターの限界・注意事項")
    st.markdown("""
<div class="warn-text">
• 社会保険料は標準報酬月額等級表で計算していますが、月額変更届・算定基礎届のタイミングによる差異は考慮していません<br>
• 住民税の均等割（年間約5,000円程度）は含まれていません<br>
• 年末調整・確定申告による医療費控除・生命保険料控除等は考慮していません<br>
• 法人税は概算です。地方法人税・法人住民税・法人事業税を含む実効税率は異なります<br>
• 消費税は計算に含まれていません<br>
• 結果は必ず税理士にご確認ください
</div>
""", unsafe_allow_html=True)

# ── メインタブ ────────────────────────────────────────────
with tab_main:
    col_input, col_result = st.columns([1, 1.2], gap="large")

    with col_input:
        st.markdown("### 📥 数字を入れる")
        sales_man = st.number_input(
            "あきたん会社の売上（万円）",
            min_value=500, max_value=100000, value=1800, step=100, key="sales"
        )
        corp_exp_man = st.number_input(
            "法人経費・役員報酬除く（万円）",
            min_value=0, max_value=50000, value=300, step=50, key="corp_exp",
            help="通信費・地代家賃・外注費など。役員報酬は含めない"
        )
        pearl_man = st.number_input(
            "パール事業の利益（万円）",
            min_value=0, max_value=5000, value=10, step=10, key="pearl",
            help="ちこむんの個人事業利益（売上−仕入等）"
        )
        gaichuu_man = st.number_input(
            "外注費（万円）",
            min_value=0, max_value=5000, value=100, step=1, key="gaichuu",
            help="非統合（ちこむん個人事業）の場合のみ有効。\n法人経費に加算され、同額がちこむんの個人事業収入になります。\n統合（役員化）した場合は自動的にゼロになります。"
        )
        st.markdown(
            '<p class="note-text">💡 外注費は非統合の場合のみ有効：法人経費に加算＆ちこむん収入に加算</p>',
            unsafe_allow_html=True
        )

        step_val = step_options[st.session_state.get("step_label", list(step_options.keys())[1])]
        h_rate = st.session_state.get("health_pct", 5.79) / 100
        p_rate = st.session_state.get("pension_pct", 9.15) / 100
        r_rate = st.session_state.get("resident_pct", 10.0) / 100

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        st.markdown(
            f'<p class="note-text">税率設定：{st.session_state.get("city_name","大垣市")} ／ '
            f'健保{st.session_state.get("health_pct",5.79):.2f}% 厚年{st.session_state.get("pension_pct",9.15):.2f}% '
            f'住民税{st.session_state.get("resident_pct",10.0):.1f}%<br>'
            f'刻み幅：{step_val//10000}万円　変更は「税率設定」タブから</p>',
            unsafe_allow_html=True
        )

    # ── 計算実行 ──
    sales = sales_man * 10000
    corp_expenses = corp_exp_man * 10000
    pearl_profit = pearl_man * 10000
    gaichuu_hi = gaichuu_man * 10000

    t_start = time.time()
    with st.spinner("計算中... ⚙️"):
        df = run_simulation(sales, corp_expenses, pearl_profit, gaichuu_hi,
                            h_rate, p_rate, r_rate, step_val)
    elapsed = time.time() - t_start

    with col_result:
        st.markdown("### 📈 最適解")

        if df is None or df.empty:
            st.error("計算できる組み合わせがありません。数字を見直してください。")
        else:
            best = df.loc[df['世帯手残り'].idxmax()]
            integrated = bool(best['統合'])

            # 計算時間
            st.markdown(
                f'<p class="note-text">計算時間：{elapsed:.2f}秒 ／ {len(df):,}パターンを検証</p>',
                unsafe_allow_html=True
            )

            # メイン結果カード
            st.markdown(f"""
            <div class="result-main">
                <div class="label-text">世帯の年間手残り（最大）</div>
                <div class="big-number">¥{best['世帯手残り']:,}</div>
                <div style="margin-top:8px">
                    {'<span class="badge-yes">✅ 事業統合 推奨</span>' if integrated else '<span class="badge-no">❌ 事業統合 不要</span>'}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 内訳カード
            c1, c2 = st.columns(2)

            def detail_html(label, salary, d, is_corp=False):
                if is_corp:
                    return f"""
                    <div class="result-card">
                        <div class="label-text">{label}</div>
                        <div class="value-text">¥{int(d['法人留保']):,}</div>
                        <div class="detail-text">
                            法人利益（税前）：¥{int(d['法人留保']) + int(d['法人税']):,}<br>
                            法人税：−¥{int(d['法人税']):,}
                        </div>
                    </div>"""
                si = d.get('あきたん健保', 0) if 'あきたん' in label else d.get('ちこむん健保', 0)
                pi = d.get('あきたん厚年', 0) if 'あきたん' in label else d.get('ちこむん厚年', 0)
                it = d.get('あきたん所得税', 0) if 'あきたん' in label else d.get('ちこむん所得税', 0)
                ft = d.get('あきたん復興税', 0) if 'あきたん' in label else d.get('ちこむん復興税', 0)
                rt = d.get('あきたん住民税', 0) if 'あきたん' in label else d.get('ちこむん住民税', 0)
                net = d.get('あきたん手取り', 0) if 'あきたん' in label else d.get('ちこむん手取り', 0)
                return f"""
                <div class="result-card">
                    <div class="label-text">{label}</div>
                    <div class="value-text">報酬 ¥{int(salary):,}</div>
                    <div class="label-text" style="margin-top:8px">手取り</div>
                    <div class="value-text">¥{int(net):,}</div>
                    <div class="detail-text">
                        健康保険：−¥{int(si):,}<br>
                        厚生年金：−¥{int(pi):,}<br>
                        所得税（復興税込）：−¥{int(it):,}　※うち復興税 ¥{int(ft):,}<br>
                        住民税：−¥{int(rt):,}
                    </div>
                </div>"""

            with c1:
                st.markdown(detail_html(
                    "あきたん役員報酬", best['あきたん報酬'], best
                ), unsafe_allow_html=True)

            with c2:
                if integrated:
                    c_label = "ちこむん報酬（役員）"
                    c_sal = best['ちこむん報酬']
                    st.markdown(detail_html(c_label, c_sal, best), unsafe_allow_html=True)
                else:
                    # 非統合：外注費＋パール利益の内訳を表示
                    c_income = int(best['ちこむん収入'])
                    c_it = int(best['ちこむん所得税'])
                    c_rt = int(best['ちこむん住民税'])
                    c_net = int(best['ちこむん手取り'])
                    st.markdown(f"""
                    <div class="result-card">
                        <div class="label-text">ちこむん（個人事業・現状維持）</div>
                        <div class="value-text">収入合計 ¥{c_income:,}</div>
                        <div class="detail-text">
                            パール利益：¥{int(pearl_profit):,}<br>
                            外注費収入：¥{int(gaichuu_hi):,}<br>
                            ────────────────<br>
                            所得税（復興税込）：−¥{c_it:,}<br>
                            住民税：−¥{c_rt:,}<br>
                            ※社保は扶養または国保別途
                        </div>
                        <div class="label-text" style="margin-top:8px">手取り</div>
                        <div class="value-text">¥{c_net:,}</div>
                    </div>
                    """, unsafe_allow_html=True)

            # 法人留保（外注費の扱い明示）
            eff_exp = int(best['法人経費_実効'])
            gaichuu_disp = int(best['外注費'])
            st.markdown(f"""
            <div class="result-card">
                <div class="label-text">法人留保（税引後）</div>
                <div class="value-text">¥{int(best['法人留保']):,}</div>
                <div class="detail-text">
                    法人利益（税前）：¥{int(best['法人留保']) + int(best['法人税']):,}<br>
                    法人税：−¥{int(best['法人税']):,}<br>
                    ────────────────<br>
                    法人経費（役員報酬除く）：¥{eff_exp:,}
                    {'　※外注費¥' + f'{gaichuu_disp:,}を含む' if gaichuu_disp > 0 else '　※外注費なし（統合）'}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # グラフ
            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
            st.markdown("### 📊 あきたん報酬 vs 世帯手残り")

            df_g = df[df['統合'] == integrated].groupby('あきたん報酬')['世帯手残り'].max().reset_index()
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_g['あきたん報酬'] / 10000,
                y=df_g['世帯手残り'] / 10000,
                mode='lines',
                line=dict(color='#d4a853', width=2),
                fill='tozeroy',
                fillcolor='rgba(212,168,83,0.1)',
                name='世帯手残り（万円）'
            ))
            fig.add_trace(go.Scatter(
                x=[best['あきたん報酬'] / 10000],
                y=[best['世帯手残り'] / 10000],
                mode='markers',
                marker=dict(color='#ff6b9d', size=12, symbol='star'),
                name=f'最適解 {int(best["あきたん報酬"])//10000}万円'
            ))
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(15,15,26,0.8)',
                font=dict(color='#c8b8e0', family='Noto Sans JP'),
                xaxis=dict(title='あきたん役員報酬（万円）', gridcolor='#2a2a4a', color='#8888aa'),
                yaxis=dict(title='世帯手残り（万円）', gridcolor='#2a2a4a', color='#8888aa'),
                legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color='#c8b8e0')),
                margin=dict(l=10, r=10, t=10, b=10),
                height=280
            )
            st.plotly_chart(fig, use_container_width=True)

            # 判定コメント
            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
            if integrated:
                st.markdown(
                    f'<p class="note-text">💡 売上{sales_man}万円では、ちこむんを<strong style="color:#4caf50">役員化する方が有利</strong>です。</p>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<p class="note-text">💡 売上{sales_man}万円では、ちこむんは<strong style="color:#ef5350">個人事業のままの方が有利</strong>です。</p>',
                    unsafe_allow_html=True
                )
            st.markdown(
                '<p class="note-text">⚠️ 本シミュレーターは概算です。均等割・各種控除・消費税等は含みません。税理士への確認を強く推奨します。</p>',
                unsafe_allow_html=True
            )
