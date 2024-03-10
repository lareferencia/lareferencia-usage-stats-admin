from flask import render_template
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder import ModelView, ModelRestApi

from . import appbuilder, db

from .models import Source, Country

 
class CountryView(ModelView):
    datamodel = SQLAInterface(Country)
 
class SourceView(ModelView):
    datamodel = SQLAInterface(Source)


"""
    Create your Model based REST API::

    class MyModelApi(ModelRestApi):
        datamodel = SQLAInterface(MyModel)

    appbuilder.add_api(MyModelApi)


    Create your Views::


    class MyModelView(ModelView):
        datamodel = SQLAInterface(MyModel)


    Next, register your Views::


    appbuilder.add_view(
        MyModelView,
        "My View",
        icon="fa-folder-open-o",
        category="My Category",
        category_icon='fa-envelope'
    )
"""

"""
    Application wide 404 error handler
"""


@appbuilder.app.errorhandler(404)
def page_not_found(e):
    return (
        render_template(
            "404.html", base_template=appbuilder.base_template, appbuilder=appbuilder
        ),
        404,
    )


db.create_all()
appbuilder.add_view(CountryView, "List Country", icon="fa-folder-open-o", category="", category_icon="fa-envelope")
appbuilder.add_view(SourceView, "List Source", icon="fa-folder-open-o", category="", category_icon="fa-envelope")
appbuilder.add_api(CountryView)
appbuilder.add_api(SourceView)


