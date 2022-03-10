import re

import scrapy
from loguru import logger

import datetime


class MissingDataSelector:
    def __init__(self):
        pass

    def get(self):
        return None

    def extract(self):
        return None


class ParserOneProperty:
    def __init__(self) -> None:
        self.name = "immowelt"
        self.dt = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    def get_all_metadata(self, selector) -> dict:
        metadata_selector = selector.xpath('a')

        if len(metadata_selector) > 0:
            metadata_selector = metadata_selector[0]
        else:
            self.__error(metadata_selector)

        metadata = {}
        metadata.update(self._get_title(metadata_selector))
        metadata.update(self._get_price_size(metadata_selector))
        metadata.update(self._get_link(metadata_selector))

        metadata.update({"timestamp": self.dt})

        return metadata

    def __error(self, selector):

        if not selector:
            logger.error(f"can not find metadata from the selector: {selector}")
            return True
        else:
            return False

    def __select_first_from_selector(self, selector, xpath, first_only=True):
        try:
            selected_selector = selector.xpath(xpath)
        except Exception as e:
            logger.error(
                f"can not select xpath ({xpath}) from the selector: {selector}\n{e}"
            )

        if self.__error(selected_selector):
            mds = MissingDataSelector()
            return mds if first_only else selected_selector
        else:
            return selected_selector[0] if first_only else selected_selector

    def _get_title(self, metadata_selector):

        xpaths = {
            # "title": 'div[@class="FactsSection-1460e"]/div[@class="mainFacts-1b550"]/div[@class="FactsContainer-73861"]/h2/text()',
            # "subtitle": 'div[@class="FactsSection-1460e"]/div[@class="mainFacts-1b550"]/div[@class="FactsContainer-73861"]/div[@class="ProjectFacts-fc5f2 fact-ab1cd"]/div[i/text()="home"]/span/text()',
            "title": 'div[2]/div[1]/div[1]/h2/text()',
            "subtitle": './/div[i/text()="check"]/span/text()',
        }

        titles = {}
        for k in xpaths:
            titles[k] = self.__select_first_from_selector(
                metadata_selector, xpaths[k]
            ).get()

        return titles

    def _get_address(self, metadata_selector):

        xpaths = {
            "home": './/div[i/text()="home"]/span/text()',
            "address": './/div[i/text()="location"]/span/text()',
        }

        addresses = {}
        for k in xpaths:
            addresses[k] = self.__select_first_from_selector(
                metadata_selector, xpaths[k]
            ).get()

        return addresses

    def _get_price_size(self, metadata_selector):
        price_size_xpaths = {
            # 'div[@class="FactsSection-1460e"]/div[@class="mainFacts-1b550"]/div[@class="FactsContainer-73861"]/div[div[@data-test="price"]]/div'
            # 'div[2]/div[1]/div[1]/div[div[@data-test="price"]]/div'
            # 'div[2]/div[1]/div[1]/div[div[@data-test="price"]]/div'
            "price": './/div[@data-test="price"]/div/text()',
            "price_max": './/div[@data-test="price-max"]/text()',
            "size": './/div[@data-test="area"]/div/text()',
            "size_max": './/div[@data-test="area-max"]/text()',
            "rooms": './/div[@data-test="rooms"]/div/text()',
            "rooms_max": './/div[@data-test="rooms-max"]/text()',
        }

        prices_and_sizes = {}

        for k in price_size_xpaths:
            prices_and_sizes[k] = self.__select_first_from_selector(
                metadata_selector, price_size_xpaths[k]
            ).get()

        for k in ["price", "size", "rooms"]:
            prices_and_sizes[k] = (prices_and_sizes.get(k, "") or "") + (prices_and_sizes.pop(f"{k}_max", "") or "")

        return prices_and_sizes

    def _get_link(self, metadata_selector):

        link_xpath = '@href'
        link = self.__select_first_from_selector(metadata_selector, link_xpath).extract()

        if link:
            return {
                "id": link.replace("https://www.immowelt.de", ""),
                "link": link
            }
        else:
            return {}

    def parse(self, selector):
        return self.get_all_metadata(selector)


class QuotesSpider(scrapy.Spider):
    name = "immowelt"
    potential_urls = {
        "berlin": "https://www.immowelt.de/liste/berlin/wohnungen/kaufen?sort=relevanz"
    }

    berlin_urls = [
        f"https://www.immowelt.de/liste/berlin/wohnungen/kaufen?d=true&sd=DESC&sf=RELEVANCE&sp={page}"
        for page in range(1,10)
    ]

    def start_requests(self):
        urls = self.berlin_urls
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):

        properties = []

        for property in response.selector.xpath('//div[@data-test="searchlist"]/div'):
            parser = ParserOneProperty()
            property_data = parser.parse(property)
            properties.append(property_data)

            logger.info(f"Retrieved {len(property_data)} properties from {response.url}.")
            yield property_data

        # next_page_xpath = '//div[@class="nbk-flex nbk-justify-between nbk-items-center nbk-p-3 lg:nbk-p-0 nbk-mt-8"]/a[last()]/@href'

        # next_page = response.selector.xpath(next_page_xpath).get()
        # if isinstance(next_page, list) and len(next_page) > 0:
        #     next_page = next_page[-1]
        # if next_page:
        #     yield response.follow(next_page, callback=self.parse)
