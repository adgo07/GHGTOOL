"""构建真实wheel/sdist并核验现有受控模板字节；隔离副本，不打包用户目录。"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tarfile
from zipfile import ZipFile


def _verify_distribution_templates(project_root: Path, output_root: Path, runtime_root: Path) -> dict:
    project_root, output_root = project_root.resolve(), output_root.resolve()
    runtime_root = runtime_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    source = runtime_root / "source"
    source.mkdir()
    for name in ("apps", "packages", "resources"):
        shutil.copytree(project_root / name, source / name,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copy2(project_root / "pyproject.toml", source / "pyproject.toml")
    archives = output_root / "archives"
    archives.mkdir()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    commands = []
    def run(args, cwd, log_name):
        commands.append(args)
        result = subprocess.run(args, cwd=cwd, env=env, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (output_root / log_name).write_text(result.stdout, encoding="utf-8")
        if result.returncode:
            raise RuntimeError(f"{log_name} exit={result.returncode}\n{result.stdout[-4000:]}")
    run([sys.executable, "-B", "-c",
         "from setuptools.build_meta import build_wheel,build_sdist;"
         f"build_wheel({str(archives)!r});build_sdist({str(archives)!r})"],
        source, "build.log")
    wheel, = archives.glob("*.whl")
    sdist, = archives.glob("*.tar.gz")
    expected = {p.relative_to(project_root).as_posix(): p.read_bytes()
                for p in (project_root / "resources/excel_templates").glob("*.xlsx")}
    if not expected:
        raise RuntimeError("no controlled Excel templates")
    with ZipFile(wheel) as z, tarfile.open(sdist) as tar:
        names = tar.getnames()
        for name in (*z.namelist(), *names):
            assert Path(name).name.lower() not in {'user.sqlite', 'projects.sqlite', 'records.sqlite'}, name
            assert '计算表' not in Path(name).parts, name
        for name, raw in expected.items():
            assert z.read(name) == raw, ("wheel template drift", name)
            matches = [n for n in names if n.endswith("/" + name)]
            assert len(matches) == 1, ("sdist missing/duplicate template", name)
            assert tar.extractfile(matches[0]).read() == raw, ("sdist template drift", name)
    installed = runtime_root / "installed"
    run([sys.executable, "-B", "-m", "pip", "install", "--no-deps", "--no-index",
         "--no-compile", "--target", str(installed), str(wheel)], output_root, "install.log")
    expected_hashes = {name: sha256(raw).hexdigest() for name, raw in expected.items()}
    probe = (
        "import sys,json,hashlib;from pathlib import Path;"
        f"sys.path.insert(0,{str(installed)!r});import resources;"
        f"installed=Path({str(installed)!r}).resolve();actual_module=Path(resources.__file__).resolve();"
        "print(json.dumps({'resource_file':str(actual_module),'installed_root':str(installed)}));"
        "assert actual_module.is_relative_to(installed), (str(actual_module),str(installed));"
        "assert sys.flags.isolated and sys.flags.no_site, 'installed probe must ignore site and environment';"
        "from importlib.resources import files;"
        f"expected=json.loads({json.dumps(expected_hashes)!r});"
        "actual={name:hashlib.sha256(files('resources').joinpath(name.removeprefix('resources/')).read_bytes()).hexdigest() for name in expected};"
        "assert actual==expected, (actual,expected);print(json.dumps(actual))"
    )
    run([sys.executable, "-I", "-S", "-B", "-c", probe], output_root, "installed-resources.log")
    result = {"templates": expected_hashes, "wheel_sha256": sha256(wheel.read_bytes()).hexdigest(),
              "sdist_sha256": sha256(sdist.read_bytes()).hexdigest(),
              "wheel_sdist_and_installed_resources_match": True,
              "no_user_databases_or_reference_directory": True, "commands": commands}
    (output_root / "proof.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def verify_distribution_templates(project_root: Path, output_root: Path) -> dict:
    # 运行副本仅存活于本次验证，不进入后续仓内生产源码扫描。
    with tempfile.TemporaryDirectory(prefix="qz-distribution-") as runtime:
        return _verify_distribution_templates(project_root, output_root, Path(runtime))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    proof = verify_distribution_templates(Path(__file__).resolve().parents[1], args.output_dir)
    print(f"distribution-templates: PASS ({len(proof['templates'])} actual templates; wheel, sdist, installed bytes)")
