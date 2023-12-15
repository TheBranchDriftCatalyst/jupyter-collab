"""
Source: https://github.com/maria-antoniak/goodreads-scraper/blob/master/get_books.py
"""
import logging
import re
from typing import Union, Tuple
from urllib.request import urlopen
from bs4 import BeautifulSoup
from argparse import Namespace
from utils.expo_backoff import ExpoBackoff
from logging import getLogger

logger = getLogger(__name__)

# Because i want to construct the series objects so that i can keep track of series
# in notion.  I am going to have this split threads whenever it parses a new book.
# We will upsert any new books that we find for the series.  We will not do anything,
# i.e., skip the process story procedure if the book already exists in the database.

def get_genres(soup):
    genres = []
    for node in soup.find_all("div", {"class": "left"}):
        current_genres = node.find_all(
            "a", {"class": "actionLinkLite bookPageGenreLink"}
        )
        current_genre = " > ".join([g.text for g in current_genres])
        if current_genre.strip():
            genres.append(current_genre)
    return genres


def series_profile(soup) -> Tuple[Union[dict, None], Union[float, None]]:
    series_link = soup.find("a", attrs={"href": re.compile(r"/series/\d+")})

    if not series_link:
        return None, None

    # Get the parent <div> of the 'Series' <dt> tag
    series_div = series_link.find_parent("div") if series_link else None

    # Extract series name and URL
    series_url = series_link["href"]
    series_name = series_link.get_text() if series_link else None

    if match := re.search(r"(.+?)\s*#\s*(\d+)", series_name):
        series_name = match[1]
        series_number = float(match[2])
    else:
        series_name = series_number = None

    with ExpoBackoff().context() as backoff:
        source = urlopen(series_url)

    # Series details page doesn't have much
    salad = BeautifulSoup(source, "html.parser")

    side_salad = {
        "total_works": int(re.search(r"(\d+) total works", salad.text)[1]),
        "primary_works": int(re.search(r"(\d+) primary works", salad.text)[1]),
    }

    return (
        {"series_name": series_name, "series_url": series_link["href"], **side_salad},
        series_number,
    )


# Example usage


def get_rating_distribution(soup):
    distribution = re.findall(r"renderRatingGraph\([\s]*\[[0-9,\s]+", str(soup))[0]
    distribution = " ".join(distribution.split())
    distribution = [int(c.strip()) for c in distribution.split("[")[1].split(",")]
    distribution_dict = {
        5: distribution[0],
        4: distribution[1],
        3: distribution[2],
        2: distribution[3],
        1: distribution[4],
    }
    return distribution_dict


def author_profile(soup):
    return dict(
        {
            "name": soup.find("span", attrs={"data-testid": "name"}).text,
            "author_url": soup.find("a", attrs={"class": "ContributorLink"}).attrs.get(
                "href"
            ),
        }
    )


def genres_profile(soup):
    # Find all genre elements
    genre_elements = soup.find_all(
        "span", class_="BookPageMetadataSection__genreButton"
    )

    genres = []

    # Loop over each genre element
    for genre_element in genre_elements:
        anchor = genre_element.find("a")
        if anchor:
            genre_name = anchor.get_text(strip=True)
            genre_url = anchor["href"]
            genres.append({"genre_name": genre_name, "genre_url": genre_url})
    return genres


def get_int_from_text(soup_element):
    try:
        return int(
                soup_element
                .text.split()[0]
                .replace(",", "")
            )
    except Exception as e:
        logger.error(f"Error getting int from text")
        return 0


def scrape_book(book_id: str, args: Namespace = None):
    if args is None:
        args = {'skip_authors': False, 'skip_shelves': False, 'skip_user_info': False}

    url = f"https://www.goodreads.com/book/show/{book_id}"
    with ExpoBackoff().context() as backoff:
        source = urlopen(url)

    soup = BeautifulSoup(source, "html.parser")

    book_cover_div = soup.find("div", class_="BookCover")
    # Find the img tag within the 'BookCover' div
    img_tag = (
        book_cover_div.find("img", class_="ResponsiveImage") if book_cover_div else None
    )

    series_prof, num_in_series = series_profile(soup)

    return {
        "id": book_id,
        "title": soup.find("h1", attrs={"data-testid": "bookTitle"}).text,
        "description": soup.find("div", {"data-testid": "description"}).text,
        "url": url,
        "image": img_tag["src"] if img_tag else None,
        "author": author_profile(soup)["name"],
        "series": series_prof,
        "number_in_series": num_in_series,
        # "year_first_published": get_year_first_published(soup),
        "genres": list(map(lambda x: x["genre_name"], genres_profile(soup))),
        "num_pages": get_int_from_text(soup.find("p", {"data-testid": "pagesFormat"})),
        "num_ratings": get_int_from_text(soup.find("span", {"data-testid": "ratingsCount"})),
        "num_reviews": get_int_from_text(soup.find("span", {"data-testid": "reviewsCount"})),
        # "average_rating": float(
        #     soup.find("span", {"itemprop": "ratingValue"}).text.strip()
        # ),
    }
