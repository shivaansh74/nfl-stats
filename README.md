# 🏈 NFL Stats CLI - Your Personal StatMuse

A powerful, lightning-fast NFL statistics tool with natural language queries. Built to impress!

## 🚀 Features

### ✅ **Player Stats**
```bash
python -m nfl_stats.main "josh allen"
python -m nfl_stats.main "tom brady 2018"
python -m nfl_stats.main "lamar jackson rookie year"
```

### ✅ **Week-Specific Stats**
```bash
python -m nfl_stats.main "josh allen week 10"
python -m nfl_stats.main "patrick mahomes week 1 2024"
```

### ✅ **Playoff Stats**
```bash
python -m nfl_stats.main "patrick mahomes playoffs"
python -m nfl_stats.main "tom brady patriots playoffs"
python -m nfl_stats.main "lamar jackson playoffs bills"
```

### ✅ **Team Context Filtering**
```bash
python -m nfl_stats.main "tom brady patriots"
python -m nfl_stats.main "brian burns giants"
python -m nfl_stats.main "carson wentz eagles"
```

### ✅ **Super Bowl Stats**
```bash
python -m nfl_stats.main "joe burrow superbowl"
python -m nfl_stats.main "patrick mahomes super bowl"
```

### ✅ **Player Comparisons** ⚔️
```bash
python -m nfl_stats.main "patrick mahomes vs josh allen 2024"
python -m nfl_stats.main "lamar jackson vs joe burrow"
python -m nfl_stats.main "derrick henry vs saquon barkley 2023"
```

### ✅ **News & Injuries** 🔍
```bash
python -m nfl_stats.main "joe burrow injuries"
python -m nfl_stats.main "travis kelce news"
```

### ✅ **Interactive Mode**
```bash
python -m nfl_stats.main
# Then type queries continuously!
```

## 🎯 Installation

```bash
cd /Users/shiv/Development/Test-Antigravity
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 📊 What Makes This Special

- **Natural Language**: Ask questions like you would to a friend
- **Smart Search**: Automatically finds the right players/teams
- **Full Career Data**: Goes back to each player's rookie season
- **Beautiful Output**: Rich terminal formatting with colors and emojis
- **Lightning Fast**: Optimized API calls and caching
- **Comprehensive**: Covers regular season, playoffs, Super Bowls, and more

## 🔥 Coming Soon

- Web frontend for sharing with friends
- Career milestone tracking
- Advanced visualizations
- Export to images/CSV

## 💡 Examples

**Compare QBs:**
```
⚔️  Patrick Mahomes vs Josh Allen (2024)
┏━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Stat  ┃ Patrick Mahomes┃  Josh Allen  ┃Winner ┃
┡━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━┩
│ Yds   │          245.5 │        219.5 │   🟢  │
│ TD    │            1.6 │          1.6 │   🟡  │
│ INT   │            0.7 │          0.4 │   🔵  │
└───────┴────────────────┴──────────────┴───────┘
```

**Playoff Performance:**
```
Tom Brady Patriots Playoffs: 41 games
74,571 yards, 541 TDs, 179 INTs
```

---

Built with ❤️ using ESPN APIs, nflverse data, and Python
