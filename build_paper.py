"""
The Newspaper - front page builder (v2: themes)
Reads news.json (made by fetch_news.py) and writes index.html.

Run:
    python fetch_news.py
    python build_paper.py
Then double-click index.html. Use the colour dots top-right to switch theme.
"""

import json
import re
import html
import datetime as dt

PAPER_NAME = "The Market Chronicle"      # rename to whatever you like
TAGLINE = "Daily morning briefing: global markets, India and currencies"
OWNER_NAME = "Sumedh Kagwade"          # shown as watermark and byline
INDIA_MAX = 9                        # stories shown in the India column
DEFAULT_THEME = "chronicle"          # chronicle | midnight | harbour | rosewood | forest


def clean(text: str, limit: int = 260) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html.unescape(re.sub(r"\s+", " ", text)).strip()
    if len(text) > limit:
        text = text[:limit].rsplit(" ", 1)[0] + "…"
    return html.escape(text)


def when(ts: float) -> str:
    return dt.datetime.fromtimestamp(ts).strftime("%d %b, %H:%M")


# ---- Sectors ---------------------------------------------------------------
# name -> words that tag a story with that sector. Edit freely.
SECTORS = {
    "Banking & Finance": [r"bank\w*", r"nbfc", r"loans?", r"lending", r"insur\w*", r"mutual funds?", r"fintech", r"hdfc", r"icici", r"sbi", r"kotak", r"credit"],
    "IT & Tech": [r"software", r"tcs", r"infosys", r"wipro", r"hcl\w*", r"tech mahindra", r"it services", r"it stocks?", r"it sector", r"it shares?", r"tech\w*", r"semiconductors?", r"chips?", r"nvidia", r"microsoft", r"alphabet", r"google", r"artificial intelligence", r"cloud"],
    "Pharma & Health": [r"pharma\w*", r"drugs?", r"health\w*", r"hospitals?", r"biotech", r"vaccines?", r"cipla", r"lupin", r"fda"],
    "Auto": [r"auto\w*", r"cars?", r"vehicles?", r"evs?", r"maruti", r"tata motors", r"mahindra", r"tesla", r"two-wheelers?", r"tyres?", r"ashok leyland"],
    "Energy": [r"oil", r"crude", r"brent", r"gas", r"opec", r"refin\w*", r"petrol\w*", r"diesel", r"power", r"solar", r"renewables?", r"coal", r"energy", r"ongc", r"reliance", r"nuclear"],
    "Metals & Mining": [r"steel", r"metals?", r"alumin(?:i)?um", r"copper", r"iron ore", r"mining", r"zinc", r"jsw", r"vedanta", r"hindalco"],
    "FMCG & Consumer": [r"fmcg", r"consumer\w*", r"retail\w*", r"nestle", r"dabur", r"britannia", r"food", r"beverages?", r"e-?commerce", r"zomato", r"swiggy", r"restaurants?"],
    "Infra & Real Estate": [r"infra\w*", r"real estate", r"realty", r"housing", r"cement", r"construction", r"larsen", r"railways?", r"ports?", r"airports?", r"dlf", r"propert(?:y|ies)"],
    "Telecom": [r"telecom\w*", r"jio", r"airtel", r"vodafone", r"bharti", r"5g", r"spectrum", r"satellites?"],
    "Economy & Policy": [r"gdp", r"inflation", r"cpi", r"wpi", r"rbi", r"fed(?!\s+up)", r"federal reserve", r"central bank\w*", r"repo", r"interest rates?", r"rate (?:hikes?|cuts?)", r"fiscal", r"budget", r"tax\w*", r"gst", r"imf", r"world bank", r"tariffs?", r"trade deficit", r"unemployment", r"payrolls?", r"pmi", r"econom\w*", r"recession", r"ecb", r"boj", r"boe", r"mpc"],
    "IPOs": [r"ipos?", r"listing", r"gmp", r"price band", r"subscription"],
    "Currency & Crypto": [r"rupee", r"dollar", r"euro", r"yen", r"forex", r"fx", r"currenc\w*", r"crypto\w*", r"bitcoin", r"ethereum", r"stablecoins?"],
    "Gold & Commodities": [r"gold", r"silver", r"commodit\w*"],
}
SECTOR_RE = {
    name: re.compile(r"\b(?:" + "|".join(terms) + r")\b", re.IGNORECASE)
    for name, terms in SECTORS.items()
}


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def tag_sectors(it: dict) -> list[str]:
    text = f'{it.get("headline", "")} {it.get("summary", "")}'
    return [slug(n) for n, rx in SECTOR_RE.items() if rx.search(text)]


def story(it: dict, with_summary: bool = True, lines: int = 3, extra: bool = False) -> str:
    summ = clean(it.get("summary", ""))
    _hk = re.sub(r"\W+", "", it["headline"].lower())[:40]
    _sk = re.sub(r"\W+", "", html.unescape(summ).lower())[:40]
    if _hk == _sk:          # summary only repeats the headline: skip it
        summ = ""
    body = f'<p class="sum l{lines}">{summ}</p>' if (with_summary and summ) else ""
    return (
        f'<article class="story{" extra" if extra else ""}" data-sec="{" ".join(tag_sectors(it))}">'
        f'<h3><a href="{html.escape(it["url"])}" target="_blank" rel="noopener">'
        f'{html.escape(it["headline"])}</a></h3>'
        f'{body}'
        f'<p class="meta">{html.escape(it["source"])}, {when(it["ts"])}</p>'
        "</article>"
    )


def fx_rows(rows: list[dict]) -> str:
    out = []
    for c in rows:
        v = c["inr"]
        val = f"{v:,.2f}" if v >= 1 else f"{v:.4f}"
        out.append(
            f'<tr><td class="sym">{html.escape(c["code"])}</td>'
            f'<td>{html.escape(c["name"])}</td>'
            f'<td class="num">{val}</td></tr>'
        )
    return "\n".join(out) or '<tr><td colspan="3">Rates unavailable right now.</td></tr>'


CSS = """
:root, [data-theme="midnight"] {
  --paper:#0D1726; --panel:#14233A; --ink:#E9EDF5; --muted:#9AA8BD; --hair:#27384F;
  --accent:#F0B429; --on-accent:#1A1405; --band:#070E19; --on-band:#F4F6FA;
  --band-line:rgba(255,255,255,.15);
}
[data-theme="chronicle"] {
  --paper:#F8F3E8; --panel:#FDFBF6; --ink:#1A1A1A; --muted:#6B665C; --hair:#E2D9C2;
  --accent:#B8860B; --on-accent:#FFFFFF; --band:#F8F3E8; --on-band:#1A1A1A;
  --band-line:#E2D9C2;
}
[data-theme="harbour"] {
  --paper:#E9F0F6; --panel:#FFFFFF; --ink:#0E2236; --muted:#54677A; --hair:#C3D1DD;
  --accent:#0A6FD1; --on-accent:#FFFFFF; --band:#0E2A47; --on-band:#F2F7FC;
}
[data-theme="rosewood"] {
  --paper:#F6EBEA; --panel:#FFFFFF; --ink:#2B1519; --muted:#7A5A5E; --hair:#E3CCCB;
  --accent:#A62340; --on-accent:#FFFFFF; --band:#3A0F1A; --on-band:#FBEFEF;
}
[data-theme="forest"] {
  --paper:#E6EEE8; --panel:#FFFFFF; --ink:#14241B; --muted:#55675B; --hair:#C2D1C7;
  --accent:#1F7A4F; --on-accent:#FFFFFF; --band:#0F2A1D; --on-band:#EEF6F0;
}
* { box-sizing: border-box; }
body { margin:0; background:var(--paper); color:var(--ink);
  font-family:"Source Serif 4", Georgia, serif; line-height:1.5; }
a { color:inherit; text-decoration:none; }
a:hover { text-decoration:underline; text-decoration-color:var(--accent); text-underline-offset:3px; }
a:focus-visible, button:focus-visible { outline:2px solid var(--accent); outline-offset:2px; }
.wrap { max-width:1180px; margin:0 auto; padding:0 20px; }

.band { background:var(--band); color:var(--on-band); border-bottom:5px solid var(--accent); }
.band .top { display:flex; justify-content:space-between; align-items:center; gap:12px;
  font-family:"IBM Plex Mono", monospace; font-size:.76rem; padding:10px 0;
  border-bottom:1px solid var(--band-line); opacity:.9; flex-wrap:wrap; }
.band h1 { font-family:"Fraunces", Georgia, serif; font-weight:800; text-align:center;
  font-size:clamp(2.4rem, 7vw, 4.8rem); letter-spacing:-.02em; line-height:1;
  margin:0; padding:26px 0 8px; }
.band .tag { text-align:center; font-style:italic; opacity:.8; padding-bottom:20px; margin:0; }

[data-theme="chronicle"] .band h1 { font-family:"Playfair Display", Georgia, serif; font-weight:900;
  text-transform:uppercase; letter-spacing:-.01em; text-shadow:3px 3px 0 var(--accent); }
.themes { display:flex; gap:8px; align-items:center; }
.themes button { width:18px; height:18px; border-radius:50%; border:2px solid var(--on-band);
  cursor:pointer; padding:0; }
.themes button[aria-pressed="true"] { box-shadow:0 0 0 2px var(--band), 0 0 0 4px var(--accent); }

.grid { display:grid; grid-template-columns:1.55fr 1fr .8fr; gap:0; padding:28px 0 56px; }
.col { padding:0 22px; border-left:1px solid var(--hair); }
.col:first-child { padding-left:0; border-left:0; }
.col:last-child { padding-right:0; align-self:start; position:sticky; top:16px; }
h2.sec { display:inline-block; background:var(--accent); color:var(--on-accent);
  font-family:"Fraunces", Georgia, serif; font-weight:600; font-size:1rem;
  margin:0 0 16px; padding:5px 12px; }

.lead { background:var(--panel); border-top:4px solid var(--accent); padding:20px 22px 16px;
  margin-bottom:8px; }
.lead h2 { font-family:"Fraunces", Georgia, serif; font-weight:800;
  font-size:clamp(1.7rem, 3.2vw, 2.5rem); line-height:1.08; margin:0 0 10px; }
.deck { font-size:1.1rem; margin:0 0 8px; color:var(--muted); }

.story { padding:14px 0; border-top:1px solid var(--hair); }
.story h3 { font-family:"Fraunces", Georgia, serif; font-weight:600; font-size:1.12rem;
  line-height:1.25; margin:0 0 4px; }
.sum { margin:4px 0; font-size:.95rem; color:var(--muted);
  display:-webkit-box; -webkit-box-orient:vertical; overflow:hidden; }
.sum.l2 { -webkit-line-clamp:2; line-clamp:2; }
.sum.l3 { -webkit-line-clamp:3; line-clamp:3; }
.meta { margin:4px 0 0; font-family:"IBM Plex Mono", monospace; font-size:.72rem; color:var(--accent); }

table { width:100%; border-collapse:collapse; font-family:"IBM Plex Mono", monospace;
  font-size:.82rem; background:var(--panel); }
th { text-align:left; font-weight:500; color:var(--muted); padding:8px 10px;
  border-bottom:2px solid var(--accent); }
td { padding:7px 10px; border-bottom:1px solid var(--hair); }
td.sym { font-weight:500; color:var(--accent); }
td.num, th.num { text-align:right; }
.note { font-size:.8rem; color:var(--muted); margin-top:10px; }

[hidden] { display:none !important; }
.wm { position:fixed; inset:0; display:grid; place-items:center; z-index:0; pointer-events:none;
  user-select:none; overflow:hidden; font-family:"Fraunces", Georgia, serif; font-weight:800;
  font-size:clamp(3rem, 11vw, 10rem); white-space:nowrap; color:var(--ink); opacity:.06;
  transform:rotate(-24deg); }
.band, main, footer { position:relative; z-index:1; }
.by { text-align:center; font-family:"IBM Plex Mono", monospace; font-size:.75rem;
  letter-spacing:.14em; text-transform:uppercase; opacity:.75; margin:0; padding-bottom:18px; }
footer { max-width:1180px; margin:0 auto; padding:18px 20px 36px; border-top:1px solid var(--hair);
  font-family:"IBM Plex Mono", monospace; font-size:.74rem; color:var(--muted); text-align:center; }
.filters { display:flex; flex-wrap:wrap; gap:8px; align-items:center; padding:20px 0 0; }
.flabel { font-family:"IBM Plex Mono", monospace; font-size:.75rem; color:var(--muted); margin-right:4px; }
.chip { font:inherit; font-size:.85rem; color:var(--ink); background:var(--panel);
  border:1px solid var(--hair); border-radius:999px; padding:5px 12px; cursor:pointer; }
.chip span { font-family:"IBM Plex Mono", monospace; font-size:.72rem; color:var(--muted); margin-left:4px; }
.chip:hover { border-color:var(--accent); }
.chip[aria-pressed="true"] { background:var(--accent); color:var(--on-accent); border-color:var(--accent); }
.chip[aria-pressed="true"] span { color:var(--on-accent); }
.chip.clear { border-style:dashed; color:var(--muted); }
.empty { color:var(--muted); font-style:italic; padding:14px 0; }
@media (max-width:900px) {
  .grid { grid-template-columns:1fr; }
  .col { padding:0; border-left:0; margin-bottom:28px; }
  .col:last-child { position:static; }
}
"""

JS_FILTER = """
(function () {
  var chips = document.querySelectorAll(".chip[data-s]");
  var clear = document.querySelector(".chip.clear");
  var sel = [];
  function apply() {
    document.querySelectorAll("[data-sec]").forEach(function (el) {
      var secs = el.getAttribute("data-sec").split(" ");
      var show = sel.length
        ? sel.some(function (x) { return secs.indexOf(x) > -1; })
        : !el.classList.contains("extra");
      el.hidden = !show;
    });
    document.querySelectorAll(".col").forEach(function (col) {
      var note = col.querySelector(".empty");
      if (!note) return;
      var visible = col.querySelectorAll("[data-sec]:not([hidden])").length;
      note.hidden = visible > 0;
    });
    chips.forEach(function (c) {
      c.setAttribute("aria-pressed", sel.indexOf(c.dataset.s) > -1);
    });
    clear.hidden = !sel.length;
  }
  chips.forEach(function (c) {
    c.addEventListener("click", function () {
      var i = sel.indexOf(c.dataset.s);
      if (i > -1) sel.splice(i, 1); else sel.push(c.dataset.s);
      apply();
    });
  });
  clear.addEventListener("click", function () { sel = []; apply(); });
  apply();
})();
"""


def main() -> None:
    with open("news.json", encoding="utf-8") as f:
        data = json.load(f)

    g, i, fx = data["global"], data["india"], data.get("fx", [])
    today = dt.datetime.now().strftime("%A, %d %B %Y")
    built = dt.datetime.fromisoformat(data["generated_at"]).strftime("%H:%M")

    lead = next((x for x in g if x.get("summary")), g[0] if g else None)
    g_rest = [x for x in g if x is not lead]

    lead_html = ""
    if lead:
        deck = clean(lead.get("summary", ""), 420)
        # hide the deck when it only repeats the headline
        head_key = re.sub(r"\W+", "", lead["headline"].lower())[:40]
        deck_key = re.sub(r"\W+", "", html.unescape(deck).lower())[:40]
        deck_html = "" if head_key == deck_key else f'<p class="deck">{deck}</p>'
        lead_html = (
            f'<section class="lead" data-sec="{" ".join(tag_sectors(lead))}">'
            f'<h2><a href="{html.escape(lead["url"])}" target="_blank" rel="noopener">'
            f'{html.escape(lead["headline"])}</a></h2>'
            f'{deck_html}'
            f'<p class="meta">{html.escape(lead["source"])}, {when(lead["ts"])}</p>'
            "</section>"
        )

    counts = {slug(n): 0 for n in SECTORS}
    for it in list(g) + list(i):
        for sl in tag_sectors(it):
            counts[sl] += 1
    chips = "".join(
        f'<button class="chip" data-s="{slug(n)}" aria-pressed="false">'
        f'{html.escape(n)} <span>{counts[slug(n)]}</span></button>'
        for n in SECTORS if counts[slug(n)] > 0
    )

    swatches = {
        "chronicle": "#B8860B", "midnight": "#F0B429", "harbour": "#0A6FD1",
        "rosewood": "#A62340", "forest": "#1F7A4F",
    }
    buttons = "".join(
        f'<button data-t="{k}" style="background:{v}" aria-label="{k} theme" '
        f'title="{k}" aria-pressed="false"></button>'
        for k, v in swatches.items()
    )

    page = f"""<!DOCTYPE html>
<html lang="en" data-theme="{DEFAULT_THEME}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{PAPER_NAME}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@900&family=Fraunces:opsz,wght@9..144,600;9..144,800&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>{CSS}</style>
<script>
try {{ var s = localStorage.getItem("paper-theme");
  if (s) document.documentElement.setAttribute("data-theme", s); }} catch (e) {{}}
</script>
</head>
<body>
<div class="wm" aria-hidden="true">{OWNER_NAME}</div>
<header class="band">
  <div class="wrap">
    <div class="top"><span>{today}</span><span>Updated {built}</span>
      <span class="themes" role="group" aria-label="Colour theme">{buttons}</span></div>
    <h1>{PAPER_NAME}</h1>
    <p class="tag">{TAGLINE}</p>
    <p class="by">Curated by {OWNER_NAME}</p>
  </div>
</header>

<main class="wrap">
  <nav class="filters" aria-label="Filter by sector">
    <span class="flabel">Sectors</span>{chips}
    <button class="chip clear" hidden>Clear</button>
  </nav>
  <div class="grid">
    <div class="col">
      <h2 class="sec">Global finance and economy</h2>
      {lead_html}
      {"".join(story(x, lines=2) for x in g_rest)}
      <p class="empty" hidden>No stories in the selected sectors today.</p>
    </div>

    <div class="col">
      <h2 class="sec">India: finance and economy</h2>
      {"".join(story(x, lines=3, extra=(n >= INDIA_MAX)) for n, x in enumerate(i))}
      <p class="empty" hidden>No stories in the selected sectors today.</p>
    </div>

    <div class="col">
      <h2 class="sec">Currency rates</h2>
      <table>
        <tr><th>Code</th><th>Currency</th><th class="num">₹ per 1</th></tr>
        {fx_rows(fx)}
      </table>
      <p class="note">Indicative mid-market rates in Indian rupees at the time of update.</p>
    </div>
  </div>
</main>
<footer>Curated by {OWNER_NAME} &middot; Sources: Finnhub, Economic Times, Mint, Moneycontrol &middot; For personal reading</footer>

<script>
(function () {{
  var root = document.documentElement, btns = document.querySelectorAll(".themes button");
  function mark() {{
    var cur = root.getAttribute("data-theme");
    btns.forEach(function (b) {{ b.setAttribute("aria-pressed", b.dataset.t === cur); }});
  }}
  btns.forEach(function (b) {{
    b.addEventListener("click", function () {{
      root.setAttribute("data-theme", b.dataset.t);
      try {{ localStorage.setItem("paper-theme", b.dataset.t); }} catch (e) {{}}
      mark();
    }});
  }});
  mark();
}})();
</script>
<script>{JS_FILTER}</script>
</body>
</html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(page)
    print("Saved index.html - open it in your browser.")


if __name__ == "__main__":
    main()
