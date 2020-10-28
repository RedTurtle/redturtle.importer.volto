# -*- coding: utf-8 -*-
from Products.CMFPlone.interfaces import IPloneSiteRoot
from redturtle.importer.base.interfaces import IPortalTypeMapping
from uuid import uuid4
from zope.component import adapter
from zope.interface import implementer
from zope.publisher.interfaces.browser import IBrowserRequest

import logging

logger = logging.getLogger(__name__)


@adapter(IPloneSiteRoot, IBrowserRequest)
@implementer(IPortalTypeMapping)
class VoltoMapping(object):
    order = 100

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, item, typekey):
        """
        """
        if item.get("_isdefaultpage", False):
            # skip this content because it will be integrated in
            # folder conversion below
            if item[typekey] in ["Document", "Portlet Page", 'Collection']:
                item["skipped"] = True
                item["skipped_message"] = "Converted default view"
            return item

        portal_type = item[typekey]
        if portal_type == "Collection":
            item[typekey] = "Document"
            item["_layout"] = ""
            self.generate_listing_query(item)
            blocks = self.generate_listing_query(item)
            item.update(blocks)
            return item
        elif portal_type == "Folder":
            item[typekey] = "Document"
            default_item = item.get("_defaultitem", {})
            if default_item:
                default_item_type = default_item.get("_type", "")
                item["text"] = default_item.get("text", "")
                if default_item_type == "Collection":
                    blocks = self.generate_listing_query(default_item)
                    item.update(blocks)
                elif default_item_type in ["Folder", "Portlet Page"]:
                    blocks = self.generate_listing_query(item)
                    item.update(blocks)
                else:
                    blocks = self.generate_listing_query(item)
                    item.update(blocks)
            else:
                blocks = self.generate_listing_query(item)
                item.update(blocks)
            item["_layout"] = ""
            item["_defaultitem"] = ""
            item["default_page"] = ""
            return item
        return item

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
