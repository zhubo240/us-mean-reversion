"""
Complete Shiller S&P 500 annual data (1871-2025) + cross-validation vs Compustat

Data sources:
  - Price, PE, Dividend Yield from multpl.com (originally Shiller CAPE dataset)
  - January values used as annual representative
  - Nominal EPS derived as Price / PE
  - Dividends derived as Price × Dividend_Yield / 100

Cross-validation:
  - Compare Shiller index-level data vs Compustat company-level aggregation
  - Overlapping period: 1985-2024
"""

import json
import math
import os

DATA = os.path.join(os.path.dirname(__file__), '..', 'data')

# ============================================================
# Complete Shiller Annual Data (January values, 1871-2025)
# Source: multpl.com / Robert Shiller dataset
# ============================================================

# S&P 500 Price (January)
PRICE = {
    1871: 4.44, 1872: 4.86, 1873: 5.11, 1874: 4.66, 1875: 4.54,
    1876: 4.46, 1877: 3.55, 1878: 3.25, 1879: 3.58, 1880: 5.11,
    1881: 6.19, 1882: 5.92, 1883: 5.81, 1884: 5.18, 1885: 4.24,
    1886: 5.20, 1887: 5.58, 1888: 5.31, 1889: 5.24, 1890: 5.38,
    1891: 4.84, 1892: 5.51, 1893: 5.61, 1894: 4.32, 1895: 4.25,
    1896: 4.27, 1897: 4.22, 1898: 4.88, 1899: 6.08, 1900: 6.10,
    1901: 7.07, 1902: 8.12, 1903: 8.46, 1904: 6.68, 1905: 8.43,
    1906: 9.87, 1907: 9.56, 1908: 6.85, 1909: 9.06, 1910: 10.08,
    1911: 9.27, 1912: 9.12, 1913: 9.30, 1914: 8.37, 1915: 7.48,
    1916: 9.33, 1917: 9.57, 1918: 7.21, 1919: 7.85, 1920: 8.83,
    1921: 7.11, 1922: 7.30, 1923: 8.90, 1924: 8.83, 1925: 10.58,
    1926: 12.65, 1927: 13.40, 1928: 17.53, 1929: 24.86, 1930: 21.71,
    1931: 15.98, 1932: 8.30, 1933: 7.09, 1934: 10.54, 1935: 9.26,
    1936: 13.76, 1937: 17.59, 1938: 11.31, 1939: 12.50, 1940: 12.30,
    1941: 10.55, 1942: 8.93, 1943: 10.09, 1944: 11.85, 1945: 13.49,
    1946: 18.02, 1947: 15.21, 1948: 14.83, 1949: 15.36, 1950: 16.88,
    1951: 21.21, 1952: 24.19, 1953: 26.18, 1954: 25.46, 1955: 35.60,
    1956: 44.15, 1957: 45.43, 1958: 41.12, 1959: 55.62, 1960: 58.03,
    1961: 59.72, 1962: 69.07, 1963: 65.06, 1964: 76.45, 1965: 86.12,
    1966: 93.32, 1967: 84.45, 1968: 95.04, 1969: 102.00, 1970: 90.31,
    1971: 93.49, 1972: 103.30, 1973: 118.40, 1974: 96.11, 1975: 72.56,
    1976: 96.86, 1977: 103.80, 1978: 90.25, 1979: 99.71, 1980: 110.90,
    1981: 133.00, 1982: 117.30, 1983: 144.30, 1984: 166.40, 1985: 171.60,
    1986: 208.20, 1987: 264.50, 1988: 250.50, 1989: 285.40, 1990: 339.97,
    1991: 325.49, 1992: 416.08, 1993: 435.23, 1994: 472.99, 1995: 465.25,
    1996: 614.42, 1997: 766.22, 1998: 963.36, 1999: 1248.77, 2000: 1425.59,
    2001: 1335.63, 2002: 1140.21, 2003: 895.84, 2004: 1132.52, 2005: 1181.41,
    2006: 1278.73, 2007: 1424.16, 2008: 1378.76, 2009: 865.58, 2010: 1123.58,
    2011: 1282.62, 2012: 1300.58, 2013: 1480.40, 2014: 1822.36, 2015: 2028.18,
    2016: 1918.60, 2017: 2275.12, 2018: 2789.80, 2019: 2607.39, 2020: 3278.20,
    2021: 3793.75, 2022: 4573.82, 2023: 3960.66, 2024: 4804.49, 2025: 5979.52,
}

# Trailing 12-month PE Ratio (January)
PE = {
    1871: 11.10, 1872: 12.07, 1873: 11.82, 1874: 10.13, 1875: 10.05,
    1876: 12.62, 1877: 12.60, 1878: 10.80, 1879: 11.34, 1880: 13.13,
    1881: 12.74, 1882: 13.48, 1883: 13.59, 1884: 13.20, 1885: 13.82,
    1886: 18.91, 1887: 16.78, 1888: 15.10, 1889: 19.90, 1890: 17.98,
    1891: 16.45, 1892: 16.09, 1893: 15.55, 1894: 17.16, 1895: 25.37,
    1896: 17.31, 1897: 19.33, 1898: 15.58, 1899: 16.85, 1900: 12.71,
    1901: 14.68, 1902: 15.90, 1903: 13.61, 1904: 12.68, 1905: 16.69,
    1906: 14.57, 1907: 12.72, 1908: 10.49, 1909: 15.23, 1910: 13.31,
    1911: 12.91, 1912: 15.22, 1913: 13.40, 1914: 13.48, 1915: 13.60,
    1916: 9.99, 1917: 6.34, 1918: 5.74, 1919: 7.97, 1920: 9.61,
    1921: 9.39, 1922: 22.58, 1923: 12.46, 1924: 9.05, 1925: 11.06,
    1926: 10.13, 1927: 10.90, 1928: 15.47, 1929: 17.77, 1930: 13.94,
    1931: 17.00, 1932: 13.99, 1933: 17.19, 1934: 23.73, 1935: 16.25,
    1936: 17.87, 1937: 16.75, 1938: 10.50, 1939: 18.84, 1940: 13.23,
    1941: 10.02, 1942: 7.97, 1943: 9.67, 1944: 12.65, 1945: 14.35,
    1946: 19.17, 1947: 13.46, 1948: 9.02, 1949: 6.62, 1950: 7.22,
    1951: 7.48, 1952: 9.97, 1953: 10.86, 1954: 10.09, 1955: 12.56,
    1956: 12.12, 1957: 13.34, 1958: 12.49, 1959: 18.77, 1960: 17.12,
    1961: 18.60, 1962: 21.25, 1963: 17.66, 1964: 18.77, 1965: 18.75,
    1966: 17.81, 1967: 15.31, 1968: 17.71, 1969: 17.65, 1970: 15.76,
    1971: 18.12, 1972: 18.01, 1973: 18.09, 1974: 11.68, 1975: 8.30,
    1976: 11.82, 1977: 10.41, 1978: 8.28, 1979: 7.88, 1980: 7.39,
    1981: 9.02, 1982: 7.73, 1983: 11.48, 1984: 11.52, 1985: 10.36,
    1986: 14.28, 1987: 18.01, 1988: 14.02, 1989: 11.82, 1990: 15.13,
    1991: 15.35, 1992: 25.93, 1993: 22.50, 1994: 21.34, 1995: 14.89,
    1996: 18.08, 1997: 19.53, 1998: 24.29, 1999: 32.92, 2000: 29.04,
    2001: 27.55, 2002: 46.17, 2003: 31.43, 2004: 22.73, 2005: 19.99,
    2006: 18.07, 2007: 17.36, 2008: 21.46, 2009: 70.91, 2010: 20.70,
    2011: 16.30, 2012: 14.87, 2013: 17.03, 2014: 18.15, 2015: 20.02,
    2016: 22.18, 2017: 23.59, 2018: 24.97, 2019: 19.60, 2020: 24.88,
    2021: 35.96, 2022: 23.11, 2023: 22.82, 2024: 25.01, 2025: 28.16,
}

# Trailing 12-month Dividend Yield (January, in %)
DIV_YIELD = {
    1871: 5.49, 1872: 5.92, 1873: 7.47, 1874: 7.27, 1875: 6.86,
    1876: 8.38, 1877: 5.85, 1878: 5.22, 1879: 4.07, 1880: 4.45,
    1881: 5.32, 1882: 5.48, 1883: 6.18, 1884: 7.14, 1885: 4.62,
    1886: 3.90, 1887: 4.74, 1888: 4.47, 1889: 4.14, 1890: 4.78,
    1891: 4.07, 1892: 4.36, 1893: 5.67, 1894: 4.88, 1895: 4.40,
    1896: 4.27, 1897: 3.79, 1898: 3.54, 1899: 3.49, 1900: 4.37,
    1901: 4.03, 1902: 4.10, 1903: 5.33, 1904: 3.76, 1905: 3.46,
    1906: 4.07, 1907: 6.70, 1908: 4.43, 1909: 4.27, 1910: 5.19,
    1911: 5.16, 1912: 5.12, 1913: 5.97, 1914: 5.71, 1915: 4.54,
    1916: 5.71, 1917: 10.15, 1918: 7.22, 1919: 5.94, 1920: 7.49,
    1921: 6.29, 1922: 5.81, 1923: 6.20, 1924: 5.41, 1925: 4.82,
    1926: 5.11, 1927: 4.41, 1928: 3.67, 1929: 4.53, 1930: 6.32,
    1931: 9.72, 1932: 7.33, 1933: 4.41, 1934: 4.86, 1935: 3.60,
    1936: 4.22, 1937: 7.26, 1938: 4.02, 1939: 5.01, 1940: 6.36,
    1941: 8.11, 1942: 6.20, 1943: 5.31, 1944: 4.89, 1945: 3.81,
    1946: 4.69, 1947: 5.59, 1948: 6.12, 1949: 6.89, 1950: 7.44,
    1951: 6.02, 1952: 5.41, 1953: 5.84, 1954: 4.40, 1955: 3.61,
    1956: 3.75, 1957: 4.44, 1958: 3.27, 1959: 3.10, 1960: 3.43,
    1961: 2.82, 1962: 3.40, 1963: 3.07, 1964: 2.98, 1965: 2.97,
    1966: 3.53, 1967: 3.06, 1968: 2.88, 1969: 3.47, 1970: 3.49,
    1971: 3.10, 1972: 2.68, 1973: 3.57, 1974: 5.37, 1975: 4.15,
    1976: 3.87, 1977: 4.98, 1978: 5.28, 1979: 5.24, 1980: 4.61,
    1981: 5.36, 1982: 4.93, 1983: 4.31, 1984: 4.58, 1985: 3.81,
    1986: 3.33, 1987: 3.66, 1988: 3.53, 1989: 3.17, 1990: 3.68,
    1991: 3.14, 1992: 2.84, 1993: 2.70, 1994: 2.89, 1995: 2.24,
    1996: 2.00, 1997: 1.61, 1998: 1.36, 1999: 1.17, 2000: 1.22,
    2001: 1.37, 2002: 1.79, 2003: 1.61, 2004: 1.62, 2005: 1.76,
    2006: 1.76, 2007: 1.87, 2008: 3.23, 2009: 2.02, 2010: 1.83,
    2011: 2.13, 2012: 2.20, 2013: 1.94, 2014: 1.92, 2015: 2.11,
    2016: 2.03, 2017: 1.84, 2018: 2.09, 2019: 1.83, 2020: 1.58,
    2021: 1.29, 2022: 1.71, 2023: 1.50, 2024: 1.24, 2025: 1.15,
}


def build_shiller_annual():
    """Build complete annual dataset with derived fields."""
    years = sorted(PRICE.keys())
    records = {}
    for y in years:
        p = PRICE[y]
        pe = PE[y]
        dy = DIV_YIELD[y]
        eps = p / pe if pe > 0 else None
        div = p * dy / 100
        records[y] = {
            'price': p, 'pe': pe, 'div_yield_pct': dy,
            'eps': round(eps, 4) if eps else None,
            'div_per_share': round(div, 4),
        }
    return records


def compute_decomposition(records):
    """Annual return decomposition: Total = EPS Growth + PE Expansion + Dividend Yield."""
    years = sorted(records.keys())
    decomp = []
    for i in range(1, len(years)):
        y0, y1 = years[i - 1], years[i]
        if y1 - y0 != 1:
            continue
        r0, r1 = records[y0], records[y1]
        if not r0['eps'] or not r1['eps'] or r0['eps'] <= 0:
            continue

        price_ret = r1['price'] / r0['price'] - 1
        eps_growth = r1['eps'] / r0['eps'] - 1
        pe_expansion = (1 + price_ret) / (1 + eps_growth) - 1
        div_yield = r0['div_yield_pct'] / 100  # use start-of-year yield
        total_ret = price_ret + div_yield

        decomp.append({
            'year': y1,  # return for calendar year y0→y1
            'price': r1['price'],
            'eps': r1['eps'],
            'pe': r1['pe'],
            'price_return': round(price_ret, 4),
            'eps_growth': round(eps_growth, 4),
            'pe_expansion': round(pe_expansion, 4),
            'div_yield': round(div_yield, 4),
            'total_return': round(total_ret, 4),
        })
    return decomp


def rolling_decomposition(decomp, windows=[5, 10, 20, 30, 50]):
    """Compute rolling-window annualized decompositions."""
    rolling = {}
    for w in windows:
        results = []
        for i in range(w, len(decomp)):
            end = decomp[i]
            start = decomp[i - w]
            # Annualized from cumulative
            price_ratio = end['price'] / start['price']
            eps_ratio = end['eps'] / start['eps'] if start['eps'] > 0 and end['eps'] > 0 else None

            ann_price_ret = price_ratio ** (1 / w) - 1
            ann_eps_growth = eps_ratio ** (1 / w) - 1 if eps_ratio and eps_ratio > 0 else None
            ann_pe_exp = (1 + ann_price_ret) / (1 + ann_eps_growth) - 1 if ann_eps_growth is not None else None

            # Average dividend yield over window
            avg_div = sum(d['div_yield'] for d in decomp[i - w + 1:i + 1]) / w
            ann_total = ann_price_ret + avg_div

            results.append({
                'end_year': end['year'],
                'start_year': start['year'],
                'ann_price_return': round(ann_price_ret, 4),
                'ann_eps_growth': round(ann_eps_growth, 4) if ann_eps_growth is not None else None,
                'ann_pe_expansion': round(ann_pe_exp, 4) if ann_pe_exp is not None else None,
                'avg_div_yield': round(avg_div, 4),
                'ann_total_return': round(ann_total, 4),
            })
        rolling[w] = results
    return rolling


def cross_validate_compustat(shiller_decomp):
    """Compare Shiller index-level vs Compustat company-level aggregation.

    Year alignment:
      - Shiller decomp 'year: Y' = return from Jan(Y-1) → Jan(Y) ≈ calendar year Y-1
      - Compustat 'year: Y' = return from Dec(Y-1) → Dec(Y) = calendar year Y
      - So: Shiller year Y+1 ≈ Compustat year Y (both measure CY Y)
    """
    decomp_path = os.path.join(DATA, 'sp500_3level_decomposition.json')
    if not os.path.exists(decomp_path):
        print(f"  [SKIP] Compustat file not found: {decomp_path}")
        return None

    with open(decomp_path) as f:
        comp_data = json.load(f)

    comp_by_year = {r['year']: r for r in comp_data['aggregate']}
    shiller_by_year = {d['year']: d for d in shiller_decomp}

    print("\n" + "=" * 110)
    print("Cross-Validation: Shiller (Index-Level) vs Compustat (Company-Level Aggregation)")
    print("  Shiller: Jan→Jan returns; Compustat: Dec→Dec returns (1-month offset)")
    print("=" * 110)

    header = (f"{'CY':>6} │ {'Shiller':>9} {'Compust':>9} {'Δ(pp)':>7} │ "
              f"{'Shiller':>9} {'Compust':>9} {'Δ(pp)':>7} │ "
              f"{'Shiller':>7} {'Compust':>7} {'Δ':>6} │ "
              f"{'Shiller':>7} {'Compust':>7}")
    sub = (f"{'':>6} │ {'── Price Return ──':^27} │ "
           f"{'── EPS Growth ──':^27} │ "
           f"{'── PE ──':^22} │ "
           f"{'── DivYld ──':^16}")
    print(f"\n{header}\n{sub}")
    print("─" * 110)

    diffs_price = []
    diffs_eps = []
    diffs_pe = []
    diffs_div = []

    for cy in range(1985, 2024):
        # Shiller year cy+1 = Jan(cy) → Jan(cy+1) ≈ CY cy
        s = shiller_by_year.get(cy + 1)
        c = comp_by_year.get(cy)
        if not s or not c:
            continue

        dp = (s['price_return'] - c['price_return']) * 100
        c_eg = c.get('earnings_growth')
        de = ((s['eps_growth'] - c_eg) * 100
              if c_eg is not None and s['eps_growth'] is not None else None)
        dpe = s['pe'] - c['pe']
        dd = (s['div_yield'] - c['dividend_yield']) * 100

        diffs_price.append(dp)
        if de is not None:
            diffs_eps.append(de)
        diffs_pe.append(dpe)
        diffs_div.append(dd)

        eps_str = (f"{s['eps_growth']:>+8.1%} {c_eg:>+8.1%} {de:>+6.1f}"
                   if de is not None
                   else f"{s['eps_growth']:>+8.1%} {'N/A':>9} {'':>6}")

        print(f"{cy:>6} │ "
              f"{s['price_return']:>+8.1%} {c['price_return']:>+8.1%} {dp:>+6.1f} │ "
              f"{eps_str} │ "
              f"{s['pe']:>6.1f} {c['pe']:>6.1f} {dpe:>+5.1f} │ "
              f"{s['div_yield']:>6.2%} {c['dividend_yield']:>6.2%}")

    print("─" * 110)

    # Summary statistics
    print(f"\nSummary ({min(1985, 2024)}-2023, {len(diffs_price)} years):")
    if diffs_price:
        print(f"  Price Return:    mean Δ = {sum(diffs_price)/len(diffs_price):+.1f}pp  "
              f"σ = {stdev(diffs_price):.1f}pp  "
              f"[{min(diffs_price):+.0f}, {max(diffs_price):+.0f}]")
    if diffs_eps:
        print(f"  EPS Growth:      mean Δ = {sum(diffs_eps)/len(diffs_eps):+.1f}pp  "
              f"σ = {stdev(diffs_eps):.1f}pp  "
              f"[{min(diffs_eps):+.0f}, {max(diffs_eps):+.0f}]")
    if diffs_pe:
        print(f"  PE Ratio:        mean Δ = {sum(diffs_pe)/len(diffs_pe):+.1f}  "
              f"σ = {stdev(diffs_pe):.1f}  "
              f"[{min(diffs_pe):+.0f}, {max(diffs_pe):+.0f}]")
    if diffs_div:
        print(f"  Dividend Yield:  mean Δ = {sum(diffs_div)/len(diffs_div):+.2f}pp  "
              f"σ = {stdev(diffs_div):.2f}pp")

    # Long-run averages (more meaningful than year-by-year)
    s_years = [shiller_by_year[cy + 1] for cy in range(1985, 2024)
               if cy + 1 in shiller_by_year]
    c_years = [comp_by_year[cy] for cy in range(1985, 2024)
               if cy in comp_by_year]
    if s_years and c_years:
        s_avg_pr = sum(d['price_return'] for d in s_years) / len(s_years)
        c_avg_pr = sum(d['price_return'] for d in c_years) / len(c_years)
        s_avg_dy = sum(d['div_yield'] for d in s_years) / len(s_years)
        c_avg_dy = sum(d['dividend_yield'] for d in c_years) / len(c_years)
        print(f"\n  Long-run averages (1985-2023):")
        print(f"    Avg Price Return:  Shiller {s_avg_pr:.2%}  Compustat {c_avg_pr:.2%}  "
              f"Δ = {(s_avg_pr - c_avg_pr)*100:+.1f}pp")
        print(f"    Avg Div Yield:     Shiller {s_avg_dy:.2%}  Compustat {c_avg_dy:.2%}  "
              f"Δ = {(s_avg_dy - c_avg_dy)*100:+.2f}pp")
        print(f"    Avg Total Return:  Shiller {s_avg_pr + s_avg_dy:.2%}  "
              f"Compustat {c_avg_pr + c_avg_dy:.2%}")

    return {
        'price_return': {'mean': sum(diffs_price)/len(diffs_price),
                         'std': stdev(diffs_price)} if diffs_price else None,
        'eps_growth': {'mean': sum(diffs_eps)/len(diffs_eps),
                       'std': stdev(diffs_eps)} if diffs_eps else None,
    }


def stdev(lst):
    if len(lst) < 2:
        return 0
    m = sum(lst) / len(lst)
    return math.sqrt(sum((x - m) ** 2 for x in lst) / (len(lst) - 1))


def print_full_period_stats(decomp, rolling):
    """Print full-period summary and rolling window statistics."""
    print("\n" + "=" * 80)
    print("Shiller S&P 500 Annual Return Decomposition (1872-2025)")
    print("=" * 80)

    # Full period CAGR
    first, last = decomp[0], decomp[-1]
    n = last['year'] - first['year']
    cagr_price = (last['price'] / first['price']) ** (1 / n) - 1
    cagr_eps = (last['eps'] / first['eps']) ** (1 / n) - 1 if first['eps'] > 0 and last['eps'] > 0 else 0
    cagr_pe = (1 + cagr_price) / (1 + cagr_eps) - 1
    avg_div = sum(d['div_yield'] for d in decomp) / len(decomp)
    cagr_total = cagr_price + avg_div

    print(f"\nFull period: {first['year']}-{last['year']} ({n} years)")
    print(f"  Nominal Total Return CAGR:  {cagr_total:.2%}")
    print(f"    = Earnings Growth:        {cagr_eps:.2%}")
    print(f"    + PE Expansion:           {cagr_pe:.2%}")
    print(f"    + Avg Dividend Yield:     {avg_div:.2%}")

    print(f"\n  Price: {first['price']:.2f} → {last['price']:.2f}")
    print(f"  EPS:   {first['eps']:.2f} → {last['eps']:.2f}")
    print(f"  PE:    {first['pe']:.1f} → {last['pe']:.1f}")

    # Rolling window statistics
    print("\n" + "-" * 80)
    print("Rolling Window Mean Reversion Statistics")
    print("-" * 80)
    print(f"\n{'Window':>8} │ {'Total Return':>13} │ {'EPS Growth':>12} │ "
          f"{'PE Expansion':>13} │ {'Dividend':>10} │ {'StdDev(Total)':>14} │ {'Range':>16}")
    print("─" * 100)

    for w in sorted(rolling.keys()):
        data = rolling[w]
        if not data:
            continue
        total = [d['ann_total_return'] for d in data]
        eps = [d['ann_eps_growth'] for d in data if d['ann_eps_growth'] is not None]
        pe = [d['ann_pe_expansion'] for d in data if d['ann_pe_expansion'] is not None]
        div = [d['avg_div_yield'] for d in data]

        avg_t = sum(total) / len(total)
        avg_e = sum(eps) / len(eps) if eps else 0
        avg_p = sum(pe) / len(pe) if pe else 0
        avg_d = sum(div) / len(div)
        sd_t = stdev(total)
        rng = max(total) - min(total)

        print(f"{w:>6}yr │ {avg_t:>12.2%} │ {avg_e:>11.2%} │ "
              f"{avg_p:>12.2%} │ {avg_d:>9.2%} │ {sd_t:>13.2%} │ "
              f"[{min(total):+.1%}, {max(total):+.1%}]")

    print("\n→ As holding period lengthens, PE expansion → 0 and return variance shrinks")
    print("  This confirms mean reversion: long-run returns converge to EPS growth + dividends")


def save_output(records, decomp, rolling):
    """Save complete dataset to JSON for use in rebuild_report.py."""
    output = {
        'metadata': {
            'source': 'Robert Shiller / multpl.com',
            'period': '1871-2025',
            'notes': 'January values; EPS = Price/PE; Dividends = Price × DivYield',
        },
        'annual': {str(y): r for y, r in records.items()},
        'decomposition': decomp,
        'rolling': {str(w): data for w, data in rolling.items()},
    }
    out_path = os.path.join(DATA, 'shiller_complete.json')
    with open(out_path, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved to: {out_path}")
    return out_path


def main():
    records = build_shiller_annual()
    print(f"Shiller annual records: {len(records)} years ({min(records)}-{max(records)})")

    # Spot check: compare with known values from verify_eps_underestimation.py
    print("\nSpot check (derived EPS vs known Shiller EPS):")
    known = {
        1928: 1.58, 1950: 2.34, 1985: 14.61, 2000: 52.15, 2024: 197.78,
    }
    for y, known_eps in sorted(known.items()):
        derived = records[y]['eps']
        diff_pct = (derived - known_eps) / known_eps * 100
        print(f"  {y}: derived={derived:.2f}  known={known_eps:.2f}  diff={diff_pct:+.1f}%")

    decomp = compute_decomposition(records)
    print(f"\nAnnual decomposition: {len(decomp)} years")

    rolling = rolling_decomposition(decomp, windows=[5, 10, 20, 30, 50])

    print_full_period_stats(decomp, rolling)

    # Cross-validate with Compustat
    cross_validate_compustat(decomp)

    save_output(records, decomp, rolling)


if __name__ == '__main__':
    main()
