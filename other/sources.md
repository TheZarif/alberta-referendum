# Sources

Retrieved 1 November 2026.

## Official results

Elections Alberta publishes the workbooks `scripts/02-download_data.py` saves.

- 2026 division files: `orEDResultsReferendum2026.cfm?EventId=202601` through `202610`, with `MODE=exED`. Question 10 is event `202610`.
- 2026 poll files: `orPollResultsReferendum2026.cfm` with the same event ids, `ED=01` through `87`, and `MODE=exED`.
- 2021 jurisdiction files: `orResultsReferendum2021.cfm?MODE=exProv&EventId=68&QUESTIONNO=1` (equalization) and `QUESTIONNO=2` (daylight saving time).

The provincial announcement is the 29 October 2026 news release: <https://www.elections.ab.ca/resources/media/news-releases/2026-10-29-2/>.

Orders in Council are summarized at <https://www.elections.ab.ca/elections/referendum/referendum-results/>.

`data/01-raw_data/manifest.json` records the URL, size, and SHA-256 of each workbook after a download.

### Two elector counts

The news release reports 3,148,205 eligible electors and 70.4% turnout on the busiest questions. That turnout is ballots cast divided by eligible electors.

The results workbooks print 3,286,778 electors and a turnout near 67.4%. That turnout is ballots cast divided by the workbook elector count. The cleaned files keep the workbook figures. They do not replace them with the news-release turnout.

### Combined ballot boxes

Fourteen voting places used one ballot box for several voting areas. Those votes sit on the first voting area, and the other areas in that place are zero. Turnout for those areas should be read at the division level.

Advance, mobile, and special-ballot rows often have no elector count.

The cleaned files follow the division workbooks. Those workbooks match the 29 October 2026 news release on every question except question 7. The workbook total for question 7 is 971,788 yes and 1,083,673 no. The news release printed 971,837 and 1,083,780. Ballots cast in the workbooks (valid + declined + rejected) are within four votes of the news release on the other questions. Spoiled ballots are kept separately and are not in that ballots-cast total.

## 2021

Equalization and daylight saving time were voted on 18 October 2021. The corrected daylight-saving totals, after Grande Prairie's yes and no counts were found to be swapped, are in the 26 October 2021 update: <https://www.elections.ab.ca/resources/media/news-releases/daylight-saving-time-official-results-updated/>.

## Separation polls

`data/01-raw_data/polls_separation.csv` is a snapshot of <https://338canada.com/alberta/polls-indy.htm> taken 1 November 2026. Question wording is not the same across firms. Where a poll asked both a general independence question and the referendum wording, 338Canada shows the referendum wording. Some Léger questions included joining the United States, and that response is folded into the separation share.

Éric Grenier's campaign average is a separate aggregate, not a row in the file: <https://www.thewrit.ca/p/alberta-referendum-poll-tracker>.

## Electoral division boundaries

`data/01-raw_data/ab_electoral_divisions_2017.geojson` was queried on 6 November 2026 from the Government of Alberta layer "Provincial Electoral Division - Current 2017" (<https://geospatial.alberta.ca/titan/rest/services/boundary/goa_administrative_area/MapServer/3>), 87 features, requested in EPSG:4326 with `maxAllowableOffset=0.002` degrees, so boundaries are simplified. Licence: Open Government Licence - Alberta. One division is named Calgary-McCall in this file and Calgary-Bhullar-McCall in the results, so the two are joined by division number.
