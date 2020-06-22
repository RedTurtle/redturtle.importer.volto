# -*- coding: utf-8 -*-
from redturtle.importer.base.interfaces import ISection
from redturtle.importer.base.interfaces import ISectionBlueprint
from redturtle.importer.base.transmogrifier.utils import defaultKeys
from redturtle.importer.base.transmogrifier.utils import defaultMatcher
from redturtle.importer.base.transmogrifier.utils import Matcher
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

        if "path-key" in options:
            pathkeys = options["path-key"].splitlines()
        else:
            pathkeys = defaultKeys(options["blueprint"], name, "path")
        self.pathkey = Matcher(*pathkeys)

        self.typekey = defaultMatcher(
            options, "type-key", name, "type", ("portal_type", "Type")
        )
        annotations = IAnnotations(self.context.REQUEST)
        self.items_in = annotations.setdefault(ITEMS_IN, {})

    def generate_listing_query(self, item):
        title_uuid = str(uuid4())
        listing_uuid = str(uuid4())
        data = {}
        query = item.get("query", [])
        if not query:
            query = [
                {
                    "i": "path",
                    "o": "plone.app.querystring.operation.string.path",
                    "v": "{uid}::1".format(uid=item.get("_uid")),
                }
            ]
        data["blocks"] = {
            title_uuid: {"@type": "title"},
            listing_uuid: {
                "@type": "listing",
                "query": query,
                "sort_on": item.get("sort_on", "getObjPositionInParent"),
                "sort_order": item.get("sort_reversed", False),
                "b_size": item.get("item_count", "30"),
                "block": listing_uuid,
            },
        }
        data["blocks_layout"] = {"items": [title_uuid, listing_uuid]}
        return data

    def __iter__(self):
        for item in self.previous:
            keys = item.keys()
            typekey = self.typekey(*keys)[0]
            pathkey = self.pathkey(*keys)[0]
            if item.get("_isdefaultpage", False):
                # skip this content because it will be integrated in
                # folder conversion below
                if item.get("_uid") in self.items_in:
                    self.items_in[item.get("_uid")][
                        "reason"
                    ] = "Converted default view"
                else:
                    self.items_in[item.get("_uid")] = {
                        "id": item.get("_id"),
                        "portal_type": item.get("_type"),
                        "title": item.get("title"),
                        "path": item.get("_path"),
                    }
                continue
            if not (typekey and pathkey):
                logger.warn("Not enough info for item: {0}".format(item))
                yield item
                continue

            if not pathkey:  # not enough info
                yield item
                continue
            original_type = item[typekey]
            if original_type == "Collection":
                item[typekey] = "Document"
                item["_layout"] = ""
                self.generate_listing_query(item)
                blocks = self.generate_listing_query(item)
                item.update(blocks)
                yield item
                continue
            elif original_type == "Folder":
                item[typekey] = "Document"
                default_item = item.get("_defaultitem", {})
                if default_item:
                    default_item_type = default_item.get("_type", "")
                    if default_item_type in ["Document", "News Item"]:
                        item["text"] = default_item.get("text")
                    elif default_item_type == "Collection":
                        blocks = self.generate_listing_query(default_item)
                        item.update(blocks)
                    elif default_item_type in ["Folder", "Portlet Page"]:
                        blocks = self.generate_listing_query(item)
                        item.update(blocks)
                else:
                    blocks = self.generate_listing_query(item)
                    item.update(blocks)
                item["_layout"] = ""
                yield item
                continue
            yield item
