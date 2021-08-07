from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import Length


class SearchForm(FlaskForm):
    title = StringField('title', validators=[Length(min=3, max=128)])
