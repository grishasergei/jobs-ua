import scrapy


class DouUaSpider(scrapy.Spider):
    name = 'dou.ua'
    start_urls = [
        'https://jobs.dou.ua/vacancies/?'
    ]

    def parse(self, response):
        matches = response.xpath('//script//text()').re(r'CSRF_TOKEN.*"(.*)\"')
        if matches:
            csrf_token = matches[0]
            
        job_urls = response.xpath('//a[@class="vt"]').extract()
