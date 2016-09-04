from robot.planner.maps.graph import AdjacencyMatrixGraph as Graph
from robot.planner.maps.graph import Node

pORG=Node((0.3,0.3))
p0=Node((1.7,0.3))
p1=Node((1.2,1.2))
p2=Node((0.6,2.3))
p3=Node((0.6,3.1))
p4=Node((0.6,3.7))
p5=Node((1.6,3.7))
p6=Node((0.7,3.9))
p7=Node((0.5,4.2))
p8=Node((0.5,4.6))
p9=Node((0.5,5.1))
p10=Node((0.7,5.7))
p11=Node((1.7,5.7))
p12=Node((1.9,5.1))
p13=Node((1.9,4.2))
p14=Node((1.7,3.9))
p15=Node((1.1,5.6))
p16=Node((1.1,6.2))
p17=Node((0.7,6.7))
p18=Node((1.1,6.8))
p19=Node((2.0,7.0))
p20=Node((1.9,7.7))
p21=Node((1.9,7.9))
p22=Node((1.4,8.1))
p23=Node((0.9,7.9))

Lk=[]
Lk.append((('door'),
          {None:[p0]
          }))
Lk.append((('hall','living room'),
          {None:[p1]
          }))
Lk.append((('hallway'),
          {None:[p3]
          }))
Lk.append((('closet','locker'),
          {None:[p5]
          }))
Lk.append((('table'),
          {None:[p8],
           "around":[p8,p7,p6,p14,p13,p12,p11,p10,p9,p8]
          }))
Lk.append((('refrigerator'),
          {None:[p16]
          }))
Lk.append((('bath','bathroom'),
          {None:[p17]
          }))
Lk.append((('kitchen'),
          {None:[p21]
          }))
Lk.append((('sink'),
          {None:[p22]
          }))
Lk.append((('oven'),
          {None:[p23]
          }))
		 
CURRENT_MAP=Graph(
   V=[pORG,p0,p1,p2,p3,p4,p5,p6,p7,p8,p9,p10,p11,p12,p13,p14,p15,p16,p17,p18,p19,p20,p21,p22,p23],
   E=[
(pORG,p0),(pORG,p1),(pORG,p2),
(p0,p1),
(p1,p2),
(p2,p3),
(p3,p4),
(p4,p5),(p4,p6),(p4,p7),(p4,p14),
(p5,p6),(p5,p13),(p5,p14),
(p6,p7),(p6,p14),
(p7,p8),
(p8,p9),
(p9,p10),(p9,p17),
(p10,p11),(p10,p15),(p10,p16),(p10,p17),(p10,p18),
(p11,p12),(p11,p15),
(p12,p13),
(p13,p14),
(p15,p16),(p15,p17),
(p16,p17),(p16,p18),
(p17,p18),(p17,p19),
(p18,p19),
(p19,p20),(p19,p21),
(p20,p21),(p20,p22),(p20,p23),
(p21,p22),(p21,p23),
(p22,p23)],
L=Lk,
directed=False)