# -*- coding: utf-8 -*-
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.utils import defaultKeys
from collective.transmogrifier.utils import defaultMatcher
from collective.transmogrifier.utils import Matcher
from uuid import uuid4
from zope.interface import implementer
from zope.interface import provider

import logging

logger = logging.getLogger(__name__)


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

    def __iter__(self):
        for item in self.previous:
            keys = item.keys()
            typekey = self.typekey(*keys)[0]
            pathkey = self.pathkey(*keys)[0]

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
                title_uuid = str(uuid4())
                listing_uuid = str(uuid4())
                item['blocks'] = {
                    title_uuid: {"@type": "title"},
                    listing_uuid: {
                        "@type": "listing",
                        "query": item['query'],
                        "block": listing_uuid,
                    },
                }
                item['blocks_layout'] = {'items': [title_uuid, listing_uuid]}
                yield item
                continue
            elif original_type == 'Folder':
                item[typekey] = 'Document'
                item['_layout'] = ''
                title_uuid = str(uuid4())
                listing_uuid = str(uuid4())
                item['blocks'] = {
                    title_uuid: {"@type": "title"},
                    listing_uuid: {
                        "@type": "listing",
                        "query": [],
                        "sort_on": "getObjPositionInParent",
                        "b_size": "20",
                        "block": listing_uuid,
                    },
                }
                item['blocks_layout'] = {'items': [title_uuid, listing_uuid]}
                yield item
                continue
            yield item
