pass                                                                                        
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[2]
OUT = (ROOT / os.environ["RESULT_DIR"]).resolve()
CACHE = ROOT / ".silnik-cache"
TEMP = Path(os.environ.get("RUNNER_TEMP", OUT / "robocze")) / "silnik"
SHA = "f517081a31b00217a3bfa303904247158997fcaa911bffe1385257aaec0a7519"
PINS = {
    "raylib": ("raysan5/raylib", "c1ab645ca298a2801097931d1079b10ff7eb9df8"),
    "box2d": ("erincatto/box2d", "8c661469c9507d3ad6fbd2fea3f1aa71669c2fe3"),
}
OPTIONS = {
    "raylib": ["-DBUILD_EXAMPLES=OFF", "-DBUILD_SHARED_LIBS=OFF",
               "-DPLATFORM=Desktop", "-DOPENGL_VERSION=3.3", "-DUSE_EXTERNAL_GLFW=OFF",
               "-DGLFW_BUILD_WAYLAND=OFF", "-DGLFW_BUILD_X11=ON"],
    "box2d": ["-DBUILD_SHARED_LIBS=OFF", "-DBOX2D_SAMPLES=OFF",
              "-DBOX2D_UNIT_TESTS=OFF", "-DBOX2D_BENCHMARKS=OFF", "-DBOX2D_DOCS=OFF",
              "-DBOX2D_PROFILE=OFF", "-DBOX2D_AVX2=OFF", "-DBOX2D_DISABLE_SIMD=OFF"],
}
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "wynik/klatki").mkdir(parents=True, exist_ok=True)
TEMP.mkdir(parents=True, exist_ok=True)


class StepFailed(Exception):
    pass


def record(name, command, code, elapsed, cwd):
    (OUT / f'{name}-polecenie.csv').write_text(
        f'cwd={cwd}\n{shlex.join(command)}\n', encoding="utf-8")
    (OUT / f'{name}-kod.csv').write_text(f'{code}\n', encoding="utf-8")
    (OUT / f'{name}-czas.csv').write_text(f'{elapsed:.6f}\n', encoding="utf-8")
    print(f'{name}: code {code}, {elapsed:.3f} s', flush=True)
    callback = globals().get('command_receipt')
    if callback:
        callback(name, command, code, elapsed, cwd)


def run(name, command, *, cwd=ROOT, seconds=60, stdout=None, env=None):
    command = [str(item) for item in command]
    output = stdout or OUT / f'{name}.csv'
    started = time.monotonic()
    with Path(output).open("wb") as out, (OUT / f'{name}-stderr.csv').open("wb") as err:
        try:
                                                                                 
                                                                          
            if os.environ.get('PETLA_DEADLINE'):
                remaining = float(os.environ['PETLA_DEADLINE']) - time.time()
                if remaining <= 0:
                    err.write(b'PETLA: limit czasu; korpus niepelny\n')
                    record(name, command, 124, time.monotonic() - started, cwd)
                    return 124
                seconds = min(seconds, remaining)
                                                                                                     
            if sys.argv[1] in ("prepare", "build", "probe", "display"):
                start_file = OUT / "start-unix.csv"
                remaining = 660 - (time.time() - float(start_file.read_text()))
                if remaining <= 0:
                    err.write(b"Wyczerpano 11 minut na przygotowanie i probe; zachowujemy wyniki.\n")
                    record(name, command, 124, time.monotonic() - started, cwd)
                    return 124
                seconds = min(seconds, max(1, int(remaining)))
                                                                                           
            executed = ["timeout", "--kill-after=5s", f'{seconds}s', *command]
            code = subprocess.run(
                executed,
                cwd=cwd, stdout=out, stderr=err, env=env).returncode
        except OSError as exc:
            err.write((str(exc) + "\n").encode("utf-8"))
            code = 127
    record(name, executed if "executed" in locals() else command,
           code, time.monotonic() - started, cwd)
    return code


def need(name, command, **kwargs):
    code = run(name, command, **kwargs)
    if code:
        raise StepFailed(f'Krok {name}: code {code}; szczegoly w {name}-stderr.csv')


def prepare():
    (OUT / "start-unix.csv").write_text(f'{time.time():.6f}\n', encoding="utf-8")
    (OUT / "metadane.json").write_text(json.dumps({
        "run_id": os.environ.get("GITHUB_RUN_ID"),
        "attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "commit": os.environ.get("GITHUB_SHA"), "pins": PINS, "options": OPTIONS,
        "duckling_sha256": SHA, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }, indent=2) + "\n", encoding="utf-8")
    sources = [ROOT / ".github/workflows/silnik.yml", *sorted((ROOT / "silnik").rglob("*"))]
    sources = [p for p in sources if p.is_file() and "__pycache__" not in p.parts]
    (OUT / "zrodla-sha256.csv").write_text("".join(
        f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(ROOT).as_posix()}\n'
        for p in sources), encoding="utf-8")
    snapshot = OUT / "zrodla"
    snapshot.mkdir(exist_ok=True)
    for p in sources:
        target = snapshot / p.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, target)
    need("sprawdziany", [sys.executable, "-B", "-m", "unittest", "discover",
                        "-s", "silnik/sprawdz", "-p", "test_sprawdz.py", "-v"], seconds=90)
    need("apt-update", ["sudo", "apt-get", "update"], seconds=120)
    need("apt-pakiety", ["sudo", "apt-get", "install", "-y", "--no-install-recommends",
        "build-essential", "cmake", "ninja-build", "pkg-config", "curl", "ca-certificates",
        "libasound2-dev", "libx11-dev", "libxrandr-dev", "libxi-dev", "libxcursor-dev",
        "libxinerama-dev", "libgl1-mesa-dev", "libglu1-mesa-dev", "libxext-dev",
        "libgl1-mesa-dri", "libglx-mesa0", "mesa-utils", "xvfb", "xauth", "ffmpeg"], seconds=150)
    for name, cmd in (("system", ["uname", "-a"]), ("cc-wersja", ["cc", "--version"]),
                      ("cmake-wersja", ["cmake", "--version"]),
                      ("ffmpeg-wersja", ["ffmpeg", "-version"])):
        need(name, cmd, seconds=10)
    download = TEMP / "pobranie"
    toolchain = TEMP / "toolchain"
    download.mkdir(exist_ok=True)
    toolchain.mkdir(exist_ok=True)
    asset = "duckling-dev-linux-x86_64.tar.gz"
    base = "https://github.com/ducktype-org/duckling/releases/download/dev-weekly/"
    if os.environ.get("ARCHIVE_CACHE_HIT") != "true":
        for file in (asset, asset + ".sha256"):
            need("pobranie-" + file, ["curl", "--fail", "--location", "--retry", "2",
                "--retry-max-time", "80", "--max-time", "60", base + file,
                "--output", download / file], seconds=100)
    else:
        (OUT / "archiwum-z-cache.csv").write_text(
            'Uzyto zachowanego archiwum; checksum sprawdzana ponownie.\n', encoding="utf-8")
    shutil.copy2(download / (asset + ".sha256"), OUT / (asset + ".sha256"))
    if (download / asset).stat().st_size != 81334394:
        raise StepFailed("ERROR ENV TOOLCHAIN: archive size differs from be929a1a")
    expected = OUT / "duckling-przypiete.sha256"
    expected.write_text(f'{SHA}  {asset}\n', encoding="utf-8")
    need("sha256-obliczone", ["sha256sum", asset], cwd=download)
                                                                                   
    need("sha256-przypiete", ["sha256sum", "--check", expected], cwd=download)
    need("sha256-sidecar-przypiete", ["sha256sum", "--check", asset + ".sha256"], cwd=download)
    need("archiwum-spis", ["tar", "-tzvf", download / asset])
    need("rozpakowanie", ["tar", "-xzf", download / asset, "-C", toolchain])
    tools = {}
    for name in ("duckc", "duck"):
        found = [p for p in toolchain.rglob(name) if p.is_file() and os.access(p, os.X_OK)]
        if len(found) != 1:
            raise StepFailed(f'Oczekiwano jednego {name}, znaleziono: {found}')
        tools[name] = str(found[0])
    (OUT / "narzedzia.json").write_text(json.dumps(tools, indent=2) + "\n", encoding="utf-8")
    for name in ("duckc", "duck"):
        need(name + "-pomoc", [tools[name], "--help"], seconds=15)
        need(name + "-wersja", [tools[name], "--version"], seconds=15)
    need("duckc-pakiet-pomoc", [tools["duckc"], "compile_package", "--help"], seconds=15)


def build():
    CACHE.mkdir(exist_ok=True)
    for name, (repo, commit) in PINS.items():
        prefix = CACHE / name
        library = prefix / "lib" / f'lib{name}.a'
        if library.is_file() and (prefix / "include").is_dir():
            (OUT / f'{name}-cache.csv').write_text("HIT: " + str(library) + "\n", encoding="utf-8")
            continue
        source = TEMP / name
        archive = TEMP / f'{name}-{commit}.tar.gz'
        source.mkdir(exist_ok=True)
        need(name + "-pobranie", ["curl", "--fail", "--location", "--retry", "2",
            "--max-time", "45", f'https://codeload.github.com/{repo}/tar.gz/{commit}',
            "--output", archive], seconds=100)
        need(name + "-zrodla", ["tar", "-xzf", archive, "--strip-components=1", "-C", source])
        build_dir = TEMP / (name + "-build")
        need(name + "-cmake", ["cmake", "-S", source, "-B", build_dir, "-G", "Ninja",
            "-DCMAKE_BUILD_TYPE=Release", "-DCMAKE_C_FLAGS=-fno-fast-math -ffp-contract=off",
            "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON", "-DCMAKE_INSTALL_LIBDIR=lib",
            f'-DCMAKE_INSTALL_PREFIX={prefix}', *OPTIONS[name]], seconds=60)
        need(name + "-budowa", ["cmake", "--build", build_dir, "--parallel", "2"], seconds=150)
        need(name + "-lokalne-pliki", ["cmake", "--install", build_dir], seconds=30)
        if not library.is_file():
            raise StepFailed(f'Brak zbudowanej biblioteki: {library}')
        evidence = prefix / "dowody"
        evidence.mkdir(exist_ok=True)
        for file in ("CMakeCache.csv", "compile_commands.json", "install_manifest.csv"):
            p = build_dir / file
            if p.is_file():
                shutil.copy2(p, evidence / file)
    for name in PINS:
        prefix = CACHE / name
        shutil.copytree(prefix / "dowody", OUT / (name + "-build"), dirs_exist_ok=True)
        need(name + "-biblioteka-sha256", ["sha256sum", prefix / "lib" / f'lib{name}.a'])


def probe():
                                                                                          
    if (OUT / "sprawdziany-kod.csv").read_text().strip() != "0":
        raise StepFailed("Sprawdziany nie przeszly; proba zabroniona")
    box2d = CACHE / "box2d/lib/libbox2d.a"
    raylib = CACHE / "raylib/lib/libraylib.a"
    reference = TEMP / "wzorzec"
    need("wzorzec-kompilacja", ["cc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
        "-fno-fast-math", "-ffp-contract=off", "-I" + str(CACHE / "box2d/include"),
        ROOT / "silnik/c/wzorzec.c", box2d, "-lm", "-o", reference], seconds=30)
    need("wzorzec", [reference], stdout=OUT / "wynik/wzorzec.csv", seconds=15)
    duckc = json.loads((OUT / "narzedzia.json").read_text())["duckc"]
    artifacts = TEMP / "duck-build"
    artifacts.mkdir(exist_ok=True)
                                                                            
    links = [str(box2d), str(raylib), "-lGL", "-lX11", "-lm", "-lpthread", "-ldl", "-lrt"]
    need("duckling-kompilacja", [duckc, "compile_package", ROOT / "silnik/proba/proba.dk",
        "-a", artifacts, "-o", "proba", "-O", "0", "--additional-link-options=" + ",".join(links)],
        seconds=150)
    found = []
    for p in artifacts.rglob("*"):
        if p.is_file() and os.access(p, os.X_OK):
            with p.open("rb") as stream:
                if stream.read(4) == b"\x7fELF":
                    found.append(p)
    (OUT / "pliki-natywne.csv").write_text("".join(str(p) + "\n" for p in found), encoding="utf-8")
    if len(found) != 1:
        raise StepFailed(f'Oczekiwano jednego wykonywalnego ELF, znaleziono {len(found)}')
    shutil.copy2(reference, OUT / "wzorzec-bin")
    shutil.copy2(found[0], OUT / "duckling-bin")
    software = dict(os.environ, LIBGL_ALWAYS_SOFTWARE="1", GALLIUM_DRIVER="llvmpipe", LP_NUM_THREADS="2")
    need("xvfb", ["xvfb-run", "--auto-servernum", "--error-file=" + str(OUT / "xvfb-server.csv"),
        "--server-args=-screen 0 800x600x24 -nolisten tcp", sys.executable, "-B", __file__,
        "display", found[0]], seconds=120, env=software)


def display(binary):
                                                                             
    renderer_code = run("opengl-renderer", ["glxinfo", "-B"], seconds=15)
    print((OUT / "opengl-renderer.csv").read_text(encoding="utf-8", errors="replace"), flush=True)
    native_code = run("duckling", [binary], cwd=OUT, stdout=OUT / "wynik/duckling.csv", seconds=90)
    return 1 if renderer_code or native_code else 0


def check():
    code_file = OUT / "duckling-kod.csv"
    code = int(code_file.read_text()) if code_file.is_file() else 125
    checker_code = run("sprawdzenie", [sys.executable, "-B", ROOT / "silnik/sprawdz/sprawdz.py",
        "--wzorzec", OUT / "wynik/wzorzec.csv", "--duckling", OUT / "wynik/duckling.csv",
        "--png", OUT / "wynik", "--kod-wyjscia", code], seconds=90)
    report = OUT / "wynik/SPRAWDZENIE.md"
    if report.is_file():
        shutil.copy2(report, OUT / "SPRAWDZENIE.md")
    else:
        (OUT / "SPRAWDZENIE.md").write_text(
            '# BLAD\n\nE212f3b75584c Ecd5b158f21b7 Eef324d26415d Ef2e01d0058c9; E91df6be85f3d E50e721e49c01 E3187caf3b3a3-stderr.csv.\n',
            encoding="utf-8")
        checker_code = 1
                                                                            
    film_code = run("film", ["ffmpeg", "-y", "-framerate", "30", "-pattern_type", "glob",
        "-i", OUT / "wynik/klatki/klatka-*.png", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", OUT / "proba.mp4"], seconds=45)
    if film_code == 0:
        film_code = run("film-parametry", ["ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height,r_frame_rate,nb_frames,duration", "-of", "json",
            OUT / "proba.mp4"], seconds=10)
    return 1 if checker_code or film_code else 0


def summary():
    (OUT / "akcje-cache.json").write_text(json.dumps({
        "restore_outcome": os.environ.get("CACHE_RESTORE_OUTCOME"),
        "save_outcome": os.environ.get("CACHE_SAVE_OUTCOME"),
        "hit": os.environ.get("CACHE_HIT"), "key": os.environ.get("CACHE_PRIMARY_KEY"),
    }, indent=2) + "\n", encoding="utf-8")
    required = ("sprawdziany", "apt-update", "apt-pakiety", "sha256-przypiete", "sha256-sidecar-przypiete",
        "duckc-pomoc", "duck-pomoc", "duckc-wersja", "duck-wersja", "duckc-pakiet-pomoc",
        "raylib-biblioteka-sha256", "box2d-biblioteka-sha256", "wzorzec-kompilacja", "wzorzec",
        "duckling-kompilacja", "opengl-renderer", "duckling", "xvfb", "sprawdzenie", "film", "film-parametry")
    lines = ["# Proba silnika", "", "| Krok | Kod | Sekundy |", "|---|---:|---:|"]
    failed = False
    names = sorted(set(required) | {p.name[:-8] for p in OUT.glob("*-kod.csv") if p.name != "wynik-kod.csv"})
    for name in names:
        p = OUT / f'{name}-kod.csv'
        code = p.read_text().strip() if p.is_file() else 'MISSING / POMINIETO'
        elapsed = OUT / f'{name}-czas.csv'
        seconds = elapsed.read_text().strip() if elapsed.is_file() else "-"
        failed |= code != "0"
        lines.append(f'| {name} | {code} | {seconds} |')
    for name in ("PREPARE", "BUILD", "PROBE", "CHECK", "CACHE_RESTORE", "CACHE_SAVE"):
        outcome = os.environ.get(name + "_OUTCOME", 'MISSING')
                                                                                     
        acceptable = outcome == "success" or (name == "CACHE_SAVE" and outcome == "skipped")
        failed |= not acceptable
        lines.append(f'| GitHub: {name.lower()} | {outcome} | - |')
    lines += ["", '125 = E1310ca2c8932 Ecd5b158f21b7 E59e1c27d6e4f Ec4d962c1f187; 124 = E55ea09e5715d Ea3fe81deb86e Ea11c79130f7c.',
              'E0c785ba70ffd, E5d94b00cd37c E6d0a271d4a15 Ede7d1b721a1e E07976e4fe9c5 E4cf6829aa937 E631f494748f8 E4fc2a55cab31. E7e41e1e0e590 Efe8d567e9001 E70f0b8e6e134 E0b8b64a241a2 (E80f410583d53/Edfbb889cf19b).',
              'E8737e8daa784, E4a61c4b97aae, Ea36c0cd8ffd0 E6717ba77b68b Ede7d1b721a1e Eff8e077840e1 MP4 Efb92a74d77b5 Eb5ff149a858d E5a55cf01f822.',
              "", 'RESULT: ' + ("BLAD" if failed else "OK"), ""]
    text = "\n".join(lines)
    (OUT / "podsumowanie.md").write_text(text, encoding="utf-8")
    (OUT / "wynik-kod.csv").write_text("1\n" if failed else "0\n", encoding="utf-8")
    print(text)
    return 0                                                         


def main():
    stage = sys.argv[1]
    started = time.monotonic()
    code = 1
    try:
        if stage == "display":
            code = display(sys.argv[2])
        else:
            code = {"prepare": prepare, "build": build, "probe": probe,
                    "check": check, "summary": summary}[stage]() or 0
    except Exception:
        traceback.print_exc()
    finally:
        (OUT / f'etap-{stage}-kod.csv').write_text(f'{code}\n', encoding="utf-8")
        (OUT / f'etap-{stage}-czas.csv').write_text(f'{time.monotonic() - started:.6f}\n', encoding="utf-8")
    return code


if __name__ == "__main__":
    sys.exit(main())
