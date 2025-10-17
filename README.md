# Why I built this and what it does  
I am a Computer Science student and I really like having all my calendars on my phone, integrated into one big calendar. The problem is my professors like to add every scheduled  
lecture to the calendar as an event. This really clougs up my calendar so I made this API gateway/Lambda to act as a middle man to filter out the non-assignments everytime its called.  
It is not set up to retain all assignment info, just due date, assignment title, and class. So if your looking to preserve more of that data, you will need to modify the code to include that.
### How to set up:  
1. Set up a lambda in AWS using lambda.py
   - You probably need to install the dependancies locally and upload a zip file
3. Set up API Gateway  
   - In the  gateway, you need to set the rout to GET /assignments  
   - You need to set timeout to at least 5 seconds (I did 30s)  
   - Set the integration to your lambda  
   - The link to enter into your calendar will be something like "https://[API_ID].execute-api.us-east-2.amazonaws.com/prod/assignments.ics"
