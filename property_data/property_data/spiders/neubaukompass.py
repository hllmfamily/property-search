import scrapy


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
        for quote in response.css('div.nbk-px-2'):
            print(quote)
            # yield quote
            # yield {
            #     'title': quote.css('span.nbk-block.nbk-truncate.nbk-pb-1').get(),
            #     'author': quote.css('small.author::text').get(),
            #     'tags': quote.css('div.tags a.tag::text').getall(),
            # }

            # next_page = response.css('li.next a::attr(href)').get()
            # if next_page is not None:
            #     yield response.follow(next_page, callback=self.parse)
