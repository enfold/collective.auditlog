from celery.utils.log import get_task_logger
from collective.celery import task


logger = get_task_logger(__name__)


@task(name="audit")
def queue_job(obj, *args, **kwargs):
    from collective.auditlog.async import runJob
    logger.warn('Logging action on {}'.format(obj.absolute_url_path()))
    runJob(obj, *args, **kwargs)

@task(name='audit-catalog-entry')
def queue_catalog_entry(obj, data):
    from collective.auditlog.catalog import catalogEntry
    logger.warn('Cataloging event for {}'.format(obj.absolute_url_path()))
    catalogEntry(obj, data)