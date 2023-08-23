# ninthage-data-analytics
A better way for the project to ingest tournament results and make use of this data in a productive way.

## Manual Game Reporting
[Game Reporter](https://duxbuse.github.io/ninthage-data-analytics/)

## Dash Board
[Dash Board](https://public.tableau.com/app/profile/sander.kaa/viz/9thAgeDataAnalysis_16379569647110/KPI)

## Discord
[Discord Server](https://discord.gg/mTDT7rgKrU)

## Perms to query BQ
| Target   | Role name | Role id |
| ------------- | ------------- | ------------- |
| Project  | BigQuery Job User  | roles/bigquery.jobUser |
| Table/View/Dataset  | BigQuery Data Viewer  | roles/bigquery.dataViewer |

## Requirements for performance metrics from TourneyKeeper

The name of the tournament must exactly match the name of an event on TourneyKeeper.
Additionally the player names in the list document must also match the player names in TourneyKeeper
## Expected file format for ingestion

To be read we require a .docx word document.
The title of the document is the tournament aka "bigbellybash.docx" -> tournament = "bigbellybash"

Then the document itself is a list of legal 9thage army lists in new recruit format but with the following requirements
```
`name` ***Ideally matches TK name***

`army` ***Must be valid 9thAge Army name***

`list` **Currently newrecruit, 9th-builder and battlescribe formats are supported***

`total points` ***optional***
```

***Note:*** All lines are trimmed and lines of length 1 or less are removed during parsing as such don't worry if there is lots of whitespace.



eg:
```text
Russell

Vampire Covenant
515 - Vampire Courtier, General (The Dead Arise), Nosferatu Bloodline (Arcane Knowledge), Wizard (Wizard Master, Occultism)
495 - Necromancer, Wizard Master, Alchemy, Necromantic Staff, Binding Scroll
370 - Barrow King, Battle Standard Bearer, Destiny's Call, Paired Weapons (Hero's Heart), Potion of Swiftness
415 - 40 Skeletons, Spear, Standard Bearer (Flaming Standard), Musician, Champion
220 - 20 Skeletons, Standard Bearer (Banner of the Relentless Company), Musician, Champion
214 - 23 Skeletons, Standard Bearer (Legion Standard), Musician, Champion
150 - 21 Zombies, Standard Bearer, Musician
135 - 8 Dire Wolves, Champion
610 - 8 Ghasts, Champion
610 - 8 Ghasts, Champion
465 - Dark Coach
300 - Court of the Damned
4499
```
## Architecture

![Architecture Diagram](architecture/ninthage-data-analytics_architecture.png)
