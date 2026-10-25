# Tripadvisor reviews scraper

Pull Tripadvisor reviews of hotels, restaurants, attractions and tours into CSV or JSON, from Python or plain curl.

I built the scraper behind this repo, the [Tripadvisor Reviews Scraper on Apify](https://apify.com/heyitsgautham/tripadvisor-reviews-scraper).
It runs on Apify's servers and is paid per result, $0.40 per 1,000 reviews.
This repo holds the code I use to call it, plus a script that turns a list of places into one spreadsheet.
The script is MIT licensed, so copy whatever helps.

## What you get back

One row per review, with the rating, title, text, review date, month of the visit, trip type, language, sub-ratings, the reviewer's tip, helpful votes, photo links and the owner's reply.
Each row also carries the place's name, type, overall rating and review count.

The scraper keeps only the reviewer's public display name.
It drops usernames, profile links, hometowns and avatars, and it removes emails and phone numbers from review text.

This row came from a run I made on 25 Oct 2026, for Le Bernardin in New York.
I left out `photoUrls` and the three `ownerResponse` fields, which were empty.

```json
{
  "status": "ok",
  "placeId": "424434",
  "placeName": "Le Bernardin",
  "placeType": "restaurant",
  "placeRating": 4.6,
  "placeReviewCount": 3704,
  "reviewId": "1082328416",
  "reviewUrl": "https://www.tripadvisor.com/ShowUserReviews-g60763-d424434-r1082328416-Le_Bernardin-New_York_City_New_York.html",
  "rating": 5,
  "title": "geaux",
  "text": "actually - for a 3 star place - not stuff - brilliant - iconic - genius - nicest staff i ever did speak to - and yeah - the food is worthy of a thousand stars -",
  "reviewDate": "2026-10-18T20:18:47.008Z",
  "visitDate": "2026-10",
  "tripType": "couples",
  "language": "en",
  "originalLanguage": "en",
  "machineTranslated": false,
  "subRatings": {"Value": 5, "Service": 5, "Food": 5, "Atmosphere": 5},
  "tip": "its oustanding - formal yet Friendly - brought our dog - puppy - and they couldn't be any more accommodating - amazing people working",
  "helpfulVotes": 0,
  "photoCount": 0,
  "reviewerName": "Leona Helmsley"
}
```

## Quick start in Python

You need a free Apify account and its API token, from Settings, then API & Integrations in the Apify Console.

```bash
pip install "apify-client>=3.3,<4"
export APIFY_TOKEN=your_token_here
```

```python
import os
from apify_client import ApifyClient

client = ApifyClient(os.environ["APIFY_TOKEN"])
run = client.actor("heyitsgautham/tripadvisor-reviews-scraper").call(run_input={
    "startUrls": ["https://www.tripadvisor.com/Hotel_Review-g60763-d93450-Reviews-Hyatt_Grand_Central_New_York-New_York_City_New_York.html"],
    "placeNames": ["Louvre Museum Paris"],
    "maxReviewsPerPlace": 50,
})
for review in client.dataset(run.default_dataset_id).iterate_items():
    print(review["placeName"], review.get("rating"), review.get("title"))
```

## Quick start with curl

This call waits for the run to finish and returns the reviews as JSON.
I ran it for the two newest 1 and 2 star reviews of the Shangri-La in Paris.

```bash
curl -X POST "https://api.apify.com/v2/acts/heyitsgautham~tripadvisor-reviews-scraper/run-sync-get-dataset-items?format=json" \
  -H "Authorization: Bearer $APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"placeNames": ["Shangri-La Paris"], "maxReviewsPerPlace": 2, "ratings": ["1", "2"]}'
```

Swap `format=json` for `format=csv` or `format=xlsx` to get a file instead.

## The script: many places into one CSV

`reviews_to_csv.py` takes a text file of places and writes every review into one CSV, with each sub-rating in its own column.
Then it prints a per-place summary, so you see at a glance which place rates lowest and how often the owner answers.

```bash
pip install -r requirements.txt
python reviews_to_csv.py examples/places.txt --max 20 --since 2026-01-01 --out reviews.csv
```

`examples/places.txt` mixes the three kinds of input the scraper takes: a URL from the UK site, a bare place ID and a name.

```
https://www.tripadvisor.co.uk/Restaurant_Review-g60763-d424434-Reviews-Le_Bernardin-New_York_City_New_York.html
188151
Louvre Museum Paris
```

This is the output from my run on 26 Oct 2026.

```
Scraping 3 places, up to 20 reviews each, at most $0.0240

Wrote 60 reviews to reviews.csv

Place                                    Reviews   Avg  Owner replied
Eiffel Tower                                  20  4.40            0%
Le Bernardin                                  20  4.20            0%
Louvre Museum                                 20  3.65            0%
```

The script passes Apify a maximum charge of every place at its full `--max`, so a run can never cost more than the number it prints first.
Places that return nothing, such as a city page or a name with no match, get printed at the end with the reason.

## Main inputs

| Input | What it does |
|---|---|
| `startUrls` | Place pages from any Tripadvisor country site, review page links, or numeric place IDs |
| `placeNames` | Names as you'd type them in Tripadvisor's search box, best with the city |
| `maxReviewsPerPlace` | Stop after this many reviews per place, 100 by default |
| `sortBy` | `newest` (default) or `detailed` |
| `ratings` | Only these star ratings, `"1"` to `"5"` |
| `languages` | Only reviews in these languages, such as `en` or `de` |
| `includeMachineTranslations` | Off drops the reviews Tripadvisor machine-translated |
| `tripTypes` | `family`, `couples`, `solo`, `business`, `friends` |
| `keyword` | Only reviews that mention this word, through Tripadvisor's own review search |
| `publishedAfter`, `publishedBefore` | A date window, such as `2026-01-01` or `7 days` |
| `onlyNewSinceLastRun` | On a schedule, return only reviews you haven't had before |

The [Store page](https://apify.com/heyitsgautham/tripadvisor-reviews-scraper) documents every field and status.

## What it costs

| Apify plan tier | Per 1,000 reviews |
|---|---|
| No discount | $0.40 |
| Bronze | $0.35 |
| Silver | $0.30 |
| Gold | $0.25 |

There's no start fee.
Places with no reviews, wrong URLs, names with no match, duplicates and failures are free.
Apify's free plan gives you $5 of credit a month, which covers 12,500 reviews at the no-discount price.

## How far it goes

One run returned all 15,048 reviews of Hyatt Grand Central New York, from 2002 to 2026, in 4 minutes 22 seconds.
In my 80-place test on 21 Oct 2026, every one of the 78 places with reviews returned them, 9,948 reviews in 65 seconds.

Where it stops:

- City pages, hotel lists and search results have no reviews of their own, so pass the page of one place.
- Names only work when Tripadvisor's search box lists the place. In my test 8 of 12 names found the right place, so check `matchedPlace` or use a URL when you need certainty.
- Photo links are the ones the review list carries, which can be fewer than `photoCount`.
- It reads public, logged-out pages only.

## License

MIT, see [LICENSE](LICENSE).
The license covers the code in this repo, not the Apify actor itself.
