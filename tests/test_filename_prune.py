import os
from pathlib import Path

# ensure required env vars for config when importing modules
os.environ.update({
    "DISCORD_TOKEN": "dummy",
    "GUILD_ID": "123",
    "TARGET_CHANNELS": "123",
    "TEST_MODE": "true",
})

from cleanup import sanitize_filename, prune_archive

def test_sanitize_filename():
    cases = {
        "nice.png": "nice.png",
        "../evil.jpg": "evil.jpg",
        "weird name (1).gif": "weird_name__1_.gif",
        "": "attachment",
    }
    for inp, expected in cases.items():
        out = sanitize_filename(inp)
        assert out == expected


def test_prune_archive(tmp_path):
    base = tmp_path / "archive"
    base.mkdir()
    # create files with sizes 100, 200, 300 bytes
    sizes = [100, 200, 300]
    files = []
    for i, s in enumerate(sizes):
        p = base / f"f{i}.bin"
        p.write_bytes(b"x" * s)
        files.append(p)

    total = sum(sizes)
    # set max to total - 150 so it must delete oldest files until under limit
    max_bytes = total - 150
    freed = prune_archive(base, max_bytes)
    assert freed >= 100
    remaining = sum(p.stat().st_size for p in base.glob("**/*") if p.is_file())
    assert remaining <= max_bytes
