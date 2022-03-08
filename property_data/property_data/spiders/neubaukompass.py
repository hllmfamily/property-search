from ctypes import addressof
import scrapy


class ParserOneProperty:
    def __init__(self) -> None:
        self.name = "neubaukompass"

    def get_all_metadata(self, selector) -> dict:
        metadata_selector = selector.xpath('//div[@class="nbk-px-2 nbk-pt-2 md:nbk-px-3 md:nbk-pt-3"]')

        metadata = {}

        metadata.update(self._get_title(metadata_selector))

        metadata.update(self._get_price_size(metadata_selector))

        return metadata

    def _get_title(self, metadata_selector):
        title_selector = metadata_selector.xpath('//div[@class="nbk-w-full nbk-flex nbk-flex-wrap nbk-justify-between nbk-items-top nbk-mt-3"]/a/h2')

        title = title_selector.xpath('//span[@class="nbk-block nbk-truncate nbk-pb-1"]/text()')
        subtitle = title_selector.xpath('//span[@class="nbk-block nbk-truncate nbk-text-base nbk-font-normal"]/text()')

        return {
            "title": title,
            "subtitle": subtitle
        }

    def _get_address(self, metadata_selector):
        address_xpath = '//p[@class="nbk-paragraph nbk-truncate"]/text()'
        return {
            "address": metadata_selector.xpath(address_xpath)
        }

    def _get_price_size(self, metadata_selector):
        price_size_xpath = 'div[@class="nbk-grid nbk-grid-cols-1 lg:nbk-grid-cols-2 nbk-gap-4"]'

        price_size_selector = metadata_selector.xpath(price_size_xpath)

        keys = ["price", "size", "rooms", "when"]
        values = []
        for i in price_size_selector:
            values.append(i.xpath('text()').extract())

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
        for property in response.selector.xpath('//div[@class="nbk-p-3 nbk-w-full md:nbk-w-1/2"]/article'):
            parser = ParserOneProperty()
            print(parser.parse(property))
            # yield quoteg
            # yield {
            #     'title': quote.css('span.nbk-block.nbk-truncate.nbk-pb-1').get(),
            #     'author': quote.css('small.author::text').get(),
            #     'tags': quote.css('div.tags a.tag::text').getall(),
            # }

            # next_page = response.css('li.next a::attr(href)').get()
            # if next_page is not None:
            #     yield response.follow(next_page, callback=self.parse)
