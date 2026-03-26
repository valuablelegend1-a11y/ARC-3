**3/20/2026 - I created basic paper drawings of my concept.**

I started off by creating some very basic and crude 2D paper drawings, that are not to scale, but helped me get a good picture of how I wanted the project to come together. There is one of the whole deign concept, one of the claw, and one of a simple wiring diagram, the MG995 and MG90s servos will all channel throughout the arm down to the PCA9685, which will connect to the arduino uno, both of which will be powered by an AC-DC converter. 
![IMG_2252](https://github.com/user-attachments/assets/20dd1f4b-d441-4cbb-8ae9-5e10e5f79b72)
![IMG_2253](https://github.com/user-attachments/assets/da8996ac-a6ed-421a-885a-42c6cb823fc1)
![IMG_2254](https://github.com/user-attachments/assets/44aef004-f42f-4ee0-b7f5-da53136003f7)

***Time Spent: 2 Hours***

**3/21/2026 11 AM - I designed the main body with support and alignment.**

I then started designing it all from the ground up in Autodesk Fusion (formerly Fusion 360).
For the main body or 'base body' I started off with a 5 inch diameter outer edge, with a roughly 0.2 inch thickness to form a cylinder, I then extruded it to a height of 3 inches, to fit all electronics and mounts. From here I added a simple divider 0.3 inches from the bottom of the cylinder, so the base mount and electronics are separated. Next I measured out specific holes in the outer shell, that will fit the female sockets of both the Arduino input cable, and a DC cord for power from an outlet converter. After that I added a reinforced frame with screw holes, for the MG995 servo in the base, to ensure it was secure and correctly positioned, with simple support pillars for added strength. 
![Screenshot 2026-03-21 113335](https://github.com/user-attachments/assets/575cd18e-440e-49c4-824c-ce280ca9ae3e)

***Time Spent: 5.5 Hours***

**3/21/2026 4 PM - I created my BOM in csv format with links and pricing.**

I had a bit more time than I expected today, so I decided to find all the specific parts I had planned, and put it in a BOM.csv document in my GitHub repository. While I was researching I found better pricing than I initially thought, and was able to slightly cut costs without hindering performance. I also realized my initial plan to use an MG90S servo for the fingers would likely not be enough, so I decided to just go with all MG995 servos, for both the joints and fingers, to simplify things and ensure functionality would not be limited. I also decided on specific filament types, choosing PETG for its ease of use and strength to weight ratio, along with better flexibility under tension. The specific filament brand I use is Elegoo, as that is the brand of my 3D printer, and the quality has been good so far, the only downside is a $15.00 shipping price, however that is including sales tax, so it may even out.
![Screenshot 2026-03-21 160516](https://github.com/user-attachments/assets/8f641399-a2be-4b2b-b7a5-7f5d457c690c)

***Time Spent: 2.5 hours***

**3/22/2026 - I created the Base Top to be fitted and rotatable.**

At this point I got started on the top piece, the 'base top' that will fit on the main body, be fully rotatable, and be directly connected to the base MG995 servo. It was fairly uncomplicated to make the main circular portion to fit on top of the body, I did it by making a thin cylinder that fits the inside of the body cylinder (with tolerance) and a slightly wider portion overtop of that, that covers it all up nicely. For the connection to the servo I decided to make a cutout that will perfectly fit the servo horn, so the horn can be screwed onto the servo, and then glued into the base top. After that I made a structure off the top of the 'lid' portion of this piece, to give distance between the yaw and pitch joints. I started out with a basic rectangle, and decided to go with a slightly more curvy shape and fileted edges, for a more aesthetical design. on top of this I put a 2 inch diameter circle, which I extruded to the length needed to fit the second MG995 servo. I made a cutout to fit the servo, with screw holes aligned for the edges to be aligned where needed, and included tolerance to ensure it fits correctly. I also left it slightly offset for stability of the next piece, and created a loft to smooth out the edges. 
![Screenshot 2026-03-22 134518](https://github.com/user-attachments/assets/7c70361e-59db-421d-a7cb-3d297224da40)

***Time Spent: 5 Hours***

**3/22/2026 9 PM - I built the first arm segment.**

Next up was the first arm segment, the 'arm bottom' which I went back and forth for a while trying to get the design to look sleek, while also fitting all the components correctly and not hindering and capability. To do this, I started by creating a vertical rectangle, with fileted edges and a space for the servo horn or the previous MG995 servo, just like on the base top. After that I added a circular portion on top, that again, fit the MG995 servo for the next pitch or elbow joint, with dedicated screw holes and adjusted tolerances. On this piece I also left the servo hole portion slightly offset from the main portion, to allow for more stability and direction. There were slight complications with my design however, and I had to redo multiple sections to allow the servo to fit correctly. To be specific, I created the servo hole first, then I later on repositioned the top part, which offset the ledge and the screw holes, and caused me to spend more time fixing alignment. Only after I had fixed that issue, I created the loft, which, unbeknownst to me, also filled in part of the servo hole and ledges.
![Screenshot 2026-03-23 101127](https://github.com/user-attachments/assets/e12b7672-ef05-4846-9584-4307a08d6900)
Fortunately it was a simple fix to just re-cut out the servo hole, and not create a loft that restricted that space again. Then I slightly modified the design, so it was much more sleek and fit the servo and overall the way I wanted it to look, and I fixed some slight issues with the edges and repositioned the top portion.
![Screenshot 2026-03-23 101021](https://github.com/user-attachments/assets/0c9e3d98-6d94-4669-836c-ae6e3a3e7765)

***Time Spent: 6 Hours***

**3/23/2026 - I made channels through the designs for wiring.**

Today I decided to solve wiring, I need to have servo wires run from the fingers and other joints, all the way to the Arduino and power in the base. To do this, I cut out slots right above each joint connection, and ran them down behind the servos and into the next piece. I used an arc shape so there would be plenty of movement freedom for when the arm was rotating. I then cut a small hole in the bottom of the base lid to ensure all the wiring can flow smoothly down into the base. After I did all this I realized it had slightly messed up my arm pieces, by clearing out areas needed for internal support and stability, so I went back through every piece and slightly altered it to ensure the wires could run correctly without compromising structural integrity.

![Screenshot 2026-03-23 102500](https://github.com/user-attachments/assets/2f55cd79-70e8-4e42-a585-f22d413a431a)
<img width="853" height="921" alt="Screenshot 2026-03-23 102604" src="https://github.com/user-attachments/assets/84de4bfe-ab45-4ed0-9cce-65df3103c301" />

***Time Spent: 3 Hours***

**3/23/2026 5 PM - I designed the arm top to connect the fingers.**

Now I am starting the top portion that connects the fingers to the rest of the design, the 'arm top'. I started off with the previous arm piece, and cut it in half to use just the bottom portion. Initially my plan was to have each finger with it's own servo, but immediately when I started designing, I realized that was highly inefficient and resorted to a gear system to control all the fingers simultaneously with one servo. I needed a place to align all these gears, so I put a 5 inch circle on top if the half-arm piece I made earlier, and extruded it to 0.4 inches thick. I needed a I put three small rods in a triangle shape, to later align the gears correctly around the servo gear, and messed with the diameter for a bit to make them small enough to fit on the inside of the gears. After this I decided to make some support columns for the vertical gears, so they could freely rotate but be secured to the hand as a whole. Initially I just made them as vertical rectangular beams, then I added simple slots in the sides, so the rod to hold the fingers would be secure.
![Screenshot 2026-03-23 170800](https://github.com/user-attachments/assets/4224722d-8882-4064-90b8-abab7aa046ac)
![Screenshot 2026-03-23 170828](https://github.com/user-attachments/assets/4a328e0c-0ec4-424f-86d6-667fd8706d7f)

***Time Spent: 5 Hours***

*3/24/2026 - I created the gears with the correct teeth ratio.*

Next up was the actual gears, I started out by drawing a simple diagram of how I wanted the gears aligned and shaped, then got going on creating the real versions in CAD.
![IMG_2256](https://github.com/user-attachments/assets/2c77363d-1ce5-405d-8fd3-9eac587a61a2)
At first, since I am new to designing, I was hand creating every tooth, which was very time consuming and not perfectly symmetrical either. At first I was using my makeshift technique to create gears in a 2:1 ratio, with 5 and 10 teeth, but when I realized I would want more teeth on both gears, I decided to learn a better technique to not spend hours deigning them a second time. I found the method of copying the gear tooth sketch, and rotating it around the center circle of the gear by way of the move/copy tool. This sped up my project a large portion, and before too long I had correct gears with 10 and 20 teeth, along with a much more symmetrical design. I spent some time aligning them how I wanted, to test how they would function. As I did this I realized that realistically I would want a number of teeth divisible by 3, for the three fingers to be aligned the same without hours tweaking. So I created yet another simple sketch, just to ensure I could still visualize what I wanted.
![IMG_2257](https://github.com/user-attachments/assets/1d8db026-f4d4-48e2-8305-36bf98605fed)
And even though my second method of designing gears was faster, it still had it's downsides, so I went in search of a more efficient way. I found the obvious answer after not too long, the circular pattern function, which can duplicate a sketch around a circular axis evenly. I got it all set up, and sure enough, in less than 10 minutes I had perfectly symmetrical and aligned gears with the correct tooth amounts of 9 and 18.
![Screenshot 2026-03-24 113656](https://github.com/user-attachments/assets/3a805901-701d-4715-8d6b-db3d6a7d5d14)

***Time Spent: 4.5 Hours***

**3/24/2026 5 PM - I made the fingers with aligned gears.**

Today I started working on the fingers themselves, I started off with a slanted line, it was 1.5 inches long and at a 75 degree angle, I added a simple parallel line, and connected them at the bottom. Then I made another set of parallel lines of the same length, slanted back the other way, and connected those at the top. Upon testing the length compared to my other parts, I realized they would be a bit short, so I increased all the lines length to 2 inches, and that fit my size expectation much more. I then extruded them to a half inch, and extruded the flat face that would be the top, so it had a flat surface. After that I created a new gear, that would line up with the horizontal gears on the previous arm piece, and therefore open and close the fingers. Next I added a simple rod through the center, that would rotate on the pillars of the arm top, to give freedom of movement but retain connection to the overall structure. Then I simply duplicated the design twice, to have three fingers of the same dimensions without any guessing. I took a few minutes arranging them to how they would be setup in the end design, and added them to the assembly design I have. After I got them positioned, I realized the gears would not quite line up, so I rearranged them all, tried again, failed again, rearranged again, and got them to a position I was satisfied with. Then I saw that my rods running through the fingers did not align with the slots in the arm top, so I went back and redid those again as well. After getting it all set back up, I saw the gears were slightly too low (as to too far right before) so I realigned them all, and finally got it all setup correctly.
![Screenshot 2026-03-24 175037](https://github.com/user-attachments/assets/8bfaffa0-49e0-4057-9cf4-37ca60b9a793)
![Screenshot 2026-03-24 175050](https://github.com/user-attachments/assets/3d57e088-6760-4fe7-8183-0fe56f1d8f71)

***Time Spent: 3.5 Hours***

**3/26/2026 - I made two separate assemblies**

Now that the majority of all the modeling was done, I decided to combine my parts into two separate assemblies, one with electronics, and one without. I started from the bottom up, inserting everything into the first assembly -the non-electronics one- and arranging them all in the orientation they are meant to be in. Most of it was pretty simple, adding parts and moving them around, I had a few slight hiccups with accidentally moving them after initial orientation, which in turn messed up the geometry of the original design. However they had simple solutions to ensure nothing would be ruined. After I completed the first assembly, I started work on the one with electronics. I found CAD models for the servos, boards, and the like on GrabCAD, and set to work adding them to a file. This proved to be a slightly more complicated process, as some parts of my designs had gotten messed up along the way, so I had to redo multiple things so it all would fit correctly. Since it would be slightly difficult to add wires twisting the directions they would need to be in the design, I decided to add all components except wires, and just make a separate wiring diagram. Note: my particular design has all electronic components hidden on the inside, they are there, just not open visible without taking it apart.
![Screenshot 2026-03-26 114048](https://github.com/user-attachments/assets/6c4046e6-7175-4bf4-9215-4f0ed846a007)
![Screenshot 2026-03-26 114119](https://github.com/user-attachments/assets/8a7f8cf1-ed40-4b7b-a099-fdee8e791601)

***Time Spent: 3 Hours***
