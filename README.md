# Duckling Box2D port

A work in progress port of Box2D 3.1.1 to the Duckling language, with numerical physics comparisons and PNG comparison tests. The original C reference sources are included in `silnik/port/umowa-n/oryginal.tar.gz`. Both the reference and port use the MIT license.

## Portable checks

Run `python3 tools/check.py physics` and `python3 tools/check.py image`. Python 3.12 or newer is recommended. Each test module runs separately. The exit status is nonzero if any check fails. Results contain numerical counts, exit codes and differences; temporary diagnostic logs are not publication artifacts.

## Native comparison

On Linux, extract the included reference archive into a local directory and run:

```sh
mkdir -p reference
tar -xzf silnik/port/umowa-n/oryginal.tar.gz -C reference
python3 -B silnik/port/18a-run.py --box2d "$PWD/reference" --archive "$DUCKLING_ARCHIVE" --build "$PWD/build18a" --out "$PWD/results18a"
python3 tools/numbers.py results18a public-results.json
```

The pinned compiler archive SHA256 is `806f8a182643c4913c86a20f525a359098dabe80380d777a37feefd288058805`. The compiler archive is supplied separately. The native comparison requires GCC, gcov and the pinned Linux Duckling compiler. It covers 96 DIRECT cases, 96 PUBLIC cases, 821 guards and 24 parser pairs, plus additional frozen cases. Run from a Linux filesystem rather than a mounted Windows directory.

## CI

`port.yml` runs portable physics checks. `silnik.yml` runs PNG decoder and image comparator checks. `port18.yml` runs the native comparison when manually given a public compiler archive URL. Only numerical result files are uploaded. No repository secret is required. Full rendered scene comparison requires a separate graphics runtime and is not enabled by the portable image workflow.

## Known open checks

- `silnik/port/test_solver_boundaries.py`: the contact mutation count is 203 while the check requires 208; this failure remains enabled.

## Dane i kod

Port jest w toku. Katalog zawiera kod biblioteki, sprawdziany i dane fizyki. Polecenia powyzej uruchamiaja sprawdziany osobno oraz porownanie z oryginalem. Archiwum kompilatora trzeba dostarczyc osobno. Wynik dodatni sprawdzianow przenosnych nie oznacza zgodnosci wszystkich scen fizyki i obrazu.
