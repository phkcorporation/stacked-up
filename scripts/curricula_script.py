import os
from os.path import abspath, dirname
import sys
import csv
import re

# Set up django path so you can just run this in the VM
project_dir = abspath(dirname(dirname(__file__)))
sys.path.insert(0, project_dir)
os.environ["DJANGO_SETTINGS_MODULE"] = "sdp_curricula.settings"

from curricula.models import LearningMaterial, Publisher, PublisherGroup, Curriculum, GradeCurriculum
from vendors.models import Vendor, NegotiatedPrice
from schools.models import SchoolType


def define_curriculum(info, c_name, c_pub):
    try:
        c = Curriculum.objects.get(name=c_name, publisher=c_pub.group)
        print 'Found the curriculum ' + c.name
    except Curriculum.DoesNotExist:
        subject = info[4]
        c = Curriculum(name=c_name, publisher=c_pub.group, subject_area=subject)
        c.save()
        print 'Created the curriculum ' + c.name
    return c


def define_grade_curriculum(info, c):
    try:
        g = GradeCurriculum.objects.get(curriculum=c, grade_level_start=info[6], grade_level_end=info[7])
        print 'Found the curriculum set/grade curriculum for this file'
    except GradeCurriculum.DoesNotExist:
        g = GradeCurriculum(curriculum=c, grade_level_start=info[6], grade_level_end=info[7])
        g.save()
        print 'Created the curriculum set/grade curriculum'
    return g


def is_empowerment(info):
    if info[5] == 'TRUE':
        return True


def is_default(info):
    if len(info) > 8:
        if info[8] != 'FALSE':
            return True
    else:
        return True


def add_school_types(info, g, default, empowerment):
    if is_default(info):
        default.approved_curricula.add(g)
        print 'Approved for default'
    if is_empowerment(info):
        empowerment.approved_curricula.add(g)
        print 'Approved for empowerment'


def iterate_through_data(data, publisher, grade_curriculum, vendor, default,
    empowerment, is_empowerment, is_default):
    for row in data:
        isbn = row[1].strip().replace('-', '')
        if len(isbn) == 10:
            isbn = convert_10_to_13(isbn)
        if len(row[2]) > 1:
            title = row[0].strip().replace('*', '')
            try:
                if isbn == '':
                    print title
                    material = LearningMaterial.objects.get(title=title)
                    print 'Empty ISBN'
                else:
                    material = LearningMaterial.objects.get(isbn=isbn)
                    print 'Material title is ' + material.title
                print 'Found material ' + material.title
                if row[4] == 'TRUE':
                    material.isTeacherEdition = True
                    material.save()
                    print 'Updated as Teacher\'s edition'
                if row[5] != '':
                    material.quantity = int(row[5])
                    material.save()
                    print material.quantity
            except LearningMaterial.DoesNotExist:
                print 'Creating material'
                m_type = row[3]
                if row[4] == 'TRUE':
                    teachers = True
                    print 'This is a teacher\'s edition'
                else:
                    teachers = False
                if row[5] != '':
                    q = row[5]
                else:
                    q = 1
                material = LearningMaterial(isbn=isbn,
                    title=title, publisher=publisher,
                    material_type=m_type, isTeacherEdition=teachers,
                    quantity=q)
                material.save()
                print 'Material created: ' + material.title
            try:
                if isbn == '':
                    grade_curriculum.materials.get(title=material.title)
                else:
                    grade_curriculum.materials.get(isbn=material.isbn)
                print 'Looks like we already added this one to the curriculum!'
            except LearningMaterial.DoesNotExist:
                grade_curriculum.materials.add(material)
                grade_curriculum.save()
                print 'Material added to grade curriculum'

            # if '$' in row[2]:
            price = float(re.sub('[\$,]', '', row[2]))
            try:
                n = NegotiatedPrice.objects.get(value=price, material=material)
                print 'We have a price for this :)'
            except NegotiatedPrice.DoesNotExist:
                n = NegotiatedPrice(value=price, vendor=vendor, material=material)
                n.save()
                print 'Created the price'
            print material.title + ' has a price of ' + str(n.value)
            if is_default:
                n.negotiated_for_school_type.add(default)
                print 'Priced for default'
            if is_empowerment:
                n.negotiated_for_school_type.add(empowerment)
                print 'Priced for empowerment'


def check_digit_10(isbn):
    assert len(isbn) == 9
    sum = 0
    for i in range(len(isbn)):
        c = int(isbn[i])
        w = i + 1
        sum += w * c
    r = sum % 11
    if r == 10:
        return 'X'
    else:
        return str(r)


def check_digit_13(isbn):
    assert len(isbn) == 12
    sum = 0
    for i in range(len(isbn)):
        c = int(isbn[i])
        if i % 2:
            w = 3
        else:
            w = 1
        sum += w * c
    r = 10 - (sum % 10)
    if r == 10:
        return '0'
    else:
        return str(r)


def convert_10_to_13(isbn):
    assert len(isbn) == 10
    prefix = '978' + isbn[:-1]
    check = check_digit_13(prefix)
    return prefix + check


if __name__ == "__main__":
    try:
        print 'Looking for vendor with name ' + sys.argv[1]
        try:
            v = Vendor.objects.get(name=sys.argv[1])
            print 'Found ' + v.name
        except Vendor.DoesNotExist:
            v = Vendor(name=sys.argv[1])
            v.save()
            print 'Created ' + v.name
        csv_filepathname = sys.argv[2]  # Change to the CSV
        print 'Using the csv ' + csv_filepathname
    except IndexError:
        print 'Not enough arguments: vendor name and csv path expected'
    data = csv.reader(open(csv_filepathname, 'rU'), delimiter=',', quotechar='"')
    data.next()
    info = data.next()
    print info
    c_name = info[0]
    try:
        c_pub = Publisher.objects.filter(name=info[3])[0]
    except Publisher.DoesNotExist:
        new_group = PublisherGroup(name=info[3])
        new_group.save()
        c_pub = Publisher(name=info[3], group=new_group)
        c_pub.save()
    print 'Found a publisher named ' + c_pub.name
    c = define_curriculum(info, c_name, c_pub)
    g = define_grade_curriculum(info, c)
    default = SchoolType.objects.get(name="Default")
    empowerment = SchoolType.objects.get(name="Empowerment")
    add_school_types(info, g, default, empowerment)
    data.next()
    print 'Starting data iteration ...'
    iterate_through_data(data, c_pub, g, v, default,
        empowerment, is_empowerment(info), is_default(info))
