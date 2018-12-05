import scrapy
from datetime import datetime


class RabotaUaSpider(scrapy.Spider):
    name = 'rabota.ua'
    start_urls = [
        u'https://rabota.ua/ua/вакансии'
    ]

    def parse(self, response):
        job_category = getattr(self, 'job_category', None)
        if job_category:
            job_categories_href = [u'https://rabota.ua/вакансии/{}'.format(job_category)]
        else:
            job_categories_href = response.xpath('//div[contains(concat(" ", @class, " "), " f-rubrics-itemsblock ")]//li//a/@href').extract()

        self.logger.info('Found {} categories to scrape'.format(len(job_categories_href)))

        for job_category_href in job_categories_href:
            job_category = job_category_href.split('/')[-2]
            yield response.follow(job_category_href, callback=self.parse_job_category, meta={'job_category': job_category})

    def parse_job_category(self, response):
        self.logger.info('Parsing %s', response.url)

        job_category = response.meta.get('job_category')
        jobs = response.xpath('//h3[contains(concat(" ", normalize-space(@class), " "), " f-vacancylist-vacancytitle ")]//a/@href').extract()

        for job in jobs:
            yield response.follow(job, callback=self.parse_job, meta={'job_category': job_category})

        next_page = response.xpath('//dd[@class="nextbtn"]/a/@href').extract_first()
        if next_page:
            yield response.follow(next_page, callback=self.parse_job_category, meta={'job_category': job_category})

    def parse_job(self, response):
        title = response.xpath('//title/text()').extract_first()
        l = title.rfind('-') + 2
        r = title.rfind('|') - 1

        city = response.xpath('//li[@id="d-city"]//span[@class="d-ph-value"]/text()').extract_first()
        if not city:
            city = response.xpath('//span[@itemprop="city"]/text()').extract_first()

        position = response.xpath('//div[@class="d_content"]/h1/text()').extract_first()
        if not position:
            position = response.xpath('//h1[@itemprop="title"]/text()').extract_first()

        description = ' '.join(response.xpath('//div[@class="f-vacancy-description"]//text()').extract())
        if not description:
            description = ' '.join(response.xpath('.//node()[preceding-sibling::div[@class="d-items"]][following-sibling::*="Відправити резюме"]//text()').extract())

        salary = response.xpath('//span[@class="money"]/text()').extract_first()
        if not salary:
            salary = response.xpath('//li[@id="d-salary"]//span[@class="d-ph-value"]/text()').extract_first()

        yield {
            'position': position,
            'salary': salary,
            'company': title[l:r],
            'location': city,
            'description': description,
            'category': response.meta.get('job_category'),
            'id': response.url.split('/')[-1][7:],
            'url': response.url,
            'advertiser': 'rabota.ua',
            'date': datetime.today().strftime('%Y-%m-%d')
        }
