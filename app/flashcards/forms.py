"""Flashcard-related WTForms."""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length


class FlashcardForm(FlaskForm):
    subject_id = SelectField("Subject", coerce=int, validators=[DataRequired()])
    front = StringField(
        "Front",
        validators=[DataRequired(), Length(min=1, max=500)],
        description="The question or prompt shown first.",
    )
    back = TextAreaField(
        "Back",
        validators=[DataRequired(), Length(min=1, max=1000)],
        description="The answer, revealed after flipping the card.",
    )
    submit = SubmitField("Save flashcard")