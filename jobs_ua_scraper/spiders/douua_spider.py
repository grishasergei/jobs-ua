import scrapy
import json
from datetime import datetime


class DouUaSpider(scrapy.Spider):
    name = 'dou.ua'
    start_urls = [
        'https://jobs.dou.ua'
    ]
    headers = {
     'Accept': 'application/json, text/javascript, */*; q=0.01',
     'Accept-Encoding': 'gzip, deflate, br',
     'Accept-Language': 'en-US,en;q=0.8,ru;q=0.6,sv;q=0.4',
     'Connection': 'keep-alive',
     'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
     'Host': 'jobs.dou.ua',
     'Origin': 'https://jobs.dou.ua',
     'Referer': 'https://jobs.dou.ua/vacancies/?',
     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
     'X-Requested-With': 'XMLHttpRequest'
    }
    cookies = {
        'lang': 'en',
        '_gat': '1',
    }

    def parse(self, response):
        matches = response.xpath('//script//text()').re(r'CSRF_TOKEN.*"(.*)\"')
        if matches:
            csrf_token = matches[0]

        self.logger.info('CSRF token: ' + csrf_token)

        yield scrapy.FormRequest('https://jobs.dou.ua/vacancies/xhr-load/?',
                                 headers=self.headers,
                                 cookies={
                                     **self.cookies,
                                     **{'csrftoken': csrf_token}
                                 },
                                 formdata={
                                     'csrfmiddlewaretoken': csrf_token,
                                     'count': '0'
                                 },
                                 method='POST',
                                 meta={'csrf_token': csrf_token},
                                 callback=self.parse_jobs,
                                 dont_filter=True)

    def parse_jobs(self, response):
        csrf_token = response.meta.get('csrf_token')
        data = json.loads(response.body)

        selector = scrapy.Selector(text=data['html'], type='html')
        job_urls = selector.xpath('//a[@class="vt"]/@href').extract()
        for job_url in job_urls:
            self.logger.debug(job_url)
            yield response.follow(job_url,
                                  callback=self.parse_job,
                                  encoding='utf-8',
                                  headers=self.headers,
                                  cookies={
                                      **self.cookies,
                                      **{'csrftoken': csrf_token}
                                  })

        count = response.meta.get('count')
        if not count:
            count = 0
        else:
            count = int(count)

        if not data['last']:
            self.logger.info('Parsing {}...'.format(count))
            yield scrapy.FormRequest('https://jobs.dou.ua/vacancies/xhr-load/?',
                                     headers=self.headers,
                                     cookies={
                                         **self.cookies,
                                         **{'csrftoken': csrf_token}
                                     },
                                     formdata={
                                         'csrfmiddlewaretoken': csrf_token,
                                         'count': '{}'.format(count)
                                     },
                                     method='POST',
                                     meta={
                                         'csrf_token': csrf_token,
                                         'count': '{}'.format(count + data['num'])
                                     },
                                     callback=self.parse_jobs,
                                     dont_filter=True)
        else:
            self.logger.info('LAST')

    def parse_job(self, response):
        self.logger.debug('Parsing {}'.format(response.url))
        yield {
            'position': response.xpath('//h1[@class="g-h2"]//text()').extract_first(),
            'salary': response.xpath('//span[@class="salary"]//text()').extract_first(),
            'company': response.xpath('//div[@class="l-n"]/a/text()').extract_first(),
            'location': response.xpath('//span[@class="place"]//text()').extract_first(),
            'description': ' '.join(response.xpath('//div[@class="l-vacancy"]//p//text()').extract()),
            'category': 'it',
            'id': response.url.split('/')[6],
            'url': response.url,
            'advertiser': 'dou.ua',
            'date': datetime.today().strftime('%Y-%m-%d')
        }
