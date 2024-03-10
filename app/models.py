from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy import DateTime
from datetime import datetime

from lareferenciastatsdb import Source, Country