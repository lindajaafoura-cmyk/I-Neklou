
MONGODB_MODELS = {
    'reservation', 'restaurant', 'menuitem', 'restaurantgallery', 'promotion',
    'userprofile', 'loyaltypoints', 'loyaltytransaction', 'review',
    'loyaltyreward', 'userredemption', 'favorite'
}

MONGODB_APP = 'pages'
MONGODB_DB = 'mongodb'


class MongoRouter:
    def _is_mongo_model(self, model):
        return (
            model._meta.app_label == MONGODB_APP and
            model._meta.model_name in MONGODB_MODELS
        )

    def db_for_read(self, model, **hints):
        if self._is_mongo_model(model):
            return MONGODB_DB
        return 'default'

    def db_for_write(self, model, **hints):
        if self._is_mongo_model(model):
            return MONGODB_DB
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        # Allow relations even across databases (e.g., between User in SQLite and Models in MongoDB)
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if db == MONGODB_DB:
            return (
                app_label == MONGODB_APP and
                model_name in MONGODB_MODELS
            )
        if app_label == MONGODB_APP and model_name in MONGODB_MODELS:
            return False
        return True
