**3/20/2026 - I created basic paper drawings of my concept.**

I started off by creating some very basic and crude 2D paper drawings, that are not to scale, but helped me get a good picture of how I wanted the project to come together. There is one of the whole deign concept, one of the claw, and one of a simple wiring diagram, the MG995 and MG90s servos will all channel throughout the arm down to the PCA9685, which will connect to the arduino uno, both of which will be powered by an AC-DC converter. 
![IMG_2252](https://github.com/user-attachments/assets/20dd1f4b-d441-4cbb-8ae9-5e10e5f79b72)
![IMG_2253](https://github.com/user-attachments/assets/da8996ac-a6ed-421a-885a-42c6cb823fc1)
![IMG_2254](https://github.com/user-attachments/assets/44aef004-f42f-4ee0-b7f5-da53136003f7)

*Time Spent: 2 Hours*

------------------------------------------------------------------------

**3/21/2026 11 AM - I designed the main body with support and alignment.**

I then started designing it all from the ground up in Autodesk Fusion (formerly Fusion 360).
For the main body or 'base body' I started off with a 5 inch diameter outer edge, with a roughly 0.2 inch thickness to form a cylinder, I then extruded it to a height of 3 inches, to fit all electronics and mounts. From here I added a simple divider 0.3 inches from the bottom of the cylinder, so the base mount and electronics are separated. Next I measured out specific holes in the outer shell, that will fit the female sockets of both the Arduino input cable, and a DC cord for power from an outlet converter. After that I added a reinforced frame with screw holes, for the MG995 servo in the base, to ensure it was secure and correctly positioned, with simple support pillars for added strength. 
![Screenshot 2026-03-21 113335](https://github.com/user-attachments/assets/575cd18e-440e-49c4-824c-ce280ca9ae3e)

*Time Spent: 5.5 Hours*

----------------------------------------------------------------------------

**3/21/2026 4 PM - I created my BOM in csv format with links and pricing.**

I had a bit more time than I expected today, so I decided to find all the specific parts I had planned, and put it in a BOM.csv document in my GitHub repository. While I was researching I found better pricing than I initially thought, and was able to slightly cut costs without hindering performance. I also realized my initial plan to use an MG90S servo for the fingers would likely not be enough, so I decided to just go with all MG995 servos, for both the joints and fingers, to simplify things and ensure functionality would not be limited. I also decided on specific filament types, choosing PETG for its ease of use and strength to weight ratio, along with better flexibility under tension. The specific filament brand I use is Elegoo, as that is the brand of my 3D printer, and the quality has been good so far, the only downside is a $15.00 shipping price, however that is including sales tax, so it may even out.
![Screenshot 2026-03-21 160516](https://github.com/user-attachments/assets/8f641399-a2be-4b2b-b7a5-7f5d457c690c)

*Time Spent: 2.5 hours*

--------------------------------------------------------------------

**3/22/2026 - I created the Base Top to be fitted and rotatable.**

At this point I got started on the top piece, the 'base top' that will fit on the main body, be fully rotatable, and be directly connected to the base MG995 servo. It was fairly uncomplicated to make the main circular portion to fit on top of the body, I did it by making a thin cylinder that fits the inside of the body cylinder (with tolerance) and a slightly wider portion overtop of that, that covers it all up nicely. For the connection to the servo I decided to make a cutout that will perfectly fit the servo horn, so the horn can be screwed onto the servo, and then glued into the base top. After that I made a structure off the top of the 'lid' portion of this piece, to give distance between the yaw and pitch joints. I started out with a basic rectangle, and decided to go with a slightly more curvy shape and fileted edges, for a more aesthetical design. on top of this I put a 2 inch diameter circle, which I extruded to the length needed to fit the second MG995 servo. I made a cutout to fit the servo, with screw holes aligned for the edges to be aligned where needed, and included tolerance to ensure it fits correctly. I also left it slightly offset for stability of the next piece, and created a loft to smooth out the edges. 
<img width="1148" height="910" alt="Screenshot 2026-03-22 134518" src="https://github.com/user-attachments/assets/f72d685a-f1a0-4017-8baf-2f7399950a86" />


*Time Spent: 5 Hours*

-----------------------------------------------------------

**3/22/2026 9 PM - I built the first arm segment.**

Next up was the first arm segment, the 'arm bottom' which I went back and forth for a while trying to get the design to look sleek, while also fitting all the components correctly and not hindering and capability. To do this, I started by creating a vertical rectangle, with fileted edges and a space for the servo horn or the previous MG995 servo, just like on the base top. After that I added a circular portion on top, that again, fit the MG995 servo for the next pitch or elbow joint, with dedicated screw holes and adjusted tolerances. On this piece I also left the servo hole portion slightly offset from the main portion, to allow for more stability and direction. There were slight complications with my design however, and I had to redo multiple sections to allow the servo to fit correctly. To be specific, I created the servo hole first, then I later on repositioned the top part, which offset the ledge and the screw holes, and caused me to spend more time fixing alignment. Only after I had fixed that issue, I created the loft, which, unbeknownst to me, also filled in part of the servo hole and ledges.
![Screenshot 2026-03-23 101127](https://github.com/user-attachments/assets/e12b7672-ef05-4846-9584-4307a08d6900)
Fortunately it was a simple fix to just re-cut out the servo hole, and not create a loft that restricted that space again. Then I slightly modified the design, so it was much more sleek and fit the servo and overall the way I wanted it to look, and I fixed some slight issues with the edges and repositioned the top portion.
![Screenshot 2026-03-23 101021](https://github.com/user-attachments/assets/0c9e3d98-6d94-4669-836c-ae6e3a3e7765)

*Time Spent: 6 Hours*

-----------------------------------------------------------------

**3/23/2026 - I made channels through the designs for wiring.**

Today I decided to solve wiring, I need to have servo wires run from the fingers and other joints, all the way to the Arduino and power in the base. To do this, I cut out slots right above each joint connection, and ran them down behind the servos and into the next piece. I used an arc shape so there would be plenty of movement freedom for when the arm was rotating. I then cut a small hole in the bottom of the base lid to ensure all the wiring can flow smoothly down into the base. After I did all this I realized it had slightly messed up my arm pieces, by clearing out areas needed for internal support and stability, so I went back through every piece and slightly altered it to ensure the wires could run correctly without compromising structural integrity.

![Screenshot 2026-03-23 102500](https://github.com/user-attachments/assets/2f55cd79-70e8-4e42-a585-f22d413a431a)
<img width="853" height="921" alt="Screenshot 2026-03-23 102604" src="https://github.com/user-attachments/assets/84de4bfe-ab45-4ed0-9cce-65df3103c301" />

*Time Spent: 3 Hours*

--------------------------------------------------------------------

**3/23/2026 5 PM - I designed the arm top to connect the fingers.**

Now I am starting the top portion that connects the fingers to the rest of the design, the 'arm top'. I started off with the previous arm piece, and cut it in half to use just the bottom portion. Initially my plan was to have each finger with it's own servo, but immediately when I started designing, I realized that was highly inefficient and resorted to a gear system to control all the fingers simultaneously with one servo. I needed a place to align all these gears, so I put a 5 inch circle on top if the half-arm piece I made earlier, and extruded it to 0.4 inches thick. I needed a I put three small rods in a triangle shape, to later align the gears correctly around the servo gear, and messed with the diameter for a bit to make them small enough to fit on the inside of the gears. After this I decided to make some support columns for the vertical gears, so they could freely rotate but be secured to the hand as a whole. Initially I just made them as vertical rectangular beams, then I added simple slots in the sides, so the rod to hold the fingers would be secure.
![Screenshot 2026-03-23 170800](https://github.com/user-attachments/assets/4224722d-8882-4064-90b8-abab7aa046ac)
![Screenshot 2026-03-23 170828](https://github.com/user-attachments/assets/4a328e0c-0ec4-424f-86d6-667fd8706d7f)

*Time Spent: 5 Hours*

-------------------------------------------------------------------

**3/24/2026 - I created the gears with the correct teeth ratio.**

Next up was the actual gears, I started out by drawing a simple diagram of how I wanted the gears aligned and shaped, then got going on creating the real versions in CAD.
![IMG_2256](https://github.com/user-attachments/assets/2c77363d-1ce5-405d-8fd3-9eac587a61a2)
At first, since I am new to designing, I was hand creating every tooth, which was very time consuming and not perfectly symmetrical either. At first I was using my makeshift technique to create gears in a 2:1 ratio, with 5 and 10 teeth, but when I realized I would want more teeth on both gears, I decided to learn a better technique to not spend hours deigning them a second time. I found the method of copying the gear tooth sketch, and rotating it around the center circle of the gear by way of the move/copy tool. This sped up my project a large portion, and before too long I had correct gears with 10 and 20 teeth, along with a much more symmetrical design. I spent some time aligning them how I wanted, to test how they would function. As I did this I realized that realistically I would want a number of teeth divisible by 3, for the three fingers to be aligned the same without hours tweaking. So I created yet another simple sketch, just to ensure I could still visualize what I wanted.
![IMG_2257](https://github.com/user-attachments/assets/1d8db026-f4d4-48e2-8305-36bf98605fed)
And even though my second method of designing gears was faster, it still had it's downsides, so I went in search of a more efficient way. I found the obvious answer after not too long, the circular pattern function, which can duplicate a sketch around a circular axis evenly. I got it all set up, and sure enough, in less than 10 minutes I had perfectly symmetrical and aligned gears with the correct tooth amounts of 9 and 18.
![Screenshot 2026-03-24 113656](https://github.com/user-attachments/assets/3a805901-701d-4715-8d6b-db3d6a7d5d14)

*Time Spent: 4.5 Hours*

--------------------------------------------------------------

**3/24/2026 5 PM - I made the fingers with aligned gears.**

Today I started working on the fingers themselves, I started off with a slanted line, it was 1.5 inches long and at a 75 degree angle, I added a simple parallel line, and connected them at the bottom. Then I made another set of parallel lines of the same length, slanted back the other way, and connected those at the top. Upon testing the length compared to my other parts, I realized they would be a bit short, so I increased all the lines length to 2 inches, and that fit my size expectation much more. I then extruded them to a half inch, and extruded the flat face that would be the top, so it had a flat surface. After that I created a new gear, that would line up with the horizontal gears on the previous arm piece, and therefore open and close the fingers. Next I added a simple rod through the center, that would rotate on the pillars of the arm top, to give freedom of movement but retain connection to the overall structure. Then I simply duplicated the design twice, to have three fingers of the same dimensions without any guessing. I took a few minutes arranging them to how they would be setup in the end design, and added them to the assembly design I have. After I got them positioned, I realized the gears would not quite line up, so I rearranged them all, tried again, failed again, rearranged again, and got them to a position I was satisfied with. Then I saw that my rods running through the fingers did not align with the slots in the arm top, so I went back and redid those again as well. After getting it all set back up, I saw the gears were slightly too low (as to too far right before) so I realigned them all, and finally got it all setup correctly.
![Screenshot 2026-03-24 175037](https://github.com/user-attachments/assets/8bfaffa0-49e0-4057-9cf4-37ca60b9a793)
![Screenshot 2026-03-24 175050](https://github.com/user-attachments/assets/3d57e088-6760-4fe7-8183-0fe56f1d8f71)

*Time Spent: 3.5 Hours*

---------------------------------------------------------------------------------

**3/25/2026 11 AM - I designed the base bottom with an interchangeable system**

Lastly for the modeling, I needed to get the base system set up, the 'base bottom'. I want the base to be able to be interchangeable, so I can have multiple of them, and easily move the arm around without unscrewing the whole base. To start I wanted to use an interlocking pin system, so I could slid it on and rotate it into place, so I started designing it. And very quickly I realized that this would be highly inefficient, as each pin would have limited size, and it could easily slide out. So I scrapped all that, and decided to start fresh. This time I decided to use a dovetail design, as it is super easy to both design, and to use in general. So I made a basic trapezoid on the top of my first baseplate, and created a matching sized cutout on the base of the arm (with tolerance). For the actual base plate I just made a simple square, with a slightly bigger length than the base body, and a hole in each of the corners for screws. This will allow my to create at least two, one for my desk and one for the wall, that I can bolt on and leave there and just remove the arm.
![Screenshot 2026-03-25 110911](https://github.com/user-attachments/assets/5c176333-fd61-4e60-86e0-2d0736f58eea)
![Screenshot 2026-03-25 110924](https://github.com/user-attachments/assets/2a9e3aa4-c4ca-4ba8-b2e7-7295015f25c1)

*Time Spent: 2.5 Hours*

-------------------------------------------------

**3/25/2026 3 PM - I added the wiring diagram**

Now that all the modeling is done, I decided to add my wiring diagram. So I researched, and ultimately decided to use EasyEDA, because it is free, web based, and very well liked. I first added on my Uno R4, and a basic power supply representation. I could not find the exact model of PCA9685 board that I am using, so I picked the closest one and added that as well. Then I went about connecting these two together, and to the power supply. After I ensured I did not have any wires crossed (quite literally) I added the MG995s to the diagram, in the actual PCA9685 I am using, the plug ins for all three servo wires are aligned, but in this board I found they are not. So I decided to just connect the wires to the literal power and signal wires they would be drawing from, even if they are in a different spot. I then saved it as a PDF and added that to my repository, and attached a separate screenshot here.
![Screenshot 2026-03-25 150108](https://github.com/user-attachments/assets/78b95068-590d-4ab8-94e6-64223869c3fe)

*Time Spent: 1.5 Hours*

--------------------------------------------------

**3/26/2026 - I made two separate assemblies**

Now that the majority of all the modeling was done, I decided to combine my parts into two separate assemblies, one with electronics, and one without. I started from the bottom up, inserting everything into the first assembly -the non-electronics one- and arranging them all in the orientation they are meant to be in. Most of it was pretty simple, adding parts and moving them around, I had a few slight hiccups with accidentally moving them after initial orientation, which in turn messed up the geometry of the original design. However they had simple solutions to ensure nothing would be ruined. After I completed the first assembly, I started work on the one with electronics. I found CAD models for the servos, boards, and the like on GrabCAD, and set to work adding them to a file. This proved to be a slightly more complicated process, as some parts of my designs had gotten messed up along the way, so I had to redo multiple things so it all would fit correctly. Since it would be slightly difficult to add wires twisting the directions they would need to be in the design, I decided to add all components except wires, and just make a separate wiring diagram. Note: my particular design has all electronic components hidden on the inside, they are there, just not open visible without taking it apart.
![Screenshot 2026-03-26 114048](https://github.com/user-attachments/assets/6c4046e6-7175-4bf4-9215-4f0ed846a007)
![Screenshot 2026-03-26 114119](https://github.com/user-attachments/assets/8a7f8cf1-ed40-4b7b-a099-fdee8e791601)

*Time Spent: 3 Hours*

**3/26/2026 3 PM - I added a simple cutout for bearing balls**

Secondly today, I realized I would want some bearing balls in the top portion of the base pieces, so they would rotate smoother and with less scraping. So I found some basic ones that fit my needs, and added them to my BOM with pricing and the link. I also realized that this brought my cost back up evenly to $180, as I found a cheaper part option the other day that lowered cost. Then I made a simple cutout in the top and bottom of my base body and base top pieces respectively, so everything would fit and turn smoothly.
<img width="1059" height="1003" alt="Screenshot 2026-03-26 145605" src="https://github.com/user-attachments/assets/1cc268e4-edf6-4eb8-aaa9-ce7e8d1b821b" />
<img width="1355" height="859" alt="Screenshot 2026-03-26 145551" src="https://github.com/user-attachments/assets/0e2d0895-7275-4138-a209-460d1a50aba6" />

*Time Spent: 30 Minutes*

**3/27/2026 - I wrote the Arduino firmware**

Now that everything manual is established, I went to work on the code. I will be writing some firmware to put on the Arduino Uno R4, and some additional Python code for precise calculations and smooth movement, along with a simple GUI for user-friendly control. To start, I built the Arduino code, I haven't had a lot of experience building INO files, but I did some research and got to work making it all function. I used the WiFiS3 library which is the Uno R4's built in library, and added the Adafruit_PWMServoDriver
library to use with the PCA9685 to control the servos. I decided to set it up so the commands could come in using ASCII with \n at the end acting as an 'enter' button, so it puts the bytes into cmdBuffer until it sees \n, then calls handleCommand to run it. Here is how I handled the PWM math. Since MG995 servos use standard RC PWM: 50Hz frequency and 20ms period, with pulse width between 500Us (0°) and 2500Us (180°), and a 12 bit counter, starting from 0 that's a total of 4096 ticks per period, which means the conversion is ticks = pulseUs * 4096 / 20,000, meaning the setPWM call sets the on ticks to 0 and the off tick to ticks, which produces ticks/4096 * 20ms pulse at the output pin.
<img width="2002" height="1227" alt="Screenshot 2026-03-27 104405" src="https://github.com/user-attachments/assets/2d1be920-c3c8-4509-b104-cd1eee73552a" />

*Time Spent: 2.5 Hours*

**3/27/2026 3 PM - I coded the Python script**

After completing the Arduino firmware, I got started on the Python program, which will be mostly for the angle input and GUI, with some added benefits. i decided to put calculation, communication, and visualization into three separate lanes, the Main Thread handles drawing the Tkiinter window, which was a process to figure out, because Tkinter doesn't like multi-threading, so I used afteridle to 'drop' and 'pick up' the thread. Then the Motion Thread ensures it runs at 50Hz, so the servos dont just jump to the target, but rather glide smoothly to the set position. Lastly an AI Socket Thread that sits and waits for commands, it doesn't move the servos itself, it just updates the targetangle variable, so the Motion Thread can notice it and act upon it. Next I used an IK solver to work trigonometry to turn a 3D point into servo degrees. it does this by treating the arm as a triangle, and using the Law of Cosines to calculate the interior angle of the elbow. It also has a simple 'elbow up' flag, to ensure it does not try to reach the selected position whilst flipping the orientation back and forth. Also some simple coordinate mapping ensures that the servos understand that their horizontal (90 degrees) is actually up, and 0 degrees is actually flat, it does this by using 90 - degrees(rad_angle) to translate the servo position correctly to what we see vs what the servo thinks. Then I added all the filler and def commands, and did brief revising to have it be somewhat clean, and added simple comments for most commands to help explain functions.
<img width="3223" height="1679" alt="Screenshot 2026-03-27 153052" src="https://github.com/user-attachments/assets/1151f419-8f26-4409-b94c-6cf5f403ce65" />

*Time Spent: 4 Hours*

**3/29/2026 - I finished my repository and added licenses**

Lastly for the planning portion of this project, I wrapped up my GitHub Repository. This included editing the README with text sizes and correct images, adding simple explanations to my other folders for extra direction, and editing my journal and BOM files. I then created a license file, and added all the specifics of how I wanted it to be used, including adding an MIT license for the code, and a CC BY-SA 4.0 for everything else. To finish it off I did a quick once over of every file, image, folder, and the like, just to ensure that everything was in place how I wanted it to be.
![Screenshot 2026-03-29 141833](https://github.com/user-attachments/assets/c0306f16-8489-422f-9d57-3e99d01c37ab)

*Time Spent: 1 Hour*

**4/9/2026 - I edited designs and removed a soldering iron from my BOM**

I decided to edit the servo horn securing situation, so the parts would hold together without glue or other methods, and can be
easily removed and edited as needed. I also updated my BOM to remove a soldering iron from my costs, as that is not a part of my materials list.
<img width="1359" height="1167" alt="Screenshot 2026-04-09 114540" src="https://github.com/user-attachments/assets/57b31477-015e-4568-a818-8caffe6a429d" />

*Time Spent: Half an Hour*

**4/26/2026 - I edited my BOM with better price management**

So after my initial project review, I was encouraged to use better cost optimization and find better prices. So I searched for a while, found some better deals and prices, and added everything to both my BOM.csv file and in my readme. I also removed filament from my BOM, as I found out it would not be funded. This lowered my total to $51.00 USD, or $107.00 USD including filament, which I will buy myself.
<img width="2000" height="859" alt="Screenshot 2026-04-26 141846" src="https://github.com/user-attachments/assets/615dd833-3063-4008-9e3f-e31dc28f7f4c" />

*Time Spent: 1 Hour*

**6/13/2026 - I started printing!**

So I finally got the filament, and decided to start on printing the parts from the ground up (mostly).
I started off with the 'base_body' piece, which is the main cylindrical body that will hold the power converter, arduino board, and the base servo for pitch (left-right) movement.
I pulled the design into the slicer, and oriented it to lay on it's side, so that and tension on the piece will not just rip between the layers and snap it. I used 75% gyroid infill, for high density but without wasting material. Then I added two pauses to the print, to switch the filament from black to green, then back to black to get a nice center green stripe. It used about 200g of filament and took a bit over 6 hours, and turned out very well with some light support scarring but no other issues.
<img width="1277" height="737" alt="Screenshot 2026-06-13 190903" src="https://github.com/user-attachments/assets/9e9a76f6-7c04-4447-9394-11f25a3f807d" />
<img width="1158" height="895" alt="WIN_20260613_19_17_12_Pro" src="https://github.com/user-attachments/assets/2d6d96d8-3b1f-4776-baa0-faeca0e3bd16" />

*Time Spent: 2 Hours*

**6/14/2026 - I iterated and printed the next part**

So for the next part, the 'base_top' I wanted to print it on its side for better integrity. I got it all sliced, and it only used a little more support than it would if it was in the suggested orientation. I got it all set up and started printing it. About 3 hours in, I went to check on it, only to find that it spaghettied horribly (filament strands everywhere and trying to print on thin air). So I modified the orientation, added beefier supports, and edited settings for a hopefully smoother print. After another 3 hours of printing, at the exact same second it failed again. I still have no idea why this happened and even the footage doesn't reveal it. For this one however, the completed portion was more salvagable than its successor, so I was able to test attaching half of it to the previous piece. This revealed that although they would fit together, they would not lock tight enough, and the clips were so weak that even removing support structure snapped two of them. So I took a step back, fixed the compromised faces in CAD, and switched the part orientation instead to the suggested side. The reasons I didn't do this originally were 1. It could make the part slightly less strong under load (I raised the wall count and infill to compensate) and 2. I couldn't put that nice green stripe up the center like the last piece (I will have to later glue on a piece of green or just go without it). Ultimately the part turned out and worked very well with just some minor sanding.
<img width="1274" height="737" alt="Screenshot 2026-06-13 165454" src="https://github.com/user-attachments/assets/326a76e3-3324-4c40-ad09-33c895ce29dc" />
<img width="1555" height="924" alt="WIN_20260614_17_00_31_Pro" src="https://github.com/user-attachments/assets/afc67621-dc78-40ef-ae11-fa2e6d5a45ad" />
<img width="1270" height="741" alt="Screenshot 2026-06-14 171107" src="https://github.com/user-attachments/assets/ab997fbb-e04a-4eb7-b592-b0b4ec855055" />
<img width="992" height="929" alt="WIN_20260614_16_46_46_Pro" src="https://github.com/user-attachments/assets/67ea11a0-b43f-4641-a396-7f669e4a9e77" />

*Time Spent: 4 Hours*


**6/16/2026 - I made my best 3D print ever!**

The next piece in my lineup was the 'arm_bottom' piece, which is the center of the arm, and the only piece featuring the servo moving it and its own servo rotating the same way! This piece was fairly simple to setup, I just used the auto orientation and added two simple pauses for the color change. I also lowered the infill to 65%, because this part is so solid that any more than that is just wasting material. It printed in a few hours, and everything went perfectly. When it finished, I was in shock by how perfectly it came out. With no supports and no odd angles, it had the perfect setup to print amazing, and it did not disappoint. There were no botched sides, no random strings, and no print scars whatsoever. It truly is a masterpiece.
<img width="1278" height="740" alt="Screenshot 2026-06-16 114506" src="https://github.com/user-attachments/assets/3c05d281-857f-4e25-b246-46daaf58e61c" />
<img width="1920" height="1080" alt="WIN_20260616_12_49_25_Pro" src="https://github.com/user-attachments/assets/f8fc7f89-be4a-453b-bbed-c7cd413ba17c" />

*Time Spent: 1.5 Hours*


**6/23/2026 - I made the next piece**

Next up to create was the 'arm_top' which is a very important piece, because it will hold the fingers, gears, and the servo to move those. It is also set up in such a way that it is rather difficult to print, as there are multiple different angles and parts to it. I set this piece up using a much lower infill of 45%, because it is not taking as much stress from multiple angles. The first version used auto orientation, and pretty similar support settings to it's predecessor. It got done with the first half perfectly, but about 2 hours in, it completely flopped. Stringing everywhere, sides peeling off the bed, and messed up sides. So I messed with the support settings for a bit, changed the angle to fully sideways, and wiped off the build plate for better adhesion. This one worked perfectly, it came out smooth and the supports peeled right off. I realized after the fact that I had not done a thorough wipe down of the plate, and that was likely why so many prints had failed.
<img width="1276" height="742" alt="Screenshot 2026-06-16 114432" src="https://github.com/user-attachments/assets/e7099517-9ffc-4e1c-b8a0-4f2502cab955" />
<img width="1920" height="1080" alt="WIN_20260616_12_49_51_Pro" src="https://github.com/user-attachments/assets/1fe3eec1-6964-4c7d-9740-19a8a683cc9d" />

*Time Spent: 2.5 Hours*


**6/23/2026 3:59 PM - I printed the gears green**

After all the previous prints, it was very satisfying to have a simple print that basically couldn't fail: The gears. They are flat on the top and bottom, rather small, and overall a simple structure. I set them up in the slicer at 80% infill since they will be under a lot of strain, and set up the printer with just green filament for them. Since they will be laying down, and that is the orientation I am printing them, doing multiple colors would be useless. So i did just green to get a nice color pop for the top, and because that is what i have the most of. They printed great, super quick and no issues, and they fit perfectly on the previous piece. Another print down.
<img width="1279" height="740" alt="Screenshot 2026-06-16 114535" src="https://github.com/user-attachments/assets/c830a157-1376-4e0b-88c3-fef85d14179e" />
<img width="1920" height="1080" alt="WIN_20260623_15_53_42_Pro" src="https://github.com/user-attachments/assets/ba3830f1-fb9e-45ee-ade1-70c122a799aa" />

*Time Spent: 45 minutes*


**6/24/2026 - I created the fingers**

The next piece to do was the fingers. I knew it would be crucial for these to print well, as they are doing all the -quite literally- heavy lifting. So I set them up in the slicer, using the same 80% infill as the last piece for strength, and 4 walls for thickness. I got them set up to print, and just as they started, I realized that I had forgotten to add a color switch. I went to just add it, but I realized it would not look right with the rest of the pieces, and at the same time I noticed how bad the orientation was. They were vertical, meaning tension on them could pull them apart between the layers, and printing time would just be very long. So I reoriented them (I dont have a picture of that) and added the color change. They printed great, and fit in the slots on the 'arm-top' perfectly.
<img width="1276" height="736" alt="Screenshot 2026-06-16 114547" src="https://github.com/user-attachments/assets/e5c7d9ee-5659-400a-a7ab-c0f035d49fa0" />
<img width="1920" height="1080" alt="WIN_20260623_16_17_50_Pro" src="https://github.com/user-attachments/assets/d99022fe-8286-45c8-8063-895d0b1dba46" />

Time Spent: 2 Hours


**6/26/2026 - I made the final piece!**

Then came the time to create: The last piece, the 'base_bottom'. Which is a very crucial piece, as this is the actual base that the whole arm will be mounted on. The first version is actually pretty simple, it uses a dovetail joint to nicely slide onto the body, and 4 simple holes to be screwed into the desired surface. Later on there will be multiple different bases set up at different locations, so I can just slide the arm off one base and onto the next. But for now, this simple one will work great for testing! I got it sliced up at 80% infill and 4 walls for high strength, and oriented it on it's side. Which was rather sad to do, because it would have been great to print it fast and flat, but having good layer direction is better in this case. I first decided to print a quick test piece of the dovetail joint, because it worked great in the assembly, but tolerances change things. The first one did not fit at all, it was just a bit misaligned and it made the whole thing wayyy off. The second one was better, but it was very very tight, not really what you want for quick switchability. Then the final test piece worked great, so I printed the final version with those updated measurements. It came out very well, and fit as expected.
<img width="1277" height="743" alt="Screenshot 2026-06-26 164732" src="https://github.com/user-attachments/assets/769fa5cf-9841-416a-9052-76fac5cfb98c" />
<img width="1920" height="1080" alt="WIN_20260626_16_36_20_Pro" src="https://github.com/user-attachments/assets/d87d1149-07a8-45ec-9cdd-2b03d40907f7" />

*Time Spent: 1.5 Hours*

**7/4/2026 - I received the parts! Well, most of them.**

My electronics finally came in! They arrived intact, and at first it seemed that they had all successfully arrived. But when I got to the end of the package, I saw there was no AC-DC converter(power cable whatsoever. Thankfully all the other components came in and looked great, and it was great to see them all lain out on my workbench. Unfortunately the package weight suggested that potentially the cable was at one point in the package, and must have been later lost in transit or stolen. So I reached out to AliExpress and the manufacturer(which I didn't expect to hear back from). And began the waiting process of getting the refund to order a new one. The next day I checked on the refund status, only to realize that they wanted 'more proof' that I had not received the item. Which is kinda difficult to prove, as I literally did not receive it. So I just did my best to emphasize the fact that I received the other 7 items, and the package weight showed that at one point the cable was likely inside. For now I will continue to contact the manufacturer and the shipping company, and hope one of these three will respond so I can go about purchasing a new part. 
<img width="1918" height="857" alt="WIN_20260704_18_59_43_Pro" src="https://github.com/user-attachments/assets/8b50a605-8d4b-4b0f-b718-d01a0615f953" />
<img width="815" height="540" alt="Screenshot 2026-07-04 190030" src="https://github.com/user-attachments/assets/a8bd2456-6eef-4ca9-a264-2ac7ea106b18" />

*Time Spent: 1 Hour*


**7/6/2026 - I tested the parts**

Now that most of my parts were in, it was time to test them and hope my tolerances were enough. And immediately upon pulling the servos out of the bag, I could see that they were not quite as described. On each one on the side where the wires come out, there was a little plastic knob protruding from the side to cover the wire entrance. This wouldn't have been an issue, except that this was not on any of the seller images(I went back and checked) so I had not factored it into my designs. And unfortunately this meant that the servos would not fit into any of the parts right away. Thankfully on the three of the pieces it was fairly simple to carve out a slot, with just a bit of time and elbow grease. And all in all the other parts appeared to look good, and there was nothing else that really needed fitting tests, so everything should go as planned. --see next journal entry because one piece did need to be redone but it is a long process so I'll put it in a separate entry--
<img width="1920" height="1080" alt="WIN_20260706_12_52_27_Pro" src="https://github.com/user-attachments/assets/53a57496-32ea-4f1e-bd2c-ec1706d3cb38" />
<img width="1920" height="1080" alt="WIN_20260706_13_02_02_Pro" src="https://github.com/user-attachments/assets/7c907c83-aafc-4459-88e7-1cdf10c1d792" />

*Time Spent: 2 Hours*


**7/6/2026 2 PM - I redesigned a part**

So unfortunately since the servos had an unexpected piece attached, I had to redesign one of my parts. Which wasn't all too bad, considering that there were some other slight issues with it that could've been ignored, but were worth fixing while I was at it. So I pulled the design back up in fusion, and edited a bunch of the positioning so everything fit better. I got it printing right away and it seemed to turn out as expected(9 hour print) but then the realization hit, in my midnight redesign spree I had accidentally shifted the space for the servo a half-inch in the wrong direction. So now instead of being 0.5in off alignment, it was a full inch off, which wouldn't even partially work. So I went back to the drawing board, undid all my work, and shifted it back in the other direction. This turned out to make the space for the servo stick slightly out of the side of the part, which was something I was really trying to avoid, since this was meant to be a 'sleek and adaptable' robotic arm. This lead to more redesigning to cover up the slot, and in turn actually gave the piece a slightly new look that I actually enjoyed. And since the new design gave the circular top portion more support, and that was the only part that was really under any stress, I was able to lower the infill to just 35% (down from 45%) which basically compensated for the added material of the redesigned portion.
<img width="1920" height="1080" alt="WIN_20260706_14_23_59_Pro" src="https://github.com/user-attachments/assets/983e0d77-12c8-4c97-9058-0a26393e3e3d" />
<img width="1277" height="740" alt="Screenshot 2026-07-06 142203" src="https://github.com/user-attachments/assets/fe8b9b25-d61f-4540-9945-9a82b18359a0" />

*Time Spent: 2.5 Hours*


**7/16/26 - I designed and printed the feet**

Next thing to create was the 'base_feet', which I decided to design to literally slide onto my current base piece, for easier connection and less redesigning. I started off with just the basic corner shape and a cylinder in the corner to slot in nicely, then the foot coming off the side for the stability. It printed quick and came out well. The tolerance was absolutely perfect, like I genuinely have only ever achieved this perfect of a fit once or twice, and this is one of them. And since it fit, I decided to head back to fusion and give it a little bit of a stylistic look, and it also will increase the strength when under a lot of tension from the leaning arm. 
<img width="4284" height="5712" alt="IMG_2663" src="https://github.com/user-attachments/assets/f5cb3c7b-42f6-483b-96d8-7442fd5a3410" />
<img width="4284" height="5712" alt="IMG_2664" src="https://github.com/user-attachments/assets/5db41673-1e4c-4481-b2f0-6448b085018f" />

*Time Spent: 1 Hour*


**7/17/26 - I modified a design for usability**

So I really liked my design for the base pieces, using a dovetail shape for simple moving and replacing. But there was one slight issue, the base_body could literally just slide off the side of the dovetail when the arm was moving. And I knew this was a point of concern, but I hadn't really decided how to fix it until now. Really it was quite simple, I just cut out small slots on both ends of the base_bottom dovetail, and extended the sides a little past the size of the base_body. Then I made a couple little pins that could slide in those slots, and keep the whole thing stuck tightly together, while maintaining the simple switch out I wanted.
<img width="4284" height="5712" alt="IMG_2665" src="https://github.com/user-attachments/assets/e786b28b-4bbb-4bf1-bc79-2e01cdc48602" />
<img width="4284" height="5712" alt="IMG_2666" src="https://github.com/user-attachments/assets/0e84beb0-3cc4-4b7d-9e50-da0d47c45153" />
<img width="4032" height="3024" alt="IMG_2667" src="https://github.com/user-attachments/assets/aaed3267-c071-4dcb-9d2e-455e50c42fdf" />

*Time Spent: 45 Minutes*


**7/21/26 - I tested and fixed the code**

So now that my replacement power source came in(the first one was missing from the order) I could finally test out the whole setup before assembly! So i got it all wired, double checked my wires, and flashed the code. The arduino instantly displayed it's IP address, so i plugged that into the python code to run the whole system. The python code initaited beautifully, and the GUI looked great. But of course, no system ever works the first time, or usually the second either. And alas, when I moved the arm position in the GUI, i got absolutely no reaction from the servos. My first thought was that the power source wasn't working, so I redid the wiring on that multiple times, still nothing. I did some more research on possible issues, and it seemed like the only viable answer was that either the power connection was bad, or the PCA module was DOA(dead on arrival). But in a moment of clarity, I decided to write a test script that simply moved all the servos with no initation. And that worked perfectly, they all spun and did exactly what they were supposed to. So then I knew it was an issue with the python code, I spent over an hour debugging and redoing things, but for the most part everything seemed good, but the tests still failed. Finally, after hours of testing, I saw my ridicously obvious mistake, I had forgotten to click the 'connect' button in my GUI. Literally a simple click had wasted hours of my time and a significant amount of AI token usage. So I reran the program, clicked the connect button, and it still didn't work. This time I was able to find the issue much sooner, again a stupidly simple fix of the power converter plug falling out of the outlet. After plugging back in and reinitializing, it ran perfectly! All the servos turned as intended and the GUI functioned correctly! After that I spent a little bit of time just editing the code to make the servos spin more smoothly, and a couple other simple updates, but it all worked as intended!
<img width="4284" height="5712" alt="IMG_2670" src="https://github.com/user-attachments/assets/8327fd1d-5b91-4707-8101-ac6f0e05cebf" />
<img width="5712" height="4284" alt="IMG_2671" src="https://github.com/user-attachments/assets/c10b1f65-b47a-4619-ba76-2fbe180810c7" />

*Time Spent: 2.5 Hours*


**7/22/26 - I started assembly!**

This was my first day of true assembly! Finally after months of work getting to actually put the parts together and set it all up! So I started off with making sure all the servo horns fit in the slots, but of course, they did not. Even with scaling and tolerances and everything they did not fit. So i went through the tedious process, of using a soldering iron to melt out layers of plastic on the inside of the parts. Even after doing this for a while on one part, it still did not fit whatsoever. Then I finally had a 'duh' moment, and realized I could just melt down the servo horn itself to fit better. So in another 15 minutes I had one servo horn that fit perfectly, and got started on the next, which went so much faster with this new technique. Before too long I had them all fitting perfectly and nicely glued in place. I also got the PCA module with it's power plug and the arduino with it's battery all glued into the base.
<img width="240" height="320" alt="new2" src="https://github.com/user-attachments/assets/568c2e70-e60c-480e-90bc-9808a06898fd" />
<img width="320" height="280" alt="new" src="https://github.com/user-attachments/assets/00490abb-8a10-4d58-99f4-6ec241732bfe" />

*Time Spent: 2 Hours*


**7/23/26 - I ran the wires and screwed everything in**

Now that I knew most of the parts would fit, the next step was to legnthen the servo wires and run them through each piece. This was a fairly simple and task, I just had to measure and estimate the length I would need for each servo to go from it's piece down to the base, and still have enough extra length so movement isn't restricted. Thankfully since the pack of jumper wires I ordered came with 40 of each male-male, male-female, and female-female wires, I could pretty easily connect each of the servo wires to the PCA module. I also took the time to after connecting each of the three wires, to go every 4 inches or so along them and tape them together in a nice line. This will make sure everything fits nice, looks nice, and no wires get mixed up. Then I just simply slotted each of the servos into place, and screwed them nicely in. For the last one(in the base) I did need to slighty rework it so it would align correctly and the top would close, but that wasn't too hard and didn't require reprinting. And as a last second thought, I decided to add a switch to the arduino battery, becuase otherwise it would always be left on and I didn't want to have to take it apart every night.

<img width="480" height="640" alt="old" src="https://github.com/user-attachments/assets/2a8fb982-dfa3-4bf0-9518-9a413f694efa" />
<img width="320" height="320" alt="IMG_2682" src="https://github.com/user-attachments/assets/76d2a68d-0522-4937-b668-ba9cad59545a" />
<img width="5712" height="4284" alt="IMG_2681" src="https://github.com/user-attachments/assets/bd8e61a6-be99-44ac-836e-030a5565e8f4" />

*Time Spent: 1.5 Hours*


**7/25/26-8/2/26 - I did the final steps!...and they failed**

So the last thing I had to do was screw it all together! And the process itself went quite well, everything attacked as desired, and nothing seemed largely faulty. But when I got it all assembled and started trying to use the GUI to rotate it, there were some obvious issues. Apparently when I had screwed on the pieces to the servos, I had forgotten to make sure the servo position was set to the corresponding angle I was screwing the arm piece on in, so the servo thought it was at 90 degrees but the arm was actually in the 160 degree positions. But that was a simple fix, and before too long I had it all set up correctly this time. And yet again there were issues, the code wasn't communicating correctly with the servos, meaning they moved very slowly at first, then flew towards the position, which would cause any arm to fall over, no matter the stability. So I refactored, and refactored, and refactored, again and again and again, just trying to get it to work how I envisioned. Finally after 5+ hours of work trying to fix it across multiple days, I decided to consult AI coding tools. And before too much longer there was steady progress, the arm would move more smoothly, and the angles were correct. Ultimately it just came down to the fact that the code is a bit beyond what I have truly learned, and I have no problem seeking help when I need it, and since no one in my family can code, obviously the AI came in handy to fix some issues.
<img width="240" height="320" alt="IMG_2725" src="https://github.com/user-attachments/assets/5d62b9d2-cbab-4bfb-81a9-6cd623d9f685" />
<img width="3825" height="1666" alt="Screenshot 2026-08-05 163447" src="https://github.com/user-attachments/assets/84804f4a-da92-48ee-9c86-b2fad7dd756d" />

*Time Spent: 5.5 Hours(across a couple days of doing the same things over an over)*


**8/5/26 - I printed two pieces**
So I realized that part of the reason the shoulder joint was having so much trouble was because the arm top piece was a bit too heavy, so I decided to reprint it at a much lower infill, since it really wasn't that structural of a piece and could have less strength. It was a simple and fast print, came out well, and I got it all switched out with the old one. It really helped, and gave the shoulder much more strength in general. Also I realized the clips for my base pieces wer starting to break due to being under too much stress, so I actually just snapped all of them off and designed a new piece to glue on that would fix that issue and actually give it a cleaner look. It didn't quite fit right the first time, but it was enough for some testing and the fixes were super simple, so I just threw together the fixed one and it went great.
<img width="3832" height="2016" alt="Screenshot 2026-08-07 112929" src="https://github.com/user-attachments/assets/083ee38d-d0ac-4e80-a7a8-f0766651cbeb" />
<img width="3834" height="1981" alt="Screenshot 2026-08-07 113136" src="https://github.com/user-attachments/assets/5d4328d9-1201-4e8c-be3e-029279a98774" />

*Time Spent: 1.5 Hours*
