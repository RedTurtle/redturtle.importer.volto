# -*- coding: utf-8 -*-
from copy import deepcopy
from itertools import groupby
from redturtle.importer.base.browser.migrations import RedTurtlePlone5MigrationMain
from plone import api
from urllib.parse import urlparse
from plone.outputfilters.browser.resolveuid import uuidToObject

import re
import requests

RESOLVEUID_RE = re.compile("^[./]*resolve[Uu]id/([^/]*)/?(.*)$")


class VoltoMigrationMain(RedTurtlePlone5MigrationMain):
    """
    """

    def generate_broken_links_list(self):
        """
        We generate this list from the other method
        """
        pass

    def scripts_post_migration(self):
        super(VoltoMigrationMain, self).scripts_post_migration()
        self.fix_volto_references()

    def fix_volto_references(self):
        brains = api.content.find(object_provides="plone.restapi.behaviors.IBlocks")
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
        self.write_broken_links(broken_links)

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
                data[k] = self.fix_references_in_blocks(item=item, data=v, parent=data)
            if k not in ["src", "url", "href"] or "resolveuid" in v:
                continue
            is_image = "@@images" in v
            url_parsed = urlparse(v)
            path = url_parsed.path
            if is_image:
                path = path.split("@@images")[0]
            scheme = url_parsed.scheme
            if scheme != "":
                resolveuid_url = self.path2uuid(is_image=is_image, path=path, url=v)
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
            path = "/".join(item_path + tuple([x for x in path.split("../") if x]))

            resolveuid_url = self.path2uuid(is_image=is_image, path=path, url=v)
            if resolveuid_url:
                data[k] = resolveuid_url
        return data
