"""Study goal form."""
from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField
from wtforms.validators import DataRequired, NumberRange


class StudyGoalForm(FlaskForm):
    daily_goal_minutes = IntegerField(
        "Daily goal (minutes)",
        validators=[DataRequired(), NumberRange(min=5, max=1440, message="Must be between 5 and 1440 minutes.")],
    )
    weekly_goal_minutes = IntegerField(
        "Weekly goal (minutes)",
        validators=[DataRequired(), NumberRange(min=5, max=10080, message="Must be between 5 and 10080 minutes.")],
    )
    submit = SubmitField("Save goals")