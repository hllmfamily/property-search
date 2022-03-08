from re import sub
import scrapy
from loguru import logger
import re


class MissingDataSelector:
    def __init__(self):
        pass

    def get(self):
        return None


class ParserOneProperty:
    def __init__(self) -> None:
        self.name = "neubaukompass"

    def get_all_metadata(self, selector) -> dict:
        metadata_selector = selector.xpath('div[@class="nbk-px-2 nbk-pt-2 md:nbk-px-3 md:nbk-pt-3"]')

        if len(metadata_selector) > 0:
            metadata_selector = metadata_selector[0]
        else:
            self.__error(metadata_selector)

        metadata = {}
        metadata.update(self._get_title(metadata_selector))
        metadata.update(self._get_price_size(metadata_selector))

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
            logger.error(f"can not select xpath ({xpath}) from the selector: {selector}\n{e}")

        if self.__error(selected_selector):
            return MissingDataSelector if first_only else selected_selector
        else:
            return selected_selector[0] if first_only else selected_selector

    def _get_title(self, metadata_selector):

        titles_xpath = 'div[@class="nbk-w-full nbk-flex nbk-flex-wrap nbk-justify-between nbk-items-top nbk-mt-3"]/a/h2'
        title_selector = self.__select_first_from_selector(metadata_selector, titles_xpath)

        xpaths = {
            'title': 'span[@class="nbk-block nbk-truncate nbk-pb-1"]/text()',
            'subtitle': 'span[@class="nbk-block nbk-truncate nbk-text-base nbk-font-normal"]/text()'
        }

        titles = {}
        for k in xpaths:
            titles[k] = self.__select_first_from_selector(title_selector, xpaths[k]).get()

        return titles

    def _get_address(self, metadata_selector):
        address_xpath = 'p[@class="nbk-paragraph nbk-truncate"]/text()'
        address = self.__select_first_from_selector(metadata_selector, address_xpath)

        return {
            "address": address
        }

    def _get_price_size(self, metadata_selector):
        price_size_xpath = 'div[@class="nbk-grid nbk-grid-cols-1 lg:nbk-grid-cols-2 nbk-gap-4"]/div/p'

        price_size_selectors = self.__select_first_from_selector(metadata_selector, price_size_xpath, first_only=False)

        if not len(price_size_selectors) == 4:
            logger.error(
                f"can not find all the price and size info."
                f"found {len(price_size_selectors)} while 4 is needed: {price_size_selectors}"
            )
            return {}
        else:
            keys = ["price", "size", "rooms", "when"]
            values = []
            for i in price_size_selectors:
                i_value = re.split("<|>", i.extract())[-3].strip()
                values.append(i_value)

            return dict(zip(keys, values))

    def parse(self, selector):
        return self.get_all_metadata(selector)


class QuotesSpider(scrapy.Spider):
    name = "neubaukompass"
    potential_urls = {
        "berlin": "https://www.neubaukompass.com/new-build-real-estate/berlin-region/"
    }


    def start_requests(self):
        urls = [
            u for _,u in self.potential_urls.items()
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):

        properties = []

        for property in response.selector.xpath('//div[@class="nbk-p-3 nbk-w-full md:nbk-w-1/2"]/article'):
            parser = ParserOneProperty()
            property_data = parser.parse(property)
            properties.append(property_data)

            logger.debug(property_data)
            yield property_data

        next_page_xpath = '//div[@class="nbk-flex nbk-justify-between nbk-items-center nbk-p-3 lg:nbk-p-0 nbk-mt-8"]/a[last()]/@href'
        # next_page = response.css('li.next a::attr(href)').get()
        next_page = response.selector.xpath(next_page_xpath).get()
        if isinstance(next_page, list) and len(next_page) > 0:
            next_page = next_page[-1]
        if next_page:
            yield response.follow(next_page, callback=self.parse)
