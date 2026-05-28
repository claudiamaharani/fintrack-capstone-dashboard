import pandas as pd
import plotly.express as px
import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="FinTrack Dashboard",
    page_icon="📊",
    layout="wide",
)

DATA_FILES = {
    "Business Transactions": "fintrack_business_clean_dataset.csv",
    "Personal Transactions": "fintrack_personal_clean_dataset.csv",
}

@st.cache_data
def load_data(filename: str) -> pd.DataFrame:
    path = Path(__file__).parent / filename
    df = pd.read_csv(path, parse_dates=["transaction_date"])
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    df = df.sort_values("transaction_date")
    df["year_month"] = df["transaction_date"].dt.to_period("M").astype(str)
    return df


def filter_data(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filter Transaksi")

    min_date = df["transaction_date"].min()
    max_date = df["transaction_date"].max()
    date_range = st.sidebar.date_input(
        "Rentang tanggal",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    transaction_types = df["transaction_type"].unique().tolist()
    selected_types = st.sidebar.multiselect(
        "Tipe transaksi",
        options=transaction_types,
        default=transaction_types,
    )

    categories = df["category"].unique().tolist()
    selected_categories = st.sidebar.multiselect(
        "Kategori",
        options=categories,
        default=categories,
    )

    payment_methods = df["payment_method"].unique().tolist()
    selected_payments = st.sidebar.multiselect(
        "Metode pembayaran",
        options=payment_methods,
        default=payment_methods,
    )

    min_amount = float(df["amount"].min())
    max_amount = float(df["amount"].max())
    amount_range = st.sidebar.slider(
        "Rentang jumlah (Rp)",
        min_value=min_amount,
        max_value=max_amount,
        value=(min_amount, max_amount),
        step=max(1.0, (max_amount - min_amount) / 100),
    )

    start_date, end_date = date_range
    mask = (
        (df["transaction_date"] >= pd.to_datetime(start_date))
        & (df["transaction_date"] <= pd.to_datetime(end_date))
        & df["transaction_type"].isin(selected_types)
        & df["category"].isin(selected_categories)
        & df["payment_method"].isin(selected_payments)
        & df["amount"].between(amount_range[0], amount_range[1])
    )

    return df.loc[mask].copy()


def format_currency(value: float) -> str:
    return f"Rp {value:,.0f}".replace(",", ".")


def analyze_personal_ratio(df: pd.DataFrame) -> pd.DataFrame:
    """Analisis rasio pengeluaran pribadi vs pemasukan per bulan."""
    df_copy = df.copy()
    df_copy["month"] = df_copy["transaction_date"].dt.to_period("M")
    
    monthly = df_copy.pivot_table(
        index="month",
        columns="transaction_type",
        values="amount",
        aggfunc="sum",
        fill_value=0,
    ).reset_index()
    
    monthly["rasio_pengeluaran (%)"] = (monthly.get("Pengeluaran", 0) / monthly.get("Pemasukan", 1)) * 100
    monthly["month"] = monthly["month"].astype(str)
    return monthly


def analyze_business_cashflow(df: pd.DataFrame) -> tuple:
    """Analisis arus kas bisnis dan top kategori pengeluaran."""
    df_copy = df.copy()
    df_copy["month"] = df_copy["transaction_date"].dt.to_period("M")
    
    monthly = df_copy.pivot_table(
        index="month",
        columns="transaction_type",
        values="amount",
        aggfunc="sum",
        fill_value=0,
    ).reset_index()
    monthly["month"] = monthly["month"].astype(str)
    
    # Top 3 kategori pengeluaran
    pengeluaran = df_copy[df_copy["transaction_type"] == "Pengeluaran"]
    top_3 = pengeluaran.groupby(["month", "category"])["amount"].sum().reset_index()
    top_3 = top_3.sort_values(["month", "amount"], ascending=[True, False])
    top_3_monthly = top_3.groupby("month").head(3)
    top_3_monthly["month"] = top_3_monthly["month"].astype(str)
    
    return monthly, top_3_monthly


def main() -> None:
    st.title("FinTrack Smart Financial Dashboard")
    st.markdown(
        "Lihat kondisi keuangan Anda lebih mudah melalui visualisasi transaksi dan cashflow secara real-time."
    )

    st.markdown(
        """
        <style>
        /* Sidebar: soft light-gray with subtle blue-green accent */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #f7f8fa 0%, #eef3f8 100%);
            border-right: 1px solid rgba(30,58,138,0.06);
        }
        section[data-testid="stSidebar"] .css-1d391kg,
        section[data-testid="stSidebar"] .css-1v0mbdj,
        section[data-testid="stSidebar"] label {
            color: #0f172a !important;
        }
        section[data-testid="stSidebar"] .stButton>button {
            background-color: #2b6cb0;
            color: white;
        }
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 20px;
            margin-bottom: 24px;
        }
        .kpi-card {
            background: #f8fafc;
            border-radius: 18px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(2,6,23,0.06);
            border: 1px solid rgba(15, 23, 42, 0.04);
            color: #0f172a;
        }
        .kpi-card .icon {
            width: 46px;
            height: 46px;
            border-radius: 12px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 12px;
            font-size: 20px;
        }
        .kpi-card .title {
            font-size: 13px;
            font-weight: 500;
            color: #64748b;
            margin: 0 0 8px;
            letter-spacing: 0.3px;
        }
        .kpi-card .value {
            font-size: 22px;
            font-weight: 700;
            margin: 0;
            line-height: 1.2;
            color: #1e293b;
        }
        .kpi-card .value .currency {
            font-size: 22px;
            font-weight: 700;
            color: #1e293b;
            display: inline;
            margin: 0;
        }
        /* Blue, green and light gray variants */
        .kpi-card.blue { background: linear-gradient(180deg, #eef6ff 0%, #e0efff 100%); }
        .kpi-card.blue .icon { background: #1f4e79; color: white; }
        .kpi-card.green { background: linear-gradient(180deg, #eef9f3 0%, #e0f2e8 100%); }
        .kpi-card.green .icon { background: #2e7d32; color: white; }
        .kpi-card.soft { background: linear-gradient(180deg, #fbfbfb 0%, #f2f4f7 100%); }
        .kpi-card.soft .icon { background: #475569; color: white; }
        .kpi-card.red { background: linear-gradient(180deg, #fff6f6 0%, #ffecec 100%); }
        .kpi-card.red .icon { background: #b71c1c; color: white; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    dataset_name = st.sidebar.selectbox(
        "Pilih tipe user",
        list(DATA_FILES.keys()),
    )

    df = load_data(DATA_FILES[dataset_name])
    filtered = filter_data(df)

    st.subheader("Ringkasan Data")
    total_transactions = len(filtered)
    total_amount = filtered["amount"].sum()
    average_value = filtered["amount"].mean() if len(filtered) else 0.0
    last_date = (
        filtered["transaction_date"].max().strftime("%Y-%m-%d")
        if len(filtered)
        else "-"
    )
    income = filtered.loc[filtered["transaction_type"] == "Pemasukan", "amount"].sum()
    expense = filtered.loc[filtered["transaction_type"] == "Pengeluaran", "amount"].sum()

    st.markdown(
        f"""
        <div class="kpi-grid">
            <div class="kpi-card blue">
                <div class="icon">📊</div>
                <p class="title">Total Transaksi</p>
                <p class="value">{total_transactions:,}</p>
            </div>
            <div class="kpi-card green">
                <div class="icon">💰</div>
                <p class="title">Total Nominal</p>
                <p class="value"><span class="currency">{format_currency(total_amount)}</span></p>
            </div>
            <div class="kpi-card red">
                <div class="icon">📉</div>
                <p class="title">Total Pengeluaran</p>
                <p class="value"><span class="currency">{format_currency(expense)}</span></p>
            </div>
        </div>
        <div class="kpi-grid" style="grid-template-columns: repeat(2, minmax(0, 1fr));">
            <div class="kpi-card green">
                <div class="icon">📈</div>
                <p class="title">Total Pemasukan</p>
                <p class="value"><span class="currency">{format_currency(income)}</span></p>
            </div>
            <div class="kpi-card soft">
                <div class="icon">📊</div>
                <p class="title">Rata-rata Nominal</p>
                <p class="value"><span class="currency">{format_currency(average_value)}</span></p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.subheader("Visualisasi Transaksi")

    trend = (
        filtered.groupby("year_month")["amount"]
        .sum()
        .reset_index()
        .sort_values("year_month")
    )
    category_counts = filtered["category"].value_counts()
    payment_counts = filtered["payment_method"].value_counts()
    type_counts = filtered["transaction_type"].value_counts()

    chart_col1, chart_col2 = st.columns((2, 1))
    with chart_col1:
        st.markdown("### Tren Nominal per Bulan")
        trend_fig = px.area(
            trend,
            x="year_month",
            y="amount",
            labels={"year_month": "Bulan", "amount": "Total (Rp)"},
            template="plotly_white",
            color_discrete_sequence=["#1f5f9e"],
        )
        trend_fig.update_traces(
            fill="tozeroy",
            fillcolor="rgba(31, 95, 158, 0.3)",
            line=dict(color="#1f5f9e", width=3),
            marker=dict(size=8, color="#1f5f9e", line=dict(color="white", width=2)),
            hovertemplate="<b>%{x}</b><br>Total: <b>Rp %{y:,.0f}</b><extra></extra>",
        )
        trend_fig.update_layout(
            autosize=True,
            margin=dict(t=15, b=20, l=30, r=5),
            height=350,
            xaxis=dict(automargin=True, showgrid=True, gridwidth=1, gridcolor="rgba(200,200,200,0.2)"),
            yaxis=dict(automargin=True, showgrid=True, gridwidth=1, gridcolor="rgba(200,200,200,0.2)"),
            hovermode="x unified",
            plot_bgcolor="rgba(248,250,252,0.5)",
        )
        st.plotly_chart(trend_fig, use_container_width=True)

    with chart_col2:
        st.markdown("### Distribusi Tipe Transaksi")
        type_data = type_counts.reset_index(name="Jumlah").rename(columns={"transaction_type": "Tipe Transaksi"})
        type_fig = px.bar(
            type_data,
            x="Tipe Transaksi",
            y="Jumlah",
            color="Tipe Transaksi",
            color_discrete_sequence=["#2b8cc4", "#4fb07f", "#1f5f9e", "#85c99b"],
            template="plotly_white",
            text="Jumlah",
        )
        type_fig.update_traces(
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Jumlah: <b>%{y} transaksi</b><extra></extra>",
            marker=dict(line=dict(color="white", width=2)),
        )
        type_fig.update_layout(
            showlegend=False,
            autosize=True,
            margin=dict(t=15, b=20, l=30, r=5),
            height=350,
            xaxis=dict(automargin=True, showgrid=False),
            yaxis=dict(automargin=True, showgrid=True, gridwidth=1, gridcolor="rgba(200,200,200,0.2)"),
            hovermode="closest",
            plot_bgcolor="rgba(248,250,252,0.5)",
        )
        st.plotly_chart(type_fig, use_container_width=True)

    cat_pay_col1, cat_pay_col2 = st.columns((1, 1))
    
    with cat_pay_col1:
        st.markdown("### Kategori Transaksi")
        category_fig = px.bar(
            category_counts.reset_index(name="Jumlah").rename(columns={"category": "Kategori"}),
            x="Jumlah",
            y="Kategori",
            orientation="h",
            color="Kategori",
            color_discrete_sequence=["#4fb07f", "#7fd6b6", "#2b8cc4", "#1f5f9e", "#9fcfc0"],
            template="plotly_white",
        )
        category_fig.update_layout(
            showlegend=False,
            autosize=True,
            margin=dict(t=15, b=20, l=100, r=5),
            height=350,
            xaxis=dict(automargin=True),
            yaxis=dict(automargin=True),
        )
        st.plotly_chart(category_fig, use_container_width=True)

    with cat_pay_col2:
        st.markdown("### Metode Pembayaran")
        payment_fig = px.pie(
            payment_counts.reset_index(name="Jumlah").rename(columns={"payment_method": "Metode"}),
            names="Metode",
            values="Jumlah",
            color_discrete_sequence=["#2b8cc4", "#1f5f9e", "#4fb07f", "#9fcfc0"],
            hole=0.4,
            template="plotly_white",
        )
        payment_fig.update_layout(
            autosize=True,
            margin=dict(t=15, b=15, l=5, r=5),
            height=320,
        )
        st.plotly_chart(payment_fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Analisis Pertanyaan Bisnis")
    
    analysis_tab1, analysis_tab2 = st.tabs([
        "❓ Rasio Pengeluaran Pribadi",
        "💼 Arus Kas Bisnis"
    ])
    
    with analysis_tab1:
        if dataset_name == "Personal Transactions":
            st.markdown("#### Apakah pengguna mampu menjaga pengeluaran pribadi tetap di bawah 80% dari total pemasukan setiap bulan?")
            monthly_personal = analyze_personal_ratio(filtered)
            
            ratio_fig = px.line(
                monthly_personal,
                x="month",
                y="rasio_pengeluaran (%)",
                markers=True,
                title="Rasio Pengeluaran Pribadi per Bulan vs. Batas 80%",
                labels={"month": "Bulan", "rasio_pengeluaran (%)": "Rasio (%)"},
                color_discrete_sequence=["#1f5f9e"],
            )
            ratio_fig.add_hline(
                y=80,
                line_dash="dash",
                line_color="#b71c1c",
                annotation_text="80% Threshold",
            )
            ratio_fig.update_layout(
                template="plotly_white",
                hovermode="x unified",
                autosize=True,
                margin=dict(t=20, b=30, l=40, r=10),
                height=380,
                xaxis=dict(automargin=True),
                yaxis=dict(automargin=True),
            )
            st.plotly_chart(ratio_fig, use_container_width=True)
            
            avg_ratio = monthly_personal["rasio_pengeluaran (%)"].mean()
            st.info(
                f"📊 **Rata-rata Rasio Pengeluaran:** {avg_ratio:.1f}%  \n"
                f"✅ **Status:** {'Terjaga' if avg_ratio < 80 else 'Perlu Perhatian'} "
                f"(Seharusnya di bawah 80%)"
            )
        else:
            st.warning("⚠️ Analisis ini hanya tersedia untuk data Personal Transactions")
    
    with analysis_tab2:
        if dataset_name == "Business Transactions":
            st.markdown("#### Kondisi Arus Kas Bisnis & Top Kategori Pengeluaran")
            monthly_business, top_3_business = analyze_business_cashflow(filtered)
            
            # Arus kas
            cashflow_fig = px.line(
                monthly_business,
                x="month",
                y=["Pemasukan", "Pengeluaran"],
                markers=True,
                title="Arus Kas Bisnis: Pemasukan vs. Pengeluaran per Bulan",
                labels={"month": "Bulan", "value": "Jumlah (Rp)"},
                color_discrete_sequence=["#2e7d32", "#b71c1c"],
            )
            cashflow_fig.update_layout(
                template="plotly_white",
                hovermode="x unified",
                autosize=True,
                margin=dict(t=20, b=30, l=40, r=10),
                height=380,
                xaxis=dict(automargin=True),
                yaxis=dict(automargin=True),
            )
            st.plotly_chart(cashflow_fig, use_container_width=True)
            
            # Top kategori pengeluaran
            top_3_pivot = top_3_business.pivot_table(
                index="month",
                columns="category",
                values="amount",
                fill_value=0,
            )
            
            top_cat_fig = px.bar(
                top_3_business,
                x="month",
                y="amount",
                color="category",
                title="Top 3 Kategori Pengeluaran Bisnis Terbesar per Bulan",
                labels={"month": "Bulan", "amount": "Nominal (Rp)", "category": "Kategori"},
                barmode="stack",
                color_discrete_sequence=["#4fb07f", "#2b8cc4", "#1f5f9e", "#7fd6b6", "#9fcfc0"],
            )
            top_cat_fig.update_layout(
                template="plotly_white",
                autosize=True,
                margin=dict(t=20, b=30, l=40, r=10),
                height=380,
                xaxis=dict(automargin=True),
                yaxis=dict(automargin=True),
            )
            st.plotly_chart(top_cat_fig, use_container_width=True)
            
            avg_ratio_bisnis = (monthly_business.get("Pengeluaran", 0).sum() / monthly_business.get("Pemasukan", 1).sum()) * 100
            st.info(
                f"💼 **Rata-rata Rasio Pengeluaran Bisnis:** {avg_ratio_bisnis:.1f}%  \n"
                f"✅ **Status:** {'Sehat' if avg_ratio_bisnis < 50 else 'Stabil' if avg_ratio_bisnis < 70 else 'Perlu Perhatian'}"
            )
        else:
            st.warning("⚠️ Analisis ini hanya tersedia untuk data Business Transactions")
    
    st.markdown("---")
    st.subheader("Data Transaksi")
    st.dataframe(filtered.reset_index(drop=True))

    csv_data = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Unduh data terfilter sebagai CSV",
        data=csv_data,
        file_name="filtered_transactions.csv",
        mime="text/csv",
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("Dashboard dibuat menggunakan Streamlit. Filter pada sidebar untuk menjelajah data transaksi.")


if __name__ == "__main__":
    main()
