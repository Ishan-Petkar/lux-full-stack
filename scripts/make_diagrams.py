"""Generate every diagram into docs/diagrams/ :  python scripts/make_diagrams.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
OUT = Path(__file__).resolve().parent.parent / "docs" / "diagrams"
OUT.mkdir(parents=True, exist_ok=True)
for old in OUT.glob("*.png"):
    old.unlink()

import diagrams_b as B  # noqa: E402
import diagrams_c as C  # noqa: E402
import diagrams_d as D  # noqa: E402

# still valid from the first version: recommendation sequence + flowchart, DFD level 0
B.seq_recommend(OUT / "08_sequence_recommend.png")
B.activity_reco(OUT / "11_flow_recommendation.png")
B.dfd0(OUT / "12_dfd_level0.png")
C.run(OUT)
D.run(OUT)
