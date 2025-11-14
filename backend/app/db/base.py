from app.db.base_class import Base
from app.models.university import University
from app.models.user import User
from app.models.staff import Staff
from app.models.faculty import Faculty
from app.models.kafedra import Kafedra
from app.models.student_group import StudentGroup
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.room import Room
from app.models.subject import Subject
from app.models.timeslot import Timeslot
from app.models.lesson import Lesson
from app.models.lesson_group import LessonGroup
from app.models.schedule_meta import ScheduleMeta
from app.models.schedule_changelog import ScheduleChangelog
from app.models.approval_road import ApprovalRoad
from app.models.request import Request
from app.models.request_document import RequestDocument
from app.models.request_approval_step import RequestApprovalStep
from app.models.event import Event, EventRegistration
from app.models.payment import Payment, PaymentHistory
from app.models.library import LibraryAccess
from app.models.elective import Elective, ElectiveRegistration
from app.models.broadcast import Broadcast

__all__ = [
    "Base",
    "University",
    "User",
    "Staff",
    "Faculty",
    "Kafedra",
    "StudentGroup",
    "Student",
    "Teacher",
    "Room",
    "Subject",
    "Timeslot",
    "Lesson",
    "LessonGroup",
    "ScheduleMeta",
    "ScheduleChangelog",
    "Request",
    "RequestDocument",
    "RequestApprovalStep",
    "ApprovalRoad",
    "Event",
    "EventRegistration",
    "Payment",
    "PaymentHistory",
    "LibraryAccess",
    "Elective",
    "ElectiveRegistration",
    "Broadcast",
]
