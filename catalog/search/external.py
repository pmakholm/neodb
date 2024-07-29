import asyncio
import logging
import time
import traceback
from urllib.parse import quote_plus, urlparse

import httpx
import requests
from django.conf import settings
from lxml import html

from catalog.common import *
from catalog.models import *
from catalog.sites.bibliotek_dk import get_bibliotekdk_token
from catalog.sites.spotify import get_spotify_token
from catalog.sites.tmdb import TMDB_DEFAULT_LANG

SEARCH_PAGE_SIZE = 5  # not all apis support page size
logger = logging.getLogger(__name__)


class SearchResultItem:
    def __init__(
        self, category, source_site, source_url, title, subtitle, brief, cover_url
    ):
        self.class_name = "base"
        self.category = category
        self.external_resources = {
            "all": [
                {
                    "url": source_url,
                    "site_name": source_site,
                    "site_label": source_site,
                }
            ]
        }
        self.source_site = source_site
        self.source_url = source_url
        self.display_title = title
        self.subtitle = subtitle
        self.display_description = brief
        self.cover_image_url = cover_url

    @property
    def verbose_category_name(self):
        return self.category.label

    @property
    def url(self):
        return f"/search?q={quote_plus(self.source_url)}"

    @property
    def scraped(self):
        return False


class BibliotekDk:
    @classmethod
    def search(cls, q: str, page=1):
        results = []
        search_url = f"https://fbi-api.dbc.dk/SimpleSearch/graphql"
        graphQuery = """
    query all ($q: SearchQuery!, $filters: SearchFilters, $offset: Int!, $limit: PaginationLimit!, $search_exact: Boolean) {
      search(q: $q, filters: $filters, search_exact: $search_exact) {
        works(limit: $limit, offset: $offset) {
          workId
          latestPublicationDate
          series {
            title
          }
          mainLanguages {
            isoCode
            display
          }
          workTypes
          manifestations {
            mostRelevant{
              pid
              ownerWork {
                workTypes
              }
              cover {
                detail
                origin
              }
              materialTypes {
                ...materialTypesFragment
              }
              publisher
              edition {
                summary
                edition
              }
            }
          }
          creators {
            ...creatorsFragment
          }
          materialTypes {
            ...materialTypesFragment
          }
          fictionNonfiction {
            display
          }
          genreAndForm
          titles {
            main
            full
          }
          abstract
        }
        hitcount
      }
      monitor(name: "bibdknext_search_all")
    }
    fragment creatorsFragment on Creator {
  ... on Corporation {
    __typename
    display
    nameSort
    roles {
      function {
        plural
        singular
      }
      functionCode
    }
  }
  ... on Person {
    __typename
    display
    nameSort
    roles {
      function {
        plural
        singular
      }
      functionCode
    }
  }
}
    fragment materialTypesFragment on MaterialType {
  materialTypeGeneral {
    code
    display
  }
  materialTypeSpecific {
    code
    display
  }
}
        """
        query = {
            "query": graphQuery,
            "variables": {
                "filters": {"workTypes": ["literature"]},
                "limit": SEARCH_PAGE_SIZE,
                "offset": (page - 1) * SEARCH_PAGE_SIZE,
                "q": {"all": q},
                "search_exact": False,
            },
        }
        try:
            r = requests.post(
                search_url,
                json=query,
                headers={"Authorization": "Bearer " + get_bibliotekdk_token()},
            )
            for work in r.json()["data"]["search"]["works"]:
                try:
                    source_url = (
                        "https://bibliotek.dk/materiale/title/" + work["workId"]
                    )
                    title = work["titles"]["full"][0]

                    authors = []
                    for creator in work["creators"]:
                        authors.append(creator["display"])

                    subtitle = ", ".join(authors)
                    brief = work["abstract"][0] if work["abstract"] else ""
                    cover_url = work["manifestations"]["mostRelevant"][0]["cover"][
                        "detail"
                    ]

                    results.append(
                        SearchResultItem(
                            ItemCategory.Book,
                            SiteName.BibliotekDK,
                            source_url,
                            title,
                            subtitle,
                            brief,
                            cover_url,
                        )
                    )
                except:
                    logger.error(traceback.format_exc())

        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(
                "Bibliotek.dk search error", extra={"query": q, "exception": e}
            )
        return results


class Goodreads:
    @classmethod
    def search(cls, q: str, page=1):
        results = []
        search_url = f"https://www.goodreads.com/search?page={page}&q={quote_plus(q)}"
        try:
            r = requests.get(
                search_url,
                timeout=3,
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:107.0) Gecko/20100101 Firefox/107.0",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": BasicDownloader.get_accept_language(),
                    "Accept-Encoding": "gzip, deflate",
                    "Connection": "keep-alive",
                    "DNT": "1",
                    "Upgrade-Insecure-Requests": "1",
                    "Cache-Control": "no-cache",
                },
            )
            if r.url.startswith("https://www.goodreads.com/book/show/"):
                # Goodreads will 302 if only one result matches ISBN
                site = SiteManager.get_site_by_url(r.url)
                if site:
                    res = site.get_resource_ready()
                    if res:
                        subtitle = f"{res.metadata.get('pub_year')} {', '.join(res.metadata.get('author', []))} {', '.join(res.metadata.get('translator', []))}"
                        results.append(
                            SearchResultItem(
                                ItemCategory.Book,
                                SiteName.Goodreads,
                                res.url,
                                res.metadata["title"],
                                subtitle,
                                res.metadata.get("brief"),
                                res.metadata.get("cover_image_url"),
                            )
                        )
            else:
                h = html.fromstring(r.content.decode("utf-8"))
                books = h.xpath('//tr[@itemtype="http://schema.org/Book"]')
                for c in books:  # type:ignore
                    el_cover = c.xpath('.//img[@class="bookCover"]/@src')
                    cover = el_cover[0] if el_cover else None
                    el_title = c.xpath('.//a[@class="bookTitle"]//text()')
                    title = "".join(el_title).strip() if el_title else None
                    el_url = c.xpath('.//a[@class="bookTitle"]/@href')
                    url = "https://www.goodreads.com" + el_url[0] if el_url else None
                    el_authors = c.xpath('.//a[@class="authorName"]//text()')
                    subtitle = ", ".join(el_authors) if el_authors else None
                    results.append(
                        SearchResultItem(
                            ItemCategory.Book,
                            SiteName.Goodreads,
                            url,
                            title,
                            subtitle,
                            "",
                            cover,
                        )
                    )
        except requests.exceptions.RequestException as e:
            logger.warning(f"Search {search_url} error: {e}")
        except Exception as e:
            logger.error("Goodreads search error", extra={"query": q, "exception": e})
        return results


class GoogleBooks:
    @classmethod
    def search(cls, q, page=1):
        results = []
        api_url = f"https://www.googleapis.com/books/v1/volumes?country=us&q={quote_plus(q)}&startIndex={SEARCH_PAGE_SIZE*(page-1)}&maxResults={SEARCH_PAGE_SIZE}&maxAllowedMaturityRating=MATURE"
        try:
            j = requests.get(api_url, timeout=2).json()
            if "items" in j:
                for b in j["items"]:
                    if "title" not in b["volumeInfo"]:
                        continue
                    title = b["volumeInfo"]["title"]
                    subtitle = ""
                    if "publishedDate" in b["volumeInfo"]:
                        subtitle += b["volumeInfo"]["publishedDate"] + " "
                    if "authors" in b["volumeInfo"]:
                        subtitle += ", ".join(b["volumeInfo"]["authors"])
                    if "description" in b["volumeInfo"]:
                        brief = b["volumeInfo"]["description"]
                    elif "textSnippet" in b["volumeInfo"]:
                        brief = b["volumeInfo"]["textSnippet"]["searchInfo"]
                    else:
                        brief = ""
                    category = ItemCategory.Book
                    # b['volumeInfo']['infoLink'].replace('http:', 'https:')
                    url = "https://books.google.com/books?id=" + b["id"]
                    cover = (
                        b["volumeInfo"]["imageLinks"]["thumbnail"]
                        if "imageLinks" in b["volumeInfo"]
                        else None
                    )
                    results.append(
                        SearchResultItem(
                            category,
                            SiteName.GoogleBooks,
                            url,
                            title,
                            subtitle,
                            brief,
                            cover,
                        )
                    )
        except requests.exceptions.RequestException as e:
            logger.warning(f"Search {api_url} error: {e}")
        except Exception as e:
            logger.error("GoogleBooks search error", extra={"query": q, "exception": e})
        return results


class TheMovieDatabase:
    @classmethod
    def search(cls, q, page=1):
        results = []
        api_url = f"https://api.themoviedb.org/3/search/multi?query={quote_plus(q)}&page={page}&api_key={settings.TMDB_API3_KEY}&language={TMDB_DEFAULT_LANG}&include_adult=true"
        try:
            j = requests.get(api_url, timeout=2).json()
            if j.get("results"):
                for m in j["results"]:
                    if m["media_type"] in ["tv", "movie"]:
                        url = f"https://www.themoviedb.org/{m['media_type']}/{m['id']}"
                        if m["media_type"] == "tv":
                            cat = ItemCategory.TV
                            title = m["name"]
                            subtitle = f"{m.get('first_air_date', '')} {m.get('original_name', '')}"
                        else:
                            cat = ItemCategory.Movie
                            title = m["title"]
                            subtitle = f"{m.get('release_date', '')} {m.get('original_name', '')}"
                        cover = (
                            f"https://image.tmdb.org/t/p/w500/{m.get('poster_path')}"
                            if m.get("poster_path")
                            else None
                        )
                        results.append(
                            SearchResultItem(
                                cat,
                                SiteName.TMDB,
                                url,
                                title,
                                subtitle,
                                m.get("overview"),
                                cover,
                            )
                        )
            else:
                logger.warning(f"TMDB search '{q}' no results found.")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Search {api_url} error: {e}")
        except Exception as e:
            logger.error("TMDb search error", extra={"query": q, "exception": e})
        return results


class Spotify:
    @classmethod
    def search(cls, q, page=1):
        results = []
        api_url = f"https://api.spotify.com/v1/search?q={q}&type=album&limit={SEARCH_PAGE_SIZE}&offset={page*SEARCH_PAGE_SIZE}"
        try:
            headers = {"Authorization": f"Bearer {get_spotify_token()}"}
            j = requests.get(api_url, headers=headers, timeout=2).json()
            if j.get("albums"):
                for a in j["albums"]["items"]:
                    title = a["name"]
                    subtitle = a["release_date"]
                    for artist in a["artists"]:
                        subtitle += " " + artist["name"]
                    url = a["external_urls"]["spotify"]
                    cover = a["images"][0]["url"] if a.get("images") else None
                    results.append(
                        SearchResultItem(
                            ItemCategory.Music,
                            SiteName.Spotify,
                            url,
                            title,
                            subtitle,
                            "",
                            cover,
                        )
                    )
            else:
                logger.warning(f"Spotify search '{q}' no results found.")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Search {api_url} error: {e}")
        except Exception as e:
            logger.error("Spotify search error", extra={"query": q, "exception": e})
        return results


class Bandcamp:
    @classmethod
    def search(cls, q, page=1):
        results = []
        search_url = f"https://bandcamp.com/search?from=results&item_type=a&page={page}&q={quote_plus(q)}"
        try:
            r = requests.get(search_url, timeout=2)
            h = html.fromstring(r.content.decode("utf-8"))
            albums = h.xpath('//li[@class="searchresult data-search"]')
            for c in albums:  # type:ignore
                el_cover = c.xpath('.//div[@class="art"]/img/@src')
                cover = el_cover[0] if el_cover else None
                el_title = c.xpath('.//div[@class="heading"]//text()')
                title = "".join(el_title).strip() if el_title else None
                el_url = c.xpath('..//div[@class="itemurl"]/a/@href')
                url = el_url[0] if el_url else None
                el_authors = c.xpath('.//div[@class="subhead"]//text()')
                subtitle = ", ".join(el_authors) if el_authors else None
                results.append(
                    SearchResultItem(
                        ItemCategory.Music,
                        SiteName.Bandcamp,
                        url,
                        title,
                        subtitle,
                        "",
                        cover,
                    )
                )
        except requests.exceptions.RequestException as e:
            logger.warning(f"Search {search_url} error: {e}")
        except Exception as e:
            logger.error("Bandcamp search error", extra={"query": q, "exception": e})
        return results


class ApplePodcast:
    @classmethod
    def search(cls, q, page=1):
        results = []
        search_url = f"https://itunes.apple.com/search?entity=podcast&limit={page*SEARCH_PAGE_SIZE}&term={quote_plus(q)}"
        try:
            r = requests.get(search_url, timeout=2).json()
            for p in r["results"][(page - 1) * SEARCH_PAGE_SIZE :]:
                if p.get("feedUrl"):
                    results.append(
                        SearchResultItem(
                            ItemCategory.Podcast,
                            SiteName.RSS,
                            p["feedUrl"],
                            p["trackName"],
                            p["artistName"],
                            "",
                            p["artworkUrl600"],
                        )
                    )
        except requests.exceptions.RequestException as e:
            logger.warning(f"Search {search_url} error: {e}")
        except Exception as e:
            logger.error(
                "ApplePodcast search error", extra={"query": q, "exception": e}
            )
        return results


class Fediverse:
    @staticmethod
    async def search_task(host, q, category=None):
        api_url = f"https://{host}/api/catalog/search?query={quote_plus(q)}{'&category='+category if category else ''}"
        async with httpx.AsyncClient() as client:
            results = []
            try:
                response = await client.get(
                    api_url,
                    timeout=2,
                )
                r = response.json()
            except Exception as e:
                logger.error(
                    f"Fediverse search {host} error",
                    extra={"url": api_url, "query": q, "exception": e},
                )
                return []
            if "data" in r:
                for item in r["data"]:
                    if any(
                        urlparse(res["url"]).hostname in settings.SITE_DOMAINS
                        for res in item.get("external_resources", [])
                    ):
                        continue
                    url = f"https://{host}{item['url']}"  # FIXME update API and use abs urls
                    try:
                        cat = ItemCategory(item["category"])
                    except Exception:
                        cat = ""
                    results.append(
                        SearchResultItem(
                            cat,
                            host,
                            url,
                            item["display_title"],
                            "",
                            item["brief"],
                            item["cover_image_url"],
                        )
                    )
        return results

    @classmethod
    def search(cls, q: str, page: int = 1, category: str | None = None):
        from takahe.utils import Takahe

        peers = Takahe.get_neodb_peers()
        c = category if category != "movietv" else "movie,tv"
        tasks = [Fediverse.search_task(host, q, c) for host in peers]
        # loop = asyncio.get_event_loop()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = []
        for r in loop.run_until_complete(asyncio.gather(*tasks)):
            results.extend(r)
        return results


class ExternalSources:
    @classmethod
    def search(cls, c, q, page=1):
        if not q:
            return []
        results = []
        results.extend(
            Fediverse.search(q, page, category=c if c and c != "all" else None)
        )
        if c == "" or c is None:
            c = "all"
        if c == "all" or c == "movietv":
            results.extend(TheMovieDatabase.search(q, page))
        if c == "all" or c == "book":
            results.extend(BibliotekDk.search(q, page))
            results.extend(GoogleBooks.search(q, page))
            results.extend(Goodreads.search(q, page))
        if c == "all" or c == "music":
            results.extend(Spotify.search(q, page))
            results.extend(Bandcamp.search(q, page))
        if c == "podcast":
            results.extend(ApplePodcast.search(q, page))
        return results
