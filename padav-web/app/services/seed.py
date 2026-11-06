from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.exam import Exam
from app.models.subject import Subject

EXAMS = [
    ("ssc-cgl", "SSC CGL", "एसएससी सीजीएल", "SSC", "Combined Graduate Level Examination"),
    ("ssc-chsl", "SSC CHSL", "एसएससी सीएचएसएल", "SSC", "Combined Higher Secondary Level Examination"),
    ("bank-po", "Banking PO", "बैंकिंग पीओ", "Banking", "Probationary Officer examinations"),
    ("bank-clerk", "Banking Clerk", "बैंकिंग क्लर्क", "Banking", "Clerical cadre examinations"),
    ("upsc-cse", "UPSC Civil Services", "यूपीएससी सिविल सेवा", "UPSC", "Civil Services Preliminary and Main examinations"),
    ("rrb-ntpc", "Railway RRB NTPC", "रेलवे आरआरबी एनटीपीसी", "Railway", "Non-Technical Popular Categories examination"),
    ("state-gov", "State Government Exams", "राज्य सरकारी परीक्षाएँ", "State", "State public service and government examinations"),
]

SUBJECTS = [
    ("quantitative-aptitude", "Quantitative Aptitude", "मात्रात्मक योग्यता", "Build confident problem-solving and calculation speed."),
    ("reasoning", "Reasoning", "रीज़निंग", "Learn patterns, logic, and efficient solving methods."),
    ("english", "English Language", "अंग्रेज़ी भाषा", "Practice grammar, vocabulary, and reading comprehension."),
    ("general-awareness", "General Awareness", "सामान्य जागरूकता", "Strengthen current and static general knowledge."),
    ("general-studies", "General Studies", "सामान्य अध्ययन", "Create a strong foundation across core exam subjects."),
    ("current-affairs", "Current Affairs", "समसामयिक घटनाएँ", "Review important national and international developments."),
]


def seed_development_data(db: Session) -> None:
    """Insert stable starter catalog data without overwriting user content."""
    for code, name, name_hi, category, description in EXAMS:
        if not db.query(Exam).filter(Exam.code == code).first():
            db.add(Exam(code=code, name=name, name_hi=name_hi, category=category, description=description))
    db.flush()

    ssc = db.query(Exam).filter(Exam.code == "ssc-cgl").one()
    for index, (slug, name, name_hi, description) in enumerate(SUBJECTS, start=1):
        subject = db.query(Subject).filter(Subject.exam_id == ssc.id, Subject.name == name).first()
        if not subject:
            subject = Subject(exam_id=ssc.id, name=name, name_hi=name_hi, description=description, sort_order=index)
            db.add(subject)
            db.flush()
        if not db.query(Course).filter(Course.title == f"{name}: Foundations").first():
            db.add(Course(
                subject_id=subject.id,
                title=f"{name}: Foundations",
                title_hi=f"{name_hi}: आधारभूत पाठ्यक्रम",
                description=description,
                instructor="Padav Learning Team",
                level="beginner",
                total_lessons=12 + index,
                estimated_hours=5 + index,
                is_free=True,
            ))
    db.commit()
