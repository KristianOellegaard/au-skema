#!/usr/bin/env python
# coding: utf-8

import requests
from pyquery import PyQuery as pq
import sys
import datetime
import os
import argparse
from textwrap import wrap
import json

class SchemaEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, SchemaEntry):
            return { 
                'subject': obj.subject,
                'day': obj.day,
                'hours': obj.hours,
                'start_time': obj.start_time,
                'end_time': obj.end_time,
                'week_from': obj.week_from,
                'week_to': obj.week_to,
                'location': obj.location,
                'type': obj.type
            }
        if isinstance(obj, Subject):
            return obj.name
        return json.JSONEncoder.default(self, obj)

class Subject(object):

    def __init__(self, name):
        self.name = name

class Schema(object):

    days = ['Mandag', 'Tirsdag', 'Onsdag', 'Torsdag', 'Fredag']

    def __init__(self, week_number, student_number):
        self.week_number = week_number
        self.student_number = student_number

        s = requests.session()

        data = {'aarskort': student_number, 'B1': 'S%F8g'}

        s.get("http://services.science.au.dk/apps/skema/VaelgElevskema.asp?webnavn=skema&amp;sprog=da")
        r = s.post("http://services.science.au.dk/apps/skema/ElevSkema.asp", data=data)

        d = pq(r.text)

        classes = []
        time_slots = []

        for subject in d("h3"):
            obj = d(subject).next()
            type = "Unknown"
            while obj.next():
                if obj.is_("h3"):
                    break
                if obj.is_("strong"):
                    type = obj.text()
                if obj.is_("table"):
                    for row in obj.find("tr"):
                        team, day, hours, location, weeks, none = [pq(x) for x in pq(row).find("td")]
                        week_text = weeks.text().replace("uge ", "")
                        if len(weeks.text().split("-")) == 2:
                            week_from, week_to = week_text.split("-")
                        else:
                            week_from = week_to = week_text
                        classes.append(SchemaEntry(subject=Subject(subject.text), day=day.text(), hours=hours.text(),
                            week_from=int(week_from), week_to=int(week_to), location=location.text(), type=type))
                        if hours.text().split(" - ")[0] not in time_slots:
                            time_slots.append(int(hours.text().split(" - ")[0]))
                        if hours.text().split(" - ")[1] not in time_slots:
                            time_slots.append(int(hours.text().split(" - ")[1]))
                obj = obj.next()

        self.entries = [c for c in classes if c.week_from <= week_number <= c.week_to]
        time_slots = sorted(time_slots, key=lambda c: int(c))
        self.time_slots = range(time_slots[0], time_slots[-1])

    def weekly_schedule(self):
        schedule = {}
        for day in self.days:
            schedule[day] = []
            classes_for_day = [c for c in self.entries if c.day == day]
            classes_for_day = sorted(classes_for_day, key=lambda c: int(c.hours.split(" - ")[0]))
            for c in classes_for_day:
                schedule[day].append(c)
        return schedule

class SchemaEntry(object):

    def __init__(self, subject, day, hours, week_from, week_to, location, type):
        self.subject = subject
        self.day = day
        self.hours = hours
        self.start_time = int(hours.split(" - ")[0])
        self.end_time = int(hours.split(" - ")[1])
        self.week_from = week_from
        self.week_to = week_to
        self.location = location
        self.type = type

    def __unicode__(self):
        return "%s\n%s\n%s" % (self.subject.name, "\n".join(self.location.split(",")), "\n".join(wrap(self.type, 20)))


def get_table_from_schema(s):
    from prettytable import PrettyTable
    ws = s.weekly_schedule()
    x = PrettyTable(['Time'] + Schema.days)
    for time_slot in s.time_slots:
        classes_by_hour = []
        for day in Schema.days:
            class_list = [se.__unicode__() for se in ws[day] if se.start_time == time_slot or se.start_time < time_slot < se.end_time ] or ['']
            classes_by_hour.append(class_list[0] + "\n")
        x.add_row(["%s-%s" % (time_slot, time_slot+1)] + classes_by_hour)
    return x

def plain_format(s, w, n):
    header = "=== Uge " + str(w) + " - " + str(n) + " ===\n"
    return header + get_table_from_schema(s).__str__()

def json_format(s, w, n):
    ws = s.weekly_schedule()
    return json.dumps(ws, cls=SchemaEncoder)

def html_format(s, w, n):
    return get_table_from_schema(s).get_html_string()

def main():
    formats = { 'plain': plain_format, 'html': html_format, 'json': json_format }

    parser = argparse.ArgumentParser(
        epilog="""If you get tired of writing your student number all the time,
                  this can be saved in ~/.au-skema. The number from this file
                  will be used as the default.""")
    parser.add_argument('week', type=int, nargs='?',
                        default=datetime.date.today().isocalendar()[1],
                        help='week number for which to show the schedule')
    parser.add_argument('student', nargs='?',
                        default=open(os.path.join(os.environ['HOME'], ".au-skema")).read().replace("\n", ""),
                        help='your student number')
    parser.add_argument('-f', '--format', default='plain', choices=formats.keys(),
                        help='the output format to use')

    args = parser.parse_args()

    schema = Schema(week_number=args.week, student_number=args.student)
    formatter = formats[args.format]
    print formatter(schema, args.week, args.student)

if __name__ == "__main__":
    main()
    
