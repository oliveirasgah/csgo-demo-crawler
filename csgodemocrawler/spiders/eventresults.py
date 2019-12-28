# -*- coding: utf-8 -*-
import json
import re
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
        for rel_match_url in response.xpath('//div[contains(@class, "result-con")]//a/@href').extract():
            abs_match_url = response.urljoin(rel_match_url)
            yield scrapy.Request(abs_match_url, self.scrape_match_page)


    def scrape_match_page(self, response):
        ''' Scrapes match page for relevant metadata info and for the GOTV-demo download URL '''
        rel_gotv_demo_url = response\
            .xpath('//div[contains(@class, "streams")]//a[contains(@href, "demo")]/@href')\
            .get()

        if not rel_gotv_demo_url:
            return

        abs_gotv_demo_url = response.urljoin(rel_gotv_demo_url)

        team_names = response\
            .xpath('//div[contains(@class, "teamsBox")]//div[@class="team"]//div[@class="teamName"]//text()')\
            .extract()

        team_1 = team_names[0]
        team_2 = team_names[1]

        match_format_raw = response\
            .xpath('///div[@class="match-page"]//div[contains(@class, "veto-box")][1]//div/text()')\
            .get()

        if match_format_raw:
            m = re.match(r'^Best of ([0-9]{1})', match_format_raw.strip())
            match_format = m.group(1)

        if match_format and int(match_format) > 1:
            raw_draft = response\
                .xpath('//div[@class="match-page"]//div[contains(@class, "veto-box")][2]//div/text()')\
                .extract()

            raw_draft = [draft_step for draft_step in raw_draft if draft_step.strip() != '']
            draft = []

            for choice in raw_draft:
                if choice.find(team_1) < 0 and choice.find(team_2) < 0:
                    # default pick
                    continue

                if choice.find(team_1) >= 0:
                    # 1st team's choice
                    team = team_1[:]
                    choice = choice.replace(team, '').strip()

                elif choice.find(team_2) >= 0:
                    # 2nd team's choice
                    team = team_2[:]
                    choice = choice.replace(team, '').strip()

                tokens = choice.split(' ')

                action = tokens[2].strip()
                chosen_map = tokens[3].strip()

                draft.append({
                    'team': team,
                    'action': action,
                    'map': chosen_map
                })

        print()
        print(f'Match URL :: {response.url}')
        print(f'Teams :: {team_1} VS {team_2}')
        print(f'Match Format :: bo{str(match_format)}')
        print(json.dumps(draft, indent=4))
        print()

        # initializing match manifest with competing teams & GOTV-demo URL
        match_info = {
            'teams': team_names,
            'match_url': response.url,
            'gotv_demo_url': abs_gotv_demo_url
        }

        # saving draft info - if available
        if raw_draft:
            match_info['draft'] = raw_draft
            match_info['parsed_draft'] = draft

        if 'matches' not in self.event_manifest:
            self.event_manifest['matches'] = []
        # appending match info to manifest
        self.event_manifest['matches'].append(match_info)
