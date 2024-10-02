# config.py

api_key = ""
auto_apply = "No"
final_apply_button = "No"


profile = """
Results-driven software engineer with over 8 years of experience specializing in full-stack development, 
mobile app design, and cloud infrastructure. Proficient in a wide range of programming languages and 
frameworks including React, Node.js, and Flutter, with a strong focus on creating efficient, 
scalable solutions for both web and mobile platforms. Expertise in integrating cloud technologies 
such as AWS to optimize performance and reduce operational costs. Proven track record in leading 
cross-functional teams, mentoring junior developers, and managing complex projects from concept 
to deployment. Strong understanding of agile methodologies and test-driven development, 
with a focus on delivering high-quality, user-friendly applications. Adept at problem-solving, 
collaborating with stakeholders, and aligning technical solutions with business objectives 
to drive growth and innovation.

CORE COMPETENCIES

Languages: JavaScript, Python, Java, HTML5, CSS3
Web Development: React, Node.js, RESTful APIs, Microservices
Mobile Development: Flutter, React Native
Cloud Technologies: AWS, Azure, Google Cloud
Databases: MongoDB, MySQL, PostgreSQL
DevOps: Jenkins, Docker, Kubernetes
Methodologies: Agile, Scrum, Test-Driven Development
Version Control: Git, GitHub, Bitbucket
Soft Skills: Leadership, Collaboration, Communication
PROFESSIONAL EXPERIENCE

Senior Software Engineer – Tech Solutions Inc., Chicago, IL | June 2018 – Present
Led a team of engineers to develop a scalable e-commerce platform, reducing costs and improving performance.

Software Engineer – Innovatech Solutions, Springfield, IL | August 2014 – June 2018
Developed client-facing web applications, improving project completion rates and system efficiency.

EDUCATION
Bachelor of Science in Computer Science – University of Illinois, Champaign, IL | May 2014
Dean’s List (2013-2014), Graduated with Distinction

CERTIFICATIONS
AWS Certified Solutions Architect – Amazon Web Services, 2019
Certified Scrum Master – Scrum Alliance, 2017

ADDITIONAL INFORMATION
Languages: English (Native), Spanish (Conversational)
Hobbies: Hiking, Guitar, Open-Source Contributions
"""

profile_answer_questions = """
 Any date and time is fine for interview.
 Have you worked for this company before: No
 Answer No for all have you ever worked for question
 I am completely flexible to work any day, any time, in office, remote, hybrid or any.
 My full name: John Smith
 Date of birth: 26/11/2000
 My email: johnsmith@gmail.com
 Planning to relocate
 Mobile: 8888888888
 What proof of work eligibility can be provided:Sharecode
 I was not referred by anyone to the job.
 I am not a past employee. I do not have any relatives or family members working in the company.
 Expected salary: 26000
 Salary Currency: British Pound (GBP)
 Are you authorized to work in the jobs location/country: Yes
 Are you authorized to work in the job's location?: Yes
 Type of job looking for: Permanent - Full-time, Permanent - Part-time
 Notice period length: 1 month
 Preferred job location: On-site, Hybrid, Remote
 When will you be able to join: 06/10/2024
 Education: 1)Bachelor of Science in Computer Science – University of Illinois, Champaign, IL | Graduated May 2014
 Highest level of education: Bachelors
 Languages known: English, Spanish, French
 Age: 24
 Agreeable to all pre-employment checks, has valid passport and work permit.
 Linkedin profile: www.linkedin.com/in/johnsmith343432
 Previous job titles: 

 1) Senior Software Engineer – Tech Solutions Inc., Chicago, IL | June 2018 – Present

 2) Innovatech Solutions, Springfield, IL | August 2014 – June 2018


Are you legally allowed to live and work in the country?: Yes
Are you currently volunteering?: No
Have you reached normal school leaving age?: Yes                 
Where did you hear about this role?: Google 
Do you have a personal relationship or friendship with any current employee?: No
Have you worked here before?: No
Have you got any disability?: No
Are you a Veteran, Reservist or member of the Army Cadet Force, Air Training Corps or Sea Cadet Corp?: No
Are you unemployed and not currently in employment or undertaking training?: No
Please indicate your professional registration status: Not required for this post


        """






template_path = "Template.docx"
current_resume = "Current - resume.docx"

job_search_keywords = [
    "Full-Stack Developer", "Software Engineer", "React Developer",
    "Node.js Developer", "Mobile App Developer", "Flutter Developer",
    "Cloud Engineer", "DevOps Engineer", "AWS Specialist", "Agile Developer"

]

pagination_limit = 3

master_csv = "master_job_listings.csv"
latest_csv = "latest_job_listings.csv"


chrome_experimental_options = {
    "disable-blink-features": "AutomationControlled",
    "detach": True
}

resume_folder = "Resumes"

placeholders = {
    "profile_placeholder": "<*profile*>",
    "skills_placeholder": "<*skills*>"
}

# URL for Indeed homepage
indeed_homepage_url = "https://uk.indeed.com/?from=gnav-homepage&from=gnav-util-homepage"

# Replace text format
font = 'Times New Roman'
size = 12
bold = False