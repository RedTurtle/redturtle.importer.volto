# -*- coding: utf-8 -*-
from copy import deepcopy
from itertools import groupby
from plone import api
from plone.outputfilters.browser.resolveuid import uuidToObject
from redturtle.importer.base.interfaces import IPostMigrationStep
from urllib.parse import urlparse
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface

import json
import logging
import re
import requests

logger = logging.getLogger(__name__)
RESOLVEUID_RE = re.compile("^[./]*resolve[Uu]id/([^/]*)/?(.*)$")


@adapter(Interface, Interface)
@implementer(IPostMigrationStep)
class FixVoltoReferences(object):
    order = 50

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, transmogrifier):
        """
        """
        logger.info("## Fix volto references ##")
        brains = api.content.find(
            object_provides="plone.restapi.behaviors.IBlocks"
        )
        broken_links = []

        for brain in brains:
            item = brain.getObject()
            blocks = getattr(item, "blocks", {})
            if not blocks:
                continue
            item.blocks = self.fix_references_in_blocks(
                item=item, data=deepcopy(blocks)
            )
            if self.has_broken_links(item.blocks):
                broken_links.append(brain.getURL())
        self.write_broken_links(
            paths=broken_links, transmogrifier=transmogrifier
        )

    def has_broken_links(self, blocks):
        for block in blocks.values():
            block_type = block.get("@type", "")
            if block_type == "text":
                entity_map = block.get("text", {}).get("entityMap", {})
                for entity in entity_map.values():
                    if entity.get("type") != "LINK":
                        continue
                    url = entity.get("data", {}).get("href", "")
                    if self.is_invalid_url(url=url):
                        return True
            else:
                if (
                    self.is_invalid_url(block.get("src", ""))
                    or self.is_invalid_url(block.get("href", ""))
                    or self.is_invalid_url(block.get("url", ""))
                ):
                    return True
        return False

    def is_invalid_url(self, url):
        if not url:
            # empty field
            return False
        if "resolveuid" in url:
            match = RESOLVEUID_RE.match(url)
            if match is None:
                return True  #  broken link
            uid, suffix = match.groups()
            if not uuidToObject(uid):
                return True
        if not url.startswith("http") or not url.startswith("mailto"):
            return True  # broken link
        try:
            res = requests.get(url, timeout=5)
            if res.status_code != "200":
                return True
        except Exception:
            return True
        return False

    def path2uuid(self, is_image, path, url):
        try:
            ref_obj = api.content.get(path)
        except Exception:
            return ""
        if not ref_obj or ref_obj == api.portal.get():
            return ""
        if is_image:
            return "resolveuid/{uid}/@@images/{scale}".format(
                uid=ref_obj.UID(), scale=url.split("@@images/")[1]
            )
        else:
            try:
                return "resolveuid/{}".format(ref_obj.UID())
            except AttributeError:
                return ""

    def fix_references_in_blocks(self, item, data, parent={}):
        for k, v in list(data.items()):
            if isinstance(v, dict):
                data[k] = self.fix_references_in_blocks(
                    item=item, data=v, parent=data
                )
            if k not in ["src", "url", "href"] or "resolveuid" in v:
                continue
            is_image = "@@images" in v
            url_parsed = urlparse(v)
            path = url_parsed.path
            if is_image:
                path = path.split("@@images")[0]
            scheme = url_parsed.scheme
            if scheme != "":
                resolveuid_url = self.path2uuid(
                    is_image=is_image, path=path, url=v
                )
                if resolveuid_url:
                    data[k] = resolveuid_url
                continue

            parent_levels = 0
            for key, group in groupby(path.split("../")):
                if key == "":
                    parent_levels = len(list(group))
            item_path = (
                parent_levels
                and item.getPhysicalPath()[:-parent_levels]
                or item.getPhysicalPath()
            )
            path = "/".join(
                item_path + tuple([x for x in path.split("../") if x])
            )

            resolveuid_url = self.path2uuid(
                is_image=is_image, path=path, url=v
            )
            if resolveuid_url:
                data[k] = resolveuid_url
        return data

    def write_broken_links(self, paths, transmogrifier):
        section = transmogrifier.get("results")
        if section is None:
            logger.warning(
                '"results" section not found in transmogrifier configuration.'
                " Unable to write broken links file."
            )
            return
        file_name = section.get("broken-links-tiny")
        file_path = "{dir}/{portal_id}_{file_name}".format(
            dir=section.get("migration-dir"),
            portal_id=api.portal.get().getId(),
            file_name=file_name,
        )
        with open(file_path, "w") as fp:
            json.dump(paths, fp)
