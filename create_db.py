#!/usr/bin/python

# Program to generate scores from race results sheets
# format: Bib # , Name , age , gender , time 

import sys
import os
import csv
import math
import sqlite3
import common
import datetime

try:
  os.remove( 'results.db' )
except:
  pass
conn = sqlite3.connect('results.db')
c = conn.cursor()

c.execute( "create table race    ( id INTEGER PRIMARY KEY AUTOINCREMENT  , name string , date date , factor integer , url string )" )
c.execute( "create table athlete ( id INTEGER PRIMARY KEY AUTOINCREMENT  , name string , sex string , age integer , points float )" )
c.execute( "create index athname on athlete(name)" ) # cut creation time from 50.8 to 30.8
c.execute( "create table results  ( id INTEGER PRIMARY KEY AUTOINCREMENT  , race integer , athlete integer , rank integer , points float )" )
c.execute( "create index resath on results(athlete)" ) #cut creation time from 30.8 to 1.26 (!!) 

def find_racer( name , age , gender ):
  try:
    age = int( age )
    c.execute( "select id , age from athlete where name=? and sex=? and ( ( age >= ? ) and ( age <= ? ) or age is null )" , 
               ( name , gender , age - 2 , age + 2 ) ) 
  except:
    c.execute( "select id , age from athlete where name=? and sex=?" , ( name , gender  ) )
  try:
    row = c.fetchone()
    if isinstance( age , int ): 
      if row[ 1 ] == None or age>row[1]:
        c.execute( "update athlete set age = ? where id = ?" , ( age , row[ 0 ] ) )
    return row[ 0 ]
  except:
    return None

def try_add( name , age , gender ):
  id = find_racer( name , age , gender )
  if id <> None:
    return id
  try:
    age = int( age )
    c.execute( "insert into athlete( name , sex , age ) values( ? , ? , ? )" , ( name , gender , age ) )
  except:
    c.execute( "insert into athlete( name , sex ) values( ? , ? )" , ( name , gender ) )
  return c.lastrowid

 
def add_gender( race_id , racers ):
  rank = 1 
  seen = {}
  for racer in racers:
    if not seen.has_key( racer ):
      c.execute( "insert into results(  race , athlete , rank ) values(?,?,?)" , ( race_id , racer , rank ) )
      rank = rank + 1 
      seen[ racer ] = 1
    else:
      pass
      #print "Skipping" , race_id , racer , rank
   
def fixName( name ):
   cs = name.split( "," )
   if len( cs ) > 1:
     name = cs[1]+" "+cs[0]
   name = " ".join( name.split() )
   return name


def main():
  sheets = os.popen( "ls -t data/*.csv" ).readlines()

  for sheet in sheets:
    sheet = sheet.strip()
    with open( sheet ) as results_file:
      print >> sys.stderr , "processing" , sheet 
      def pop():
        l = results_file.readline().strip().split(",")
        if len(l)==1:
          return l[0]
        else:
          return l[1]

      event = pop()

      dp = [ int(x) for x in pop().strip().split('-') ]
      date = datetime.date( dp[0] , dp[1], dp[2]  )

      if date < datetime.date.today()-datetime.timedelta(365):
        print "******event is over a year old, skipping" 
        continue 
      #so much ugly code, especially this:
      fs = pop()
      url = fs
      fs = pop()
      factor = int( fs )

      c.execute( "insert into race(name,factor,date,url) values(?,?,?,?)" , ( event , factor , date , url ) )
      race_id = c.lastrowid

      male_race   = []
      female_race = [] 
      result_reader = csv.reader( results_file , delimiter = ',' , quotechar = '"' )
      for result in result_reader:
        result = [unicode(cell, 'utf-8') for cell in result]
        (name,age,gender,time) = [ result[a].strip().upper() for a in (1,2,3,-1) ]

        name = fixName( name ) 
        gender = gender.upper()
        gender=gender.strip()
        if len(gender)>1:
          gender = gender[:1]
        athlete_id = try_add( name , age , gender )
        try:
          age = str(age)
          #print name , gender , time 
          gender = gender.upper()
          if gender == 'M':
            male_race.append( athlete_id )
          elif gender == 'F':
            female_race.append( athlete_id )  
          else: 
            pass 
        except:
          print >> sys.stderr , "No age for " , name 
      add_gender( race_id , male_race )
      add_gender( race_id , female_race )

main()
conn.commit()
