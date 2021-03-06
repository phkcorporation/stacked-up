from .models import School
from vendors.models import InventoryRecord, NegotiatedPrice
from curricula.models import GradeCurriculum
from students.models import Grade, Cohort
from core.models import SchoolAggregate
from django.views.generic import ListView
import simplejson as json
from django.shortcuts import get_object_or_404
from django.db.models import Q


class SchoolCurriculaMatch(ListView):

    context_object_name = "book_inventory"
    template_name = "analysis/school_curricula_match.html"

    def get_queryset(self):
        self.school = School.objects.get(school_code=self.kwargs['id'])
        each_book = InventoryRecord.objects.filter(school=self.school).prefetch_related('material__publisher__group')
        return each_book

    def get_context_data(self, **kwargs):
        context = super(SchoolCurriculaMatch, self).get_context_data(**kwargs)
        all_books = context['book_inventory']
        matched_books = {}
        unmatched_books = {}
        matched_curricula = {}
        for book in all_books:
            match_list = book.material.curricula.all()
            title = book.material.title
            isbn = book.material.isbn
            teacher_edition = book.material.isTeacherEdition
            publisher = book.material.publisher
            material_type = book.material.material_type
            total_book_count = 0
            total_book_count = total_book_count + book.qty_onsite + book.qty_to_student_home + book.qty_to_student_class + book.qty_lost_stolen + book.qty_unusable
            book_count_list = [book.qty_onsite, book.qty_to_student_home, book.qty_to_student_class, book.qty_lost_stolen, book.qty_unusable]
            if match_list:
                for match in match_list:
                    curricula_set = (match.curriculum.name, str(match.grade_level_start) + ' to ' + str(match.grade_level_end), match.curriculum.subject_area, match.curriculum.publisher, match.pk)
                try:
                    matched_curricula[curricula_set] = total_book_count + matched_curricula[curricula_set]
                except KeyError:
                    matched_curricula[curricula_set] = total_book_count
                matched_books[isbn] = {'matches': match_list, 'title': title, 'teacher_edition': teacher_edition, 'material_type': material_type, 'publisher': publisher, 'book_count': book_count_list}
            else:
                unmatched_books[isbn] = {'title': title, 'teacher_edition': teacher_edition, 'material_type': material_type, 'publisher': publisher, 'book_count': book_count_list}
        context['matched_books'] = matched_books
        context['unmatched_books'] = unmatched_books
        context['matched_curricula'] = matched_curricula
        context['school'] = self.school
        return context


class AnalysisSchoolInventory(ListView):

    context_object_name = "book_inventory"
    template_name = "analysis/school_inventory.html"

    def get_queryset(self):
        self.school = School.objects.get(school_code=self.kwargs['id'])
        inventory = InventoryRecord.objects.filter(school=self.school)
        return inventory

    def get_context_data(self, **kwargs):
        context = super(AnalysisSchoolInventory, self).get_context_data(**kwargs)
        context['school'] = self.school
        return context


class SchoolInventory(ListView):

    context_object_name = "inventory"
    template_name = "inventory.html"

    def get_queryset(self):
        self.school = get_object_or_404(School, school_code=self.kwargs['id'])
        inventory = InventoryRecord.objects.select_related('material').filter(school=self.school)
        return inventory

    def get_context_data(self, **kwargs):
        context = super(SchoolInventory, self).get_context_data(**kwargs)
        context['school'] = self.school
        return context


class SchoolDetailView(ListView):

    context_object_name = "book_inventory"
    template_name = "analysis/school.html"

    def get_queryset(self):
        self.school = School.objects.get(school_code=self.kwargs['id'])
        each_book = InventoryRecord.objects.filter(school=self.school)
        return each_book

    def get_context_data(self, **kwargs):
        context = super(SchoolDetailView, self).get_context_data(**kwargs)
        context['school'] = self.school
        return context


class AnalysisSchoolsListView(ListView):

    context_object_name = "schools"
    template_name = "analysis/schools_list.html"
    model = School


class SchoolAggregateView(ListView):

    context_object_name = "curricula"
    template_name = "school_aggregate.html"

    def get_queryset(self):
        self.school = get_object_or_404(School, school_code=self.kwargs['id'])
        all_books = InventoryRecord.objects.select_related('material').filter(school=self.school)
        return all_books

    def is_enough_books(self, number_of_books, students_in_grade):
        if number_of_books >= students_in_grade:
            return True
        else:
            return False

    def get_materials_for_grade_curriculum(self, students_in_grade, subject,
                                           all_books, cohort, grade_curriculum_id, grade_curriculum_name):
        self.curriculum_list[subject]['curricula'][grade_curriculum_name] = {
            'necessary_material': {},
            'cost_shortfall': 0,
            'book_shortfall': 0,
            'likely_curriculum': False
        }
        grade_curriculum = GradeCurriculum.objects.get(id=grade_curriculum_id)
        self.curriculum_list[subject]['curricula'][grade_curriculum_name]['necessary_material'] = []
        if (grade_curriculum == cohort.grade.likely_math_curriculum) or (grade_curriculum == cohort.grade.likely_reading_curriculum):
            self.curriculum_list[subject]['curricula'][grade_curriculum_name]['likely_curriculum'] = True
        for material in grade_curriculum.necessary_materials.all():
            cost_of_book = self.get_material_price(material)
            if all_books.filter(material=material).exists():
                number_of_books = all_books.get(material=material).get_inventory_total()
                enough_books = self.is_enough_books(number_of_books, students_in_grade)
                difference = number_of_books - students_in_grade
                numerical_difference = difference
            else:
                number_of_books = 'No records found'
                difference = students_in_grade * -1
                numerical_difference = students_in_grade * -1
                enough_books = False
                self.curriculum_list[subject]['curricula'][grade_curriculum_name]['cost_shortfall'] += (students_in_grade * cost_of_book)
                self.curriculum_list[subject]['curricula'][grade_curriculum_name]['book_shortfall'] += (students_in_grade)
            if number_of_books != 'No records found' and (students_in_grade - number_of_books) >= 0:
                self.curriculum_list[subject]['curricula'][grade_curriculum_name]['cost_shortfall'] += (students_in_grade - number_of_books) * cost_of_book
                self.curriculum_list[subject]['curricula'][grade_curriculum_name]['book_shortfall'] += (students_in_grade - number_of_books)
            else:
                self.curriculum_list[subject]['curricula'][grade_curriculum_name]['cost_shortfall'] += 0
                self.curriculum_list[subject]['curricula'][grade_curriculum_name]['book_shortfall'] += 0
            self.curriculum_list[subject]['curricula'][grade_curriculum_name]['necessary_material'].append(
                {
                    'title': material.title,
                    'total_copies': number_of_books,
                    'needed': students_in_grade,
                    'cost': cost_of_book,
                    'enough': enough_books,
                    'difference': difference,
                    'numerical_difference': numerical_difference,
                    'pk': material.pk
                }
            )

    def get_material_price(self, material):
        prices = NegotiatedPrice.objects.filter(material=material)
        if len(prices) > 1:
            for price in prices:
                if self.school.school_type in price.negotiated_for_school_type.all():
                    return price.value
        else:
            return prices[0].value

    def get_grade_curricula_by_subject(self, students_in_grade, subject, all_books, cohort):
        self.curriculum_list[subject] = {
            'curricula': {}
        }
        if subject == "math":
            for grade_curriculum in cohort.associated_math_curriculum.all():
                self.get_materials_for_grade_curriculum(students_in_grade, 'math', all_books, cohort, grade_curriculum.id, grade_curriculum.curriculum.name)
        if subject == "reading":
            for grade_curriculum in cohort.associated_reading_curriculum.all():
                self.get_materials_for_grade_curriculum(students_in_grade, 'reading', all_books, cohort, grade_curriculum.id, grade_curriculum.curriculum.name)

    def get_school_aggregate(self, school):
        """
            In this school, we have x students, x books of the common materials, and x shortfall
        """
        aggregate = SchoolAggregate.objects.get(school=school)
        data = {}
        data['students'] = aggregate.number_of_students
        data['material_count'] = aggregate.number_of_common_materials
        data['difference'] = data['material_count'] - data['students'] * 2  # times two subjects
        return data

    def get_context_data(self, **kwargs):
        context = super(SchoolAggregateView, self).get_context_data(**kwargs)
        try:
            grade = self.kwargs['grade']
        except KeyError:
            grade = self.school.grade_start
        cohort_set = Cohort.objects.filter(grade=get_object_or_404(Grade, school=self.school, grade_level=grade))
        current_cohort = cohort_set.get(year_end=2013)
        current_grade = Grade.objects.get(school=self.school, grade_level=grade)
        students_in_grade = current_cohort.number_of_students
        grades = Grade.objects.filter(school=self.school).order_by('grade_level')
        self.curriculum_list = {}
        self.get_grade_curricula_by_subject(students_in_grade, 'reading', context['curricula'], current_cohort)
        self.get_grade_curricula_by_subject(students_in_grade, 'math', context['curricula'], current_cohort)
        context['current_grade'] = current_grade.human_grade
        context['grades'] = grades
        context['students'] = current_cohort.number_of_students
        context['school_aggregate'] = self.get_school_aggregate(self.school)
        context['curriculum_list'] = self.curriculum_list
        context['pssa_test_scores'] = json.dumps([obj for obj in cohort_set.values()])
        context['school'] = self.school
        context['request'] = self.request
        return context
