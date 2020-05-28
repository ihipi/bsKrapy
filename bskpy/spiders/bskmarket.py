# -*- coding: utf-8 -*-
import scrapy
import re
from scrapy import Request
from scrapy.loader import ItemLoader

from bskpy.items import BskpyItem


class BskmarketSpider(scrapy.Spider):
    name = 'bskmarket'
    allowed_domains = ['labsk.net']
    start_urls = ['http://labsk.net/index.php?board=22.0/']
    titleCellsClass = "subject lockedbg2"
    currentPage = 0
    maxNextPageIterations = 3

    def __init__(self, name=None, jocs="", **kwargs):
        super().__init__(name, **kwargs)
        self.jocs = jocs.split(",")

    def start_requests(self):
        return [Request(url=self.start_urls[0], callback=self.login)]

    def login(self, response):
        inputs = response.xpath('//input')
        print(inputs[-2].attrib['name'], inputs[-2].attrib['value'])
        return scrapy.FormRequest('http://labsk.net/index.php?action=login2',
                                  formdata={'user': 'xxxx@yahoo.com', 'passwrd': 'xxxx',
                                            'cockielength': '120',
                                            inputs[-2].attrib['name']: inputs[-2].attrib['value'],
                                            inputs[-1].attrib['name']: inputs[-1].attrib['value']},
                                  callback=self.parse, dont_filter=True)

    def parse(self, response):
        """
        for post in response.xpath('//td[@class="' + self.titleCellsClass + '"]/div/span/a'):
            yield {
                "title": post.css('a::text').get(),
                "link": post.xpath('//a/@href').get()
            }
        """
        postLinks = response.xpath('//td[@class="' + self.titleCellsClass + '"]/div/span/a/@href')
        yield from response.follow_all(postLinks, self.parsePost)
        nextPage = self.getNextPage()
        if nextPage is not None:
            yield response.follow(nextPage, callback=self.parse)

    def parsePost(self, response):
        text = response.xpath('string(//div[@class="inner"])').extract()
        titol = response.xpath('//div[@class="keyinfo"]/h5/a/text()').get()
        if (len(self.jocs) > 0):
            for joc in self.jocs:
                if re.search(r"({})".format(joc), text[0], re.IGNORECASE):
                    yield {
                        "joc": joc,
                        "title": titol,
                        "text": text,
                        "link": response.url
                    }
                    l = ItemLoader(item=BskpyItem(), response=response)
                    l.add_value('joc', joc)
                    l.add_value('title', titol)
                    l.add_value('url', response.url)
                    l.add_value('text', text)
                    return l.load_item()

        else:
            yield {
                "title": titol,
                "text": text,
                "link": response.url
            }

    def getNextPage(self):
        if self.currentPage < self.maxNextPageIterations:
            self.currentPage += 1
            return "http://labsk.net/index.php?board=22." + str(20 * self.currentPage)
