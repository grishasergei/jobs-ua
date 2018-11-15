import scrapy


class WorkUaSpider(scrapy.Spider):
    name = 'work.ua'
    start_urls = [
        'https://www.work.ua/jobs/by-category/'
    ]

    def parse(self, response):
        only_job_category = getattr(self, 'only_job_category', None)
        if only_job_category:
            job_categories_href = ['https://www.work.ua/jobs-{}/'.format(only_job_category)]
        else:
            job_categories_href = response.xpath('//*[@id="js-ajax-container"]').xpath('.//li//@href').extract()
            job_categories_href = job_categories_href[:-3]

        self.logger.info('Found {} job categories to parse'.format(len(job_categories_href)))

        for job_category_href in job_categories_href:
            job_category = job_category_href.split('/')[-2][5:]
            yield response.follow(job_category_href, callback=self.parse_job_category, meta={'category': job_category})

    def parse_job_category(self, response):
        self.logger.info('Parsing ' + response.url)

        jobs = response.xpath('//h2[@class="add-bottom-sm"]//a')
        job_category = response.meta.get('category')

        for job in jobs:
            yield response.follow(job, callback=self.parse_job, meta={'category': job_category})

        next_page = response.xpath('//a[text()="Наступна"]/@href').extract_first()
        if next_page:
            yield response.follow(next_page, callback=self.parse_job_category, meta={'category': job_category})

    def parse_job(self, response):
        # self.logger.info('Parsing ' + response.url)
        yield {
            'job title':  response.xpath('//*[@id="h1-name"]/text()').extract_first(),
            'salary': ' '.join(response.xpath('//*[@id="center"]/div/div[2]/div[1]/div[3]/div/h3//text()').extract()),
            'company': response.xpath('//*[text()="Компанія:"]/following-sibling::dd[1]/a//text()').extract_first(),
            'location': response.xpath('//*[text()="Місто:"]/following::dd/text()').extract_first(),
            'description': ' '.join(response.xpath('.//node()[preceding-sibling::*="Опис вакансії"][following-sibling::div[@class="form-group hidden-print"]]//text()').extract()),
            'category': response.meta.get('category'),
            'id': response.url.split('/')[-2],
            'url': response.url,
            'advertiser': 'work.ua',
        }

