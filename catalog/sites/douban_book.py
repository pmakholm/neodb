from catalog.common import *
from .douban import *
from catalog.book.models import *
from catalog.book.utils import *
import logging


_logger = logging.getLogger(__name__)


@SiteList.register
class DoubanBook(AbstractSite):
    ID_TYPE = IdType.DoubanBook
    URL_PATTERNS = [r"\w+://book\.douban\.com/subject/(\d+)/{0,1}", r"\w+://m.douban.com/book/subject/(\d+)/{0,1}"]
    WIKI_PROPERTY_ID = '?'
    DEFAULT_MODEL = Edition

    @classmethod
    def id_to_url(self, id_value):
        return "https://book.douban.com/subject/" + id_value + "/"

    def scrape(self):
        content = DoubanDownloader(self.url).download().html()

        isbn_elem = content.xpath("//div[@id='info']//span[text()='ISBN:']/following::text()")
        isbn = isbn_elem[0].strip() if isbn_elem else None

        title_elem = content.xpath("/html/body//h1/span/text()")
        title = title_elem[0].strip() if title_elem else f"Unknown Title {self.id_value}"

        subtitle_elem = content.xpath(
            "//div[@id='info']//span[text()='副标题:']/following::text()")
        subtitle = subtitle_elem[0].strip()[:500] if subtitle_elem else None

        orig_title_elem = content.xpath(
            "//div[@id='info']//span[text()='原作名:']/following::text()")
        orig_title = orig_title_elem[0].strip()[:500] if orig_title_elem else None

        language_elem = content.xpath(
            "//div[@id='info']//span[text()='语言:']/following::text()")
        language = language_elem[0].strip() if language_elem else None

        pub_house_elem = content.xpath(
            "//div[@id='info']//span[text()='出版社:']/following::text()")
        pub_house = pub_house_elem[0].strip() if pub_house_elem else None

        pub_date_elem = content.xpath(
            "//div[@id='info']//span[text()='出版年:']/following::text()")
        pub_date = pub_date_elem[0].strip() if pub_date_elem else ''
        year_month_day = RE_NUMBERS.findall(pub_date)
        if len(year_month_day) in (2, 3):
            pub_year = int(year_month_day[0])
            pub_month = int(year_month_day[1])
        elif len(year_month_day) == 1:
            pub_year = int(year_month_day[0])
            pub_month = None
        else:
            pub_year = None
            pub_month = None
        if pub_year and pub_month and pub_year < pub_month:
            pub_year, pub_month = pub_month, pub_year
        pub_year = None if pub_year is not None and pub_year not in range(
            0, 3000) else pub_year
        pub_month = None if pub_month is not None and pub_month not in range(
            1, 12) else pub_month

        binding_elem = content.xpath(
            "//div[@id='info']//span[text()='装帧:']/following::text()")
        binding = binding_elem[0].strip() if binding_elem else None

        price_elem = content.xpath(
            "//div[@id='info']//span[text()='定价:']/following::text()")
        price = price_elem[0].strip() if price_elem else None

        pages_elem = content.xpath(
            "//div[@id='info']//span[text()='页数:']/following::text()")
        pages = pages_elem[0].strip() if pages_elem else None
        if pages is not None:
            pages = int(RE_NUMBERS.findall(pages)[
                        0]) if RE_NUMBERS.findall(pages) else None
            if pages and (pages > 999999 or pages < 1):
                pages = None

        brief_elem = content.xpath(
            "//h2/span[text()='内容简介']/../following-sibling::div[1]//div[@class='intro'][not(ancestor::span[@class='short'])]/p/text()")
        brief = '\n'.join(p.strip()
                          for p in brief_elem) if brief_elem else None

        contents = None
        try:
            contents_elem = content.xpath(
                "//h2/span[text()='目录']/../following-sibling::div[1]")[0]
            # if next the id of next sibling contains `dir`, that would be the full contents
            if "dir" in contents_elem.getnext().xpath("@id")[0]:
                contents_elem = contents_elem.getnext()
                contents = '\n'.join(p.strip() for p in contents_elem.xpath(
                    "text()")[:-2]) if contents_elem is not None else None
            else:
                contents = '\n'.join(p.strip() for p in contents_elem.xpath(
                    "text()")) if contents_elem is not None else None
        except Exception:
            pass

        img_url_elem = content.xpath("//*[@id='mainpic']/a/img/@src")
        img_url = img_url_elem[0].strip() if img_url_elem else None

        # there are two html formats for authors and translators
        authors_elem = content.xpath("""//div[@id='info']//span[text()='作者:']/following-sibling::br[1]/
            preceding-sibling::a[preceding-sibling::span[text()='作者:']]/text()""")
        if not authors_elem:
            authors_elem = content.xpath(
                """//div[@id='info']//span[text()=' 作者']/following-sibling::a/text()""")
        if authors_elem:
            authors = []
            for author in authors_elem:
                authors.append(RE_WHITESPACES.sub(' ', author.strip())[:200])
        else:
            authors = None

        translators_elem = content.xpath("""//div[@id='info']//span[text()='译者:']/following-sibling::br[1]/
            preceding-sibling::a[preceding-sibling::span[text()='译者:']]/text()""")
        if not translators_elem:
            translators_elem = content.xpath(
                """//div[@id='info']//span[text()=' 译者']/following-sibling::a/text()""")
        if translators_elem:
            translators = []
            for translator in translators_elem:
                translators.append(RE_WHITESPACES.sub(' ', translator.strip()))
        else:
            translators = None

        cncode_elem = content.xpath(
            "//div[@id='info']//span[text()='统一书号:']/following::text()")
        cubn = cncode_elem[0].strip() if cncode_elem else None

        series_elem = content.xpath(
            "//div[@id='info']//span[text()='丛书:']/following-sibling::a[1]/text()")
        series = series_elem[0].strip() if series_elem else None

        imprint_elem = content.xpath(
            "//div[@id='info']//span[text()='出品方:']/following-sibling::a[1]/text()")
        producer = imprint_elem[0].strip() if imprint_elem else None

        data = {
            'title': title,
            'subtitle': subtitle,
            'orig_title': orig_title,
            'author': authors,
            'translator': translators,
            'language': language,
            'pub_house': pub_house,
            'pub_year': pub_year,
            'pub_month': pub_month,
            'binding': binding,
            'price': price,
            'pages': pages,
            'isbn': isbn,
            'cubn': cubn,
            'brief': brief,
            'contents': contents,
            'series': series,
            'producer': producer,
            'cover_image_url': img_url,
        }

        works_element = content.xpath('//h2/span[text()="这本书的其他版本"]/following-sibling::span[@class="pl"]/a/@href')
        if works_element:
            r = re.match(r'\w+://book.douban.com/works/(\d+)', works_element[0])
            data['required_resources'] = [{
                'model': 'Work',
                'id_type': IdType.DoubanBook_Work,
                'id_value': r[1] if r else None,
                'title': data['title'],
                'url': works_element[0],
            }]

        pd = ResourceContent(metadata=data)
        pd.lookup_ids[IdType.ISBN] = isbn
        pd.lookup_ids[IdType.CUBN] = cubn
        pd.cover_image, pd.cover_image_extention = BasicImageDownloader.download_image(img_url, self.url)
        return pd


@SiteList.register
class DoubanBook_Work(AbstractSite):
    ID_TYPE = IdType.DoubanBook_Work
    URL_PATTERNS = [r"\w+://book\.douban\.com/works/(\d+)"]
    WIKI_PROPERTY_ID = '?'
    DEFAULT_MODEL = Work

    @classmethod
    def id_to_url(self, id_value):
        return "https://book.douban.com/works/" + id_value + "/"

    def bypass_scrape(self, data_from_link):
        if not data_from_link:
            return None
        pd = ResourceContent(metadata={
            'title': data_from_link['title'],
        })
        return pd

    def scrape(self):
        content = DoubanDownloader(self.url).download().html()
        title_elem = content.xpath("//h1/text()")
        title = title_elem[0].split('全部版本(')[0].strip() if title_elem else None
        if not title:
            raise ParseError(self, 'title')
        pd = ResourceContent(metadata={
            'title': title,
        })
        return pd
