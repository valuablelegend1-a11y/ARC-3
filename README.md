# ARC-3

## What it is:
My ARC-3 is a 3 DoF and 3 fingered robotic arm, designed to be sleek and powerful, while also providing complete adaptability. It will feature both interchangeable bases and not require connection to your computer, as it runs through WiFi. It is set up to have a smooth orange and black body, with all electronics and wiring safely hidden on the inside. It will be powered by an external power socket, using a PCA9685 module to handle current, and an Arduino R4 WiFi for the controller. For the movement it will have 4 MG995 servos, one to rotate the base (yaw) two as shoulder and elbow joints (pitch) and one more, to open and close the fingers using a gear system and a 2:1 ratio.

## How to use it:
To start off, you need to ensure weight distribution is good, I would place it in your desired location, then fully extend the arm horizontally. This will ensure that it is secure, whether you are wall mounting or using a desktop stand. Then you need to establish the code, specifically this project runs two codebases. One is firmware on an Arduino Uno R4 WiFi, and one is a Python program running on your computer. To start you need to upload the code to your preferred code editors, then in the Arduino code you must input your WiFi information. After you do that and upload the code, the board's IP address should be displayed in the serial monitor. You simply copy and paste that IP into the Python code, and you are ready to go. Upon running the code, a GUI should pop up on the screen, with simple controls and functions and a cool color scheme. You can control the ARC-3's position using the touchpad, hold the space key to close the claw, and the hold the control key to close it. 

## Why I am building this:
I am creating this project for a couple reasons, I don't have much CAD experience, so I am using this to learn more about the process, and how I can be more efficient with it. Ultimately to acheive my goals faster and more effectively. I also have little practice with wiring systems, I have done some light Arduino projects in the past, but nothing of this level. So I am doing my best to learn how it all works, and how I can put different things together to make something new. Another reason is to learn to code better, I have done some programming in Python, and barely scratched the surface in Arduino code, aka C/C++, so I am trying to put what I know together, and learn more along the way to expand my understanding of the languages. 

## Notes:
1. Total cost is aproximately $180.00 USD, this is including sales tax and extra shipping costs, however costs may shift depending on store circumstances.
2. The code is using advanced IK and trigonometry functions, which are things I have not have had much time to study, therefore they may be incorrect. If so please let me know, so I can correct any issues.
3. Any further suggestions as to design or improvements are highly encouraged and greatly appreciated.
4. My full assembly design titled 'assembly_with_electronics' *does* have electronics, but since I designed them to be safely tucked away from view, none of them are visible from the outside. 

Here is the full assembly screenshot, wiring diagram, and BOM in table format with links.

Assembly:
<img width="1341" height="1138" alt="Screenshot 2026-03-26 114048" src="https://github.com/user-attachments/assets/43d78876-010a-4fa5-9947-3038451f413d" />

Wiring Diagram:
<img width="2522" height="1412" alt="Screenshot 2026-03-25 150108" src="https://github.com/user-attachments/assets/36a4b16f-0ab9-4d22-b1bb-70d68d1c05db" />

BOM:
| Item | Quantity | Unit Price | Link | Notes |
| :--- | :--- | :--- | :--- | :--- |
| MG995 Servos (4 pack) | 1 | 16.99 | https://www.amazon.com/gp/product/B07NQJ1VZ2/ref=ewc_pr_img_6?smid=A2QTZX14X1D97I&th=1 | For Pitch Joints And Fingers |
| Black PETG Filament (1kg) | 2 | 13.99 |https://us.elegoo.com/products/rapid-petg-filament-1-75mm-colored-1kg?variant=43734204252341 | Main Color |
| Orange PETG Filament (1kg) | 1 | 16.99 | https://us.elegoo.com/products/rapid-petg-filament-1-75mm-colored-1kg?variant=43734204481717 | Secondary Color |
| Arduino Uno R4 WiFi | 1 | 27.50 | https://www.sparkfun.com/arduino-uno-r4-wifi.html | Controller |
| PCA9685 Servo Motor Driver | 1 | 6.99 | https://www.amazon.com/gp/product/B07ZNJRVHL/ref=ewc_pr_img_2?smid=A2Z10KY0342329&th=1 | Power Distribution |
| 5V 8A AC to DC Power Adapter | 1 | 18.49 | https://www.amazon.com/gp/product/B078RZBL8X/ref=ewc_pr_img_3?smid=AA0YO4F2UD50F&th=1 | High Current Supply |
| M/M Jumper Wires (20 pack) | 1 | 2.95 | https://www.sparkfun.com/jumper-wires-connected-6-m-m-20-pack.html | Wiring Extensions |
| Soldering Iron Kit | 1 | 25.99 | https://www.amazon.com/gp/product/B07XSHCY7P/ref=ewc_pr_img_4?th=1 | For Connecting Wires |
| DC Power Jack Adapter | 1 | 3.75 | https://www.sparkfun.com/dc-barrel-jack-adapter-female.html | For Power From Converter |
| F/F Jumper Wires (20 pack) | 1 | 2.75 | https://www.sparkfun.com/jumper-wires-connected-6-f-f-20-pack.html | Wiring Extensions |
| 20 Gauge Wire (10FT) | 1 | 9.99 | https://www.amazon.com/gp/product/B0CQFWZRVY/ref=ewc_pr_img_1?smid=AKGNN9YQ6U3GA&th=1 | For Connecting Converter To Board |
| Ball Bearings (20 Pack) | 1 | 5.60 | https://www.amazon.com/gp/product/B081SRSHLQ/ref=sw_img_1?smid=A1THAZDOWP300U&th=1 | For smooth rotation |
