"""Subject-related WTForms."""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length

from app.models.subject import SUBJECT_COLORS


class SubjectForm(FlaskForm):
    name = StringField(
        "Subject name",
        validators=[DataRequired(), Length(min=1, max=100)],
    )
    description = TextAreaField(
        "Description",
        validators=[Length(max=500)],
    )
    color = SelectField(
        "Color",
        choices=[(c, c.capitalize()) for c in SUBJECT_COLORS],
        validators=[DataRequired()],
    )
    submit = SubmitField("Save subject")