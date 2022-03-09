import re

import scrapy
from loguru import logger

import datetime


class MissingDataSelector:
    def __init__(self):
        pass

    def get(self):
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
            return MissingDataSelector if first_only else selected_selector
        else:
            return selected_selector[0] if first_only else selected_selector

    def _get_title(self, metadata_selector):

        xpaths = {
            "title": 'div[@class="FactsSection-1460e"]/div[@class="mainFacts-1b550"]/div[@class="FactsContainer-73861"]/h2/text()',
            "subtitle": 'div[@class="FactsSection-1460e"]/div[@class="mainFacts-1b550"]/div[@class="FactsContainer-73861"]/div[@class="ProjectFacts-fc5f2 fact-ab1cd"]/div[i/text()="home"]/span/text()',
        }

        titles = {}
        for k in xpaths:
            titles[k] = self.__select_first_from_selector(
                metadata_selector, xpaths[k]
            ).get()

        return titles

    def _get_address(self, metadata_selector):
        address_xpath = 'p[@class="nbk-paragraph nbk-truncate"]/text()'
        address = self.__select_first_from_selector(metadata_selector, address_xpath)

        return {"address": address}

    def _get_price_size(self, metadata_selector):
        price_size_xpath = (
            'div[@class="FactsSection-1460e"]/div[@class="mainFacts-1b550"]/div[@class="FactsContainer-73861"]/div[div[@data-test="price"]]/div'
        )

        price_size_selectors = self.__select_first_from_selector(
            metadata_selector, price_size_xpath, first_only=False
        )

        if not len(price_size_selectors) == 3:
            logger.warning(
                f"can not find all the price and size info."
                f"found {len(price_size_selectors)} while 3 is needed: {price_size_selectors}"
            )

        price_size = {
            i.xpath('@data-test').get(): f"{i.xpath('div/text()').get()}{i.xpath('div/div/text()').get()}"
            for i in price_size_selectors
        }
        price_size["size"] = price_size.pop("area")

        return price_size

    def _get_link(self, metadata_selector):

        link_xpath = '@href'
        link = self.__select_first_from_selector(metadata_selector, link_xpath).extract()

        return {
            "id": link.replace("https://www.immowelt.de", ""),
            "link": link
        }

    def parse(self, selector):
        return self.get_all_metadata(selector)


class QuotesSpider(scrapy.Spider):
    name = "immowelt"
    potential_urls = {
        "berlin": "https://www.immowelt.de/liste/berlin/wohnungen/kaufen?sort=relevanz"
    }

    berlin_urls = [
        f"https://www.immowelt.de/liste/berlin/wohnungen/kaufen?d=true&sd=DESC&sf=RELEVANCE&sp={page}"
        for page in range(100)
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

            logger.debug(property_data)
            yield property_data

        # next_page_xpath = '//div[@class="nbk-flex nbk-justify-between nbk-items-center nbk-p-3 lg:nbk-p-0 nbk-mt-8"]/a[last()]/@href'

        # next_page = response.selector.xpath(next_page_xpath).get()
        # if isinstance(next_page, list) and len(next_page) > 0:
        #     next_page = next_page[-1]
        # if next_page:
        #     yield response.follow(next_page, callback=self.parse)
