import logging
import xmlrpc.client

_logger = logging.getLogger(__name__)


class BaseRpc(object):
    rpc_model = None
    rpc_common = None
    uid = 1
    password = "not_defined"
    db = "odoo"

    def set_config(self, host, database, port):
        try:
            # _logger.info("set database", database)
            self.db = database
            url = "http://{}:{}".format(host, port)
            
            if int(port) == 443:
                url = "https://{}".format(host)

            # _logger.info("Link Url", url)
            self.rpc_common = xmlrpc.client.ServerProxy(
                '{}/xmlrpc/2/common'.format(url))
            # _logger.info("common version", self.rpc_common.version())
            self.rpc_model = xmlrpc.client.ServerProxy(
                '{}/xmlrpc/2/object'.format(url))
        except Exception as e:
            _logger.info("[ERROR]")
            _logger.info(e)

    def set_auth(self, login, password):
        self.password = password
        self.uid = self.rpc_common.authenticate(self.db, login, password, {})
        _logger.info(f"Set Auth With UID : {self.uid}")

    def model(self, model, method, filters=[], **kwargs):
        # _logger.info("kwarg", kwargs)
        return self.rpc_model.execute_kw(self.db, self.uid, self.password, model, method, [filters])

    def create(self, model, values=None):
        if values is None:
            raise AttributeError('No values for create')
        return self.rpc_model.execute_kw(self.db, self.uid, self.password, model, 'create', [values])

    def search(self, model, filters):
        return self.rpc_model.execute_kw(self.db, self.uid, self.password, model, 'search', filters)

    def write(self, model, id, values=None):
        if values is None:
            raise AttributeError('No values for write')
        return self.rpc_model.execute_kw(self.db, self.uid, self.password, model, 'write', [[id], values])

    def unlink(self, model, document_ids, context=None):
        # if not context: context = {}
        return self.rpc_model.execute_kw(self.db, self.uid, self.password, model, 'unlink', document_ids)

    def search_read(self, model, filters, fields=None, **kwargs):
        # _logger.info("extra", kwargs)
        context = {}
        if fields is None:
            fields = ['name', 'id']
        if not kwargs:
            kwargs = {}
        kwargs.update({
            "fields": fields
        })
        context.update(**kwargs)
        # _logger.info("context", context)
        return self.rpc_model.execute_kw(self.db, self.uid, self.password, model, 'search_read', [filters], context)

    def get_or_create(self, model, filters=None):
        if filters is None:
            filters = []

        query = self.search_read(model, filters, ['id'])
        if len(query) == 1:
            _logger.info(f"FOUND {model} : {query[0]}")
            return query[0]['id'], False
        elif len(query) == 0:
            values = {}
            for filter in filters:
                values[filter[0]] = filter[2]
            _logger.info(f"CREATE with : {values}")
            id = self.create(model, values=values)
            return id, True
        else:
            # Response.status = "409"
            raise KeyError(f"query return {len(query)} objects")

    def update_or_create(self, model, filters=None, values=None):
        if filters is None:
            filters = []

        if values is None:
            raise AttributeError('No values for create')

        query = self.search_read(model, filters, ["id"])
        if len(query) == 1:
            _logger.info(f"FOUND {model} : {query[0]}")
            result = self.write(model, query[0].get("id"), values)
            return result, False
        elif len(query) == 0:
            values = {}
            for filter in filters:
                values[filter[0]] = filter[2]
            _logger.info(f"CREATE with : {values}")
            pk = self.create(model, values=values)
            return pk, True
        else:
            raise KeyError(f"query return {len(query)} objects")
