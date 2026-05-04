import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ─── ページ設定 ───────────────────────────────────────────
st.set_page_config(
    page_title="役員報酬シミュレーター",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── カスタムCSS ──────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans JP', sans-serif;
}

.main { background-color: #0f0f1a; }

h1 { color: #d4a853 !important; font-size: 1.4rem !important; }
h2 { color: #d4a853 !important; font-size: 1.1rem !important; }
h3 { color: #c8b8e0 !important; font-size: 1rem !important; }

.stNumberInput label, .stSlider label, .stSelectbox label {
    color: #c8b8e0 !important;
}

.result-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border: 1px solid #d4a853;
    border-radius: 12px;
    padding: 20px;
    margin: 8px 0;
}

.result-main {
    background: linear-gradient(135deg, #2a1a0e 0%, #1e1a0e 100%);
    border: 2px solid #d4a853;
    border-radius: 16px;
    padding: 24px;
    text-align: center;
    margin: 12px 0;
}

.big-number {
    font-size: 2.2rem;
    font-weight: 700;
    color: #d4a853;
}

.label-text {
    font-size: 0.85rem;
    color: #8888aa;
    margin-bottom: 4px;
}

.value-text {
    font-size: 1.1rem;
    color: #e8e0f0;
    font-weight: 700;
}

.badge-yes {
    background: #1a3a1a;
    color: #4caf50;
    border: 1px solid #4caf50;
    border-radius: 20px;
    padding: 4px 16px;
    font-size: 0.9rem;
    font-weight: 700;
}

.badge-no {
    background: #3a1a1a;
    color: #ef5350;
    border: 1px solid #ef5350;
    border-radius: 20px;
    padding: 4px 16px;
    font-size: 0.9rem;
    font-weight: 700;
}

.section-divider {
    border-top: 1px solid #333355;
    margin: 16px 0;
}

.note-text {
    font-size: 0.75rem;
    color: #666688;
    line-height: 1.6;
}

.stTabs [data-baseweb="tab-list"] {
    background-color: #1a1a2e;
    border-radius: 8px;
}

.stTabs [data-baseweb="tab"] {
    color: #8888aa !important;
}

.stTabs [aria-selected="true"] {
    color: #d4a853 !important;
    background-color: #2a2a3e !important;
}
</style>
""", unsafe_allow_html=True)


# ─── 計算関数 ─────────────────────────────────────────────
def get_salary_deduction(salary):
    """給与所得控除（6段階）"""
    if salary <= 550000: return salary
    elif salary <= 1610000: return 550000
    elif salary <= 1800000: return salary * 0.4 - 100000
    elif salary <= 3600000: return salary * 0.3 + 80000
    elif salary <= 6600000: return salary * 0.2 + 440000
    elif salary <= 8500000: return salary * 0.1 + 1100000
    else: return 1950000

def get_income_tax(taxable):
    """所得税（累進課税）"""
    if taxable <= 0: return 0
    elif taxable <= 1950000: return taxable * 0.05
    elif taxable <= 3300000: return taxable * 0.10 - 97500
    elif taxable <= 6950000: return taxable * 0.20 - 427500
    elif taxable <= 9000000: return taxable * 0.23 - 636000
    elif taxable <= 18000000: return taxable * 0.33 - 1536000
    elif taxable <= 40000000: return taxable * 0.40 - 2796000
    else: return taxable * 0.45 - 4796000

def calc_net(salary, health_rate, pension_rate, resident_rate, health_max, pension_max):
    """個人の手取り計算"""
    if salary <= 0:
        return 0, 0, 0, 0
    h_ins = min(salary, health_max) * health_rate
    p_ins = min(salary, pension_max) * pension_rate
    si = h_ins + p_ins
    deduction = get_salary_deduction(salary)
    taxable = max(0, salary - deduction - si - 480000)
    i_tax = get_income_tax(taxable)
    r_tax = taxable * resident_rate
    net = salary - si - i_tax - r_tax
    return net, si, i_tax, r_tax

def run_simulation(sales, corp_expenses, pearl_profit, health_rate, pension_rate,
                   resident_rate, health_max, pension_max, step=200000):
    """総当たりシミュレーション"""
    results = []
    limit = sales + pearl_profit - corp_expenses

    for s_a in range(3000000, min(50000001, int(limit) + 1), step):
        for s_c in range(0, 15000001, step):
            if (s_a + s_c) > limit:
                break
            for integrated in [True, False]:
                cur_sales = sales + (pearl_profit if integrated else 0)
                cur_salary = s_a + (s_c if integrated else 0)
                corp_profit = cur_sales - corp_expenses - cur_salary
                if corp_profit < 0:
                    continue

                # 法人税（800万の壁）
                if corp_profit <= 8000000:
                    c_tax = corp_profit * 0.25
                else:
                    c_tax = 2000000 + (corp_profit - 8000000) * 0.34
                c_cash = corp_profit - c_tax

                # あきたん手取り
                net_a, si_a, it_a, rt_a = calc_net(s_a, health_rate, pension_rate,
                                                     resident_rate, health_max, pension_max)

                # ちこむん手取り
                if integrated:
                    net_c, si_c, it_c, rt_c = calc_net(s_c, health_rate, pension_rate,
                                                         resident_rate, health_max, pension_max)
                else:
                    p_income = max(0, pearl_profit - 650000 - 480000)
                    i_tax_c = get_income_tax(p_income)
                    r_tax_c = p_income * resident_rate
                    net_c = pearl_profit - i_tax_c - r_tax_c
                    si_c = 0

                total = net_a + net_c + c_cash
                results.append({
                    'あきたん報酬': s_a,
                    'ちこむん報酬': s_c,
                    '統合': integrated,
                    '世帯手残り': int(total),
                    '法人留保': int(c_cash),
                    'あきたん手取り': int(net_a),
                    'ちこむん手取り': int(net_c),
                })

    if not results:
        return None
    df = pd.DataFrame(results)
    return df


# ─── UI ──────────────────────────────────────────────────
st.markdown("## 💎 役員報酬 最適化シミュレーター")
st.markdown('<p class="note-text">※ 概算シミュレーションです。実際の税務処理は税理士にご確認ください。</p>', unsafe_allow_html=True)

# タブ
tab_main, tab_settings = st.tabs(["📊 シミュレーション", "⚙️ 税率設定"])

with tab_settings:
    st.markdown("### 税率・保険料設定")
    st.markdown('<p class="note-text">市区町村によって異なる数値を変更できます（デフォルトは大垣市・岐阜県2026年想定）</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        health_pct = st.number_input("健康保険料率（介護込・労使折半後%）",
                                      value=5.79, min_value=1.0, max_value=15.0, step=0.01,
                                      key="health_pct",
                                      help="岐阜県: 10.02%÷2 + 介護1.56%÷2 ≒ 5.79%")
        pension_pct = st.number_input("厚生年金料率（労使折半後%）",
                                       value=9.15, min_value=1.0, max_value=15.0, step=0.01,
                                       key="pension_pct",
                                       help="全国一律: 18.3%÷2 = 9.15%")
    with col2:
        resident_pct = st.number_input("住民税率（%）",
                                        value=10.0, min_value=5.0, max_value=15.0, step=0.1,
                                        key="resident_pct",
                                        help="ほとんどの市区町村で10%")
        city_name = st.text_input("市区町村名（表示用）", value="大垣市", key="city_name")
        health_max_man = st.number_input("健康保険上限年収（万円）",
                                          value=1668, min_value=500, max_value=5000, step=12,
                                          key="health_max")
        pension_max_man = st.number_input("厚生年金上限年収（万円）",
                                           value=780, min_value=300, max_value=2000, step=12,
                                           key="pension_max")

    health_rate = health_pct / 100
    pension_rate = pension_pct / 100
    resident_rate = resident_pct / 100
    health_max = health_max_man * 10000
    pension_max = pension_max_man * 10000

with tab_main:
    # ─ 入力エリア（PC:左カラム / スマホ:上） ─
    col_input, col_result = st.columns([1, 1.2], gap="large")

    with col_input:
        st.markdown("### 📥 数字を入れる")

        sales_man = st.number_input(
            "あきたん会社の売上（万円）",
            min_value=500, max_value=100000, value=1800, step=100,
            key="sales"
        )
        corp_exp_man = st.number_input(
            "法人経費・役員報酬除く（万円）",
            min_value=0, max_value=50000, value=300, step=50,
            key="corp_exp",
            help="通信費・地代家賃・外注費など。役員報酬は含めない"
        )
        pearl_man = st.number_input(
            "パール事業の利益（万円）",
            min_value=0, max_value=5000, value=10, step=10,
            key="pearl",
            help="ちこむんの個人事業利益（売上−仕入等）"
        )

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        st.markdown(f'<p class="note-text">税率設定：{st.session_state.get("city_name","大垣市")} ／ 健保{st.session_state.get("health_pct",5.79):.2f}% 厚年{st.session_state.get("pension_pct",9.15):.2f}% 住民税{st.session_state.get("resident_pct",10.0):.1f}%<br>変更は「税率設定」タブから</p>', unsafe_allow_html=True)

    # ─ 計算 ─
    sales = sales_man * 10000
    corp_expenses = corp_exp_man * 10000
    pearl_profit = pearl_man * 10000

    # セッション状態から税率取得（タブ間で保持）
    h_rate = st.session_state.get("health_pct", 5.79) / 100
    p_rate = st.session_state.get("pension_pct", 9.15) / 100
    r_rate = st.session_state.get("resident_pct", 10.0) / 100
    h_max = st.session_state.get("health_max", 1668) * 10000
    p_max = st.session_state.get("pension_max", 780) * 10000

    with st.spinner("計算中... ⚙️"):
        df = run_simulation(sales, corp_expenses, pearl_profit,
                            h_rate, p_rate, r_rate, h_max, p_max)

    with col_result:
        st.markdown("### 📈 最適解")

        if df is None or df.empty:
            st.error("計算できる組み合わせがありません。数字を見直してください。")
        else:
            best = df.loc[df['世帯手残り'].idxmax()]
            integrated = bool(best['統合'])

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

            # 内訳
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"""
                <div class="result-card">
                    <div class="label-text">あきたん役員報酬</div>
                    <div class="value-text">¥{int(best['あきたん報酬']):,}</div>
                    <div class="label-text" style="margin-top:8px">手取り</div>
                    <div class="value-text">¥{int(best['あきたん手取り']):,}</div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div class="result-card">
                    <div class="label-text">ちこむん報酬{'（役員）' if integrated else '（個人事業）'}</div>
                    <div class="value-text">¥{int(best['ちこむん報酬']) if integrated else pearl_profit:,}</div>
                    <div class="label-text" style="margin-top:8px">手取り</div>
                    <div class="value-text">¥{int(best['ちこむん手取り']):,}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="result-card">
                <div class="label-text">法人留保（税引後）</div>
                <div class="value-text">¥{int(best['法人留保']):,}</div>
            </div>
            """, unsafe_allow_html=True)

            # ─ グラフ ─
            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
            st.markdown("### 📊 あきたん報酬 vs 世帯手残り")

            # ベスト統合モードでのグラフ
            df_graph = df[df['統合'] == integrated].copy()
            df_graph_agg = df_graph.groupby('あきたん報酬')['世帯手残り'].max().reset_index()

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_graph_agg['あきたん報酬'] / 10000,
                y=df_graph_agg['世帯手残り'] / 10000,
                mode='lines',
                line=dict(color='#d4a853', width=2),
                fill='tozeroy',
                fillcolor='rgba(212,168,83,0.1)',
                name='世帯手残り（万円）'
            ))
            # 最適点マーカー
            fig.add_trace(go.Scatter(
                x=[best['あきたん報酬'] / 10000],
                y=[best['世帯手残り'] / 10000],
                mode='markers',
                marker=dict(color='#ff6b9d', size=12, symbol='star'),
                name=f'最適解 ¥{int(best["あきたん報酬"])/10000:.0f}万'
            ))
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(15,15,26,0.8)',
                font=dict(color='#c8b8e0', family='Noto Sans JP'),
                xaxis=dict(
                    title='あきたん役員報酬（万円）',
                    gridcolor='#2a2a4a',
                    color='#8888aa'
                ),
                yaxis=dict(
                    title='世帯手残り（万円）',
                    gridcolor='#2a2a4a',
                    color='#8888aa'
                ),
                legend=dict(
                    bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#c8b8e0')
                ),
                margin=dict(l=10, r=10, t=10, b=10),
                height=280
            )
            st.plotly_chart(fig, use_container_width=True)

            # 損益分岐点のヒント
            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
            if integrated:
                st.markdown(f'<p class="note-text">💡 この売上規模（{sales_man}万円）では、ちこむんを<strong style="color:#4caf50">役員化する方が有利</strong>です。</p>', unsafe_allow_html=True)
            else:
                st.markdown(f'<p class="note-text">💡 この売上規模（{sales_man}万円）では、ちこむんは<strong style="color:#ef5350">個人事業のままの方が有利</strong>です。</p>', unsafe_allow_html=True)

            st.markdown('<p class="note-text">※ 本シミュレーターは簡易計算です。税理士への確認を推奨します。</p>', unsafe_allow_html=True)
