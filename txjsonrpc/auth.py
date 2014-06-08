from zope.interface import Interface, implements

try:
    from twisted import web
except ImportError:
    web = None

from twisted.cred.portal import IRealm, Portal


class HTTPAuthRealm(object):

    implements(IRealm)

    def __init__(self, resource):
        self.resource = resource

    def logout(self):
        pass

    def requestAvatar(self, avatarId, mind, *interfaces):
        if web.resource.IResource in interfaces:
            return web.resource.IResource, self.resource, self.logout
        raise NotImplementedError()


def _wrapTwistedWebResource(resource, checkers, credFactories=[],
                            realmName=""):
    if not web:
        raise ImportError("twisted.web does not seem to be installed.")
    from twisted.web import guard

    defaultCredFactory = guard.BasicCredentialFactory(realmName)
    credFactories.insert(0, defaultCredFactory)
    realm = HTTPAuthRealm(resource)
    portal = Portal(realm, checkers)
    return guard.HTTPAuthSessionWrapper(portal, credFactories)


def wrapResource(resource, *args, **kwargs):
    if web.resource.IResource.providedBy(resource):
        return _wrapTwistedWebResource(resource, *args, **kwargs)
    elif web2.iweb.IResource.providedBy(resource):
        return _wrapTwistedWeb2Resource(resource, *args, **kwargs)
