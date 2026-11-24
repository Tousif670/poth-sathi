import sys
from pathlib import Path

_repo_root = str(Path(__file__).resolve().parent.parent.parent)
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from scripts.build_tier0 import TIER0_MAPPINGS, build_tier0  # noqa: E402


def test_build_tier0_generates_all_static_files(tmp_path: Path) -> None:
    counts = build_tier0(out_dir=tmp_path)

    for _, dst_name in TIER0_MAPPINGS:
        out_file = tmp_path / dst_name
        assert out_file.exists(), f"Missing generated file {dst_name}"
        assert counts[dst_name] > 0
