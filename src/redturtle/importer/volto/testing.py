# -*- coding: utf-8 -*-
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE

# from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2

import redturtle.importer.volto


class RedturtleImporterVoltoLayer(PloneSandboxLayer):

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        import plone.restapi

        self.loadZCML(package=plone.restapi)
        self.loadZCML(package=redturtle.importer.volto)

    # def setUpPloneSite(self, portal):
    #     applyProfile(portal, 'redturtle.importer.volto:default')


REDTURTLE_IMPORTER_VOLTO_FIXTURE = RedturtleImporterVoltoLayer()


REDTURTLE_IMPORTER_VOLTO_INTEGRATION_TESTING = IntegrationTesting(
    bases=(REDTURTLE_IMPORTER_VOLTO_FIXTURE,),
    name='RedturtleImporterVoltoLayer:IntegrationTesting',
)


REDTURTLE_IMPORTER_VOLTO_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(REDTURTLE_IMPORTER_VOLTO_FIXTURE,),
    name='RedturtleImporterVoltoLayer:FunctionalTesting',
)


REDTURTLE_IMPORTER_VOLTO_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        REDTURTLE_IMPORTER_VOLTO_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE,
    ),
    name='RedturtleImporterVoltoLayer:AcceptanceTesting',
)
