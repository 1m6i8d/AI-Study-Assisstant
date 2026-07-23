"""Quiz generation and answer-submission forms."""
from flask_wtf import FlaskForm
from wtforms import SelectField, IntegerField, SelectMultipleField, SubmitField
from wtforms.validators import DataRequired, NumberRange


class QuizGenerateForm(FlaskForm):
    subject_id = SelectField("Subject", coerce=int, validators=[DataRequired()])
    question_types = SelectMultipleField(
        "Question types",
        choices=[
            ("multiple_choice", "Multiple choice"),
            ("true_false", "True/False"),
            ("short_answer", "Short answer"),
        ],
        default=["multiple_choice"],
        validators=[DataRequired(message="Select at least one question type.")],
    )
    question_count = IntegerField(
        "Number of questions",
        default=5,
        validators=[DataRequired(), NumberRange(min=1, max=15, message="Between 1 and 15 questions.")],
    )
    submit = SubmitField("Generate quiz")