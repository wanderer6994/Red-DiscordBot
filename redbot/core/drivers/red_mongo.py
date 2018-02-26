import motor.motor_asyncio
from .red_base import BaseDriver

__all__ = ["Mongo"]


class Mongo(BaseDriver):
    """
    Subclass of :py:class:`.red_base.BaseDriver`.
    """
    def __init__(self, cog_name, **kwargs):
        super().__init__(cog_name)
        self.host = kwargs['HOST']
        self.port = kwargs['PORT']
        self.admin_user = kwargs['USERNAME']
        self.admin_pass = kwargs['PASSWORD']
        self.db_name = kwargs.get('DB_NAME', 'default_db')

        from ..data_manager import instance_name

        self.instance_name = instance_name

        self.url = "mongodb://{}:{}@{}:{}/{}".format(
            self.admin_user, self.admin_pass, self.host, self.port,
            self.db_name
        )

        self.conn = motor.motor_asyncio.AsyncIOMotorClient(self.url)

    @property
    def db(self) -> motor.core.Database:
        """
        Gets the mongo database for this cog's name.

        .. warning::

            Right now this will cause a new connection to be made every time the
            database is accessed. We will want to create a connection pool down the
            line to limit the number of connections.

        :return:
            PyMongo Database object.
        """
        return self.conn.get_database()

    def get_collection(self) -> motor.core.Collection:
        """
        Gets a specified collection within the PyMongo database for this cog.

        Unless you are doing custom stuff ``collection_name`` should be one of the class
        attributes of :py:class:`core.config.Config`.

        :param str collection_name:
        :return:
            PyMongo collection object.
        """
        return self.db[self.cog_name]

    @staticmethod
    def _parse_identifiers(identifiers):
        uuid, identifiers = identifiers[0], identifiers[1:]
        return uuid, identifiers

    async def get(self, *identifiers: str):
        mongo_collection = self.get_collection()

        dot_identifiers = '.'.join(identifiers)

        partial = await mongo_collection.find_one(
            filter={'_id': self.unique_cog_identifier},
            projection={dot_identifiers: True}
        )

        if partial is None:
            raise KeyError("No matching document was found and Config expects"
                           " a KeyError.")

        for i in identifiers:
            partial = partial[i]
        return partial

    async def set(self, *identifiers: str, value=None):
        dot_identifiers = '.'.join(identifiers)

        mongo_collection = self.get_collection()

        await mongo_collection.update_one(
            {'_id': self.unique_cog_identifier},
            update={"$set": {dot_identifiers: value}},
            upsert=True
        )

    async def clear(self, *identifiers: str):
        dot_identifiers = '.'.join(identifiers)
        mongo_collection = self.get_collection()

        await mongo_collection.update_one(
            {'_id': self.unique_cog_identifier},
            update={"$unset": {dot_identifiers: 1}}
        )


def get_config_details():
    host = input("Enter host address: ")
    port = int(input("Enter host port: "))

    admin_uname = input("Enter login username: ")
    admin_password = input("Enter login password: ")

    db_name = input("Enter mongodb database name: ")

    if admin_uname == "":
        admin_uname = admin_password = None

    ret = {
        'HOST': host,
        'PORT': port,
        'USERNAME': admin_uname,
        'PASSWORD': admin_password,
        'DB_NAME': db_name
    }
    return ret