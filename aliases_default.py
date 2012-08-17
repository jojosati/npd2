# -*- coding: utf-8 -*-

now_alias = {
        "$today" : "$now",
        "$yesterday" : "$now(-1)",
        "$tomorrow" : "$now(+1.)",
        "$thisweek" : "$now.bow.prd(+7.)",
        "$lastweek" : "$now.bow.prd(-7.)",
        "$thismonth" : "$now(1).prd(0,+1.)",
        "$lastmonth" : "$now(1).prd(0,-1)",
        "$thisyear" : "$now(1,1).prd(0,0,+1.)",
        "$lastyear" : "$now(1,1).prd(0,0,-1)",
        "$bom" : "$now(1)",
        "$boy" : "$now(1,1)",
        }
