# Sentaurus Process Command Index

Primary source: a locally extracted, licensed SProcess manual under `references/sprocess-user-guide/`.

Use this as a quick entry point, then search or open the listed chunks for syntax details. The public repository does not include proprietary manual text; generate these chunks locally from documentation you are allowed to use.

## Core `.cmd` Topics

- command-file syntax and Tcl input: `sprocess-ug-007-pages-0049-0056.md`
- materials, aliases, and regionwise parameters: `sprocess-ug-007-pages-0049-0056.md`, `sprocess-ug-008-pages-0057-0064.md`
- coordinate systems and wafer orientation: `sprocess-ug-008-pages-0057-0064.md`, `sprocess-ug-009-pages-0065-0072.md`, `sprocess-ug-010-pages-0073-0080.md`
- defining initial structures with `line`, `region`, and `init`: `sprocess-ug-009-pages-0065-0072.md`, `sprocess-ug-010-pages-0073-0080.md`
- saving structures and device-simulation output: `sprocess-ug-010-pages-0073-0080.md`, `sprocess-ug-011-pages-0081-0088.md`
- ion implantation overview and examples: `sprocess-ug-011-pages-0081-0088.md` through `sprocess-ug-014-pages-0105-0112.md`
- meshing and remeshing topics: search `refinebox`, `mgoals`, `grid`, and `remesh` under `references/sprocess-user-guide/`

## Appendix Command Entries

- `contact`: `sprocess-ug-118-pages-0937-0944.md`
- `deposit`: `sprocess-ug-119-pages-0945-0952.md`, `sprocess-ug-120-pages-0953-0960.md`
- `diffuse`: `sprocess-ug-120-pages-0953-0960.md`, `sprocess-ug-121-pages-0961-0968.md`
- `etch`: `sprocess-ug-122-pages-0969-0976.md`, `sprocess-ug-123-pages-0977-0984.md`
- `grid`: `sprocess-ug-125-pages-0993-1000.md` through `sprocess-ug-128-pages-1017-1024.md`
- `implant`: `sprocess-ug-129-pages-1025-1032.md` through `sprocess-ug-131-pages-1041-1048.md`
- `init`: `sprocess-ug-131-pages-1041-1048.md` through `sprocess-ug-134-pages-1065-1072.md`
- `line`: `sprocess-ug-135-pages-1073-1080.md`, `sprocess-ug-136-pages-1081-1088.md`
- `mask`: `sprocess-ug-137-pages-1089-1096.md`, `sprocess-ug-138-pages-1097-1104.md`
- `mgoals`: `sprocess-ug-139-pages-1105-1112.md`
- `photo`: `sprocess-ug-142-pages-1129-1136.md`, `sprocess-ug-143-pages-1137-1144.md`
- `refinebox`: `sprocess-ug-148-pages-1177-1184.md` through `sprocess-ug-153-pages-1217-1224.md`
- `region`: `sprocess-ug-153-pages-1217-1224.md`, `sprocess-ug-154-pages-1225-1232.md`
- `strip`: `sprocess-ug-160-pages-1273-1280.md`
- `struct`: `sprocess-ug-160-pages-1273-1280.md`, `sprocess-ug-161-pages-1281-1288.md`

## Useful Searches

```powershell
rg -n "implant <species>|implant .*dose|tilt|rotation" references\sprocess-user-guide
rg -n "deposit .*thickness|etch .*thickness|photo|mask name" references\sprocess-user-guide
rg -n "line .*loc|region .*substrate|init .*wafer|struct tdr" references\sprocess-user-guide
rg -n "refinebox|mgoals|grid remesh|NetActive" references\sprocess-user-guide
```
