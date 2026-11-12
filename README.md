# PolyXRD Graphite

<div align="center">
  <img src="resources/logo-horizontal.png" alt="PolyXRD Graphite" width="420">
</div>

A small XRD analysis tool for graphite materials — from the C(002) peak position it gives the **degree of graphitization g** (expressed via the interlayer spacing d002)
and the **stacking thickness Lc**; from **(110)** (preferred, 2θ ≈ 77.5°, requires scanning to 72–82°) or **(100)**
(backup, 2θ ≈ 42.4°, d ≈ 0.213 nm) it gives the **crystallite size La**; it also corrects 2θ with a spiked-in Si internal standard,
and back-calculates the Caglioti parameters from the full-angle spectrum of the Si standard to subtract instrumental broadening.

Two release forms are provided: the **Setup installer** (public release, with registration mechanism) and the
**single-file internal evaluation build** (no installation, for internal use, no registration mechanism).

> Current version **v1.2.0** · UI supports **Simplified Chinese / English / Japanese**,
> switchable at runtime from the **Language** menu in the menu bar (the choice is stored locally).
>
> Current version **v1.2.0** · UI available in **Simplified Chinese / English / Japanese**,
> switchable at runtime from the **Language** menu (top-right); the choice is remembered locally.
>
> Version **v1.2.0** · UI supports **Simplified Chinese / English / Japanese**,
> switchable at runtime from the **Language** menu (settings are saved locally).

Member of the PolyXRD family: [PolyXRD](https://github.com/PolyXRD) (data analysis) ·
PolyXRD-Converter (format conversion) · PolyXRD-SynthPattern (pattern synthesis) ·
PolyXRD-RutAna (TiO₂ polymorph ratio) · **Graphite (degree of graphitization / Lc / La)**

## Features

**① Calculation page**
- Sample information (sample name / client / operator / remarks) is written directly into the report
- Target and wavelength: Cu/Co/Mo/Fe/Cr Kα1, Kα2, Kα average, or a custom λ
  (for Cu Kα1 both 1.5405929 CODATA and 1.54056 traditional values are provided, to reproduce existing reports)
- Peak input: 2θ and FWHM of C(002), measured and standard 2θ of the Si(111) internal standard, La peak ((110) / (100) / do not calculate)
- Result cards: g, Lc, La, d002; the detail table keeps a per-item record (including Δ2θ, per-peak instrumental broadening, pure broadening β)
- Criterion hints: g out of range (<0 or >100%), La peak position deviating from theory by >0.5°, missing instrumental broadening, etc.
- Report export: TXT (with formulae, K values, broadening model and hints) / CSV (UTF-8 BOM, opens directly in Excel)

**② Pattern and peak finding**
- Reads two-column text patterns (`.txt` / `.xy` / `.dat` / `.csv` / `.asc` / `.prn`, automatically skipping comments and headers)
- Automatic peak finding + per-peak pseudo-Voigt fitting (peak position, FWHM, peak height, relative intensity, η, R²)
- **Peak-angle annotation**: each identified peak shows its fitted 2θ at the peak top (e.g. `26.417°`), with a leader line pointing to the peak top;
  labels auto-avoid collisions (directly above → stepped lift → horizontal shift), never covering the curve, crossing the border or hiding theoretical peak-position labels.
  The "Annotate 2θ on plot" checkbox in the header turns it all off with one click, giving a clean unannotated pattern
- **Delete misidentified peaks**: select a row in the peak table and press the "Delete Selected Peak" button (or the Delete key);
  it is removed only from the peak table/pattern, leaving the raw pattern data unchanged; "Automatic peak finding" restores it
- **Centroid**: the peak table can toggle a `Centroid 2θ` column (centre-of-gravity method: after background subtraction, the intensity-weighted mean angle of the whole peak shape,
  the same definition as the Centroid column in the MDI Jade peak table); the pattern's horizontal axis marks each peak's centroid with small amber ticks,
  and the selected peak also gets a dashed line and a value. "Centroid → C(002)" / "Centroid → Si(111)" fill the centroid angle into the calculation page,
  kept side by side with the existing "Set as C(002) / Set as Si(111)" (fitted peak position)
- **Fixed-position fitting**: the graphite (110) intensity is often below 5% of (002) and is easily filtered out by the threshold; enter a 2θ to fit directionally at that
  position so even weak peaks get an FWHM
- One click fills the selected peak into the calculation page (C(002) / La peak / Si(111))
- Axis ticks use neat 1 / 2 / 2.5 / 5 ×10ᵏ steps, with label space reserved in pixels at the top, so even the tallest peak's label is not clipped

**③ Si standard / instrumental broadening**
- Reads a pure Si (or LaB₆) standard pattern, automatically identifies 111/220/311/400/331/422… by theoretical peak positions,
  and fits FWHM peak by peak
- Least-squares fit of Caglioti: FWHM² = U·tan²θ + V·tanθ + W, giving RMS and point count
- After fitting, automatically applied to the instrumental broadening at C(002) and (110), with no need to re-measure the standard

**④ Method and criteria**: formulae, workflow, FAQ and references (shown in the current language)

**⑤ Top-right tip icon (?)**: permanently at the right end of the tab bar; clicking it on any tab opens a one-page "Measurement and calculation essentials" —
two scan schemes (25–29.5° / 72–82° / standard 20–90°), the calculation chain (Bragg → Franklin → Scherer),
the instrumental broadening subtraction model, applicability limits (microstrain broadening not separated) and radiation wavelength. Same entry as "Help → Measurement and calculation essentials".

## Calculation formulae and parameter basis

| Item | Formula / value | Basis |
|---|---|---|
| Degree of graphitization g | g = (0.3440 − d002) / (0.3440 − 0.3354) × 100% | Franklin, *Acta Cryst.* 1951, 4, 253 (the original expresses it as c₀/2; this tool uniformly rewrites it as d002, the two being numerically equivalent) |
| d002 | d = λ / (2 sinθ), θ taken from the peak position **after internal-standard correction** | Bragg |
| 2θ correction | Δ2θ = 2θ(Si, standard) − 2θ(Si, measured), added equally to the C(002) and La peaks | Internal standard method |
| Lc | Lc = 0.89 λ / (β cosθ) | Iwashita et al., *Carbon* 2004, 42, 701 (standard XRD procedure for carbon materials) |
| La | La = 1.84 λ / (β cosθ), (110) preferred | Same as above; Warren, *Phys. Rev.* 1941, 59, 693 (hk band) |
| Instrumental broadening | Gaussian: β = √(βobs² − βinst²); Lorentzian: β = βobs − βinst | Choose one; the same batch of samples must be consistent and noted in the report |
| Unit of β | Input in °, converted to radians internally by Scherrer | — |
| Peak centroid (Centroid) | G = Σ(Iᵢ − bᵢ)·2θᵢ / Σ(Iᵢ − bᵢ), bᵢ is the linear background | NBS Technical Note 600, Section 5 (Pike & Wilson); *Polycrystalline X-ray Diffraction Techniques and Applications*, Chapter 5, "Centre of Gravity Method"; Centroid column of the MDI Jade peak table |

**Why La must use (110)/(100)**: La reflects the in-plane domain size of graphite layers and requires hk0-type reflections. (002)
gives the layer-stacking direction (Lc) and cannot be used to compute La. The (110) peak at 72–82° has a high angle, so the same Δd corresponds to a
larger Δ2θ (higher resolution), and no other strong graphite peaks overlap in that range; the (100) peak at 42.4° is more intense,
but lies close to neighbouring three-dimensional reflections, so peak separation has larger error and it is only a backup.

**Why a Si internal standard must be added**: C(002) is near 26.5°; sample-loading height, surface defocus and transparency effects all
shift peak positions as a whole; these geometric errors are approximately the same for all peaks in the same pattern, so point-by-point subtraction with an internal standard is most effective.
A 0.01° peak-position error brings about a 0.15 percentage-point error in g, so the internal standard is not optional.

## Recommended measurement conditions

| Goal | Scan range | Step size | Dwell |
|---|---|---|---|
| C(002) → g, Lc | 24–30° | ≤ 0.02° | ≥ 1 s |
| (110) → La (preferred) | **72–82°** | ≤ 0.02° | ≥ 2 s (weak peak) |
| (100) → La (backup) | 40–45° | ≤ 0.02° | ≥ 1 s |
| Si standard (full angle) | 20–120° | Same as sample | Same as sample |

Sample preparation: mix about 10–20 wt% Si powder into the graphite, fill the holder, level and press lightly; prepare the Si standard separately,
with slits and scan parameters identical to the sample.

## Build

```bat
REM Internal evaluation build (no registration mechanism, status bar shows "Internal Evaluation Build", folder form)
build_exe.bat

REM Setup installer (with registration mechanism; requires Inno Setup 6)
build_installer.bat

REM For release, zip the internal evaluation build folder (GitHub Release asset)
7z a -tzip dist\PolyXRD-Graphite-v1.2.0-internal-win64.zip PolyXRD-Graphite-v1.2.0-internal
```

Artifacts:

- `dist\PolyXRD-Graphite-v1.2.0-internal\` (internal evaluation build, **folder** form, distributed as a whole directory)
- `dist\PolyXRD-Graphite-v1.2.0-internal-win64.zip` (same as above, for the Release asset)
- `dist\PolyXRD-Graphite-Setup-v1.2.0.exe` (installer)
- Optional single-file (portable build): `build_exe.bat onefile` → `dist\PolyXRD-Graphite-v1.2.0-internal.exe`

The internal evaluation build now defaults to **onedir (folder)**: the single-file version unpacks about 58 MB to
`%TEMP%\_MEIxxxx` on every launch; if that machine's `%TEMP%` is not writable (insufficient permissions, blocked by security software,
or TEMP pointing to a non-existent directory), it pops up `Error: Could not create temporary directory!`
and exits immediately; the folder version does not unpack, starts faster, and does not depend on `%TEMP%`.

The internal evaluation build is detected the same way as the rest of the family: `packaging\internal_eval.marker` is embedded at build time,
and `graphite_app._detect_variant()` checks whether that file exists.

## Registration code (installer)

The registration code is generated by the developer from the "organization/department name", validated offline with no machine code needed;
the same registration code can be used on multiple computers within the same organization:

```bash
python make_reg_code.py "XX University School of Materials Science and Engineering"          # generate
python make_reg_code.py --verify PXRD1-XXXX-...   # validate and echo the unit name
```

Format `PXRD1-XXXX-XXXX-...`, content is Base32(UTF8(unit name) + 0x00 + HMAC-SHA256[:8]).
The security level is offline obfuscation (the key is shipped with the software), suitable for the "copyright notice + self-service registration" scenario.

**Installer runtime behaviour** (`setup` variant, without `internal_eval.marker`):

- Unregistered: a copyright prompt appears once on every launch; after confirming, functionality is unrestricted (no feature lock, notice only);
- "Help → Enter Registration Code": after successful registration the far right of the status bar shows "Registered: <Organization/Department Name>";
- Registration status is stored in `%APPDATA%\PolyXRD\Registration\Graphite.json`, re-validated at startup,
  and any manually edited or forged file is treated as unregistered.

## Development and testing

```bash
python graphite_engine.py            # calculation engine self-check (including re-computation of documented examples)
python -m pytest tests -q            # unit tests (engine + trilingual + registration code)
python tools/smoke_gui.py            # GUI offscreen smoke test (no manual clicks)
python tools/make_assets.py          # regenerate icon / splash / logo
```

`tests/test_engine.py` pins the worked example from the Shimadzu application dataset AP_XRD-001 "Determination of the Degree of Graphitization":
Si(111) measured 28.4541° (standard 28.44135°) → C(002) 26.5584° corrected to 26.54565°,
d002 = 0.33551 nm, g ≈ 98.8% (98.8% when the wavelength uses the traditional value 1.54056, 98.7% when using CODATA
1.5405929; the difference comes entirely from the wavelength value).

## Version history

**v1.2.0** (2026-10-29)
- Added **peak centroid (Centroid)**: by the centre-of-gravity method G = Σ(I−b)·2θ/Σ(I−b), background subtraction uses the linear background from that peak's fit,
  with a window of ±min(4×FWHM, half the distance to the nearest neighbouring peak); the peak table gains a switchable `Centroid 2θ` column,
  the pattern's horizontal axis gains amber centroid ticks, and the selected peak shows a dashed line and a "Centroid xx°" label
- Added "Centroid → C(002)" / "Centroid → Si(111)" buttons: fill the centroid angle into the calculation page for the degree-of-graphitization calculation;
  the original "Set as C(002) / Set as La peak / Set as Si(111)" (fitted peak position) is kept, the two conventions compared side by side
- Calculation engine gains `peak_centroid()` / `peak_centroids()`, and `PeakFit` records the fitted background (bg_slope, bg_intercept)
- The method page gains a section "Two conventions of peak position — fitted peak position and centroid" (trilingual), explaining definition, source, Kα2 bias and applicability limits
- **Fix**: the single-file internal evaluation build reported `Could not create temporary directory!` on startup — the build now defaults to
  the onedir folder form (no longer unpacks to %TEMP%), and the single-file form is optional via `build_exe.bat onefile`

**v1.1.1** (2026-10-29)
- Peak annotation reworked in the pattern area: removed the small red peak-position dots, replaced by fitted 2θ angle labels hung at the peak top (leader line + rounded label),
  the selected peak's label is solid green; labels auto-avoid collisions and converge at the edges, so even the tallest peak is not clipped by the top border
- Added the "Annotate 2θ on plot" header checkbox (when off, the curve fills the canvas); the top-bar hint changed to "Label = identified peak 2θ; dashed line = theoretical peak position"
- Added "Delete Selected Peak" (with the Delete shortcut): misidentified peaks can be removed from the peak table and pattern, raw pattern data unchanged
- Theoretical peak-position dashed labels changed to `C(002) / C(100) / C(110)` with a light background to avoid confusion with grid lines
- Axis switched to neat ticks (1/2/2.5/5×10ᵏ), vertical-axis ticks right-aligned; splash-screen version number now read from source code

**v1.0.1** (2025-10)
- Internal evaluation build notice moved to the center of the status bar (bold red)

**v1.0.0** (2025-10)
- First release: g / Lc / La calculation, peak finding and pseudo-Voigt fitting, Si standard Caglioti, trilingual UI, registration mechanism

## Directory layout

```
graphite_engine.py     Calculation engine (Bragg / degree of graphitization / Scherrer / Caglioti / peak finding / report)
graphite_app.py        Main program (PySide6, single-file distribution)
i18n.py                Trilingual copy + method description page + tip page (measurement and calculation essentials)
registration.py        Family-wide registration mechanism
make_reg_code.py       Registration code generation (for developers)
resources/             app-icon.png/.ico, splash-screen.png, logo-horizontal.png
tools/                 make_assets.py, smoke_gui.py, build_assets.sh
packaging/             internal_eval.marker, installer.iss, ChineseSimplified.isl
tests/                 test_engine.py, test_i18n.py
```

## License

Dual license (academic / commercial); see [LICENSE](LICENSE) and [LICENSE-CN](LICENSE-CN).
The academic license is limited to non-commercial academic research and teaching; commercial use requires a separate written authorization.
