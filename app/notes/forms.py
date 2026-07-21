"""Note-related WTForms."""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length


class NoteForm(FlaskForm):
    title = StringField(
        "Title",
        validators=[DataRequired(), Length(min=1, max=200)],
    )
    subject_id = SelectField(
        "Subject",
        coerce=int,
        validators=[DataRequired()],
    )
    content = TextAreaField(
        "Content",
        validators=[DataRequired()],
    )
    tags = StringField(
        "Tags",
        validators=[Length(max=200)],
        description="Comma-separated, e.g. exam, chapter-3, important",
    )
    submit = SubmitField("Save note")