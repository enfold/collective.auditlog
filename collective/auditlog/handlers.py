import json
from importlib import import_module
from zope.component import getUtility
from zope.interface.interfaces import ComponentLookupError
from zope.lifecycleevent import IObjectAddedEvent
from zope.lifecycleevent import IObjectRemovedEvent
from zope.lifecycleevent import IObjectCopiedEvent
from zope.schema import Field
from plone.app.discussion.interfaces import IComment
from plone.registry.interfaces import IRegistry
from Products.CMFCore.interfaces import IContentish
from collective.auditlog.action import AuditActionExecutor
from collective.auditlog.utils import addLogEntry
from collective.auditlog.utils import getObjectInfo
from collective.auditlog.utils import getSite
from collective.auditlog.utils import getUID
from plone.app.contentrules import handlers as cr_handlers


def execute_event(obj, event=None):
    if event is None:
        # ActionSuceededEvent does not send an object first
        event = obj
        obj = event.object
    if isinstance(obj, Field):
        return
    executor = None
    for ev in get_automatic_events():
        if ev.providedBy(event) and obj is not None:
            executor = AuditActionExecutor(None, None, event)
            executor()
            break
    if executor is None:
        # plone sends some events twice, first wrapped. Ignore those.
        if getattr(event, 'object', None) is not None:
            cr_handlers.execute_rules(event)


def moved_event(event):
    # only execute moved event if it's not a added or removed event since
    # those are handled elsewhere and they base off of this event class
    if (IObjectAddedEvent.providedBy(event) or
            IObjectRemovedEvent.providedBy(event)):
        return

    obj = event.object
    if not (IContentish.providedBy(obj) or IComment.providedBy(obj)):
        return
    execute_event(obj, event)


def created_event(event):
    obj = event.object

    if IObjectCopiedEvent.providedBy(event):
        return  # ignore this event since we're listening to cloned instead

    if IContentish.providedBy(obj) or IComment.providedBy(obj):
        execute_event(obj, event)
    else:
        return


def loggedout_event(event):
    obj = event.object
    data = {'info': '', 'action': 'logged out'}
    log_entry(obj, data)


def archetypes_initialized(event):
    """Pick up the delayed IObjectAddedEvent when an Archetypes object is
    initialised.
    """
    obj = event.object

    cr_handlers.init()
    delayed_event = cr_handlers._status.delayed_events.get(
        'IObjectInitializedEvent-audit-%s' % getUID(obj), None)
    if delayed_event is not None:
        cr_handlers._status.delayed_events[
            'IObjectInitializedEvent-audit-%s' % getUID(obj)] = None
        execute_event(obj, delayed_event)


def get_automatic_events():
    events = []
    site = getSite()
    try:
        qi = site.portal_quickinstaller
        installed = qi.isProductInstalled('collective.auditlog')
    except AttributeError:
        installed = False
    if installed:
        try:
            registry = getUtility(IRegistry)
            key = 'collective.auditlog.interfaces.IAuditLogSettings.automaticevents'
            automaticevents = registry[key]
            for ev in automaticevents:
                module, interface = ev.rsplit('.', 1)
                imported = import_module(module)
                automatic = getattr(imported, interface, None)
                if automatic is not None:
                    events.append(automatic)
        except ComponentLookupError:
            # no registry, no events
            pass
    return events


def log_entry(obj, data, request=None):
    data.update(getObjectInfo(obj, request=request))
    addLogEntry(obj, data)


def custom_event(event):
    obj = event.object
    request = getattr(event, 'request', None)
    info = event.info
    if info:
        try:
            tmp = json.loads(info)
        except ValueError:
            info = json.dumps({'info': info})

    data = {'info': event.info, 'action': event.action}
    log_entry(obj, data, request)
