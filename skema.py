#!/usr/bin/env python
# coding: utf-8
import requests
from pyquery import PyQuery as pq
import sys
import datetime


try:
    week_number = int(sys.argv[1])
except IndexError:
    week_number = datetime.date.today().isocalendar()[1]
except Exception:
    print "Please provide a week number, e.g. %s (the current week)" % datetime.date.today().isocalendar()[1]
    exit(1)

s = requests.session()

data = {'aarskort': 'KO87148', 'B1': 'S%F8g'}

s.get("http://services.science.au.dk/apps/skema/VaelgElevskema.asp?webnavn=skema&amp;sprog=da")
r = s.post("http://services.science.au.dk/apps/skema/ElevSkema.asp", data=data)


#class R(object):
#    text = ""
#r = R()
#r.text = open("test.html").read()


d = pq(r.text)

days = ['Mandag', 'Tirsdag', 'Onsdag', 'Torsdag', 'Fredag']

classes = []

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
                week_from, week_to = weeks.text().replace("uge ", "").split("-")
                classes.append({'subject': subject.text, 'day': day.text(), 'hours': hours.text(),
                                'week_from': int(week_from), 'week_to': int(week_to), 'location': location.text(), 'type': type})
        obj = obj.next()

classes_for_week = [c for c in classes if c['week_from'] <= week_number <= c['week_to']]

print "SKEMA FOR UGE %s" % week_number

for day in days:
    print "====", day.upper(), "===="
    classes_for_day = [c for c in classes_for_week if c['day'] == day]
    classes_for_day = sorted(classes_for_day, key=lambda c: int(c['hours'].split(" - ")[0]))
    for c in classes_for_day:
        print c['hours'], c['subject'], c['type']

