import argparse
import html
import logging
import os
import duckdb
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _svg_text(value) -> str:
    """Escape text for safe embedding in SVG/XML."""
    return html.escape(str(value), quote=True)


def get_default_paths():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    gold_dir = os.path.join(base_dir, "data", "gold")
    figures_dir = os.path.join(base_dir, "reports", "figures")
    return gold_dir, figures_dir


def create_carrier_chart(gold_dir: str, figures_dir: str):
    df = pd.read_parquet(os.path.join(gold_dir, "airline_summary.parquet"))
    df = df.sort_values("avg_delay_minutes", ascending=True)

    width = 750
    bar_h = 32
    row_h = 60
    top = 120
    rows = max(len(df), 1)
    footer_y = top + rows * row_h + 24
    height = footer_y + 60
    svg = [
        f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" style="background:#ffffff; font-family:sans-serif; border:1px solid #e2e8f0; border-radius:8px;">',
        f'<text x="40" y="45" font-size="20" font-weight="bold" fill="#1e293b">{_svg_text("Carrier Performance: Average Delay vs On-Time %")}</text>',
        f'<text x="40" y="70" font-size="13" fill="#64748b">{_svg_text("Benchmark of 5.82M scheduled flights across major US carriers")}</text>',
    ]

    # Draw bars
    bar_y = top
    colors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444"]
    for i, row in df.iterrows():
        airline = row["airline"]
        avg_delay = row["avg_delay_minutes"]
        on_time = row["on_time_pct"]
        bar_len = max(int(float(avg_delay) * 28), 0)
        color = colors[i % len(colors)]

        svg.append(f'<text x="40" y="{bar_y + 22}" font-size="14" font-weight="600" fill="#334155">{_svg_text(airline)}</text>')
        # Delay bar
        svg.append(f'<rect x="200" y="{bar_y}" width="{bar_len}" height="{bar_h}" rx="4" fill="{color}" fill-opacity="0.9"/>')
        svg.append(f'<text x="{210 + bar_len}" y="{bar_y + 21}" font-size="13" font-weight="bold" fill="{color}">{_svg_text(f"{avg_delay} min delay")}</text>')
        svg.append(f'<text x="560" y="{bar_y + 21}" font-size="13" fill="#64748b">{_svg_text(f"On-Time: {on_time}%")}</text>')
        bar_y += row_h

    # Legend / footer
    svg.append(f'<line x1="40" y1="{footer_y - 20}" x2="710" y2="{footer_y - 20}" stroke="#e2e8f0" stroke-width="1"/>')
    svg.append(f'<text x="40" y="{footer_y}" font-size="12" fill="#94a3b8">{_svg_text("Source: Kaggle Aviation Delay Lakehouse (Silver/Gold Mart)")}</text>')
    svg.append('</svg>')

    out_file = os.path.join(figures_dir, "carrier_delay_comparison.svg")
    with open(out_file, "w") as f:
        f.write("\n".join(svg))
    logger.info(f"Generated: {out_file}")


def create_routes_chart(gold_dir: str, figures_dir: str):
    df = pd.read_parquet(os.path.join(gold_dir, "route_summary.parquet")).head(8)

    width = 750
    height = 460
    svg = [
        f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" style="background:#ffffff; font-family:sans-serif; border:1px solid #e2e8f0; border-radius:8px;">',
        '<text x="40" y="45" font-size="20" font-weight="bold" fill="#1e293b">Top Corridors by Average Flight Delay</text>',
        '<text x="40" y="70" font-size="13" fill="#64748b">Highest average delay routes across major origin-destination pairs</text>',
    ]

    bar_y = 105
    for i, row in df.iterrows():
        route = row["route"]
        delay = row["avg_delay_minutes"]
        flights = row["total_flights"]
        bar_w = int(delay * 28)

        svg.append(f'<text x="40" y="{bar_y + 19}" font-size="13" font-weight="600" fill="#334155">{route}</text>')
        svg.append(f'<rect x="130" y="{bar_y}" width="{bar_w}" height="26" rx="4" fill="#6366f1" fill-opacity="0.85"/>')
        svg.append(f'<text x="{140 + bar_w}" y="{bar_y + 18}" font-size="12" font-weight="bold" fill="#4338ca">{delay:.2f} m</text>')
        svg.append(f'<text x="480" y="{bar_y + 18}" font-size="12" fill="#64748b">Volume: {flights:,} flights | Dist: {row["avg_distance_miles"]:.0f} mi</text>')
        bar_y += 38

    svg.append('<line x1="40" y1="420" x2="710" y2="420" stroke="#e2e8f0" stroke-width="1"/>')
    svg.append('<text x="40" y="440" font-size="12" fill="#94a3b8">Source: DuckDB Aggregation over Silver Parquet</text>')
    svg.append('</svg>')

    out_file = os.path.join(figures_dir, "worst_delay_routes.svg")
    with open(out_file, "w") as f:
        f.write("\n".join(svg))
    logger.info(f"Generated: {out_file}")


def create_hourly_chart(gold_dir: str, figures_dir: str):
    df = pd.read_parquet(os.path.join(gold_dir, "temporal_trends.parquet"))

    width = 750
    height = 380
    svg = [
        f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" style="background:#ffffff; font-family:sans-serif; border:1px solid #e2e8f0; border-radius:8px;">',
        '<text x="40" y="45" font-size="20" font-weight="bold" fill="#1e293b">Diurnal Delay Profile (Departure Hour 00:00 - 23:00)</text>',
        '<text x="40" y="70" font-size="13" fill="#64748b">Hourly average delay curve showing temporal stability across scheduled operations</text>',
    ]

    # Chart canvas coordinates: x: 80 to 700, y: 110 to 300
    svg.append('<line x1="80" y1="300" x2="700" y2="300" stroke="#cbd5e1" stroke-width="1.5"/>')
    svg.append('<line x1="80" y1="110" x2="80" y2="300" stroke="#cbd5e1" stroke-width="1.5"/>')

    # Y-axis ticks for delay (0 to 15 min)
    for d in [0, 5, 10, 15]:
        y_pos = int(300 - (d / 15.0) * 180)
        svg.append(f'<line x1="75" y1="{y_pos}" x2="700" y2="{y_pos}" stroke="#f1f5f9" stroke-width="1"/>')
        svg.append(f'<text x="50" y="{y_pos + 4}" font-size="11" fill="#94a3b8">{d}m</text>')

    points = []
    for i, row in df.iterrows():
        hour = int(row["departure_hour"])
        delay = float(row["avg_delay_minutes"])
        x = 80 + int((hour / 23.0) * 600)
        y = int(300 - (delay / 15.0) * 180)
        points.append((x, y, hour, delay))

    # Draw polyline
    polyline_str = " ".join([f"{p[0]},{p[1]}" for p in points])
    svg.append(f'<polyline fill="none" stroke="#0ea5e9" stroke-width="3" stroke-linecap="round" points="{polyline_str}"/>')

    # Draw dots and hour labels
    for p in points:
        x, y, h, d = p
        svg.append(f'<circle cx="{x}" cy="{y}" r="4" fill="#0284c7"/>')
        if h % 3 == 0:
            svg.append(f'<text x="{x - 6}" y="320" font-size="11" fill="#64748b">{h:02d}h</text>')

    svg.append('<text x="340" y="348" font-size="12" font-weight="600" fill="#475569">Scheduled Departure Hour (UTC)</text>')
    svg.append('</svg>')

    out_file = os.path.join(figures_dir, "hourly_delay_trend.svg")
    with open(out_file, "w") as f:
        f.write("\n".join(svg))
    logger.info(f"Generated: {out_file}")


def create_delay_factors_chart(gold_dir: str, figures_dir: str):
    df = pd.read_parquet(os.path.join(gold_dir, "delay_factor_summary.parquet"))

    width = 750
    row_h = 42
    top = 110
    rows = max(len(df), 1)
    footer_y = top + rows * row_h + 24
    height = footer_y + 60
    svg = [
        f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" style="background:#ffffff; font-family:sans-serif; border:1px solid #e2e8f0; border-radius:8px;">',
        f'<text x="40" y="45" font-size="20" font-weight="bold" fill="#1e293b">{_svg_text("Largest Delay Factor & Operational Outcome Breakdown")}</text>',
        f'<text x="40" y="70" font-size="13" fill="#64748b">{_svg_text("Distribution of flight causes across 5.8M aviation records")}</text>',
    ]

    bar_y = 110
    colors = {
        "Flight Cancelled": "#ef4444",
        "Flight Diverted": "#f97316",
        "None (On-Time / Early)": "#10b981",
        "Air System / NAS Delay": "#3b82f6",
        "Security Delay": "#8b5cf6",
        "Airline / Carrier Delay": "#a855f7",
        "Late Aircraft Delay": "#d946ef",
        "Weather Delay": "#06b6d4",
        "Unspecified / Not Reported": "#94a3b8",
    }

    for i, row in df.iterrows():
        factor = row["largest_delay_factor"]
        count = row["flight_count"]
        pct = row["pct_of_total"]
        color = colors.get(factor, "#64748b")
        bar_w = max(int((float(pct) / 55.0) * 350), 1)

        svg.append(f'<text x="40" y="{bar_y + 19}" font-size="13" font-weight="600" fill="#334155">{_svg_text(factor)}</text>')
        svg.append(f'<rect x="280" y="{bar_y}" width="{bar_w}" height="26" rx="4" fill="{color}" fill-opacity="0.9"/>')
        svg.append(f'<text x="{290 + bar_w}" y="{bar_y + 18}" font-size="12" font-weight="bold" fill="{color}">{_svg_text(f"{pct:.1f}%")}</text>')
        svg.append(f'<text x="590" y="{bar_y + 18}" font-size="12" fill="#64748b">{_svg_text(f"{int(count):,} flights")}</text>')
        bar_y += row_h

    svg.append(f'<line x1="40" y1="{footer_y - 20}" x2="710" y2="{footer_y - 20}" stroke="#e2e8f0" stroke-width="1"/>')
    svg.append(f'<text x="40" y="{footer_y}" font-size="12" fill="#94a3b8">{_svg_text("Source: Derived largest_delay_factor feature (Silver/Gold Parquet)")}</text>')
    svg.append('</svg>')

    out_file = os.path.join(figures_dir, "delay_factor_distribution.svg")
    with open(out_file, "w") as f:
        f.write("\n".join(svg))
    logger.info(f"Generated: {out_file}")


def create_airport_bottlenecks_chart(gold_dir: str, figures_dir: str):
    df = pd.read_parquet(os.path.join(gold_dir, "airport_bottlenecks.parquet"))
    df = df.sort_values("total_operations", ascending=False).head(15)

    width = 750
    row_h = 32
    top = 110
    rows = max(len(df), 1)
    footer_y = top + rows * row_h + 30
    height = footer_y + 50
    svg = [
        f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" style="background:#ffffff; font-family:sans-serif; border:1px solid #e2e8f0; border-radius:8px;">',
        f'<text x="40" y="45" font-size="20" font-weight="bold" fill="#1e293b">{_svg_text("Airport Hub Delay & Congestion Analysis")}</text>',
        f'<text x="40" y="70" font-size="13" fill="#64748b">{_svg_text("Origin vs Destination arrival delay performance across major airport hubs")}</text>',
    ]

    bar_y = 110
    for i, row in df.iterrows():
        code = row["airport_code"]
        ops = row["total_operations"]
        dep_delay = row["avg_origin_delay"]
        arr_delay = row["avg_destination_delay"]

        svg.append(f'<text x="40" y="{bar_y + 18}" font-size="13" font-weight="bold" fill="#1e293b">{_svg_text(code)}</text>')
        svg.append(f'<text x="90" y="{bar_y + 18}" font-size="12" fill="#64748b">{_svg_text(f"{int(ops):,} ops")}</text>')

        # Dep delay bar (blue)
        dep_w = max(int(float(dep_delay) * 18), 0)
        svg.append(f'<rect x="230" y="{bar_y}" width="{dep_w}" height="14" rx="3" fill="#3b82f6"/>')
        svg.append(f'<text x="{240 + dep_w}" y="{bar_y + 11}" font-size="10" fill="#1d4ed8">{_svg_text(f"Origin: {dep_delay}m")}</text>')

        # Arr delay bar (orange)
        arr_w = max(int(float(arr_delay) * 18), 0)
        svg.append(f'<rect x="440" y="{bar_y}" width="{arr_w}" height="14" rx="3" fill="#f97316"/>')
        svg.append(f'<text x="{450 + arr_w}" y="{bar_y + 11}" font-size="10" fill="#c2410c">{_svg_text(f"Dest: {arr_delay}m")}</text>')

        bar_y += row_h

    svg.append(f'<line x1="40" y1="{footer_y - 20}" x2="710" y2="{footer_y - 20}" stroke="#e2e8f0" stroke-width="1"/>')
    svg.append(f'<text x="40" y="{footer_y}" font-size="12" fill="#94a3b8">{_svg_text("Source: DuckDB Airport Bottlenecks Mart (data/gold/airport_bottlenecks.parquet)")}</text>')
    svg.append('</svg>')

    out_file = os.path.join(figures_dir, "airport_bottlenecks.svg")
    with open(out_file, "w") as f:
        f.write("\n".join(svg))
    logger.info(f"Generated: {out_file}")


def generate_all_visualizations(gold_dir=None, figures_dir=None):
    default_gold, default_figures = get_default_paths()
    gold_dir = gold_dir or default_gold
    figures_dir = figures_dir or default_figures

    logger.info("=" * 50)
    logger.info("STEP 5: VISUALIZATION GENERATION")
    logger.info("=" * 50)
    logger.info(f"Reading Gold marts from: {gold_dir}")
    logger.info(f"Writing figures to: {figures_dir}")
    os.makedirs(figures_dir, exist_ok=True)

    create_carrier_chart(gold_dir, figures_dir)
    create_routes_chart(gold_dir, figures_dir)
    create_hourly_chart(gold_dir, figures_dir)
    create_delay_factors_chart(gold_dir, figures_dir)
    create_airport_bottlenecks_chart(gold_dir, figures_dir)

    logger.info("All visualizations successfully created in SVG format.")
    logger.info("-" * 50 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Visualizations from Gold Parquet")
    parser.add_argument("--gold", default=None, help="Directory containing Gold Parquet marts")
    parser.add_argument("--figures", default=None, help="Directory to save figures")
    args = parser.parse_args()
    generate_all_visualizations(args.gold, args.figures)
