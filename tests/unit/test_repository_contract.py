import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_public_repository_contains_required_contract_files():
    for name in (
        "pyproject.toml", "LICENSE", "SECURITY.md", "CONTRIBUTING.md",
        "docs/architecture/public-private-boundary.md", ".github/workflows/quality.yml",
    ):
        assert (ROOT / name).is_file(), name


def test_each_readme_links_to_the_other_language():
    for source, target in (("README.md", "README.zh-CN.md"), ("README.zh-CN.md", "README.md")):
        assert f"({target})" in (ROOT / source).read_text(encoding="utf-8")


def test_public_tree_excludes_local_configuration_and_private_assets():
    names = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT
    ).decode().split("\0")
    for name in filter(None, names):
        path = Path(name.lower())
        assert not {"private", ".venv", "credentials"}.intersection(path.parts), name
        assert not path.name.startswith(".env"), name
        assert path.suffix not in {".pem", ".key", ".p12"}, name
