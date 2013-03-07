from django.db import models
from datetime import datetime


class School(models.Model):
    school_id = models.IntegerField()
    name = models.CharField(max_length=200, blank=True)
    grade_start = models.IntegerField()
    grade_end = models.IntegerField()
    street_addr = models.CharField(max_length=100, blank=True)
    zipcode = models.CharField(max_length=5, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    website = models.CharField(max_length=100, blank=True)
    school_level = models.CharField(max_length=100, blank=True)

    def __unicode__(self):
        return self.name


class Grade(models.Model):
    school = models.ForeignKey(School)
    grade_level = models.IntegerField()

    def __unicode__(self):
        return "%s, Grade %s" % (self.school.name, self.grade_level)


class Cohort(models.Model):
    YEARS = []

    for r in range(2008, (datetime.now().year + 1)):
        YEARS.append((r, r))

    grade = models.ForeignKey(Grade)
    # Cohort year, ex. 2008-2009
    year_start = models.IntegerField(max_length=2, choices=YEARS)
    year_end = models.IntegerField(max_length=2, choices=YEARS)
    math_advanced_percent = models.DecimalField(blank=True, max_digits=5, decimal_places=1)
    math_proficient_percent = models.DecimalField(blank=True, max_digits=5, decimal_places=1)
    math_basic_percent = models.DecimalField(blank=True, max_digits=5, decimal_places=1)
    math_below_basic_percent = models.DecimalField(blank=True, max_digits=5, decimal_places=1)
    read_advanced_percent = models.DecimalField(blank=True, max_digits=5, decimal_places=1)
    read_proficient_percent = models.DecimalField(blank=True, max_digits=5, decimal_places=1)
    read_basic_percent = models.DecimalField(blank=True, max_digits=5, decimal_places=1)
    read_below_basic_percent = models.DecimalField(blank=True, max_digits=5, decimal_places=1)
    math_combined_percent = models.DecimalField(blank=True, max_digits=5, decimal_places=1)
    read_combined_percent = models.DecimalField(blank=True, max_digits=5, decimal_places=1)

class Cohort2012To2013(models.Model):
    grade = models.ForeignKey(Grade)
    size = models.PositiveIntegerField()

class PublisherGroup(models.Model):
    name = models.CharField(max_length=100)
    def __unicode__(self):
        return self.name

class Publisher(models.Model):
    name = models.CharField(max_length=200)
    publisher_id = models.CharField(max_length=50, blank=True)
    group = models.ForeignKey(PublisherGroup, blank=True)
    def __unicode__(self):
        return "%s, part of %s" % (self.name, self.group.name)

class Textbook(models.Model):
    isbn = models.CharField(max_length=10)
    title = models.CharField(max_length=200)
    publisher = models.ForeignKey(Publisher)
    # Cost only loaded for books associated with a state curricula
    cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    isTeacherEdition = models.BooleanField(default=False)
    def __unicode__(self):
        return "%s, %s" % (self.isbn, self.title)

class InventoryRecord(models.Model):
    school = models.ForeignKey(School)
    textbook = models.ForeignKey(Textbook)
    qty_onsite = models.IntegerField()
    qty_to_student_home = models.IntegerField()
    qty_to_student_class = models.IntegerField()
    qty_lost_stolen = models.IntegerField()
    qty_unusable = models.IntegerField()
    qty_reallocated = models.IntegerField()
    def __unicode__(self):
        return "%s, %s" % (self.school.name, self.textbook.title)

class Curriculum(models.Model):
    """ 
    The superset of curriculum, may include many 
    curriculum sets for multiple grades 
    """
    name = models.CharField(max_length=100)
    SUBJECTS = [('Reading', 'Reading'),
                ('Mathematics', 'Mathematics'),
                ('Language Arts', 'Language Arts'),
                ('Science', 'Science'),
                ('Social Studies', 'Social Studies')]
    publisher = models.ForeignKey(PublisherGroup)
    is_empowerment = models.BooleanField(default=False)
    subject_area = models.CharField(max_length=100, choices=SUBJECTS)

class CurriculumSet(models.Model):
    curriculum = models.ForeignKey(Curriculum)
    name = models.CharField(max_length=100)
    books = models.ManyToManyField(Textbook)
    grade_level_start = models.IntegerField()
    grade_level_end = models.IntegerField()

