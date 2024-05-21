import six
from collective.auditlog import db
from collective.auditlog.models import LogEntry
from plone.api import user as user_api
from Products.Five.browser import BrowserView
from sqlalchemy import desc
from sqlalchemy import or_


class LogView(BrowserView):

    page_size = 100

    columns = [{'name': 'userid', 'label': 'User Id', 'sortable': True},
               {'name': 'name', 'label': 'Name', 'sortable': False},
               {'name': 'email', 'label': 'Email', 'sortable': False},
               {'name': 'performed_on', 'label': 'Date', 'sortable': True},
               {'name': 'uid', 'label': 'UID', 'sortable': True},
               {'name': 'type', 'label': 'Type', 'sortable': True},
               {'name': 'title', 'label': 'Title', 'sortable': True},
               {'name': 'path', 'label': 'Path', 'sortable': True},
               {'name': 'site_name', 'label': 'Site', 'sortable': True},
               {'name': 'working_copy', 'label': 'Working Copy', 'sortable': True},
               {'name': 'action', 'label': 'Action', 'sortable': True},
               {'name': 'info', 'label': 'Notes', 'sortable': True}]

    @property
    def page(self):
        page = self.request.get('page', '1')
        page = int(page)
        return page

    @property
    def direction(self):
        dir = self.request.get('direction', 'desc')
        return dir

    def new_direction(self, order, column):
        new = 'asc'
        if order == column and self.direction == 'asc':
            new = 'desc'
        return new

    @property
    def pagination_next(self):
        url = self.request.URL
        if self.request.QUERY_STRING:
            url = url + '?' + self.request.QUERY_STRING
            url = url.replace('page=', 'page=' + str(self.page + 1) + '&prev=')
            if 'page' not in url:
                url = url + '&page=2'
        else:
            url = url + "?page=" + str(self.page + 1)
        return url

    @property
    def loglines(self):
        order = self.request.get('order', 'performed_on')
        if order == 'userid':
            order = 'user'
        query = self.request.get('query', '')
        session = db.getSession()
        try:
            if self.direction == 'asc':
                lines = session.query(LogEntry).order_by(order)
            else:
                lines = session.query(LogEntry).order_by(desc(order))
            if query:
                if six.PY2:
                    query = unicode(query)
                lines = lines.filter(or_(LogEntry.user.contains(query),
                                         LogEntry.uid.contains(query),
                                         LogEntry.type.contains(query),
                                         LogEntry.title.contains(query),
                                         LogEntry.path.contains(query),
                                         LogEntry.site_name.contains(query),
                                         LogEntry.working_copy.contains(query),
                                         LogEntry.action.contains(query),
                                         LogEntry.info.contains(query))
                                     )
            lines = lines.limit(self.page_size)
            lines = lines.offset((self.page - 1) * self.page_size)
            lines = lines.all()
            results = list()
            for line in lines:
                username = line.user
                user = user_api.get(username=username)
                if not user:
                    user = user_api.get(userid=username)
                if user:
                    username = user.getUserName()
                    userid = user.getId()
                    fullname = user.getProperty('fullname')
                    if not fullname:
                        fullname = username
                    last_name = user.getProperty('last_name', default=None)
                    if last_name:
                        first_name = user.getProperty('first_name')
                        name = f'{last_name}, {first_name}'
                    else:
                        name = fullname
                    email = user.getProperty('email')
                else:
                    userid = name = email = username
                result = dict(userid=userid, name=name, email=email)
                for column in self.columns:
                    column_name = column['name']
                    if column_name not in ('userid', 'name', 'email'):
                        result[column_name] = getattr(line, column_name, '')
                results.append(result)
            return results
        finally:
            session.close()
