from flask import render_template
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder import ModelView, ModelRestApi

from . import appbuilder, db

from .models import Source, Country

 
class CountryView(ModelView):
    datamodel = SQLAInterface(Country)
 
class SourceView(ModelView):
    datamodel = SQLAInterface(Source)

    # labels 
    label_columns = {'source_id':'Source','name':'Name','type':'Type','site_id':'SiteID','country_iso':'Country', 'updated_at':'Updated'}

    list_columns = ['source_id','name','type','site_id','country_iso', 'updated_at']
    
    edit_columns = ['source_id','name','url','institution','type','site_id','national_site_id','regional_site_id','auth_token','country_iso','identifier_prefix','identifier_map_regex','identifier_map_replace','identifier_map_filename','identifier_map_type']
    add_columns = edit_columns

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


