# Output Directory Structure Design

## Overview

The output directory structure is designed to balance two competing goals:
1. **Group related files together** - All operations on the same source material should be easily discoverable
2. **Prevent filename conflicts** - Different commands might create files with the same name

## Structure

```
output/<base-name>/<command>/
```

Where:
- `<base-name>` is derived from the input file name (without extension)
- `<command>` is the command name (`render`, `iterate`, `analyze`, `fix-pedal`)

## Design Rationale

### Use Cases Considered

1. **Multiple iterations on the same seed**
   - `iterate -i seed.json -o v1.json`
   - `iterate -i seed.json -o v2.json`
   - **Result**: Both go to `output/seed/iterate/` - grouped together ✓

2. **Analyze then iterate on the same MIDI**
   - `analyze -i song.mid -o analysis.json` → `output/song/analyze/analysis.json`
   - `iterate -i song.mid -o composition.json` → `output/song/iterate/composition.json`
   - **Result**: Both under `output/song/` - easy to find related files ✓

3. **Using analyze output as iterate input**
   - `analyze -i song.mid -o analysis.json` → `output/song/analyze/analysis.json`
   - `iterate -i output/song/analyze/analysis.json -o comp.json` → `output/song/iterate/comp.json`
   - **Result**: Detects original base name "song" from path, keeps files grouped ✓

4. **Multiple renders from the same JSON**
   - `render -i comp.json -o v1.mid` → `output/comp/render/v1.mid`
   - `render -i comp.json -o v2.mid` → `output/comp/render/v2.mid`
   - **Result**: Both grouped together ✓

5. **Filename conflicts between commands**
   - `analyze -i song.mid -o composition.json` → `output/song/analyze/composition.json`
   - `iterate -i song.mid -o composition.json` → `output/song/iterate/composition.json`
   - **Result**: No conflict - separated by command subdirectory ✓

### Alternative Structures Considered

#### Option 1: `output/<command>/<base-name>/` (Original)
- **Pros**: Clear command separation
- **Cons**: Related operations on same source are separated
- **Example**: `analyze -i song.mid` and `iterate -i song.mid` go to different top-level directories

#### Option 2: `output/<base-name>/` (No command separation)
- **Pros**: All files for a source together
- **Cons**: Filename conflicts between commands (both might create `composition.json`)
- **Example**: `analyze` and `iterate` both create `composition.json` in same directory

#### Option 3: `output/<base-name>/<command>/` (Chosen)
- **Pros**: 
  - Groups by source material (all operations on `song.mid` under `output/song/`)
  - Prevents filename conflicts (commands separated)
  - Maintains grouping when using outputs as inputs
- **Cons**: Slightly more nested structure
- **Example**: Best of both worlds - grouped but separated

## Implementation Details

### Base Name Detection

The `_derive_base_name_from_path()` function handles several cases:

1. **Standard input file**: `input/song.mid` → base name `"song"`

2. **File in output directory**: `output/song/analyze/analysis.json` → base name `"song"` (extracted from path structure)

3. **Absolute path**: `/absolute/path/file.json` → base name `"file"` (uses stem)

4. **Relative path outside output**: `../other/file.json` → base name `"file"` (uses stem)

### Path Resolution

- **Absolute paths**: Used as-is (user has explicit control)
- **Relative paths**: Resolved relative to `output/<base-name>/<command>/`
- **No path provided**: Uses default filename in the output directory

## Examples

### Example 1: Simple Iteration
```bash
./pianist iterate -i seed.json -o updated.json --render
```
Creates:
- `output/seed/iterate/updated.json`
- `output/seed/iterate/updated.json.gemini.txt` (if using -g/--gemini)
- `output/seed/iterate/updated.mid` (auto-generated from output name if -m/--midi not provided)

### Example 2: Analyze then Iterate
```bash
./pianist analyze -i song.mid -o analysis.json
./pianist iterate -i song.mid -o composition.json
```
Creates:
- `output/song/analyze/analysis.json`
- `output/song/iterate/composition.json`

Both are under `output/song/` for easy discovery.

### Example 3: Using Output as Input
```bash
./pianist analyze -i song.mid -o analysis.json
./pianist iterate -i output/song/analyze/analysis.json -o comp.json
```
Creates:
- `output/song/analyze/analysis.json`
- `output/song/iterate/comp.json` (detects "song" from path, maintains grouping)

## Migration Notes

If you have existing files in the old structure (`output/<command>/<base-name>/`), they will continue to work. New files will use the new structure (`output/<base-name>/<command>/`). You may want to manually reorganize old files if desired.

