from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired


class AddVideoForm(FlaskForm):
    youtube_url = StringField("YouTube URL", validators=[DataRequired()])
    submit = SubmitField("Add video")


class AddBookForm(FlaskForm):
    title_query = StringField("Book title", validators=[DataRequired()])
    submit = SubmitField("Add book")