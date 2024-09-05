# config.py

api_key = ""

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