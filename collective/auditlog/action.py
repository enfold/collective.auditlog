import json
from Acquisition import aq_parent
from OFS.SimpleItem import SimpleItem
from zope.component import adapts
from zope.interface import Interface, implements
from zope.formlib import form

from plone.app.contentrules.browser.formhelper import AddForm, EditForm
from plone.contentrules.rule.interfaces import IRuleElementData, IExecutable
try:
    from Products.PloneFormGen.interfaces import IPloneFormGenField
except ImportError:
    class IPloneFormGenField(Interface):
        pass

from Products.Archetypes.interfaces import (
    IObjectInitializedEvent, IObjectEditedEvent, IBaseObject)
from zope.lifecycleevent.interfaces import (
    IObjectCreatedEvent, IObjectModifiedEvent,
    IObjectMovedEvent, IObjectRemovedEvent, IObjectAddedEvent)
from plone.app.iterate.relation import WorkingCopyRelation
from OFS.interfaces import IObjectClonedEvent

import inspect
from plone.app.iterate.interfaces import (
    ICheckinEvent, IBeforeCheckoutEvent, ICancelCheckoutEvent,
    IWorkingCopy)
from Products.CMFCore.interfaces import IActionSucceededEvent
from Products.PluggableAuthService.interfaces.events import (
    IUserLoggedInEvent, IUserLoggedOutEvent)
from zope.globalrequest import getRequest
from zope.component import getUtility
from plone.registry.interfaces import IRegistry

from collective.auditlog.utils import getObjectInfo
from collective.auditlog.utils import addLogEntry

import logging
logger = logging.getLogger('collective.auditlog')


class IAuditAction(Interface):
    pass


class AuditAction(SimpleItem):
    implements(IAuditAction, IRuleElementData)
    element = 'plone.actions.Audit'
    summary = u"Audit"


class AuditActionExecutor(object):
    implements(IExecutable)
    adapts(Interface, IAuditAction, Interface)

    def __init__(self, context, element, event):
        self.context = context
        self.element = element
        self.event = event

    def canExecute(self, rule, req):
        event = self.event
        obj = event.object
        event_iface = [i for i in event.__implemented__.interfaces()][0]

        # for archetypes we need to make sure we're getting the right moved
        # event here so we do not duplicate
        if (not IObjectEditedEvent.providedBy(event) and
                rule is not None and event_iface != rule.rule.event):
            return False
        # if archetypes, initialization also does move events
        if (IObjectMovedEvent.providedBy(event) and
                IBaseObject.providedBy(obj) and
                obj.checkCreationFlag()):
            return False
        if req.environ.get('disable.auditlog', False):
            return False
        return True

    def get_history_comment(self):
        ''' Given an object and a IActionSucceededEvent,
        extract the comment of the transition.
        '''
        action = self.event.action
        if not action:
            return ''
        history = self.event.object.workflow_history
        for transition in reversed(history[self.event.workflow.id]):
            if transition.get('action') == action:
                return transition.get('comments', '')
        return ''

    def __call__(self):
        req = getRequest()
        if req.environ.get('disable.auditlog', False):
            return True

        event = self.event
        obj = event.object
        # order of those checks is important since some interfaces
        # base off the others
        rule = inspect.stack()[1][0].f_locals.get('self', None)
        registry = getUtility(IRegistry)
        trackWorkingCopies = registry['collective.auditlog.interfaces.IAuditLogSettings.trackworkingcopies']  # noqa

        if not self.canExecute(rule, req):
            return True  # cut out early, we can't do this event

        data = {
            'info': ''
        }

        if IPloneFormGenField.providedBy(obj):
            # if ploneformgen field, use parent object for modified data
            data['field'] = obj.getId()
            obj = aq_parent(obj)

        # the order of those interface checks matters since some interfaces
        # inherit from others
        if IObjectRemovedEvent.providedBy(event):
            # need to keep track of removed events so it doesn't get called
            # more than once for each object
            action = 'removed'
        elif (IObjectInitializedEvent.providedBy(event) or
                IObjectCreatedEvent.providedBy(event) or
                IObjectAddedEvent.providedBy(event)):
            action = 'added'
        elif IObjectMovedEvent.providedBy(event):
            # moves can also be renames. Check the parent object
            if event.oldParent == event.newParent:
                if rule is None or 'Rename' in rule.rule.title:
                    info = {'previous_id': event.oldName}
                    data['info'] = json.dumps(info)
                    action = 'rename'
                else:
                    # cut out here, double action for this event
                    return True
            else:
                if rule is None or 'Moved' in rule.rule.title:
                    parent_path = '/'.join(event.oldParent.getPhysicalPath())
                    previous_location = parent_path + '/' + event.oldName
                    info = {'previous_location': previous_location}
                    data['info'] = json.dumps(info)
                    action = 'moved'
                else:
                    # step out immediately since this could be a double action
                    return True
        elif IObjectModifiedEvent.providedBy(event):
            action = 'modified'
        elif IActionSucceededEvent.providedBy(event):
            info = {'transition': event.action,
                    'comments': self.get_history_comment()}
            data['info'] = json.dumps(info)
            action = 'workflow'
        elif IObjectClonedEvent.providedBy(event):
            action = 'copied'
        elif ICheckinEvent.providedBy(event):
            info = {'message': event.message}
            data['info'] = json.dumps(info)
            action = 'checked in'
            req.environ['disable.auditlog'] = True
            data['working_copy'] = '/'.join(obj.getPhysicalPath())
            obj = event.baseline
        elif IBeforeCheckoutEvent.providedBy(event):
            action = 'checked out'
            req.environ['disable.auditlog'] = True
        elif ICancelCheckoutEvent.providedBy(event):
            action = 'cancel check out'
            req.environ['disable.auditlog'] = True
            data['working_copy'] = '/'.join(obj.getPhysicalPath())
            obj = event.baseline
        elif IUserLoggedInEvent.providedBy(event):
            action = 'logged in'
            info = {'user': event.object.getUserName()}
            data['info'] = json.dumps(info)
        elif IUserLoggedOutEvent.providedBy(event):
            action = 'logged out'
        else:
            logger.warn('no action matched')
            return True

        if IWorkingCopy.providedBy(obj):
            # if working copy, iterate, check if Track Working Copies is
            # enabled
            if trackWorkingCopies:
                # if enabled in control panel, use original object and move
                # working copy path to working_copy
                data['working_copy'] = '/'.join(obj.getPhysicalPath())
                relationships = obj.getReferences(
                    WorkingCopyRelation.relationship)
                # check relationships, if none, something is wrong, not logging
                # action
                if len(relationships) > 0:
                    obj = relationships[0]
                else:
                    return True
            else:
                # if not enabled, we only care about checked messages
                if 'check' not in action:
                    return True

        data.update(getObjectInfo(obj))
        data['action'] = action

        addLogEntry(obj, data)
        return True


class AuditAddForm(AddForm):
    form_fields = form.FormFields(IAuditAction)  # needed for Plone4 (formlib)
    schema = IAuditAction  # needed for Plone5 (z3c.form)
    label = u"Add Audit Action"
    form_name = u"Configure element"

    def create(self, data):
        a = AuditAction()
        form.applyChanges(a, self.form_fields, data)
        return a


class AuditEditForm(EditForm):
    form_fields = form.FormFields(IAuditAction)
    label = u"Edit Audit Action"
    form_name = u"Configure element"
