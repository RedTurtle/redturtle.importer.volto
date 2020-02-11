# -*- coding: utf-8 -*-
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.utils import defaultKeys
from collective.transmogrifier.utils import defaultMatcher
from collective.transmogrifier.utils import Matcher
from uuid import uuid4
from zope.annotation.interfaces import IAnnotations
from zope.interface import implementer
from zope.interface import provider

import logging

logger = logging.getLogger(__name__)

ITEMS_IN = "redturtle.importer.base.items_in"


@implementer(ISection)
@provider(ISectionBlueprint)
class VoltoCustomMapping(object):
    """Mapping types for Volto
    """

    def __init__(self, transmogrifier, name, options, previous):
        self.transmogrifier = transmogrifier
        self.name = name
        self.options = options
        self.previous = previous
        self.context = transmogrifier.context

        if 'path-key' in options:
            pathkeys = options['path-key'].splitlines()
        else:
            pathkeys = defaultKeys(options['blueprint'], name, 'path')
        self.pathkey = Matcher(*pathkeys)

        self.typekey = defaultMatcher(
            options, 'type-key', name, 'type', ('portal_type', 'Type')
        )
        annotations = IAnnotations(self.context.REQUEST)
        self.items_in = annotations.setdefault(ITEMS_IN, {})

    def generate_listing_query(self, item):
        title_uuid = str(uuid4())
        listing_uuid = str(uuid4())
        item['blocks'] = {
            title_uuid: {"@type": "title"},
            listing_uuid: {
                "@type": "listing",
                "query": item.get('query', []),
                "sort_on": item.get('sort_on', ''),
                "b_size": item.get('item_count', ''),
                "block": listing_uuid,
            },
        }
        item['blocks_layout'] = {'items': [title_uuid, listing_uuid]}

    def __iter__(self):
        for item in self.previous:
            keys = item.keys()
            typekey = self.typekey(*keys)[0]
            pathkey = self.pathkey(*keys)[0]
            if item.get('_isdefaultpage', False):
                # skip this content because it will be integrated in
                # folder conversion below
                if item.get("_uid") in self.items_in:
                    self.items_in[item.get("_uid")][
                        'reason'
                    ] = 'Converted default view'
                else:
                    self.items_in[item.get("_uid")] = {
                        "id": item.get("_id"),
                        "portal_type": item.get("_type"),
                        "title": item.get("title"),
                        "path": item.get("_path"),
                    }
                continue
            if not (typekey and pathkey):
                logger.warn('Not enough info for item: {0}'.format(item))
                yield item
                continue

            if not pathkey:  # not enough info
                yield item
                continue
            original_type = item[typekey]
            if original_type == 'Collection':
                item[typekey] = 'Document'
                item['_layout'] = ''
                self.generate_listing_query(item)
                yield item
                continue
            elif original_type == 'Folder':
                item[typekey] = 'Document'
                default_item = item.get('_defaultitem', {})
                if default_item:
                    default_item_type = default_item.get('_type', '')
                    if default_item_type in ['Document', 'News Item']:
                        item['text'] = default_item.get('text')
                    elif default_item_type == 'Collection':
                        self.generate_listing_query(default_item)
                    elif default_item_type in ['Folder', 'Portlet Page']:
                        self.generate_listing_query(item)
                else:
                    self.generate_listing_query(item)
                item['_layout'] = ''
                yield item
                continue
            yield item
