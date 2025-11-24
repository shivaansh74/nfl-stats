# NFL Stats App - Query Support Matrix

## ✅ Queries with Rich UI Components

These queries return structured data and display in custom React components:

### 1. **Player Comparisons** → `ComparisonView`
```
mahomes vs allen 2024
saquon barkley vs derrick henry
justin jefferson vs tyreek hill
```

### 2. **Player Biographies** → `PlayerCard`
```
tom brady bio
how old is patrick mahomes
jalen hurts college
```

### 3. **League Leaders** → `LeaderboardTable`
```
nfl passing leaders 2024
top 10 rushing touchdowns
receiving yards leaders
sacks leaders
```

### 4. **Trending Players** → `TrendingPlayers`
```
trending players
hot waiver pickups
```

### 5. **Depth Charts** → `RosterView`
```
eagles starting qb
chiefs running backs
49ers tight end
```

### 6. **Fantasy Points** → `FantasyPointsCard`
```
saquon barkley fantasy points 2024
ceedee lamb fantasy stats
```

### 7. **Draft Information** → Structured Data
```
when was mahomes drafted
lamar jackson draft pick
```

### 8. **Awards/MVP** → Structured Data
```
lamar jackson mvp
aaron donald dpoy
```

### 9. **Injury Reports** → Structured Data
```
christian mccaffrey injury
tyreek hill injury status
```

### 10. **Multi-Player Aggregations** → Structured Data
```
eagles receivers stats
chiefs running backs combined
```

---

## 📝 Queries with Text/HTML Fallback

These queries work perfectly but display formatted console output (still looks good!):

### 1. **General Player Stats**
```
patrick mahomes 2024 stats
derrick henry rushing yards 2023
josh allen passing touchdowns
```
*Shows: Formatted table with season stats*

### 2. **Longest Plays** (with animations!)
```
tyreek hill longest catch
derrick henry longest run
patrick mahomes longest pass
```
*Shows: Play details + animated GIF visualization*

### 3. **Career Stats**
```
tom brady career stats
aaron rodgers career touchdowns
```
*Shows: Career totals and per-game averages*

### 4. **Rookie Year Stats**
```
lamar jackson rookie year
justin herbert rookie stats
```
*Shows: First season statistics*

### 5. **Playoff Stats**
```
mahomes playoffs 2023
josh allen playoff stats
```
*Shows: Postseason performance*

### 6. **Opponent-Specific Stats**
```
mahomes vs bills
josh allen vs chiefs playoffs
```
*Shows: Head-to-head performance*

### 7. **Quarter-Specific Stats**
```
lamar jackson 4th quarter stats
mahomes 2nd quarter performance
```
*Shows: Quarter-by-quarter breakdown*

### 8. **Threshold Queries**
```
derrick henry games with 100+ yards
mahomes games with 3+ touchdowns
```
*Shows: List of games meeting criteria*

### 9. **Month/Time Filters**
```
justin jefferson december stats
lamar jackson prime time games
```
*Shows: Filtered statistics*

### 10. **Team Queries**
```
chiefs schedule
eagles record
patriots week 5
```
*Shows: Team information and schedules*

---

## 🎯 All Queries Work!

**Important**: Every query type is fully functional! The difference is just in presentation:
- ✅ **Rich UI queries** = Custom React components with animations
- 📝 **Fallback queries** = Beautifully formatted HTML tables

Both look professional and provide all the data you need. The fallback is actually the original CLI output which is already very polished with Rich library formatting.

---

## 🚀 Future Enhancements

To add rich UI for remaining queries, we could create:

1. **PlayerStatsCard** - For general player stats
2. **PlayVisualization** - Better integration of play animations
3. **CareerTimeline** - Visual career progression
4. **TeamScheduleView** - Calendar-style schedule
5. **ThresholdGamesTable** - Highlighted games list

But the current system is already production-ready and handles all query types gracefully!
