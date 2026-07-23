"""Timetable entry form."""
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, TimeField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, ValidationError

from app.models.timetable_entry import DAY_NAMES


class TimetableEntryForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(min=1, max=150)])
    subject_id = SelectField("Subject (optional)", coerce=int, validators=[Optional()])
    entry_type = SelectField(
        "Type",
        choices=[("recurring", "Recurring weekly"), ("one_off", "One-time")],
        validators=[DataRequired()],
    )
    day_of_week = SelectField(
        "Day of week",
        choices=[(str(i), name) for i, name in enumerate(DAY_NAMES)],
        validators=[Optional()],
    )
    specific_date = DateField("Date", validators=[Optional()])
    start_time = TimeField("Start time", validators=[DataRequired()])
    end_time = TimeField("End time", validators=[DataRequired()])
    submit = SubmitField("Save entry")

    def validate_end_time(self, field):
        if self.start_time.data and field.data and field.data <= self.start_time.data:
            raise ValidationError("End time must be after start time.")

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False
        if self.entry_type.data == "recurring" and self.day_of_week.data in (None, ""):
            self.day_of_week.errors.append("Select a day for a recurring entry.")
            return False
        if self.entry_type.data == "one_off" and not self.specific_date.data:
            self.specific_date.errors.append("Select a date for a one-time entry.")
            return False
        return True