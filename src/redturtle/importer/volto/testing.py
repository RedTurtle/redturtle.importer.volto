# -*- coding: utf-8 -*-
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2
from time import sleep

import plone.restapi
import redturtle.importer.base
import redturtle.importer.volto
import redturtle.volto
import six
import sys
import os


class RedturtleImporterVoltoLayer(PloneSandboxLayer):

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        self.loadZCML(package=plone.restapi)
        self.loadZCML(package=redturtle.importer.volto)

    # def setUpPloneSite(self, portal):
    #     applyProfile(portal, 'redturtle.importer.volto:default')


class RedturtleImporterVoltoDockerLayer(PloneSandboxLayer):

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.

        import collective.folderishtypes
        import collective.volto.cookieconsent

        self.loadZCML(package=plone.restapi)
        self.loadZCML(package=redturtle.importer.base)
        self.loadZCML(package=redturtle.importer.volto)
        self.loadZCML(package=collective.folderishtypes)
        self.loadZCML(package=collective.volto.cookieconsent)
        self.loadZCML(package=redturtle.volto)

    def setUp(self):
        """
        wait until docker image is ready
        """
        os.environ["DRAFTJS_CONVERTER_URL"] = "http://localhost:3000/html_converter"
        ping_url = "http://127.0.0.1:8080/Plone"
        for i in range(1, 10):
            try:
                result = six.moves.urllib.request.urlopen(ping_url)
                if result.code == 200:
                    break
            except six.moves.urllib.error.URLError:
                sleep(3)
                sys.stdout.write(".")
            if i == 9:
                sys.stdout.write("Docker Instance could not be started !!!")

        super(RedturtleImporterVoltoDockerLayer, self).setUp()

    def setUpPloneSite(self, portal):
        applyProfile(portal, "redturtle.volto:default")


REDTURTLE_IMPORTER_VOLTO_FIXTURE = RedturtleImporterVoltoLayer()
REDTURTLE_IMPORTER_VOLTO_DOCKER_FIXTURE = RedturtleImporterVoltoDockerLayer()


REDTURTLE_IMPORTER_VOLTO_INTEGRATION_TESTING = IntegrationTesting(
    bases=(REDTURTLE_IMPORTER_VOLTO_FIXTURE,),
    name="RedturtleImporterVoltoLayer:IntegrationTesting",
)


REDTURTLE_IMPORTER_VOLTO_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(REDTURTLE_IMPORTER_VOLTO_FIXTURE,),
    name="RedturtleImporterVoltoLayer:FunctionalTesting",
)

REDTURTLE_IMPORTER_VOLTO_DOCKER_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(REDTURTLE_IMPORTER_VOLTO_DOCKER_FIXTURE,),
    name="RedturtleImporterVoltoDockerLayer:FunctionalTesting",
)

REDTURTLE_IMPORTER_VOLTO_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        REDTURTLE_IMPORTER_VOLTO_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE,
    ),
    name="RedturtleImporterVoltoLayer:AcceptanceTesting",
)
