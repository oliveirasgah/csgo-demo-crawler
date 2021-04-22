# -*- coding: utf-8 -*-

''' Event Results Page XPATH accessors '''

# The event name
get_event_name = lambda resp: resp\
    .xpath('//div[contains(@class, "eventname")]/text()')\
    .get()

# The location of the event
get_location = lambda resp: resp\
    .xpath('//td[contains(@class, "location")]//span/text()')\
    .get()

# The amount of team participating on the champtionship
get_teams_amount = lambda resp: resp\
    .xpath('//td[@class="teamsNumber"]/text()')\
    .get()

# The prizepool of the championship
get_prizepool = lambda resp: resp\
    .xpath('//td[contains(@class, "prizepool")]/text()')\
    .get()

# The championship date span
get_date_span = lambda resp: resp\
    .xpath('//td[@class="eventdate"]//span/text()')\
    .extract()

# The match URLs
get_match_urls = lambda resp: resp\
    .xpath('//div[contains(@class, "result-con")]//a/@href')\
    .extract()


''' Match Page XPATH accessors '''

# The GOTV-demo URL
get_gotv_demo_url = lambda resp: resp\
    .xpath('//div[contains(@class, "streams")]//a[contains(@href, "demo")]/@href')\
    .get()

# The match date
get_match_date = lambda resp: resp\
    .xpath('//div[@class="timeAndEvent"]/div[@class="date"]/text()')\
    .get()

# The team names
get_team_names = lambda resp: resp\
    .xpath('//div[@class="match-page"]//div[@class="team"]//div[@class="teamName"]//text()')\
    .extract()

# TODO: docs
get_lineup_containers = lambda resp: resp\
    .xpath('//div[contains(@class, "lineup") and @class != "lineups"]')

# TODO: docs
get_lineup_team = lambda container: container\
    .xpath('./div/div/a[not(contains(@href, "rank"))]//text()')\
    .get()

# TODO: docs
get_lineup_players = lambda container: container\
    .xpath('.//td[@class="player"]/a/div/div//text()')\
    .extract()

# .xpath('./div[@class="players"]/table/tbody/tr/td[@class="player"]/a/div/div//text()')\

# The match format (e.g. bo2, bo3..)
get_match_format = lambda resp: resp\
    .xpath('//div[@class="match-page"]//div[contains(@class, "veto-box")][1]//div/text()')\
    .get()

# The raw draft information
get_raw_draft_info = lambda resp: resp\
    .xpath('//div[@class="match-page"]//div[contains(@class, "veto-box")][2]//div/text()')\
    .extract()

# The maps played in this match
get_played_maps_containers = lambda resp: resp\
    .xpath('//div[@class="mapholder"]')

# The name of the played map (within supplied container)
get_map_name = lambda container: container\
    .xpath('./div[contains(@class, "played")]//div[contains(@class, "mapname")]/text()')\
    .get()

# The results fo the map (within supplied container)
get_map_results_container = lambda container: container\
    .xpath('./div[contains(@class, "results")]//*[contains(@class, "results-teamname-container")]')

# The team name to whom this result pertains to
get_map_result_teamname = lambda container: container\
    .xpath('./div[contains(@class, "results-teamname")]/text()')\
    .get()

# The resultant score of the map
get_map_result_score = lambda container: container\
    .xpath('./div[contains(@class, "results-team-score")]/text()')\
    .get()

''' Scraping sub-routines '''

def get_draft_info(response, teams):
    ''' Parses and structures the scraped draft info '''
    raw_draft = get_raw_draft_info(response)
    raw_draft = [draft_step for draft_step in raw_draft if draft_step.strip() != '']

    team_1 = teams[0]
    team_2 = teams[1]

    draft = []
    for choice in raw_draft:
        if choice.find(team_1) < 0 and choice.find(team_2) < 0:
            # default pick
            # TODO: parse default cases
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

    return draft

def get_played_maps_info(response):
    ''' Parses map info from its scraped HTML container '''
    # getting played maps HTML containers
    played_maps_containers = get_played_maps_containers(response)

    played_maps = []

    # for each played map container, we look for the desired info:
    for idx, map_container in enumerate(played_maps_containers):
        # scraping map name
        map_name = get_map_name(map_container)

        if not map_name:
            # probably an unplayed map
            #   (match decided in the previous maps)
            continue

        map_info = {
            'map': map_name,
            'scores': []
        }

        # getting results container
        results_container = get_map_results_container(map_container)

        # scraping each team name & score
        for result_container in results_container:
            team_name = get_map_result_teamname(result_container)
            score = get_map_result_score(result_container)

            map_info['scores'].append({
                'team': team_name,
                'score': score
            })

        played_maps.append(map_info)

    return played_maps
    

def get_lineups(response):
    ''' Parses the teams and players that compose the different
    lineups competing in the match '''
    lineups = {}
    lineup_containers = get_lineup_containers(response)

    for lineup_container in lineup_containers:
        team_name = get_lineup_team(lineup_container)
        if team_name not in lineups:
            lineups[team_name] = []

        players = get_lineup_players(lineup_container)
        for player in players:
            lineups[team_name].append(player)

    return lineups