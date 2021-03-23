# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import json

class EventResultsPipeline(object):
    def open_spider(self, spider):
        if spider.name == 'eventresults':
            print('Initializing manifest dictionary')
            # initializing event-manifest dictionary
            spider.event_manifest = {}

    def close_spider(self, spider):
        if spider.name == 'eventresults':
            # an 'eventresults' spider scrapes all metadata
            #    pertaining to an event and all of its matches
            #    GOTV-demo URLs; so, since we're closing this
            #    spider, we can confidently assume that all data
            #    pertaining to this event has been parsed and is
            #    available for exporting:
            if 'event_name' in spider.event_manifest:
                file_name = '-'.join(spider.event_manifest['event_name'].split(' ')) + '.json'
                # exporting event-manifest
                with open(file_name, 'w+') as fout:
                    fout.write(json.dumps(spider.event_manifest, indent=4))
