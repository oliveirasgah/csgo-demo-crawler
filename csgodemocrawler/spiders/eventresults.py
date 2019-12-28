# -*- coding: utf-8 -*-
import scrapy


class EventResultsSpider(scrapy.Spider):
    name = 'eventresults'
    allowed_domains = [ 'hltv.org' ]

    # TODO:
    # - Figure out whether we need to apply any anti-blocking strategies.

    def __init__(self, event_id, *args, **kwargs):
        ''' Constructor '''
        super(EventResultsSpider, self).__init__(*args, **kwargs)
        self.start_url = f'https://www.hltv.org/results?event={str(event_id)}'
        self.event_id = event_id
        print(f'Initializing spider, start_url :: {self.start_url}')


    def start_requests(self):
        ''' Defines starting URL '''
        yield scrapy.Request(self.start_url, self.scrape_event_page)


    def scrape_event_page(self, response):
        ''' Scrapes event page for match URLs yields them as they're found '''
        # scraping event metadata
        event_name = response.xpath('//div[contains(@class, "eventname")]/text()').get()
        location = response.xpath('//td[contains(@class, "location")]//span/text()').get()
        teams_amount = response.xpath('//td[@class="teamsNumber"]/text()').get()
        prizepool = response.xpath('//td[contains(@class, "prizepool")]/text()').get()

        dates = response.xpath('//td[@class="eventdate"]//span/text()').extract()
        # formatting date interval
        date_span = ' '.join(dates)

        print(f'\tEvent :: {event_name}')
        print(f'\tLocation :: {location}')
        print(f'\tTeams Amount :: {teams_amount}')
        print(f'\tPrize Pool :: {prizepool}')
        print(f'\tDate :: {date_span}')

        # adding metadata to event-manifest dictionary
        self.event_manifest['event_id'] = self.event_id
        self.event_manifest['event_name'] = event_name
        self.event_manifest['location'] = location
        self.event_manifest['teams_amount'] = teams_amount
        self.event_manifest['prizepool'] = prizepool
        self.event_manifest['date'] = date_span

        # scraping event match URLs & yielding them to next step in pipeline
        for rel_match_url in response.xpath('//div[contains(@class, "result-con")]//a/@href').extract():
            abs_match_url = response.urljoin(rel_match_url)
            print(f'Requesting page :: {abs_match_url}')
            yield scrapy.Request(abs_match_url, self.scrape_match_page)


    def scrape_match_page(self, response):
        ''' Scrapes match page for relevant metadata info and for the GOTV-demo download URL '''
        rel_gotv_demo_url = response.xpath('//div[contains(@class, "streams")]//a[contains(@href, "demo")]/@href').get()

        if not rel_gotv_demo_url:
            return

        team_names = response.xpath('//div[contains(@class, "teamsBox")]//div[@class="team"]//div[@class="teamName"]//text()').extract()
        print(team_names)

        abs_gotv_demo_url = response.urljoin(rel_gotv_demo_url)
        print(f'GOTV-Demo URL :: {abs_gotv_demo_url}')

        # initializing match manifest with competing teams & GOTV-demo URL
        match_manifest = {
            'teams': team_names,
            'match_url': response.url,
            'gotv_demo_url': abs_gotv_demo_url
        }

        if 'matches' not in self.event_manifest:
            self.event_manifest['matches'] = []

        # adding to event-manifest dictionary
        self.event_manifest['matches'].append(match_manifest)
