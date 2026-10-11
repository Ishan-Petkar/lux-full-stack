"""Design system: editorial minimalism.

Black on white, tiny uppercase grotesque type (Inter) with a Didone display face (Bodoni Moda) for the wordmark and titles,
warm-grey image tiles, no borders, shadows, radii or badges. Motion is CSS only: tiles rise into view, campaign images
unfold from a framed crop as you scroll (scroll-driven animations), the wordmark stays pinned and inverts over imagery.
"""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bodoni+Moda:opsz,wght@6..96,400..700&family=Inter:wght@300;400;500&display=swap');
:root {
  --bg:#fff; --ink:#000; --mute:#707070; --line:#d9d9d9; --tile:#efeee9; --panel:#f7f7f5; --ok:#000;
  --sans:'Inter', 'Helvetica Neue', Arial, sans-serif; --didone:'Bodoni Moda', 'Didot', 'Bodoni 72', Georgia, serif;
  --pad:clamp(1rem, 2.4vw, 2.4rem); --gap:.5rem; --hdr:4.4rem; --ease:cubic-bezier(.2,.7,.2,1);
}
html { scroll-behavior:smooth; }
html, body, [data-testid="stApp"], .stApp { background:var(--bg); color:var(--ink); font-family:var(--sans); font-weight:400; font-size:12px; line-height:1.55; letter-spacing:.01em; -webkit-font-smoothing:antialiased; }
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"], #MainMenu, footer,
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"] { display:none !important; }
.block-container, [data-testid="stMainBlockContainer"] { padding:0 !important; max-width:100% !important; }
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] { gap:0 !important; }
* { border-radius:0 !important; }
h1, h2, h3, h4, [data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3 { font-family:var(--sans) !important; font-weight:500 !important; color:var(--ink); letter-spacing:.04em !important; text-transform:uppercase; padding:0 !important; }
h1, [data-testid="stMarkdownContainer"] h1 { font-size:13px !important; line-height:1.4 !important; margin:0 0 1.2rem !important; }
h2, [data-testid="stMarkdownContainer"] h2 { font-size:12px !important; margin:0 !important; }
h3, [data-testid="stMarkdownContainer"] h3, h4 { font-size:12px !important; margin:0 0 .7rem !important; }
.didone, .title-d { font-family:var(--didone) !important; font-weight:500; text-transform:uppercase; letter-spacing:.01em; }
.title-d { font-size:clamp(1.2rem, 1.8vw, 1.6rem); text-align:center; margin:0 0 .3rem; }
.sub-c { text-align:center; color:var(--mute); font-size:11px; letter-spacing:.06em; text-transform:uppercase; }
p, label, li { font-family:var(--sans); } a { color:inherit; }
.muted { color:var(--mute); } .up { text-transform:uppercase; letter-spacing:.04em; } .small { font-size:11px; } .ra { text-align:right; } .strong { font-weight:500; }
.rule { height:1px; background:var(--line); margin:1.2rem 0; border:0; }
::selection { background:#000; color:#fff; }

/* ---------- motion ---------- */
[data-stale="true"], .stale-element { opacity:1 !important; transition:none !important; }
@keyframes fadeIn { from { opacity:0; } to { opacity:1; } }
@keyframes rise { from { opacity:0; transform:translateY(26px); } to { opacity:1; transform:none; } }
[class*="st-key-page-"] { animation: fadeIn .6s var(--ease) both; }
button, input, textarea, [data-baseweb="select"] > div { transition: all .25s var(--ease) !important; }
@media (prefers-reduced-motion: reduce) { * { animation-duration:.01ms !important; animation-delay:0s !important; transition-duration:.01ms !important; scroll-behavior:auto !important; } }

/* ---------- page frame ---------- */
[class*="st-key-page-"] { padding: var(--hdr) var(--pad) 3rem; }
.st-key-page-Home { padding:0 !important; gap:0 !important; }

/* ---------- header ---------- */
.st-key-hdr { position:fixed; top:0; left:0; right:0; z-index:200; padding:1.1rem var(--pad) .6rem; background:#fff; }
body:has(.zmark) .st-key-hdr { background:transparent; mix-blend-mode:difference; color:#fff; }
body:has(.zmark) .st-key-hdr * { color:#fff !important; }
.st-key-hdr, .st-key-hdr * { background-color:transparent !important; box-shadow:none !important; }
.st-key-hdr { background:#fff !important; } body:has(.zmark) .st-key-hdr { background:transparent !important; }
body:has(.zmark) .st-key-hdr input { border-bottom-color:#fff !important; }
.st-key-hdr [data-testid="stHorizontalBlock"] { display:grid !important; grid-template-columns:3rem 1fr minmax(9rem, 16rem) auto auto; column-gap:1.8rem !important; align-items:center; }
.st-key-hdr [data-testid="stColumn"] { min-width:0 !important; width:auto !important; flex:none !important; }
.st-key-hdr [data-testid="stColumn"]:nth-child(1) { grid-column:1; } .st-key-hdr [data-testid="stColumn"]:nth-child(3) { grid-column:3; justify-self:stretch; } .st-key-hdr [data-testid="stColumn"]:nth-child(4) { grid-column:4; } .st-key-hdr [data-testid="stColumn"]:nth-child(5) { grid-column:5; justify-self:end; }
.st-key-hdr [data-testid="stColumn"]:nth-child(2) { position:absolute; left:50%; top:1.1rem; transform:translateX(-50%); width:auto !important; }
.st-key-brand button { padding:0 !important; min-height:0 !important; border:0 !important; background:transparent !important; width:100%; justify-content:center; }
.st-key-brand button p { font-family:var(--didone) !important; font-size:1.7rem !important; font-weight:500 !important; letter-spacing:.06em !important; text-transform:uppercase; line-height:1; }
body:has(.zmark) .st-key-brand { visibility:hidden; }
[data-testid="stPopoverButton"] [aria-hidden="true"] { display:none !important; }
.st-key-hdr [data-testid="stPopoverButton"] { border:0 !important; background:transparent !important; padding:0 !important; min-height:0 !important; box-shadow:none !important; width:auto; }
.st-key-hdr [data-testid="stPopoverButton"] [data-testid="stIconMaterial"] { font-size:1.9rem !important; }
.st-key-hdr .stButton > button { border:0 !important; background:transparent !important; padding:0 !important; min-height:0 !important; box-shadow:none !important; justify-content:flex-end; }
.st-key-hdr .stButton > button p { font-size:11px !important; letter-spacing:.06em !important; text-transform:uppercase; font-weight:400 !important; white-space:nowrap; }
.st-key-hdr .stButton > button:hover p { text-decoration:underline; text-underline-offset:3px; }
.st-key-hdr [data-testid="stTextInput"] input { border:0 !important; border-bottom:1px solid #000 !important; background:transparent !important; padding:.2rem 0 !important; font-size:11px !important; text-transform:uppercase; letter-spacing:.06em; box-shadow:none !important; min-height:0 !important; height:1.7rem; text-align:right; }
.st-key-hdr [data-testid="stTextInput"] input::placeholder { color:#000; opacity:1; } body:has(.zmark) .st-key-hdr input::placeholder { color:#fff; }
.st-key-hdr [data-testid="stTextInput"] > div, .st-key-hdr [data-baseweb="input"], .st-key-hdr [data-baseweb="base-input"] { border:0 !important; background:transparent !important; box-shadow:none !important; }
.st-key-hdr [data-testid="InputInstructions"] { display:none; }
.st-key-hdr, .st-key-hdr > [data-testid="stLayoutWrapper"], .st-key-hdr [data-testid="stHorizontalBlock"] { width:100% !important; box-sizing:border-box; }
.st-key-hdr [data-testid="stTextInputRootElement"] { border:0 !important; border-bottom:1px solid #000 !important; background:transparent !important; }
body:has(.zmark) .st-key-hdr [data-testid="stTextInputRootElement"] { border-bottom-color:#fff !important; }
.st-key-hdr [data-testid="stTextInput"] input { border:0 !important; }

/* ---------- controls ---------- */
.stButton > button, [data-testid="stFormSubmitButton"] > button, .stDownloadButton > button {
  border:1px solid #000; background:#fff; color:#000; min-height:2.5rem; font-weight:400; box-shadow:none; }
.stButton > button p, [data-testid="stFormSubmitButton"] > button p, .stDownloadButton > button p { font-size:11px !important; letter-spacing:.08em !important; text-transform:uppercase; font-weight:400 !important; }
.stButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover, .stDownloadButton > button:hover { background:#000; color:#fff; border-color:#000; }
.stButton > button:hover p { color:#fff !important; }
.stButton > button[kind="primary"], [data-testid="stFormSubmitButton"] > button[kind="primaryFormSubmit"] { background:#000; color:#fff; }
.stButton > button[kind="primary"] p { color:#fff !important; }
.stButton > button[kind="primary"]:hover { background:#fff; color:#000; } .stButton > button[kind="primary"]:hover p { color:#000 !important; }
.stButton > button[kind="tertiary"] { border:0; background:transparent; min-height:0; padding:.1rem 0; justify-content:flex-start; }
.stButton > button[kind="tertiary"]:hover { background:transparent; } .stButton > button[kind="tertiary"]:hover p { color:#000 !important; text-decoration:underline; text-underline-offset:3px; }
.stButton > button:disabled { opacity:.35; }
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input, textarea, [data-baseweb="select"] > div { border:0 !important; border-bottom:1px solid #000 !important; background:transparent !important; box-shadow:none !important; }
[data-baseweb="base-input"], [data-baseweb="input"], [data-testid="stNumberInputContainer"] { border:0 !important; background:transparent !important; box-shadow:none !important; }
textarea { border:1px solid #d9d9d9 !important; }
label, [data-testid="stWidgetLabel"] p { font-size:10.5px !important; letter-spacing:.08em; text-transform:uppercase; color:var(--mute); }
[data-testid="stAlert"] { border:1px solid var(--line); background:#fff; color:#000; }
[data-testid="stExpander"] { border:0; border-top:1px solid var(--line); background:transparent; } [data-testid="stExpander"] summary p { font-size:11px; letter-spacing:.08em; text-transform:uppercase; }
[data-testid="stVerticalBlockBorderWrapper"]:not(:has(.tile)) { border:1px solid var(--line); background:#fff; }
[data-testid="stTabs"] [role="tab"] p { font-size:11px; letter-spacing:.08em; text-transform:uppercase; }
button[data-variant="pills"], [data-testid="stSegmentedControl"] button { border:1px solid var(--line) !important; background:#fff; color:#000; font-size:11px; letter-spacing:.06em; text-transform:uppercase; }
button[data-variant="pills"][aria-checked="true"], [data-testid="stSegmentedControl"] button[aria-checked="true"], [data-testid="stSegmentedControl"] button[kind="segmented_controlActive"] { background:#000 !important; color:#fff !important; border-color:#000 !important; }
button[data-variant="pills"][aria-checked="true"] *, [data-testid="stSegmentedControl"] button[aria-checked="true"] * { color:#fff !important; }
[data-testid="stDialog"] [role="dialog"] { animation: fadeIn .4s var(--ease) both; }
[data-testid="stToast"] { border:1px solid #000; background:#fff; box-shadow:none; }
[data-testid="stPopoverBody"] { border:1px solid #000; box-shadow:none; background:#fff; }
[data-testid="stPopoverBody"] .stButton > button[kind="tertiary"] { width:100%; }

/* ---------- product tiles ---------- */
[class*="st-key-tile-"] { position:relative; gap:0 !important; animation: rise .8s var(--ease) both; }
@supports (animation-timeline: view()) { [class*="st-key-tile-"] { animation: rise linear both; animation-timeline: view(); animation-range: entry 0% entry 45%; } }
.timg { aspect-ratio:3/4; background:var(--tile); overflow:hidden; }
.timg img { width:100%; height:100%; object-fit:cover; display:block; transition:transform 1.4s var(--ease); }
[class*="st-key-tile-"]:hover .timg img { transform:scale(1.035); }
.tmeta { display:flex; justify-content:space-between; gap:.6rem; padding:.55rem 0 0; font-size:11px; letter-spacing:.03em; text-transform:uppercase; line-height:1.4; }
.tbrand { color:var(--mute); } .tprice { padding-top:.15rem; font-size:11px; letter-spacing:.03em; }
.tsold { position:absolute; left:.6rem; top:.6rem; font-size:10px; letter-spacing:.1em; text-transform:uppercase; background:#fff; padding:.15rem .5rem; }
.tsim { color:var(--mute); font-size:10.5px; padding-top:.2rem; text-transform:none; letter-spacing:.01em; }
.tsold-img img { filter:grayscale(1) opacity(.55); }
.ph { display:flex; align-items:center; justify-content:center; height:100%; } .ph span { font-family:var(--didone); font-size:3rem; color:#bbb; }
/* the whole image is the link: an invisible button stretched over it */
[class*="st-key-cat-"], [class*="st-key-rec-"], [class*="st-key-bt-"], [class*="st-key-wl-"], [class*="st-key-rv-"], [class*="st-key-lp-"], [class*="st-key-mo-"] { position:absolute !important; top:0; left:0; width:100% !important; aspect-ratio:3/4; z-index:3; margin:0 !important; }
[class*="st-key-cat-"] > *, [class*="st-key-rec-"] > *, [class*="st-key-bt-"] > *, [class*="st-key-wl-"] > *, [class*="st-key-rv-"] > *, [class*="st-key-lp-"] > *, [class*="st-key-mo-"] > *,
[class*="st-key-cat-"] .stButton, [class*="st-key-rec-"] .stButton, [class*="st-key-bt-"] .stButton, [class*="st-key-wl-"] .stButton, [class*="st-key-lp-"] .stButton, [class*="st-key-mo-"] .stButton { width:100% !important; height:100% !important; }
[class*="st-key-cat-"] button, [class*="st-key-rec-"] button, [class*="st-key-bt-"] button, [class*="st-key-wl-"] button, [class*="st-key-rv-"] button, [class*="st-key-lp-"] button, [class*="st-key-mo-"] button { width:100% !important; height:100% !important; min-height:100% !important; opacity:0; cursor:pointer; }
[class*="st-key-qa-"] { position:absolute !important; right:0; bottom:1.55rem; width:auto !important; z-index:4; margin:0 !important; }
[class*="st-key-qa-"] button { border:0 !important; background:transparent !important; min-height:0; padding:0 .1rem; width:auto; }
[class*="st-key-qa-"] button p { font-size:15px !important; font-weight:300 !important; }
[class*="st-key-qa-"] button:hover { background:transparent !important; } [class*="st-key-qa-"] button:hover p { color:#000 !important; }

/* ---------- responsive tile grid ---------- */
GRIDROW { flex-wrap:wrap !important; gap:2.4rem var(--gap) !important; align-items:flex-start; }
GRIDCOL { flex:0 0 calc((100% - 3 * var(--gap)) / 4) !important; width:calc((100% - 3 * var(--gap)) / 4) !important; min-width:0 !important; }
@media (min-width: 1700px) { GRIDCOL { flex-basis:calc((100% - 4 * var(--gap)) / 5) !important; width:calc((100% - 4 * var(--gap)) / 5) !important; } }
@media (max-width: 1000px) { GRIDCOL { flex-basis:calc((100% - 2 * var(--gap)) / 3) !important; width:calc((100% - 2 * var(--gap)) / 3) !important; } }
@media (max-width: 700px)  { GRIDCOL { flex-basis:calc((100% - var(--gap)) / 2) !important; width:calc((100% - var(--gap)) / 2) !important; } }
/* mosaic: edge-to-edge image wall with no text */
.st-key-grid-mosaic { --gap:0px; }
.st-key-grid-mosaic [data-testid="stHorizontalBlock"] { row-gap:0 !important; }
GRIDMOS { flex:0 0 16.6667% !important; width:16.6667% !important; }
@media (max-width: 1000px) { GRIDMOS { flex:0 0 33.3333% !important; width:33.3333% !important; } }
.st-key-grid-mosaic .tmeta, .st-key-grid-mosaic .tprice { display:none; }

/* ---------- category page ---------- */
.idx { position:sticky; top:6rem; }
.idx-row { display:flex; gap:.5rem; font-size:11px; letter-spacing:.05em; text-transform:uppercase; margin-bottom:.35rem; }
.idx-row i { font-style:normal; color:var(--mute); }
.st-key-index .stButton > button { padding:0; min-height:0; justify-content:flex-start; text-align:left; }
.st-key-index .stButton > button p { text-align:left; }
.st-key-index button[kind="primary"] { background:transparent !important; border:0 !important; } .st-key-index button[kind="primary"] p { color:#000 !important; font-weight:500 !important; }
.st-key-index button[kind="primary"]:hover { background:transparent !important; }
.st-key-tools .stButton > button, .st-key-tools [data-testid="stPopover"] > button { border:0 !important; background:transparent !important; min-height:0; padding:0; box-shadow:none !important; justify-content:flex-end; }
.st-key-tools [data-testid="stPopover"] > button p { font-size:11px !important; letter-spacing:.08em !important; text-transform:uppercase; }
.st-key-tools [data-baseweb="select"] > div { border-bottom:1px solid #000 !important; min-height:2rem; background:transparent !important; }
.empty { text-align:center; padding:5rem 1rem 1.5rem; } .empty h3 { margin-top:.4rem; } .empty .muted { max-width:46ch; margin:0 auto .8rem; }

/* ---------- product page ---------- */
.pimgbig { background:var(--tile); aspect-ratio:3/4; width:min(100%, calc((100vh - 6.2rem) * .75)); margin:0 auto; overflow:hidden; }
.pimgbig img { width:100%; height:100%; object-fit:cover; display:block; animation: unfoldImg 1.4s var(--ease) both; }
@keyframes unfoldImg { from { transform:scale(1.18); opacity:.3; } to { transform:none; opacity:1; } }
.st-key-pinfo { position:sticky; top:5.5rem; align-self:flex-start; }
.pname-lg { font-size:12px; letter-spacing:.06em; text-transform:uppercase; font-weight:500; margin:0; }
.pbrand-lg { font-size:11px; letter-spacing:.08em; text-transform:uppercase; color:var(--mute); }
.pprice-lg { font-size:12px; margin-top:.2rem; } .ptax { font-size:10px; color:var(--mute); letter-spacing:.04em; text-transform:uppercase; }
.pdesc { font-size:12px; line-height:1.65; color:#000; margin:1.1rem 0; max-width:46ch; }
.avail { font-size:10.5px; letter-spacing:.08em; text-transform:uppercase; } .avail.low { color:#b00020; } .avail.out { color:#b00020; }
.facts { display:grid; grid-template-columns:auto 1fr; gap:.25rem 1.2rem; font-size:11px; margin:.6rem 0 1rem; } .facts dt { color:var(--mute); text-transform:uppercase; letter-spacing:.06em; } .facts dd { margin:0; }
.sec-title { text-align:center; margin:4rem 0 1.6rem; font-family:var(--didone); font-weight:500; text-transform:uppercase; font-size:clamp(1.1rem, 1.6vw, 1.45rem); letter-spacing:.02em; }
.sec-title small { display:block; font-family:var(--sans); font-size:10.5px; letter-spacing:.08em; color:var(--mute); margin-top:.3rem; }
.stars { display:inline-flex; align-items:center; gap:1px; } .stars .rtxt { margin-left:.4rem; font-size:11px; } .stars svg { display:block; }
.bar { display:flex; align-items:center; gap:.5rem; font-size:11px; margin:.25rem 0; } .bar > div { flex:1; height:2px; background:var(--line); } .bar i { display:block; height:100%; background:#000; }
.rev { padding:1rem 0; border-bottom:1px solid var(--line); } .rev-head { display:flex; align-items:center; gap:.7rem; flex-wrap:wrap; } .rev-body { margin:.3rem 0; line-height:1.6; max-width:70ch; }
.verified { font-size:10px; letter-spacing:.08em; text-transform:uppercase; color:var(--mute); }
.trust { font-size:11px; color:var(--mute); line-height:1.9; margin-top:1rem; } .trust .ic { margin-right:.4rem; vertical-align:-4px; }

/* ---------- bag / checkout / orders ---------- */
.thumb { width:64px; aspect-ratio:3/4; background:var(--tile); overflow:hidden; } .thumb img { width:100%; height:100%; object-fit:cover; display:block; } .thumb.sm { width:42px; }
.thumbs { display:flex; gap:6px; flex-wrap:wrap; margin:.4rem 0; }
.lname { font-size:12px; letter-spacing:.04em; text-transform:uppercase; } .lmeta { color:var(--mute); font-size:11px; }
.summary-row { display:flex; justify-content:space-between; padding:.3rem 0; } .summary-row.muted { color:var(--mute); font-size:11px; }
.summary-total { display:flex; justify-content:space-between; padding:.8rem 0 .2rem; border-top:1px solid #000; margin-top:.6rem; font-size:13px; letter-spacing:.04em; text-transform:uppercase; font-weight:500; }
.st-key-summary { position:sticky; top:5.5rem; }
.status { font-size:10px; letter-spacing:.1em; text-transform:uppercase; border:1px solid #000; padding:.12rem .5rem; } .status.bad, .status.warn { border-color:#b00020; color:#b00020; }
.pill.ok, span.pill.ok { font-size:10px; letter-spacing:.1em; text-transform:uppercase; border:1px solid #000; padding:.12rem .5rem; }
.tick { width:54px; height:54px; border:1px solid #000; display:flex; align-items:center; justify-content:center; margin:2rem auto 1rem; } .tick svg { stroke-dasharray:30; animation:draw .8s .2s var(--ease) both; margin:0; } @keyframes draw { from { stroke-dashoffset:30; } to { stroke-dashoffset:0; } }
.step { font-size:11px; letter-spacing:.08em; text-transform:uppercase; font-weight:500; margin-bottom:.7rem; display:flex; gap:.6rem; } .step span { color:var(--mute); }
.tl { display:flex; margin:1rem 0 1.6rem; } .tl-step { flex:1; position:relative; color:var(--mute); font-size:10.5px; letter-spacing:.08em; text-transform:uppercase; display:flex; flex-direction:column; gap:.5rem; padding-top:1rem; }
.tl-step::before { content:""; position:absolute; top:0; left:0; right:0; height:1px; background:var(--line); } .tl-step.on { color:#000; } .tl-step.on::before { background:#000; height:2px; top:-.5px; }
.tl-step i { display:none; } .tl-step small { color:var(--mute); text-transform:none; letter-spacing:0; }
.kpis { display:grid; grid-template-columns:repeat(auto-fit, minmax(170px, 1fr)); gap:var(--gap); margin:.8rem 0 2rem; } .kpi { border:1px solid var(--line); padding:1.1rem 1.1rem .9rem; background:#fff; }
.kpi-l { font-size:10px; letter-spacing:.12em; text-transform:uppercase; color:var(--mute); } .kpi-v { font-family:var(--didone); font-size:2rem; font-weight:500; line-height:1.2; margin:.2rem 0; }
.kpi-s { font-size:10.5px; color:var(--mute); } .kpi-d { font-weight:500; margin-right:.3rem; } .kpi-d.up { color:#1d6b3a; } .kpi-d.down { color:#b00020; }
.ch-t { font-size:11px; letter-spacing:.1em; text-transform:uppercase; font-weight:500; margin:1.2rem 0 .1rem; } .ch-s { font-size:10.5px; color:var(--mute); margin-bottom:.3rem; }
.rz-head { display:flex; justify-content:space-between; align-items:center; padding:.9rem 1rem; background:#000; color:#fff; } .rz-head .muted { color:#aaa; } .rz-amt { font-family:var(--didone); font-size:1.5rem; display:flex; gap:.8rem; align-items:center; }
.rz-amt .pill { position:static; background:#fff; color:#000; font-family:var(--sans); font-size:9px; letter-spacing:.1em; padding:.1rem .4rem; }
.bank { border:1px dashed var(--line); padding:1.2rem; text-align:center; margin:.6rem 0 1rem; }
.hint { font-size:11px; color:var(--mute); }

/* ---------- footer ---------- */
.foot { margin-top:5rem; padding:2.2rem var(--pad) 1.4rem; border-top:1px solid var(--line); font-size:11px; letter-spacing:.04em; text-transform:uppercase; }
.foot-grid { display:grid; grid-template-columns:repeat(4, 1fr); gap:2rem; } .foot b { font-weight:500; display:block; margin-bottom:.6rem; } .foot span { display:block; color:var(--mute); line-height:2; }
.foot-small { margin-top:2rem; color:var(--mute); text-transform:none; letter-spacing:0; max-width:90ch; }
@media (max-width: 700px) { .foot-grid { grid-template-columns:1fr 1fr; } }

/* ---------- landing (full-bleed campaign slides) ---------- */
.zmark { position:fixed; right:-.6vw; bottom:7vh; font-family:var(--didone); font-weight:500; font-size:23vw; line-height:.78; letter-spacing:-.045em; color:#fff; mix-blend-mode:difference; pointer-events:none; z-index:120; text-transform:uppercase; animation: fadeIn 1.6s .3s both; }
.zs { position:relative; height:100vh; min-height:520px; overflow:hidden; background:#fff; }
.zs .zi { position:absolute; inset:0; background-size:cover; background-position:center; background-color:#d9d6cf; }
@supports (animation-timeline: view()) {
  .zs .zi { animation: unfold linear both; animation-timeline: view(); animation-range: entry 0% cover 50%; }
  .zs .zcap { animation: capIn linear both; animation-timeline: view(); animation-range: entry 30% cover 55%; }
  .zs.first .zi, .zs.first .zcap { animation:none; }
}
@keyframes unfold { from { clip-path:inset(16% 14% 16% 14%); transform:scale(1.22); } to { clip-path:inset(0); transform:scale(1); } }
@keyframes capIn { from { opacity:0; transform:translateY(24px); } to { opacity:1; transform:none; } }
.zs .zcap { position:absolute; left:var(--pad); bottom:4.4rem; color:#fff; z-index:2; text-transform:uppercase; }
.zs .zcap .k { font-size:10.5px; letter-spacing:.14em; opacity:.85; } .zs .zcap .t { font-family:var(--didone); font-size:clamp(1.4rem, 2.6vw, 2.4rem); letter-spacing:.02em; margin-top:.3rem; }
.zs::after { content:""; position:absolute; inset:0; background:linear-gradient(0deg, rgba(0,0,0,.35), transparent 40%); z-index:1; pointer-events:none; }
.zs.half { height:92vh; }
[class*="st-key-zs-"] { position:relative; gap:0 !important; }
[class*="st-key-zs-"] .stElementContainer:has(button) { position:absolute; left:var(--pad); bottom:2.4rem; z-index:5; width:auto !important; }
[class*="st-key-zs-"] button { border:0 !important; background:transparent !important; color:#fff; padding:0; min-height:0; border-bottom:1px solid #fff !important; }
[class*="st-key-zs-"] button p { color:#fff !important; font-size:10.5px !important; letter-spacing:.14em !important; }
[class*="st-key-zs-"] button:hover { background:transparent !important; } [class*="st-key-zs-"] button:hover p { text-decoration:none; }
.lp-svc { display:grid; grid-template-columns:repeat(3, 1fr); gap:2rem; padding:4rem var(--pad); text-align:center; font-size:11px; letter-spacing:.08em; text-transform:uppercase; } .lp-svc b { display:block; font-weight:500; margin-bottom:.4rem; } .lp-svc span { color:var(--mute); }
@media (max-width: 700px) { .lp-svc { grid-template-columns:1fr; gap:1.4rem; } }

/* ---------- compact header on phones ---------- */
@media (max-width: 800px) {
  :root { --hdr:5.6rem; }
  .st-key-hdr [data-testid="stHorizontalBlock"] { grid-template-columns:3rem 1fr auto auto; row-gap:.6rem; column-gap:1rem !important; }
  .st-key-hdr [data-testid="stColumn"]:nth-child(3) { grid-column:1 / -1; grid-row:2; width:100% !important; }
  .st-key-hdr [data-testid="stColumn"]:nth-child(4) { grid-column:3; grid-row:1; } .st-key-hdr [data-testid="stColumn"]:nth-child(5) { grid-column:4; grid-row:1; }
  .st-key-hdr [data-testid="stTextInput"] input { text-align:left; }
  .zs .zcap { bottom:5.2rem; } .zs { height:82vh; } .zmark { font-size:30vw; bottom:12vh; }
}
</style>
"""
CSS = CSS.replace("GRIDMOS", '[class*="st-key-grid-"].st-key-grid-mosaic > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]').replace("GRIDROW", '[class*="st-key-grid-"] > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"]').replace(
    "GRIDCOL", '[class*="st-key-grid-"] > [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]')
