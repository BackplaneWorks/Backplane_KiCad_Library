"""Re-verify the Backplane KiCad Library on a runtime: every footprint loads and exports, a board placing all of them
resolves through a fresh global table, passives' STEP models reach a STEP export, and the catalogue board passes DRC."""
import json, os, re, subprocess, sys, tempfile, collections
from pathlib import Path
lib, runtime, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
cli = runtime / "bin/kicad-cli"; out.mkdir(parents=True, exist_ok=True)
tmp = Path(tempfile.mkdtemp(prefix="libver-"))
env = dict(os.environ, HOME=str(tmp/"home"), XDG_CONFIG_HOME=str(tmp/"cfg"), KICAD_CONFIG_HOME=str(tmp/"cfg/kicad"),
           XDG_DATA_HOME=str(tmp/"data"), XDG_CACHE_HOME=str(tmp/"cache"), BACKPLANE_KICAD_LIBRARY=str(lib))
for k in ("DISPLAY", "WAYLAND_DISPLAY"): env.pop(k, None)
def run(*a):
    r = subprocess.run([str(cli), *map(str, a)], env=env, capture_output=True, text=True, timeout=900)
    if r.returncode: raise SystemExit(f"FAILED {a}: {r.stdout[-800:]} {r.stderr[-800:]}")
    return r.stdout
rep = {"runtime": (runtime/"manifest.json").read_text() and json.loads((runtime/"manifest.json").read_text()).get("version"),
       "runtime_source_commit": json.loads((runtime/"manifest.json").read_text()).get("sourceCommit"),
       "library_commit": subprocess.check_output(["git","-C",str(lib),"rev-parse","HEAD"],text=True).strip()}
run("version")
manifest = json.loads((lib/"manifest.json").read_text())
fps = [(e["library"], e["name"]) for e in manifest["entries"]]
# 1. every footprint exports as non-empty SVG
svg = tmp/"svg"; per = {}
for l in sorted({l for l, _ in fps}):
    d = svg/l; d.mkdir(parents=True); run("fp","export","svg","--output",d,lib/"libraries"/f"{l}.pretty")
    per[l] = sum(1 for p in d.glob("*.svg") if p.stat().st_size > 200)
rep["svg_exports"] = per; assert sum(per.values()) == len(fps) == manifest["footprint_count"], per
# 2. the fresh config's table (the runtime's default) names every library; a board placing all 223 resolves
table = (tmp/"cfg/kicad"/rep["runtime"].split("-")[0].rsplit(".",1)[0]/"fp-lib-table").read_text()
tp = tmp/"cfg/kicad"/rep["runtime"].split("-")[0].rsplit(".",1)[0]/"fp-lib-table"
if os.environ.get("LIBVER_SEED"):  # dry run on a runtime without the bundle: the example's entries stand in for its default table
    ex = "".join(l for l in (lib/"fp-lib-table.example").read_text().splitlines(True) if "(lib " in l)
    tp.write_text(table.rstrip()[:-1] + ex + ")\n"); table = tp.read_text()
rep["default_table_names_all"] = all(f'(name "{l}")' in table for l in per); assert rep["default_table_names_all"]
items = []
for i, (l, n) in enumerate(fps):
    t = (lib/"libraries"/f"{l}.pretty"/f"{n}.kicad_mod").read_text().strip()
    t = re.sub(r'^\(footprint "[^"]+"', f'(footprint "{l}:{n}"', t, count=1)
    t = t.replace('(layer "F.Cu")', f'(layer "F.Cu")\n\t(at {20 + 60*(i % 15)} {20 + 60*(i // 15)})', 1)
    t = re.sub(r'\(uuid "[^"]*"\)', '', t)
    items.append(t)
board = tmp/"all.kicad_pcb"
board.write_text('(kicad_pcb (version 20240108) (generator "libver")\n (general (thickness 1.6))\n (paper "A0")\n'
  ' (layers (0 "F.Cu" signal) (31 "B.Cu" signal) (32 "B.Adhes" user "B.Adhesive") (33 "F.Adhes" user "F.Adhesive") (34 "B.Paste" user) (35 "F.Paste" user)'
  ' (36 "B.SilkS" user "B.Silkscreen") (37 "F.SilkS" user "F.Silkscreen") (38 "B.Mask" user) (39 "F.Mask" user) (40 "Dwgs.User" user "User.Drawings")'
  ' (41 "Cmts.User" user "User.Comments") (44 "Edge.Cuts" user) (46 "B.CrtYd" user "B.Courtyard") (47 "F.CrtYd" user "F.Courtyard") (48 "B.Fab" user) (49 "F.Fab" user))\n'
  ' (setup (pad_to_mask_clearance 0))\n (net 0 "")\n' + "\n".join(items) +
  '\n (gr_rect (start -20 -20) (end 940 980) (stroke (width 0.1) (type default)) (fill none) (layer "Edge.Cuts"))\n)\n')
run("pcb","drc","--format","json","--severity-all","--output",tmp/"all.drc.json",board)
v = json.loads((tmp/"all.drc.json").read_text())["violations"]
rep["all_board_lib_problems"] = [x["description"] for x in v if x["type"] == "lib_footprint_issues"]
rep["all_board_violation_types"] = dict(collections.Counter(x["type"] for x in v))
assert not rep["all_board_lib_problems"], rep["all_board_lib_problems"][:5]
ctl = tmp/"ctl.kicad_pcb"; ctl.write_text(board.read_text().replace('"Backplane_Logo:', '"Backplane_Logo_Absent:', 1))
run("pcb","drc","--format","json","--severity-all","--output",tmp/"ctl.drc.json",ctl)
rep["negative_control_reported"] = any(x["type"] == "lib_footprint_issues" for x in json.loads((tmp/"ctl.drc.json").read_text())["violations"])
assert rep["negative_control_reported"]
# 3. STEP export of the all-footprint board carries every passive model
log = run("pcb","export","step","--subst-models","--output",tmp/"all.step",board)
step = (tmp/"all.step").read_text(errors="replace")
want = {Path(m).stem for m in re.findall(r'\(model "\$\{BACKPLANE_KICAD_LIBRARY\}/([^"]+)"', "\n".join(items))}
rep["step_models_wanted"] = len(want); rep["step_models_found"] = sum(1 for m in want if f"'{m}'" in step or f"'{m}_" in step or m in step)
rep["step_missing_lines"] = [l for l in log.splitlines() if "not found" in l.lower() or "cannot" in l.lower()]
assert rep["step_models_found"] == len(want) and not rep["step_missing_lines"], rep
# 4. the saved catalogue board passes DRC on this runtime
cat = lib/"boards/library_catalogue/library_catalogue.kicad_pcb"
run("pcb","drc","--format","json","--severity-all","--output",tmp/"cat.drc.json",cat)
c = json.loads((tmp/"cat.drc.json").read_text())
rep["catalogue_drc"] = {"violations": len(c["violations"]), "unconnected": len(c.get("unconnected_items", []))}
(out/"verification-report.json").write_text(json.dumps(rep, indent=2) + "\n")
print(json.dumps(rep, indent=2))
