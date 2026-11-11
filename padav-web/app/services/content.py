"""Imports tests and questions from a validated JSON file. Safe to re-run."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.exam import Exam
from app.models.question import Question
from app.models.question_option import QuestionOption
from app.models.subject import Subject
from app.models.test import Test
from app.models.test_question import TestQuestion
from app.schemas.content import ContentFile, ContentQuestion, ContentTest
from app.services.base import BaseService


@dataclass
class ImportReport:
    created: int = 0
    skipped: int = 0


class ContentImporter(BaseService):
    def __init__(self, db: Session) -> None:
        super().__init__(db)
        self._subjects: dict[tuple[str, str], Subject] = {}

    def import_file(self, path: Path) -> ImportReport:
        return self.import_content(ContentFile.model_validate(json.loads(path.read_text(encoding="utf-8"))))

    def import_content(self, content: ContentFile) -> ImportReport:
        exam = self.db.scalars(select(Exam).where(Exam.code == content.exam)).first()
        if exam is None:
            raise NotFoundError(f"Exam '{content.exam}' not found; run the catalogue seed first")
        report = ImportReport()
        for spec in content.tests:
            if self.db.scalars(select(Test).where(Test.exam_id == exam.id, Test.title == spec.title)).first():
                report.skipped += 1  # never overwrite a test that users may already have attempted
                continue
            self._create_test(exam, spec)
            report.created += 1
        self.commit()  # one transaction: a failure leaves nothing half-imported
        return report

    # -- internals ----------------------------------------------------------------
    def _subject(self, exam: Exam, name: str) -> Subject:
        key = (exam.id, name)
        if key not in self._subjects:
            subject = self.db.scalars(select(Subject).where(Subject.exam_id == exam.id, Subject.name == name)).first()
            if subject is None:
                subject = Subject(exam_id=exam.id, name=name)
                self.db.add(subject)
                self.db.flush()
            self._subjects[key] = subject
        return self._subjects[key]

    def _create_test(self, exam: Exam, spec: ContentTest) -> Test:
        test = Test(
            exam_id=exam.id,
            title=spec.title,
            title_hi=spec.title_hi,
            description=spec.description,
            total_questions=len(spec.questions),
            duration_minutes=spec.duration_minutes,
            marks_per_question=spec.marks_per_question,
            negative_marks_per_question=spec.negative_marks_per_question,
            negative_marking=spec.negative_marks_per_question > 0,
            total_marks=spec.marks_per_question * len(spec.questions),
            is_free=spec.is_free,
        )
        self.db.add(test)
        self.db.flush()
        for order, item in enumerate(spec.questions):
            question = self._create_question(exam, spec, item, order)
            self.db.add(TestQuestion(test_id=test.id, question_id=question.id, sort_order=order))
        return test

    def _create_question(self, exam: Exam, spec: ContentTest, item: ContentQuestion, order: int) -> Question:
        question = Question(
            subject_id=self._subject(exam, item.subject).id,
            text=item.text,
            text_hi=item.text_hi,
            explanation=item.explanation,
            explanation_hi=item.explanation_hi,
            difficulty=item.difficulty,
            marks=spec.marks_per_question,
            negative_marks=spec.negative_marks_per_question,
            correct_option_key=item.correct,
            sort_order=order,
        )
        self.db.add(question)
        self.db.flush()
        for index, (key, text) in enumerate(sorted(item.options.items())):
            self.db.add(QuestionOption(
                question_id=question.id, key=key, text=text, text_hi=item.options_hi.get(key),
                is_correct=key == item.correct, sort_order=index,
            ))
        return question
