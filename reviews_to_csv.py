"""Export Tripadvisor reviews for a list of places into one CSV.

Usage:
    export APIFY_TOKEN=...            # from https://console.apify.com/settings/integrations
    python reviews_to_csv.py places.txt --max 50 --out reviews.csv

places.txt holds one place per line: a Tripadvisor URL from any country site,
a numeric place ID, or a name with the city ("Louvre Museum Paris").
Blank lines and lines starting with # are skipped.
"""

import argparse
import csv
import os
import sys
from collections import defaultdict
from decimal import Decimal

from apify_client import ApifyClient

ACTOR = "heyitsgautham/tripadvisor-reviews-scraper"
PRICE_PER_REVIEW = Decimal("0.0004")

COLUMNS = [
    "placeName", "placeType", "placeRating", "placeReviewCount",
    "rating", "title", "text", "reviewDate", "visitDate", "tripType",
    "language", "machineTranslated", "helpfulVotes", "photoCount",
    "hasOwnerResponse", "ownerResponseDate", "reviewUrl",
]


def read_places(path):
    urls, names = [], []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("http") or line.isdigit():
                urls.append(line)
            else:
                names.append(line)
    return urls, names


def to_row(review, sub_keys):
    row = {key: review.get(key) for key in COLUMNS}
    row["hasOwnerResponse"] = bool(review.get("ownerResponse"))
    sub = review.get("subRatings") or {}
    for key in sub_keys:
        row[f"sub_{key}"] = sub.get(key)
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("places", help="text file, one Tripadvisor URL, place ID or name per line")
    parser.add_argument("--max", type=int, default=100, help="reviews per place (default 100)")
    parser.add_argument("--since", help="only reviews published on or after this date, e.g. 2025-01-01")
    parser.add_argument("--out", default="reviews.csv")
    args = parser.parse_args()

    token = os.environ.get("APIFY_TOKEN")
    if not token:
        sys.exit("Set APIFY_TOKEN first. Get one at https://console.apify.com/settings/integrations")

    urls, names = read_places(args.places)
    if not urls and not names:
        sys.exit(f"No places found in {args.places}")

    run_input = {"startUrls": urls, "placeNames": names, "maxReviewsPerPlace": args.max}
    if args.since:
        run_input["publishedAfter"] = args.since

    # Hard ceiling on what this run can cost you: every place at its full --max.
    places = len(urls) + len(names)
    cap = PRICE_PER_REVIEW * args.max * places
    print(f"Scraping {places} places, up to {args.max} reviews each, at most ${cap:.4f}")

    client = ApifyClient(token)
    run = client.actor(ACTOR).call(run_input=run_input, max_total_charge_usd=cap, logger=None)
    if run is None or run.status != "SUCCEEDED":
        sys.exit(f"Run did not succeed: {run.status if run else 'no run'}")

    reviews, problems = [], []
    for item in client.dataset(run.default_dataset_id).iterate_items():
        if item.get("status") == "ok":
            reviews.append(item)
        else:
            problems.append(item)

    sub_keys = sorted({k for r in reviews for k in (r.get("subRatings") or {})})
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS + [f"sub_{k}" for k in sub_keys])
        writer.writeheader()
        for review in reviews:
            writer.writerow(to_row(review, sub_keys))

    by_place = defaultdict(list)
    for review in reviews:
        by_place[review["placeName"]].append(review)

    print(f"\nWrote {len(reviews)} reviews to {args.out}\n")
    print(f"{'Place':40} {'Reviews':>7} {'Avg':>5} {'Owner replied':>14}")
    for place, rows in sorted(by_place.items()):
        avg = sum(r["rating"] for r in rows) / len(rows)
        replied = sum(1 for r in rows if r.get("ownerResponse")) / len(rows)
        print(f"{place[:40]:40} {len(rows):>7} {avg:>5.2f} {replied:>13.0%}")

    for item in problems:
        print(f"\nSkipped {item.get('input')}: {item.get('status')}, {item.get('message')}")


if __name__ == "__main__":
    main()
