Changelog
=========

1.3.8 (unreleased)
------------------

- Add userid, name, and email columns to auditlog view.
  [enfold]


1.3.7 (2023-10-25)
------------------

- Don't try to convert query to unicode if we are running with python 3.
  [enfold]

- Close session after getting results.
  [enfold]


1.3.6 (2023-06-08)
------------------

- Support sqlalchemy 1.4 and 2.0
  [enfold]


1.3.5 (2021-09-10)
------------------

- Add package name to async task names.
  [enfold]


1.3.4 (2021-06-23)
------------------

- collective.celery integration
  [enfold]

- @@auditlog-view allows viewing/sorting/searching audit log entries
  [enfold]

- add login & logout audits
  [enfold]

- ability to specify the sqlalchemy DSN in config file
  [enfold]

- Notify an event before storing audit log entry.
  [enfold]

- Use custom permission for viewing audit log.
  [enfold]

- Fix tests.
  [enfold]

- Fix db connection leak.
  [enfold]

- Use valid json in info field.
  [enfold]

- Fix tests to reflect json in info field.
  [enfold]

- Make sure that the database tables are created on first use.
  [enfold]


1.3.3 (2018-07-12)
------------------

- Factored out getObjectInfo and addLogEntry.
  [reinhardt]


1.3.2 (2018-07-11)
------------------

- Skip retrieving rule when audit log is disabled completely.
  Improves performance.
  [reinhardt]


1.3.1 (2017-04-13)
------------------

- Fix upgrade step title.
  [ale-rt]


1.3.0 (2017-04-13)
------------------

- The engine parameters (like pool_recycle, echo, ...)
  can be specified through a registry record
  [ale-rt]


1.2.2 (2016-06-06)
------------------

- Make action more robust on IActionSucceededEvent
  [ale-rt]


1.2.1 (2016-05-10)
------------------

- Fix unicode issues
- Tests are working again
  [ale-rt]


1.2.0 (2016-05-03)
------------------

- First public release
