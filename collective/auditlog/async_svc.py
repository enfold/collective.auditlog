# coding=utf-8
from collective.auditlog import db
from collective.auditlog import td
from collective.auditlog.catalog import catalogEntry
from collective.auditlog.models import LogEntry
from Products.CMFCore.interfaces import ICatalogAware
from Products.CMFPlone.utils import safe_unicode
from zope.component import getUtility

# try:
#     from plone.app.async.interfaces import IAsyncService
#     ASYNC_INSTALLED = True
# except ImportError:
#     ASYNC_INSTALLED = False

try:
    import collective.celery
    from collective.auditlog.tasks import queue_job
    from collective.auditlog.tasks import queue_catalog_entry
    from celery.utils.log import get_task_logger
    logger = get_task_logger(__name__)
except ImportError:
    queue_job = None
    queue_catalog_entry = None
    import logging
    logger = logging.getLogger('collective.auditlog')


def runJob(context, **data):
    # make sure to join the transaction before we start
    session = db.getSession()
    tdata = td.get()
    if not tdata.registered:
        tdata.register(session)

    for key in data:
        value = data[key]
        if isinstance(value, str):
            data[key] = safe_unicode(value)

    log = LogEntry(**data)
    session.add(log)


def queueJob(obj, *args, **kwargs):
    """
    queue a job async if available.
    otherwise, just run normal
    """
    if queue_job and kwargs['action'] != 'Undo from ZMI':
        queue_job.delay(obj, *args, **kwargs)
    # elif ASYNC_INSTALLED:
    #     try:
    #         async = getUtility(IAsyncService)
    #         async.queueJob(runJob, obj, *args, **kwargs)
    #     except:
    #         logger.exception(
    #             "Error using plone.app.async with "
    #             "collective.auditlog. logging without "
    #             "plone.app.async...")
    #         runJob(obj, *args, **kwargs)
    else:
        runJob(obj, *args, **kwargs)


def queueCatalogEntry(obj, data):
    """
    queue a job async if available.
    otherwise, just run normal
    """
    if not ICatalogAware.providedBy(obj):
        return
    if queue_catalog_entry:
        queue_catalog_entry.delay(obj, data)
    else:
        catalogEntry(obj, data)
