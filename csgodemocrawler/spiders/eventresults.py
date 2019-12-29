# -*- coding: utf-8 -*-
import json
import re
import scrapy

from .. import scraping_functions


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
        event_name = scraping_functions.get_event_name(response)
        location = scraping_functions.get_location(response)
        teams_amount = scraping_functions.get_teams_amount(response)
        prizepool = scraping_functions.get_prizepool(response)

        dates = scraping_functions.get_date_span(response)
        # formatting date interval
        date_span = ' '.join(date.strip() for date in dates)

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
        for rel_match_url in scraping_functions.get_match_urls(response):
            abs_match_url = response.urljoin(rel_match_url)
            yield scrapy.Request(abs_match_url, self.scrape_match_page)


    def scrape_match_page(self, response):
        ''' Scrapes match page for relevant metadata info and for the GOTV-demo download URL '''
        # scraping gotv demo url
        rel_gotv_demo_url = scraping_functions.get_gotv_demo_url(response)

        # skipping this page if no demo is available
        if not rel_gotv_demo_url: 
            return
        abs_gotv_demo_url = response.urljoin(rel_gotv_demo_url)

        # extract match id from URL
        m = re.search(r'\/matches\/([0-9]+)\/', response.url)
        match_id = m.group(1)

        # scraping team names
        team_names = scraping_functions.get_team_names(response)

        team_1 = team_names[0]
        team_2 = team_names[1]

        match_format_raw = scraping_functions.get_match_format(response)

        # scraping match format {bo1, bo2, ..}
        if match_format_raw:
            m = re.match(r'^Best of ([0-9]{1})', match_format_raw.strip())
            match_format = m.group(1)

        # if the match format was bo2 or higher,
        #   there was a draft to select the maps
        if match_format and int(match_format) > 1:
            draft = scraping_functions.get_draft_info(response, team_names)

        # scraping results of maps played in this match
        maps_played = scraping_functions.get_played_maps_info(response)

        print()
        print(f'Match URL :: {response.url}')
        print(f'Teams :: {team_1} VS {team_2}')
        print(f'Match Format :: bo{str(match_format)}')
        print(json.dumps(draft, indent=4))
        print(json.dumps(maps_played, indent=4))
        print()

        # initializing match manifest with competing teams & GOTV-demo URL
        match_info = {
            'match_id': match_id,
            'match_date': scraping_functions.get_match_date(response),
            'match_url': response.url,
            'gotv_demo_url': abs_gotv_demo_url,
            'teams': team_names,
        }

        # saving draft info - if available
        if draft: match_info['draft'] = draft

        match_info['maps'] = maps_played

        if 'matches' not in self.event_manifest:
            self.event_manifest['matches'] = []
        # appending match info to manifest
        self.event_manifest['matches'].append(match_info)
