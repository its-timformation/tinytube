#!/usr/bin/env python3
"""
tinytube categorise.py
======================
Reads a tinytube-playlist.json file (exported from the ⚙ Admin → Settings → Export),
categorises each video by title keywords, and writes an updated JSON file ready to
re-import into tinytube.

Usage
-----
  python3 categorise.py                          # uses tinytube-playlist.json in same folder
  python3 categorise.py my-playlist.json        # custom input file
  python3 categorise.py in.json out.json        # custom input + output file

The script will:
  1. Load the playlist.
  2. For videos that already have a category set, leave them alone (unless --force is passed).
  3. Match each title against keyword rules to assign a category.
  4. Print a summary table.
  5. Save the updated playlist.

Pass --force to re-categorise ALL videos, ignoring existing categories.

Categories
----------
  shows     → TV episodes, cartoons, series (Peppa, Bluey, Paw Patrol, etc.)
  movies    → Films, features
  learning  → Educational, how-to, science, maths, stories, alphabet, counting
  music     → Songs, nursery rhymes, dance, sing-along
  funny     → Comedy, funny clips, jokes, silly
  other     → Anything that doesn't match

Customise the RULES dict below to add your own keywords.
"""

import json, sys, re, os

# ── Keyword rules ──────────────────────────────────────────────────────────────
# Categories are checked in order; first match wins.
# All matching is case-insensitive, on the video title.
RULES = {
    "shows": [
        r"\bpeppa\b", r"\bbluey\b", r"\bpaw patrol\b", r"\bcocomelon\b",
        r"\bblippi\b", r"\bdora\b", r"\bspongebob\b", r"\bcartoon\b",
        r"\bepisode\b", r"\bseason\b", r"\bseries\b", r"\bshow\b",
        r"\bpokemon\b", r"\bpikachu\b", r"\bmy little pony\b", r"\bmlp\b",
        r"\btransformers\b", r"\bninja turtles\b", r"\bspiderman\b",
        r"\bbob the builder\b", r"\bthomas\b", r"\bpostman pat\b",
        r"\bteletubbies\b", r"\bin the night garden\b", r"\bhey duggee\b",
        r"\bbluey\b", r"\bsuperheroes\b", r"\bavengers\b",
        r"\banime\b", r"\bcartoon network\b", r"\bnickelodeon\b",
    ],
    "movies": [
        r"\bmovie\b", r"\bfilm\b", r"\bfeature\b", r"\bfull movie\b",
        r"\bdisney\b", r"\bpixar\b", r"\bdreamworks\b",
        r"\bfrozen\b", r"\bmoana\b", r"\btoy story\b", r"\bfinding nemo\b",
        r"\bthe lion king\b", r"\baladdin\b", r"\bbeauty and the beast\b",
        r"\bencanto\b", r"\braya\b", r"\bzootopia\b", r"\binside out\b",
        r"\bcars\b", r"\bup\b", r"\bwallte\b", r"\bnemo\b",
        r"\bshrek\b", r"\bminions\b", r"\bkungu fu panda\b",
        r"\bhow to train your dragon\b",
    ],
    "learning": [
        r"\blearn\b", r"\blearning\b", r"\beducation\b", r"\beducational\b",
        r"\bscience\b", r"\bmaths\b", r"\bmath\b", r"\bnumbers\b",
        r"\balphabet\b", r"\bletters\b", r"\bcounting\b", r"\bcolou?rs?\b",
        r"\bshapes\b", r"\banimal\b", r"\banimals\b", r"\bnature\b",
        r"\bspace\b", r"\bdino(saur)?\b", r"\bdinosaurs\b",
        r"\bhow (to|do)\b", r"\bwhy\b.*\?", r"\bwhat is\b",
        r"\bstory time\b", r"\bstorybook\b", r"\bfairytale\b",
        r"\bnational geographic\b", r"\bdiscovery\b", r"\bplanet earth\b",
        r"\bkhan academy\b", r"\bsesame street\b", r"\bword\b.*\bworld\b",
        r"\bphonics\b", r"\breading\b", r"\bspelling\b",
        r"\bcooking\b", r"\bcraft\b", r"\bdraw(ing)?\b", r"\bpaint(ing)?\b",
        r"\bexperiment\b",
    ],
    "music": [
        r"\bsong\b", r"\bsongs\b", r"\bsing\b", r"\bsinging\b",
        r"\bnursery rhyme\b", r"\brhyme\b", r"\brhymes\b",
        r"\bmusic\b", r"\bmelody\b", r"\bdance\b", r"\bdancing\b",
        r"\bsing.along\b", r"\bkaraoke\b", r"\blyrics\b",
        r"\blullaby\b", r"\blullabies\b",
        r"\btwinkle\b", r"\bwheels on the bus\b", r"\brow your boat\b",
        r"\bhumpty dumpty\b", r"\bjack and jill\b", r"\bbaa baa\b",
        r"\bchant\b", r"\bclap\b",
    ],
    "funny": [
        r"\bfunny\b", r"\bfun\b", r"\blaugh\b", r"\blaughing\b",
        r"\bgiggle\b", r"\bsilly\b", r"\bgoofy\b", r"\bbloopers?\b",
        r"\bjoke\b", r"\bjokes\b", r"\bcomedy\b", r"\bprank\b",
        r"\bfail\b", r"\btry not to laugh\b", r"\bhumou?r\b",
    ],
}

# ── Categorisation logic ───────────────────────────────────────────────────────
def categorise_title(title: str) -> str:
    """Return the best-matching category for a title, or 'other'."""
    t = title.lower()
    for cat, patterns in RULES.items():
        for pat in patterns:
            if re.search(pat, t):
                return cat
    return "other"

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    force = "--force" in sys.argv
    args  = [a for a in sys.argv[1:] if not a.startswith("--")]

    input_file  = args[0] if len(args) >= 1 else "tinytube-playlist.json"
    output_file = args[1] if len(args) >= 2 else input_file  # overwrite by default

    if not os.path.exists(input_file):
        print(f"❌  File not found: {input_file}")
        print("    Export your playlist from tinytube (⚙ → Settings → Export playlist)")
        sys.exit(1)

    with open(input_file, encoding="utf-8") as f:
        data = json.load(f)

    videos = data.get("videos", [])
    if not videos:
        print("⚠️  No videos found in playlist.")
        sys.exit(0)

    counts   = {k: 0 for k in list(RULES.keys()) + ["other"]}
    skipped  = 0
    changed  = 0

    print(f"\n🎬  tinytube categorise.py")
    print(f"    Input  : {input_file}")
    print(f"    Videos : {len(videos)}")
    print(f"    Force  : {'yes — re-categorising everything' if force else 'no — skipping already-categorised'}")
    print()
    print(f"  {'#':>3}  {'Title':<40}  {'Old':>8}  {'New':>8}  {'Action'}")
    print(f"  {'─'*3}  {'─'*40}  {'─'*8}  {'─'*8}  {'─'*8}")

    for i, v in enumerate(videos):
        title   = v.get("title", "")
        old_cat = v.get("category", "")

        if old_cat and not force:
            # Already has a category — leave it
            action = "skip"
            new_cat = old_cat
            skipped += 1
        else:
            new_cat = categorise_title(title)
            if new_cat != old_cat:
                action  = "✅ set"
                changed += 1
            else:
                action  = "same"
            v["category"] = new_cat

        counts[new_cat] = counts.get(new_cat, 0) + 1
        short_title = (title[:37] + "…") if len(title) > 40 else title
        print(f"  {i+1:>3}  {short_title:<40}  {old_cat or '—':>8}  {new_cat:>8}  {action}")

    print()
    print(f"  Summary")
    print(f"  {'Category':<12}  {'Count':>5}")
    print(f"  {'─'*12}  {'─'*5}")
    for cat, count in counts.items():
        if count:
            icon = {"shows":"📺","movies":"🎞","learning":"📚","music":"🎵","funny":"😂","other":"📁"}.get(cat,"")
            print(f"  {icon} {cat:<10}  {count:>5}")
    print()
    print(f"  Changed: {changed}  |  Skipped (already set): {skipped}")

    # Write output
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n✅  Saved to: {output_file}")
    print(f"    Now go to tinytube ⚙ → Settings → Import playlist to load it.\n")

if __name__ == "__main__":
    main()
